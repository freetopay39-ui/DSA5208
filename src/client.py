import json, os, time
from datetime import datetime, timezone

from cassandra import (
    ConsistencyLevel,
    OperationTimedOut,
    ReadTimeout,
    Unavailable,
    WriteTimeout,
)
from cassandra.cluster import (
    Cluster,
    EXEC_PROFILE_DEFAULT,
    ExecutionProfile,
    NoHostAvailable,
)
from cassandra.policies import (
    FallthroughRetryPolicy,
    WhiteListRoundRobinPolicy,
)
from cassandra.query import SimpleStatement


IPS = {
    "n1": "10.20.0.11",
    "n2": "10.20.0.12",
    "n3": "10.20.0.13",
}

CLS = {
    "ONE": ConsistencyLevel.ONE,
    "QUORUM": ConsistencyLevel.QUORUM,
    "ALL": ConsistencyLevel.ALL,
}


class Logger:
    def __init__(self, path):
        self.path = path
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

    def write(self, row):
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            f.flush()
            os.fsync(f.fileno())


class NodeClient:
    def __init__(self, node, logger, timeout=10.0):
        self.node = node
        self.ip = IPS[node]
        self.logger = logger
        self.timeout = timeout

        profile = ExecutionProfile(
            load_balancing_policy=WhiteListRoundRobinPolicy([self.ip]),
            retry_policy=FallthroughRetryPolicy(),
            request_timeout=timeout,
        )

        self.cluster = Cluster(
            contact_points=[self.ip],
            connect_timeout=5,
            execution_profiles={
                EXEC_PROFILE_DEFAULT: profile
            },
        )

        self.session = self.cluster.connect()

    def close(self):
        self.cluster.shutdown()

    def execute(
        self,
        meta,
        op_id,
        phase,
        operation,
        key,
        cql,
        params=(),
        cl="ONE",
        input_value=None,
        dependency=None,
        mutation_timestamp=None,
        diagnostic_cl=None,
    ):
        stmt = SimpleStatement(
            cql,
            consistency_level=CLS[cl],
            retry_policy=FallthroughRetryPolicy(),
        )

        start_utc = datetime.now(
            timezone.utc
        ).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        t0 = time.perf_counter()

        status = "ok"
        err = None
        returned = None
        actual = None

        try:
            rs = self.session.execute(
                stmt,
                params,
                timeout=self.timeout,
            )

            host = getattr(
                rs.response_future,
                "coordinator_host",
                None,
            )

            actual = (
                getattr(host, "address", None)
                if host
                else None
            )

            if operation == "read":
                row = rs.one()

                returned = (
                    dict(row._asdict())
                    if row is not None
                    else None
                )

        except Unavailable as e:
            status = "unavailable"
            err = type(e).__name__

        except ReadTimeout as e:
            status = "read_timeout"
            err = type(e).__name__

        except WriteTimeout as e:
            status = "write_timeout"
            err = type(e).__name__

        except OperationTimedOut as e:
            status = "client_timeout"
            err = type(e).__name__

        except NoHostAvailable as e:
            status = "connection_error"
            err = type(e).__name__

        except Exception as e:
            status = "connection_error"
            err = type(e).__name__

        row = {
            **meta,

            "operation_id": op_id,
            "phase": phase,
            "operation": operation,
            "key": key,

            "input": input_value,
            "returned": returned,
            "dependency": dependency,

            "actual_statement_cl": cl,
            "diagnostic_cl": diagnostic_cl,

            "requested_coordinator": self.ip,
            "actual_coordinator": actual,

            "mutation_timestamp": mutation_timestamp,

            "started_utc": start_utc,

            "duration_ms": round(
                (time.perf_counter() - t0) * 1000,
                3,
            ),

            "status": status,
            "error_type": err,
        }

        self.logger.write(row)

        return row
