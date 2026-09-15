"""Offline regression tests; no Cassandra process or third-party packages needed."""

import contextlib
import io
import json
from pathlib import Path
import subprocess
import sys
import types
import unittest
import uuid
from unittest.mock import patch

from src import checkers, run, workloads


@contextlib.contextmanager
def test_directory():
    # Use inherited workspace permissions; Windows sandbox accounts may not
    # be able to reopen TemporaryDirectory's owner-only (0700) directories.
    root = Path(__file__).resolve().parent
    directory = root / ("_test_" + uuid.uuid4().hex)
    directory.mkdir()
    try:
        yield directory
    finally:
        assert directory.resolve().is_relative_to(root)
        for item in directory.iterdir():
            item.unlink()
        directory.rmdir()


class FakeClient:
    def __init__(self, node, logger):
        self.node = node
        self.close_count = 0

    def close(self):
        self.close_count += 1

    def execute(self, meta, op_id, phase, operation, key, cql,
                params=(), cl="ONE", input_value=None, dependency=None,
                mutation_timestamp=None, diagnostic_cl=None):
        values = {"x": "v1", "a": "original-post", "b": "dependent-write"}
        return {
            **meta,
            "operation_id": op_id,
            "phase": phase,
            "operation": operation,
            "key": key,
            "status": "ok",
            "actual_coordinator": self.node,
            "actual_statement_cl": cl,
            "returned": {"value": values[key]} if operation == "read" else None,
        }


class ScenarioRoutingTests(unittest.TestCase):
    def test_every_model_uses_only_the_scenario_coordinators(self):
        # Expected routes are deliberately independent of SCENARIO_ROUTES.
        cases = {
            "normal": ("n1", "n3"),
            "node_stop": ("n1", "n2"),
            "partition_majority": ("n1", "n2"),
            "partition_minority": ("n3", "n3"),
            "partition_cross_side": ("n1", "n3"),
        }
        for scenario, (source, target) in cases.items():
            expected = {
                "ryw": [source, target],
                "mr": [source, source, target],
                "mw": [source, target, target, target],
                "wfr": [source, source, target, target, target],
            }
            for model, sequence in expected.items():
                with self.subTest(scenario=scenario, model=model):
                    connected = []

                    def factory(node, logger):
                        if scenario == "node_stop" and node == "n3":
                            raise ConnectionError("n3 is stopped")
                        connected.append(node)
                        return FakeClient(node, logger)

                    routes = run.SCENARIO_ROUTES[scenario]
                    clients = run.make_clients(None, routes, factory)
                    rows = workloads.RUNNERS[model](
                        clients, run_id="test-run", history="fresh-history",
                        model=model, scenario=scenario, write_cl="QUORUM",
                        read_cl="ALL", routing=routes, fault_verified=False,
                    )
                    self.assertEqual(set(connected), {source, target})
                    self.assertEqual([r["actual_coordinator"] for r in rows], sequence)
                    for row in rows:
                        self.assertEqual(row["routing"], routes)
                        expected_cl = (
                            "ONE" if row["phase"] == "diagnostic"
                            else "QUORUM" if row["operation"] == "write" else "ALL"
                        )
                        self.assertEqual(row["actual_statement_cl"], expected_cl)
                    run.close_clients(clients)
                    for client in clients.values():
                        self.assertEqual(client.close_count, 1)

    def test_partial_connection_failure_closes_existing_clients(self):
        existing = FakeClient("n1", None)

        def factory(node, logger):
            if node == "n2":
                raise ConnectionError("unavailable")
            return existing

        with self.assertRaises(ConnectionError):
            run.make_clients(None, run.SCENARIO_ROUTES["node_stop"], factory)
        self.assertEqual(existing.close_count, 1)

    def test_prepare_only_needs_source_and_keeps_all_consistency(self):
        clients = {"source": FakeClient("n1", None)}
        for model in ("ryw", "mr"):
            rows = workloads.prepare(clients, "test", "fresh", model)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["actual_coordinator"], "n1")
            self.assertEqual(rows[0]["actual_statement_cl"], "ALL")
            self.assertEqual(rows[0]["phase"], "prepare")
        for model in ("mw", "wfr"):
            self.assertEqual(workloads.prepare({}, "test", "fresh", model), [])

    def test_cli_rejects_unknown_scenario_before_connecting(self):
        result = subprocess.run(
            [sys.executable, "-m", "src.run", "run", "--model", "ryw",
             "--history", "h", "--log", "unused.jsonl", "--scenario", "typo"],
            cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("invalid choice", result.stderr)

    def test_cli_logs_setup_failure_instead_of_an_empty_history(self):
        logs = []
        stub = types.ModuleType("src.client")

        class MemoryLogger:
            def __init__(self, path):
                pass

            def write(self, row):
                logs.append(row)

        def unavailable(node, logger):
            raise ConnectionError("cannot connect")

        stub.Logger = MemoryLogger
        stub.NodeClient = unavailable
        with test_directory() as directory:
            args = ["run", "run", "--model", "mr", "--history", "h",
                    "--run-id", "run-1", "--log", str(Path(directory)/"ops.jsonl"),
                    "--scenario", "node_stop"]
            with patch.dict(sys.modules, {"src.client": stub}), patch.object(sys, "argv", args):
                with self.assertRaises(ConnectionError):
                    run.main()
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["phase"], "setup")
        self.assertEqual(logs[0]["routing"], {"source": "n1", "target": "n2"})
        self.assertEqual(logs[0]["run_id"], "run-1")


class MonotonicReadTests(unittest.TestCase):
    def records(self, returned, status="ok"):
        return [
            {"operation_id": 2, "status": "ok", "returned": {"value": "v1"}},
            {"operation_id": 3, "status": status, "returned": returned},
        ]

    def test_old_and_missing_values_are_witnesses(self):
        for returned in ({"value": "v0"}, None):
            with self.subTest(returned=returned):
                self.assertEqual(checkers.mr(self.records(returned))[0], "witness")

    def test_failed_read_is_blocked_not_a_witness(self):
        for status in ("read_timeout", "unavailable", "connection_error", "client_timeout"):
            with self.subTest(status=status):
                self.assertEqual(checkers.mr(self.records(None, status))[0], "blocked")

    def test_new_value_has_no_witness(self):
        self.assertEqual(checkers.mr(self.records({"value": "v1"}))[0], "no_witness_observed")

    def test_unknown_or_malformed_value_is_inconclusive(self):
        for returned in ({"value": "unexpected"}, {}, {"value": None}):
            with self.subTest(returned=returned):
                self.assertEqual(checkers.mr(self.records(returned))[0], "inconclusive")
        rows = self.records(None)
        del rows[1]["returned"]
        self.assertEqual(checkers.mr(rows)[0], "inconclusive")

    def test_no_first_v1_means_no_witness(self):
        rows = self.records(None)
        rows[0]["returned"] = {"value": "v0"}
        self.assertEqual(checkers.mr(rows)[0], "inconclusive")

    def test_check_command_reads_a_saved_history_without_database(self):
        with test_directory() as directory:
            log = Path(directory)/"ops.jsonl"
            rows = [dict(r, history_id="h", model="mr") for r in self.records(None)]
            log.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
            args = ["run", "check", "--model", "mr", "--history", "h", "--log", str(log)]
            output = io.StringIO()
            with patch.object(sys, "argv", args), contextlib.redirect_stdout(output):
                run.main()
            self.assertIn("result: witness", output.getvalue())


if __name__ == "__main__":
    unittest.main()
