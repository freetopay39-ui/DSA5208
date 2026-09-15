import argparse
import os

from datetime import (
    datetime,
    timezone,
)

from .workloads import (
    RUNNERS,
    prepare,
)

from .checkers import (
    CHECKERS,
    load,
)


def new_run_id():
    return datetime.now(
        timezone.utc
    ).strftime(
        "run-%Y%m%dT%H%M%SZ"
    )


SCENARIO_ROUTES = {
    "normal": {"source": "n1", "target": "n3"},
    "node_stop": {"source": "n1", "target": "n2"},
    "partition_majority": {"source": "n1", "target": "n2"},
    "partition_minority": {"source": "n3", "target": "n3"},
    "partition_cross_side": {"source": "n1", "target": "n3"},
}


def make_clients(logger, routes, client_factory=None):
    """Connect only to this scenario's coordinators, once per unique node."""
    if client_factory is None:
        from .client import NodeClient

        client_factory = NodeClient

    by_node = {}
    try:
        for node in routes.values():
            if node not in by_node:
                by_node[node] = client_factory(node, logger)
    except Exception:
        close_clients(by_node)
        raise
    return {role: by_node[node] for role, node in routes.items()}


def close_clients(clients):
    closed = set()
    for c in clients.values():
        if id(c) in closed:
            continue
        closed.add(id(c))
        try:
            c.close()
        except Exception:
            pass


def add_common(parser):
    parser.add_argument(
        "--model",
        choices=[
            "ryw",
            "mr",
            "mw",
            "wfr",
        ],
        required=True,
    )

    parser.add_argument(
        "--history",
        required=True,
    )

    parser.add_argument(
        "--log",
        required=True,
    )

    parser.add_argument(
        "--run-id",
        default=None,
    )


def main():
    parser = argparse.ArgumentParser()

    sub = parser.add_subparsers(
        dest="cmd",
        required=True,
    )

    p_prepare = sub.add_parser(
        "prepare"
    )

    add_common(
        p_prepare
    )

    p_run = sub.add_parser(
        "run"
    )

    add_common(
        p_run
    )

    p_run.add_argument(
        "--scenario",
        choices=list(SCENARIO_ROUTES),
        default="partition_cross_side",
    )

    p_run.add_argument(
        "--write-cl",
        choices=[
            "ONE",
            "QUORUM",
            "ALL",
        ],
        default="ONE",
    )

    p_run.add_argument(
        "--read-cl",
        choices=[
            "ONE",
            "QUORUM",
            "ALL",
        ],
        default="ONE",
    )

    p_run.add_argument(
        "--partition-verified",
        action="store_true",
    )

    p_check = sub.add_parser(
        "check"
    )

    add_common(
        p_check
    )

    args = parser.parse_args()

    os.makedirs(
        os.path.dirname(
            args.log
        ) or ".",
        exist_ok=True,
    )

    if args.cmd == "check":
        rows = load(
            args.log,
            args.history,
            args.model,
        )

        result, reason = (
            CHECKERS[
                args.model
            ](
                rows
            )
        )

        print(
            f"result: {result}"
        )

        print(
            f"reason: {reason}"
        )

        return

    # Checking saved JSONL and displaying CLI help require no database driver.
    from .client import Logger

    logger = Logger(
        args.log
    )

    clients = {}
    run_id = args.run_id or new_run_id()
    # Preparation always happens before a fault: ALL writes through n1.
    # MW/WFR have no preparation writes and need no connection here.
    routes = (
        ({"source": "n1"} if args.model in {"ryw", "mr"} else {})
        if args.cmd == "prepare"
        else SCENARIO_ROUTES[args.scenario]
    )

    try:
        try:
            clients = make_clients(logger, routes)
        except Exception as exc:
            logger.write({
                "run_id": run_id,
                "history_id": args.history,
                "model": args.model,
                "scenario": getattr(args, "scenario", "prepare"),
                "operation_id": -1,
                "phase": "setup",
                "operation": "connect",
                "routing": routes,
                "status": "connection_error",
                "error_type": type(exc).__name__,
                "started_utc": datetime.now(timezone.utc).isoformat(),
            })
            raise

        if args.cmd == "prepare":
            output = prepare(
                clients,
                run_id,
                args.history,
                args.model,
            )

        else:
            output = (
                RUNNERS[
                    args.model
                ](
                    clients,

                    run_id=run_id,

                    history=args.history,

                    model=args.model,

                    scenario=args.scenario,

                    write_cl=args.write_cl,

                    read_cl=args.read_cl,

                    routing=routes,

                    fault_verified=(
                        args.partition_verified
                    ),
                )
            )

        if not output:
            print(
                "no prepare step required for this model"
            )

        for r in output:
            print(
                r["operation_id"],
                r["phase"],
                r["operation"],
                r["key"],
                r["status"],
                r["actual_coordinator"],
                r["returned"],
            )

    finally:
        close_clients(
            clients
        )


if __name__ == "__main__":
    main()
