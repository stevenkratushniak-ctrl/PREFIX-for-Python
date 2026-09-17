"""Customer-visible regression cases, exercised through the real CLI."""
import ast
import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout
import io
from pathlib import Path

from prefix_python.engine import correct_source
from prefix_python import cli

ROOT = Path(__file__).resolve().parents[1]


class CustomerSafetyTests(unittest.TestCase):
    def run_cli(self, *args):
        result = subprocess.run([sys.executable, "-m", "prefix_python", *map(str, args), "--json"],
                                cwd=ROOT, capture_output=True, text=True, timeout=20)
        self.assertIn(result.returncode, (0, 2), result.stderr)
        return result.returncode, json.loads(result.stdout)

    def test_literal_tabs_and_mixed_newlines_are_preserved(self):
        for source in ('value = "a\tb"\n', 'value = """first\n\tsecond"""\n',
                       'value = f"""first\n\t{1}"""\n', 'x = 1\r\ny = 2\n'):
            with self.subTest(source=repr(source)):
                result = correct_source(source)
                self.assertEqual(result.source, source)
                self.assertEqual(result.status, "ACCEPT_VALID")

    def test_indentation_fix_preserves_string_data_and_ast(self):
        source = 'if True:\n\tvalue = "a\tb"\n'
        result = correct_source(source)
        self.assertEqual(result.source, 'if True:\n    value = "a\tb"\n')
        self.assertEqual(ast.dump(ast.parse(source)), ast.dump(ast.parse(result.source)))

    def test_failed_receipt_creation_cannot_edit_source(self):
        with tempfile.TemporaryDirectory() as temp:
            path, blocked = Path(temp) / "input.py", Path(temp) / "not-a-directory"
            original = b"if True\n    print('x')\n"
            path.write_bytes(original)
            blocked.write_bytes(b"retained")
            code, result = self.run_cli(path, "--apply", "--receipt-dir", blocked)
            self.assertEqual(code, 2)
            self.assertFalse(result["wrote"])
            self.assertEqual(path.read_bytes(), original)

    def test_rollback_receipt_failure_cannot_edit_source(self):
        with tempfile.TemporaryDirectory() as temp:
            path, blocked = Path(temp) / "input.py", Path(temp) / "not-a-directory"
            path.write_bytes(b"if True:\n\tprint('x')\n")
            _, applied = self.run_cli(path, "--apply")
            current = path.read_bytes()
            blocked.write_bytes(b"retained")
            code, result = self.run_cli("--rollback", applied["receipt_path"], "--receipt-dir", blocked)
            self.assertEqual(code, 2)
            self.assertFalse(result["wrote"])
            self.assertEqual(path.read_bytes(), current)

    def test_apply_replay_rollback_preserve_crlf_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "input.py"
            original = b"if True:\r\n\tprint('x')\r\n"
            path.write_bytes(original)
            code, applied = self.run_cli(path, "--apply")
            self.assertEqual(code, 0)
            self.assertEqual(path.read_bytes(), b"if True:\r\n    print('x')\r\n")
            code, replay = self.run_cli("--replay-receipt", applied["receipt_path"])
            self.assertEqual(code, 0)
            self.assertTrue(replay["proof_trace"]["replay_verified"])
            code, _ = self.run_cli("--rollback", applied["receipt_path"])
            self.assertEqual(code, 0)
            self.assertEqual(path.read_bytes(), original)

    def test_receipt_tampering_and_malformed_shape_refuse(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "input.py"
            path.write_bytes(b"if True:\n\tprint('x')\n")
            _, applied = self.run_cli(path, "--apply")
            receipt = Path(applied["receipt_path"])
            payload = json.loads(receipt.read_text("utf-8"))
            payload["receipt_sha256"] = "0" * 64
            altered = Path(temp) / "altered.json"
            for data in (payload, [], {"receipt_kind": "apply"}, None):
                altered.write_text(json.dumps(data), "utf-8")
                for mode in ("--inspect-receipt", "--replay-receipt", "--rollback"):
                    before = path.read_bytes()
                    code, result = self.run_cli(mode, altered)
                    self.assertEqual(code, 2)
                    self.assertFalse(result["wrote"])
                    self.assertEqual(path.read_bytes(), before)

    def test_concurrent_writer_is_refused(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "input.py"
            original = b"if True\n    print('x')\n"
            path.write_bytes(original)
            with cli._mutation_lock(path):
                code, result = self.run_cli(path, "--apply")
            self.assertEqual(code, 2)
            self.assertEqual(result["refusal_code"], "apply_commit_failed")
            self.assertEqual(path.read_bytes(), original)
            self.assertFalse((path.parent / ".prefix-python-receipts").exists())
            code, _ = self.run_cli(path, "--apply")
            self.assertEqual(code, 0)

    def test_prepared_receipt_never_claims_failed_edit_as_applied(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "input.py"
            original = b"if True\n    print('x')\n"
            path.write_bytes(original)
            with patch.object(cli, "_atomic_write_text", side_effect=OSError("injected disk failure")), redirect_stdout(io.StringIO()):
                self.assertEqual(cli.main([str(path), "--apply", "--json"]), 2)
            self.assertEqual(path.read_bytes(), original)
            receipt, = (path.parent / ".prefix-python-receipts").glob("*.json")
            code, result = self.run_cli("--inspect-receipt", receipt)
            self.assertEqual(code, 2)
            self.assertEqual(result["refusal_code"], "receipt_target_postimage_mismatch")
            code, _ = self.run_cli(path, "--apply")
            self.assertEqual(code, 0)

    def test_stdin_crlf_hash_is_exact(self):
        source = b"if True\r\n    print('x')\r\n"
        result = subprocess.run([sys.executable, "-m", "prefix_python", "--stdin", "--json"],
                                cwd=ROOT, input=source, capture_output=True, timeout=20)
        import hashlib
        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(payload["input_sha256"], hashlib.sha256(source).hexdigest())
        self.assertEqual(payload["source"], "if True:\r\n    print('x')\r\n")

    def test_deep_expression_refuses_without_crashing(self):
        source = "x = " + "1+" * 4000 + "1\n"
        result = correct_source(source)
        self.assertEqual(result.state, "REFUSED")
        self.assertEqual(result.source, source)


if __name__ == "__main__":
    unittest.main()
