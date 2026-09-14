import argparse
import os

from datetime import (
    datetime,
    timezone,
)

from .client import (
    Logger,
    NodeClient,
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


def make_clients(logger):
    return {
        "n1": NodeClient(
            "n1",
            logger,
        ),

        "n3": NodeClient(
            "n3",
            logger,
        ),
    }


def close_clients(clients):
    for c in clients.values():
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

    logger = Logger(
        args.log
    )

    clients = {}

    try:
        clients = make_clients(
            logger
        )

        run_id = (
            args.run_id
            or new_run_id()
        )

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
