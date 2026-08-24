from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PrefixOperatorConsoleTests(unittest.TestCase):
    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "prefix_python.operator_console", *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_full_pilot_lifecycle_generates_reports(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "ops"
            bundle = Path(temp_dir) / "prefix-python-0.1.0-rc2.zip"
            bundle.write_text("bundle", encoding="utf-8")

            init_completed = self._run("init", "--root", str(root), "--release-bundle", str(bundle))
            self.assertEqual(init_completed.returncode, 0, init_completed.stderr)
            init_payload = json.loads(init_completed.stdout)
            self.assertTrue((root / "program.json").exists())
            self.assertEqual(init_payload["status"], "OK")

            invite_completed = self._run(
                "invite",
                "--root",
                str(root),
                "--cohort-name",
                "Founding Operator Cohort",
                "--team-name",
                "Northwind",
                "--operator-name",
                "Avery Lane",
                "--operator-email",
                "avery@northwind.dev",
                "--seat-count",
                "12",
                "--start-date",
                "2026-05-01",
            )
            self.assertEqual(invite_completed.returncode, 0, invite_completed.stderr)
            invite_payload = json.loads(invite_completed.stdout)
            self.assertTrue((root / "invites" / f"{invite_payload['invite_id']}.json").exists())

            activate_completed = self._run(
                "activate",
                "--root",
                str(root),
                "--invite-id",
                invite_payload["invite_id"],
                "--activation-date",
                "2026-05-01",
            )
            self.assertEqual(activate_completed.returncode, 0, activate_completed.stderr)
            activate_payload = json.loads(activate_completed.stdout)
            team_id = activate_payload["team_id"]
            self.assertTrue((root / "enrollments" / f"{team_id}.json").exists())

            checkpoint_completed = self._run(
                "checkpoint",
                "--root",
                str(root),
                "--team-id",
                team_id,
                "--checkpoint-date",
                "2026-05-21",
                "--onboarding",
                "complete",
                "--install",
                "complete",
                "--demo",
                "complete",
                "--replay",
                "complete",
                "--refusal",
                "complete",
                "--rollback",
                "complete",
                "--trust-level",
                "high",
                "--enterprise-interest",
                "active",
                "--replay-count",
                "8",
                "--refusal-count",
                "3",
                "--rollback-count",
                "2",
                "--open-issues",
                "0",
                "--notes",
                "Deterministic workflow validated.",
            )
            self.assertEqual(checkpoint_completed.returncode, 0, checkpoint_completed.stderr)

            issue_completed = self._run(
                "issue",
                "--root",
                str(root),
                "--team-id",
                team_id,
                "--issue-date",
                "2026-05-18",
                "--severity",
                "medium",
                "--category",
                "install",
                "--summary",
                "Initial VSIX trust prompt required acknowledgement.",
                "--status",
                "resolved",
            )
            self.assertEqual(issue_completed.returncode, 0, issue_completed.stderr)

            cohort_completed = self._run("cohort-summary", "--root", str(root), "--as-of", "2026-05-21")
            self.assertEqual(cohort_completed.returncode, 0, cohort_completed.stderr)
            cohort_payload = json.loads(cohort_completed.stdout)
            self.assertEqual(cohort_payload["summary"]["conversion_ready_teams"], 1)
            self.assertTrue(Path(cohort_payload["report_path"]).exists())

            report_path = Path(cohort_payload["report_path"])
            report_payload = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertTrue(report_payload["bundle_hash_verified"])
            self.assertIsNotNone(report_payload["workspace_fingerprint"])

            conversion_completed = self._run("conversion-summary", "--root", str(root), "--as-of", "2026-05-21")
            self.assertEqual(conversion_completed.returncode, 0, conversion_completed.stderr)
            conversion_payload = json.loads(conversion_completed.stdout)
            self.assertEqual(conversion_payload["summary"]["conversion_ready_teams"], 1)

            distribution_completed = self._run("distribution-manifest", "--root", str(root), "--as-of", "2026-05-21")
            self.assertEqual(distribution_completed.returncode, 0, distribution_completed.stderr)
            distribution_payload = json.loads(distribution_completed.stdout)
            self.assertEqual(distribution_payload["distribution_count"], 1)

    def test_reminders_and_expiration_are_deterministic(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "ops"
            bundle = Path(temp_dir) / "prefix-python-0.1.0-rc2.zip"
            bundle.write_text("bundle", encoding="utf-8")

            self.assertEqual(self._run("init", "--root", str(root), "--release-bundle", str(bundle)).returncode, 0)
            invite_completed = self._run(
                "invite",
                "--root",
                str(root),
                "--cohort-name",
                "Founding Operator Cohort",
                "--team-name",
                "Southridge",
                "--operator-name",
                "Mina Cole",
                "--operator-email",
                "mina@southridge.dev",
                "--seat-count",
                "4",
                "--start-date",
                "2026-05-01",
            )
            invite_payload = json.loads(invite_completed.stdout)
            activate_completed = self._run(
                "activate",
                "--root",
                str(root),
                "--invite-id",
                invite_payload["invite_id"],
                "--activation-date",
                "2026-05-01",
            )
            team_id = json.loads(activate_completed.stdout)["team_id"]

            reminders_completed = self._run("reminders", "--root", str(root), "--as-of", "2026-05-10")
            self.assertEqual(reminders_completed.returncode, 0, reminders_completed.stderr)
            reminders_payload = json.loads(reminders_completed.stdout)
            self.assertEqual(reminders_payload["count"], 2)

            checkpoint_completed = self._run(
                "checkpoint",
                "--root",
                str(root),
                "--team-id",
                team_id,
                "--checkpoint-date",
                "2026-05-10",
                "--onboarding",
                "complete",
                "--install",
                "complete",
                "--demo",
                "incomplete",
                "--replay",
                "incomplete",
                "--refusal",
                "complete",
                "--rollback",
                "incomplete",
                "--trust-level",
                "medium",
                "--enterprise-interest",
                "monitoring",
                "--open-issues",
                "1",
            )
            self.assertEqual(checkpoint_completed.returncode, 0, checkpoint_completed.stderr)

            expired_summary = self._run("cohort-summary", "--root", str(root), "--as-of", "2026-06-05")
            self.assertEqual(expired_summary.returncode, 0, expired_summary.stderr)
            summary_payload = json.loads(expired_summary.stdout)
            report_path = Path(summary_payload["report_path"])
            team_payload = json.loads(report_path.read_text(encoding="utf-8"))["teams"][0]
            self.assertEqual(team_payload["lifecycle_state"], "expired")
            self.assertFalse(team_payload["conversion_ready"])

    def test_rejects_conflicting_record_overwrite(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "ops"
            bundle = Path(temp_dir) / "prefix-python-0.1.0-rc2.zip"
            bundle.write_text("bundle", encoding="utf-8")

            self.assertEqual(self._run("init", "--root", str(root), "--release-bundle", str(bundle)).returncode, 0)
            first = self._run(
                "invite",
                "--root",
                str(root),
                "--cohort-name",
                "Founding Operator Cohort",
                "--team-name",
                "Northwind",
                "--operator-name",
                "Avery Lane",
                "--operator-email",
                "avery@northwind.dev",
                "--seat-count",
                "12",
                "--start-date",
                "2026-05-01",
            )
            self.assertEqual(first.returncode, 0, first.stderr)

            second = self._run(
                "invite",
                "--root",
                str(root),
                "--cohort-name",
                "Founding Operator Cohort",
                "--team-name",
                "Northwind",
                "--operator-name",
                "Avery Lane",
                "--operator-email",
                "avery@northwind.dev",
                "--seat-count",
                "18",
                "--start-date",
                "2026-05-01",
            )
            self.assertEqual(second.returncode, 2)
            payload = json.loads(second.stdout)
            self.assertEqual(payload["status"], "BLOCKED")

    def test_rejects_init_hash_mismatch(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "ops"
            bundle = Path(temp_dir) / "prefix-python-0.1.0-rc2.zip"
            bundle.write_text("bundle", encoding="utf-8")

            completed = self._run(
                "init",
                "--root",
                str(root),
                "--release-bundle",
                str(bundle),
                "--release-sha256",
                "0" * 64,
            )
            self.assertEqual(completed.returncode, 2)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["status"], "BLOCKED")
            self.assertIn("release hash", payload["reason"])

    def test_rejects_invalid_invite_inputs(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "ops"
            bundle = Path(temp_dir) / "prefix-python-0.1.0-rc2.zip"
            bundle.write_text("bundle", encoding="utf-8")
            self.assertEqual(self._run("init", "--root", str(root), "--release-bundle", str(bundle)).returncode, 0)

            completed = self._run(
                "invite",
                "--root",
                str(root),
                "--cohort-name",
                "Founding Operator Cohort",
                "--team-name",
                "Northwind",
                "--operator-name",
                "Avery Lane",
                "--operator-email",
                "avery-at-northwind.dev",
                "--seat-count",
                "0",
                "--start-date",
                "2026-05-01",
            )
            self.assertEqual(completed.returncode, 2)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["status"], "BLOCKED")

    def test_rejects_activation_after_evaluation_end(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "ops"
            bundle = Path(temp_dir) / "prefix-python-0.1.0-rc2.zip"
            bundle.write_text("bundle", encoding="utf-8")
            self.assertEqual(self._run("init", "--root", str(root), "--release-bundle", str(bundle)).returncode, 0)

            invite_completed = self._run(
                "invite",
                "--root",
                str(root),
                "--cohort-name",
                "Founding Operator Cohort",
                "--team-name",
                "Northwind",
                "--operator-name",
                "Avery Lane",
                "--operator-email",
                "avery@northwind.dev",
                "--seat-count",
                "12",
                "--start-date",
                "2026-05-01",
                "--duration-days",
                "5",
            )
            invite_payload = json.loads(invite_completed.stdout)

            activate_completed = self._run(
                "activate",
                "--root",
                str(root),
                "--invite-id",
                invite_payload["invite_id"],
                "--activation-date",
                "2026-05-10",
            )
            self.assertEqual(activate_completed.returncode, 2)
            payload = json.loads(activate_completed.stdout)
            self.assertEqual(payload["status"], "BLOCKED")

    def test_rejects_checkpoint_outside_evaluation_term(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "ops"
            bundle = Path(temp_dir) / "prefix-python-0.1.0-rc2.zip"
            bundle.write_text("bundle", encoding="utf-8")
            self.assertEqual(self._run("init", "--root", str(root), "--release-bundle", str(bundle)).returncode, 0)

            invite_completed = self._run(
                "invite",
                "--root",
                str(root),
                "--cohort-name",
                "Founding Operator Cohort",
                "--team-name",
                "Northwind",
                "--operator-name",
                "Avery Lane",
                "--operator-email",
                "avery@northwind.dev",
                "--seat-count",
                "12",
                "--start-date",
                "2026-05-01",
            )
            invite_payload = json.loads(invite_completed.stdout)
            self.assertEqual(
                self._run(
                    "activate",
                    "--root",
                    str(root),
                    "--invite-id",
                    invite_payload["invite_id"],
                    "--activation-date",
                    "2026-05-01",
                ).returncode,
                0,
            )

            checkpoint_completed = self._run(
                "checkpoint",
                "--root",
                str(root),
                "--team-id",
                invite_payload["team_id"],
                "--checkpoint-date",
                "2026-06-15",
                "--onboarding",
                "complete",
                "--install",
                "complete",
                "--demo",
                "complete",
                "--replay",
                "complete",
                "--refusal",
                "complete",
                "--rollback",
                "complete",
                "--trust-level",
                "high",
                "--enterprise-interest",
                "active",
            )
            self.assertEqual(checkpoint_completed.returncode, 2)
            payload = json.loads(checkpoint_completed.stdout)
            self.assertEqual(payload["status"], "BLOCKED")

    def test_rejects_issue_before_activation(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "ops"
            bundle = Path(temp_dir) / "prefix-python-0.1.0-rc2.zip"
            bundle.write_text("bundle", encoding="utf-8")
            self.assertEqual(self._run("init", "--root", str(root), "--release-bundle", str(bundle)).returncode, 0)

            invite_completed = self._run(
                "invite",
                "--root",
                str(root),
                "--cohort-name",
                "Founding Operator Cohort",
                "--team-name",
                "Northwind",
                "--operator-name",
                "Avery Lane",
                "--operator-email",
                "avery@northwind.dev",
                "--seat-count",
                "12",
                "--start-date",
                "2026-05-01",
            )
            invite_payload = json.loads(invite_completed.stdout)
            self.assertEqual(
                self._run(
                    "activate",
                    "--root",
                    str(root),
                    "--invite-id",
                    invite_payload["invite_id"],
                    "--activation-date",
                    "2026-05-01",
                ).returncode,
                0,
            )

            issue_completed = self._run(
                "issue",
                "--root",
                str(root),
                "--team-id",
                invite_payload["team_id"],
                "--issue-date",
                "2026-04-30",
                "--severity",
                "medium",
                "--category",
                "install",
                "--summary",
                "Invalid pre-activation issue.",
                "--status",
                "open",
            )
            self.assertEqual(issue_completed.returncode, 2)
            payload = json.loads(issue_completed.stdout)
            self.assertEqual(payload["status"], "BLOCKED")

    def test_distribution_manifest_refuses_bundle_drift(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "ops"
            bundle = Path(temp_dir) / "prefix-python-0.1.0-rc2.zip"
            bundle.write_text("bundle", encoding="utf-8")
            self.assertEqual(self._run("init", "--root", str(root), "--release-bundle", str(bundle)).returncode, 0)

            invite_completed = self._run(
                "invite",
                "--root",
                str(root),
                "--cohort-name",
                "Founding Operator Cohort",
                "--team-name",
                "Northwind",
                "--operator-name",
                "Avery Lane",
                "--operator-email",
                "avery@northwind.dev",
                "--seat-count",
                "12",
                "--start-date",
                "2026-05-01",
            )
            invite_payload = json.loads(invite_completed.stdout)
            self.assertEqual(
                self._run(
                    "activate",
                    "--root",
                    str(root),
                    "--invite-id",
                    invite_payload["invite_id"],
                    "--activation-date",
                    "2026-05-01",
                ).returncode,
                0,
            )

            bundle.write_text("tampered", encoding="utf-8")
            completed = self._run("distribution-manifest", "--root", str(root), "--as-of", "2026-05-21")
            self.assertEqual(completed.returncode, 2)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["status"], "BLOCKED")

    def test_repeated_reports_are_identical(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "ops"
            bundle = Path(temp_dir) / "prefix-python-0.1.0-rc2.zip"
            bundle.write_text("bundle", encoding="utf-8")
            self.assertEqual(self._run("init", "--root", str(root), "--release-bundle", str(bundle)).returncode, 0)
            invite_completed = self._run(
                "invite",
                "--root",
                str(root),
                "--cohort-name",
                "Founding Operator Cohort",
                "--team-name",
                "Northwind",
                "--operator-name",
                "Avery Lane",
                "--operator-email",
                "avery@northwind.dev",
                "--seat-count",
                "12",
                "--start-date",
                "2026-05-01",
            )
            invite_payload = json.loads(invite_completed.stdout)
            self.assertEqual(
                self._run(
                    "activate",
                    "--root",
                    str(root),
                    "--invite-id",
                    invite_payload["invite_id"],
                    "--activation-date",
                    "2026-05-01",
                ).returncode,
                0,
            )
            first = self._run("cohort-summary", "--root", str(root), "--as-of", "2026-05-21")
            second = self._run("cohort-summary", "--root", str(root), "--as-of", "2026-05-21")
            self.assertEqual(first.returncode, 0)
            self.assertEqual(second.returncode, 0)
            self.assertEqual(json.loads(first.stdout), json.loads(second.stdout))


if __name__ == "__main__":
    unittest.main()
