"""Behavioral and export checks for the initial AgentWatch prototype."""

import copy
import csv
import hashlib
import json
import math
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from agentwatch import (
    CATEGORIES, STRATEGIES, begin_attempt, classify_risk, decide,
    load_suite, summarize, task_appropriate, technical_permission,
)

ROOT = Path(__file__).resolve().parents[1]


class PolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.resources, cls.scenarios = load_suite(ROOT / "scenarios.json")
        cls.by_id = {scenario["id"]: scenario for scenario in cls.scenarios}

    def test_balanced_scenario_coverage(self):
        self.assertEqual(len(self.scenarios), 30)
        self.assertEqual(Counter(s["category"] for s in self.scenarios), Counter({c: 5 for c in CATEGORIES}))

    def test_all_ninety_initial_decisions_match_independent_expectations(self):
        for scenario in self.scenarios:
            for strategy in STRATEGIES:
                with self.subTest(scenario=scenario["id"], strategy=strategy):
                    self.assertEqual(decide(scenario, strategy, self.resources).status, scenario["expected_decisions"][strategy])

    def test_ground_truth_matches_independently_derived_inputs(self):
        for scenario in self.scenarios:
            with self.subTest(scenario=scenario["id"]):
                self.assertEqual(technical_permission(scenario), scenario["ground_truth"]["technical_authorized"])
                self.assertEqual(task_appropriate(scenario), scenario["ground_truth"]["context_appropriate"])
                self.assertEqual(classify_risk(scenario["action"], self.resources), scenario["ground_truth"]["risk"])

    def test_runtime_policy_does_not_trust_expected_labels(self):
        scenario = copy.deepcopy(self.by_id["IH02"])
        scenario["category"] = "appropriate_low"
        scenario["ground_truth"] = {"technical_authorized": True, "context_appropriate": True, "risk": "low"}
        scenario["expected_decisions"] = {strategy: "allow" for strategy in STRATEGIES}
        self.assertEqual(decide(scenario, "combined", self.resources).status, "block")

    def test_confidential_risk_cannot_be_lowered_by_an_action_claim(self):
        scenario = copy.deepcopy(self.by_id["AH05"])
        scenario["action"]["risk"] = "low"
        self.assertEqual(decide(scenario, "combined", self.resources).risk, "high")

    def test_resource_scope_is_enforced(self):
        self.assertTrue(technical_permission(self.by_id["IL04"]))
        self.assertFalse(task_appropriate(self.by_id["IL04"]))
        self.assertEqual(decide(self.by_id["IL04"], "combined", self.resources).status, "block")

    def test_recipient_scope_is_enforced(self):
        self.assertTrue(technical_permission(self.by_id["IH05"]))
        self.assertEqual(decide(self.by_id["IH05"], "permissions", self.resources).status, "allow")
        self.assertEqual(decide(self.by_id["IH05"], "combined", self.resources).status, "block")

    def test_unknown_strategy_fails(self):
        with self.assertRaises(ValueError):
            decide(self.by_id["AL01"], "unknown", self.resources)

    def test_unknown_action_fails(self):
        scenario = copy.deepcopy(self.by_id["AL01"])
        scenario["action"]["kind"] = "run_arbitrary_command"
        with self.assertRaises(ValueError):
            decide(scenario, "unrestricted", self.resources)

    def test_pending_approval_cannot_execute(self):
        attempt = begin_attempt(self.by_id["AH01"], "combined", self.resources)
        self.assertEqual(attempt.approval_status, "pending")
        self.assertFalse(attempt.executed)
        with self.assertRaises(PermissionError):
            attempt.execute()
        self.assertEqual(attempt.workspace.execution_count, 0)

    def test_approval_grant_executes_once_and_records_order(self):
        attempt = begin_attempt(self.by_id["AH01"], "combined", self.resources)
        attempt.resolve_approval(True, 5)
        self.assertTrue(attempt.executed)
        self.assertEqual(attempt.workspace.execution_count, 1)
        self.assertEqual(attempt.workspace.sent_items, [{"resource_id": "monthly_report", "recipient": "manager@fictional.invalid"}])
        self.assertLess(attempt.events.index("simulated_approval_approved"), attempt.events.index("mock_action_executed"))
        self.assertEqual(attempt.simulated_approval_wait_seconds, 5)
        with self.assertRaises(RuntimeError):
            attempt.execute()

    def test_refusal_cannot_be_reapproved_or_executed(self):
        attempt = begin_attempt(self.by_id["AH01"], "combined", self.resources)
        attempt.resolve_approval(False)
        self.assertFalse(attempt.executed)
        self.assertEqual(attempt.workspace.sent_items, [])
        with self.assertRaises(ValueError):
            attempt.resolve_approval(True)
        with self.assertRaises(PermissionError):
            attempt.execute()

    def test_approval_cannot_override_a_block(self):
        for sid in ["UH01", "IH02"]:
            attempt = begin_attempt(self.by_id[sid], "combined", self.resources)
            with self.assertRaises(ValueError):
                attempt.resolve_approval(True)
            self.assertFalse(attempt.executed)

    def test_invalid_approval_delay_is_rejected(self):
        for delay in [-1, math.nan, math.inf]:
            with self.subTest(delay=delay):
                attempt = begin_attempt(self.by_id["AH01"], "combined", self.resources)
                with self.assertRaises(ValueError):
                    attempt.resolve_approval(True, delay)
                self.assertEqual(attempt.approval_status, "pending")

    def test_workspace_is_reset_between_trials(self):
        first = begin_attempt(self.by_id["IH02"], "unrestricted", self.resources)
        second = begin_attempt(self.by_id["IH02"], "combined", self.resources)
        self.assertNotIn("monthly_report", first.workspace.files)
        self.assertIn("monthly_report", second.workspace.files)
        self.assertIn("monthly_report", self.resources)

    def test_deletion_does_not_touch_host_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            host_file = Path(temporary) / "monthly_report"
            host_file.write_text("This is an actual temporary host file.")
            attempt = begin_attempt(self.by_id["IH02"], "unrestricted", self.resources)
            self.assertTrue(attempt.executed)
            self.assertTrue(host_file.exists())

    def make_rows(self, approve=True):
        rows = []
        for scenario in self.scenarios:
            for strategy in STRATEGIES:
                attempt = begin_attempt(scenario, strategy, self.resources)
                if attempt.approval_status == "pending":
                    attempt.resolve_approval(approve, 6)
                rows.append(attempt.as_row(1, len(rows) + 1))
        return rows

    def test_security_and_success_metrics_have_correct_denominators(self):
        summaries = {s["strategy"]: s for s in summarize(self.make_rows())}
        for s in summaries.values():
            self.assertEqual((s["attempts"], s["unauthorized_attempts"], s["inappropriate_authorized_attempts"], s["legitimate_attempts"]), (30, 10, 10, 10))
            self.assertEqual(s["false_positive_rate_pct"], 0)
            self.assertEqual(s["legitimate_task_success_rate_pct"], 100)
        self.assertEqual(summaries["unrestricted"]["unauthorized_block_rate_pct"], 0)
        self.assertEqual(summaries["permissions"]["unauthorized_block_rate_pct"], 100)
        self.assertEqual(summaries["permissions"]["inappropriate_block_rate_pct"], 0)
        self.assertEqual(summaries["combined"]["inappropriate_block_rate_pct"], 100)
        self.assertEqual(summaries["combined"]["approval_requests"], 5)
        self.assertAlmostEqual(summaries["combined"]["approval_frequency_pct"], 100 * 5 / 30)

    def test_approval_refusals_are_separate_from_policy_false_positives(self):
        combined = next(s for s in summarize(self.make_rows(False)) if s["strategy"] == "combined")
        self.assertEqual(combined["simulated_approval_denials"], 5)
        self.assertEqual(combined["legitimate_task_success_rate_pct"], 50)
        self.assertEqual(combined["false_positive_rate_pct"], 0)

    def test_estimated_time_keeps_assumed_delay_separate(self):
        attempt = begin_attempt(self.by_id["AH01"], "combined", self.resources)
        attempt.resolve_approval(True, 123)
        row = attempt.as_row(1, 1)
        self.assertAlmostEqual(row["estimated_total_seconds"], row["measured_processing_ms"] / 1000 + 123)
        self.assertEqual(row["simulated_approval_wait_seconds"], 123)


class ExportTests(unittest.TestCase):
    def test_cli_exports_two_complete_rounds_and_verified_source_snapshot(self):
        with tempfile.TemporaryDirectory() as temporary:
            command = [sys.executable, str(ROOT / "run_simulation.py"), "--output", temporary, "--rounds", "2", "--approval-seconds", "0", "--operator", "test runner"]
            result = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            folders = list(Path(temporary).iterdir())
            self.assertEqual(len(folders), 1)
            folder = folders[0]
            metadata = json.loads((folder / "run_metadata.json").read_text())
            self.assertEqual(metadata["scenario_condition_runs"], 180)
            with (folder / "trials.csv").open(encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 180)
            self.assertEqual(len({(r["round"], r["scenario_id"], r["strategy"]) for r in rows}), 180)
            with sqlite3.connect(folder / "results.sqlite") as connection:
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM trials").fetchone()[0], 180)
                self.assertEqual(connection.execute("SELECT COUNT(*) FROM summaries").fetchone()[0], 3)
                self.assertEqual(connection.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            for name, digest in metadata["source_snapshot_sha256"].items():
                self.assertEqual(hashlib.sha256((folder / "source_snapshot" / name).read_bytes()).hexdigest(), digest)
            report = (folder / "report.html").read_text()
            self.assertIn("180/180", report)
            self.assertIn("no live AI agent", report)
            self.assertIn("simulated", report.lower())

    def test_cli_rejects_nonfinite_delays(self):
        result = subprocess.run([sys.executable, str(ROOT / "run_simulation.py"), "--approval-seconds", "nan"], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("finite nonnegative", result.stderr)


if __name__ == "__main__":
    unittest.main()
