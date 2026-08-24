from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PrefixPythonCliTests(unittest.TestCase):
    def _run(self, *args: str, stdin: str | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "prefix_python", *args],
            cwd=ROOT,
            input=stdin,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_scan_file_json(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "missing_colon.py"
            path.write_text("if ready\nprint('x')\n", encoding="utf-8")
            completed = self._run(str(path), "--json")
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["status"], "ACCEPT_FIXED")
            self.assertEqual(payload["state"], "APPLIED")
            self.assertEqual(payload["lane"], "APPLY")
            self.assertFalse(payload["wrote"])

    def test_stdin_scan(self):
        completed = self._run("--stdin", "--json", stdin="if ready\nprint('x')\n")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "ACCEPT_FIXED")
        self.assertEqual(payload["lane"], "APPLY")

    def test_apply_and_rollback_valid_preimage(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "tabs_only.py"
            path.write_text("if ready:\n\tprint('x')\n", encoding="utf-8")
            apply_completed = self._run(str(path), "--apply", "--json")
            self.assertEqual(apply_completed.returncode, 0, apply_completed.stderr)
            apply_payload = json.loads(apply_completed.stdout)
            self.assertEqual(apply_payload["status"], "ACCEPT_FIXED")
            self.assertEqual(apply_payload["lane"], "APPLY")
            self.assertTrue(apply_payload["wrote"])
            self.assertTrue(Path(apply_payload["receipt_path"]).exists())
            self.assertEqual(path.read_text(encoding="utf-8"), "if ready:\n    print('x')\n")

            rollback_completed = self._run(str(path), "--rollback", apply_payload["receipt_path"], "--json")
            self.assertEqual(rollback_completed.returncode, 0, rollback_completed.stderr)
            rollback_payload = json.loads(rollback_completed.stdout)
            self.assertEqual(rollback_payload["status"], "ACCEPT_FIXED")
            self.assertEqual(rollback_payload["lane"], "APPLY")
            self.assertTrue(rollback_payload["wrote"])
            self.assertEqual(path.read_text(encoding="utf-8"), "if ready:\n\tprint('x')\n")

    def test_replay_receipt_verifies_deterministic_apply(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "missing_colon.py"
            path.write_text("if ready\nprint('x')\n", encoding="utf-8")
            apply_completed = self._run(str(path), "--apply", "--json")
            self.assertEqual(apply_completed.returncode, 0, apply_completed.stderr)
            apply_payload = json.loads(apply_completed.stdout)

            replay_completed = self._run("--replay-receipt", apply_payload["receipt_path"], "--json")
            self.assertEqual(replay_completed.returncode, 0, replay_completed.stderr)
            replay_payload = json.loads(replay_completed.stdout)
            self.assertEqual(replay_payload["status"], "ACCEPT_VALID")
            self.assertEqual(replay_payload["lane"], "ANALYZE")
            self.assertTrue(replay_payload["proof_trace"]["replay_verified"])

    def test_inspect_receipt_reports_chain_depth(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "tabs_only.py"
            path.write_text("if ready:\n\tprint('x')\n", encoding="utf-8")
            apply_completed = self._run(str(path), "--apply", "--json")
            self.assertEqual(apply_completed.returncode, 0, apply_completed.stderr)
            apply_payload = json.loads(apply_completed.stdout)

            inspect_completed = self._run("--inspect-receipt", apply_payload["receipt_path"], "--json")
            self.assertEqual(inspect_completed.returncode, 0, inspect_completed.stderr)
            inspect_payload = json.loads(inspect_completed.stdout)
            self.assertEqual(inspect_payload["status"], "ACCEPT_VALID")
            self.assertEqual(inspect_payload["lane"], "ANALYZE")
            self.assertEqual(inspect_payload["chain_depth"], 0)
            self.assertIsNotNone(inspect_payload["proof_trace"]["receipt_id"])

    def test_advised_apply_never_writes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "orphaned_elif.py"
            original = "elif ready:\n    print('x')\n"
            path.write_text(original, encoding="utf-8")
            completed = self._run(str(path), "--apply", "--json")
            self.assertEqual(completed.returncode, 2, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["state"], "ADVISED")
            self.assertEqual(payload["lane"], "ADVISE")
            self.assertFalse(payload["wrote"])
            self.assertFalse(payload["mutation_performed"])
            self.assertEqual(path.read_text(encoding="utf-8"), original)

    def test_analyze_apply_never_writes(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "assignment_rhs.py"
            original = "value =\n"
            path.write_text(original, encoding="utf-8")
            completed = self._run(str(path), "--apply", "--json")
            self.assertEqual(completed.returncode, 2, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["state"], "REFUSED")
            self.assertEqual(payload["lane"], "ANALYZE")
            self.assertFalse(payload["wrote"])
            self.assertFalse(payload["mutation_performed"])
            self.assertEqual(path.read_text(encoding="utf-8"), original)

    def test_rollback_refuses_invalid_preimage(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "missing_colon.py"
            path.write_text("if ready\nprint('x')\n", encoding="utf-8")
            apply_completed = self._run(str(path), "--apply", "--json")
            self.assertEqual(apply_completed.returncode, 0, apply_completed.stderr)
            apply_payload = json.loads(apply_completed.stdout)

            rollback_completed = self._run(str(path), "--rollback", apply_payload["receipt_path"], "--json")
            self.assertEqual(rollback_completed.returncode, 2)
            rollback_payload = json.loads(rollback_completed.stdout)
            self.assertEqual(rollback_payload["refusal_code"], "rollback_preimage_invalid")

    def test_invalid_utf8_file_is_refused(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "invalid_utf8.py"
            path.write_bytes(b"print('x')\xff")
            completed = self._run(str(path), "--json")
            self.assertEqual(completed.returncode, 2)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["refusal_code"], "input_decode_error")

    def test_missing_path_is_refused(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            missing = Path(temp_dir) / "missing.py"
            completed = self._run(str(missing), "--json")
            self.assertEqual(completed.returncode, 2)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["refusal_code"], "path_missing")


if __name__ == "__main__":
    unittest.main()
