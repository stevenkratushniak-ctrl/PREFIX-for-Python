import contextlib
import hashlib
import io
import json
import unittest
from unittest.mock import patch

from prefix_python import cli, entitlement_gate
from prefix_python.entitlement import Status


class DistributionEntryTests(unittest.TestCase):
    denied = Status('UNACTIVATED', False, 'PREFIX is not activated.')
    entitled = Status('ACTIVE_CACHED', True, 'Synthetic fixture only.')

    def test_installed_console_script_cannot_bypass_entitlement(self):
        out = io.StringIO()
        with patch.object(entitlement_gate, 'require', return_value=self.denied), \
                patch.object(cli, '_correction_main') as correction, contextlib.redirect_stdout(out):
            code = cli.main(['sample.py', '--apply', '--json'])
        self.assertEqual(code, 3)
        correction.assert_not_called()
        self.assertFalse(json.loads(out.getvalue())['mutation_performed'])

    def test_denied_stdin_is_bound_and_unchanged(self):
        source = 'if ready\n\tprint("private source")\n'
        out = io.StringIO()
        with patch.object(entitlement_gate, 'require', return_value=self.denied), \
                patch('sys.stdin', io.StringIO(source)), contextlib.redirect_stdout(out):
            code = cli.main(['--stdin', '--json'])
        value = json.loads(out.getvalue())
        digest = hashlib.sha256(source.encode()).hexdigest()
        self.assertEqual(code, 3)
        self.assertEqual(value['source'], source)
        self.assertEqual(value['input_sha256'], digest)
        self.assertEqual(value['output_sha256'], digest)
        self.assertEqual(value['refusal_code'], 'entitlement_required')
        self.assertEqual(value['events'], [])
        self.assertFalse(value['mutation_performed'])

    def test_entitled_gate_does_not_consume_stdin(self):
        source = io.StringIO('x = 1\n')
        with patch.object(entitlement_gate, 'require', return_value=self.entitled), patch('sys.stdin', source):
            self.assertIsNone(entitlement_gate.gate(['--stdin', '--json']))
        self.assertEqual(source.tell(), 0)

    def test_license_dispatch_uses_shared_cli_without_correction(self):
        with patch('prefix_python.entitlement_cli.main', return_value=3) as license_main, \
                patch.object(cli, '_correction_main') as correction:
            self.assertEqual(cli.main(['license', 'status', '--json']), 3)
        license_main.assert_called_once_with(['status', '--json'])
        correction.assert_not_called()

    def test_entitled_dispatch_retains_qualified_correction_main(self):
        with patch.object(entitlement_gate, 'require', return_value=self.entitled), \
                patch.object(cli, '_correction_main', return_value=0) as correction:
            self.assertEqual(cli.main(['--stdin', '--json']), 0)
        correction.assert_called_once_with(['--stdin', '--json'])

    def test_commercial_operator_entry_cannot_bypass_entitlement(self):
        from prefix_python import commercial_operator_console
        with patch.object(commercial_operator_console, 'gate', return_value=3), \
                patch.object(commercial_operator_console, 'operator_main') as operator:
            self.assertEqual(commercial_operator_console.main(['sample.py']), 3)
        operator.assert_not_called()


if __name__ == '__main__':
    unittest.main()
