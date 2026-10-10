import contextlib
import getpass
import io
import unittest
from unittest.mock import patch
from prefix_python import entitlement_cli
from prefix_python.entitlement import Status

class SecureActivationInputTests(unittest.TestCase):
    key = 'synthetic-private-input-for-transport-test'
    denied = Status('INVALID_KEY',False,'The license key is invalid or inactive.')

    def run_main(self,args,input_text=''):
        out,err=io.StringIO(),io.StringIO()
        with patch('sys.stdin',io.StringIO(input_text)),contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):
            result=entitlement_cli.main(args)
        return result,out.getvalue(),err.getvalue()

    def test_stdin_transports_key_without_output(self):
        with patch.object(entitlement_cli,'activate',return_value=self.denied) as activate:
            code,out,err=self.run_main(['activate','--stdin','--json'],self.key+'\n')
        self.assertEqual(code,3)
        activate.assert_called_once_with(self.key)
        self.assertNotIn(self.key,out+err)

    def test_hidden_prompt_is_default(self):
        with patch.object(entitlement_cli.getpass,'getpass',return_value=self.key),patch.object(entitlement_cli,'activate',return_value=self.denied) as activate:
            code,out,err=self.run_main(['activate','--json'])
        self.assertEqual(code,3)
        activate.assert_called_once_with(self.key)
        self.assertNotIn(self.key,out+err)

    def test_positional_key_rejected_without_echo(self):
        err=io.StringIO()
        with contextlib.redirect_stderr(err),patch.object(entitlement_cli,'activate') as activate:
            with self.assertRaises(SystemExit) as ex:entitlement_cli.main(['activate',self.key])
        self.assertEqual(ex.exception.code,2)
        activate.assert_not_called()
        self.assertNotIn(self.key,err.getvalue())

    def test_echo_fallback_refused(self):
        with patch.object(entitlement_cli.getpass,'getpass',side_effect=getpass.GetPassWarning),contextlib.redirect_stderr(io.StringIO()),patch.object(entitlement_cli,'activate') as activate:
            with self.assertRaises(SystemExit):entitlement_cli.main(['activate'])
        activate.assert_not_called()

    def test_empty_stdin_refused_before_activation(self):
        with patch('sys.stdin',io.StringIO('\n')),contextlib.redirect_stderr(io.StringIO()),patch.object(entitlement_cli,'activate') as activate:
            with self.assertRaises(SystemExit):entitlement_cli.main(['activate','--stdin'])
        activate.assert_not_called()

    def test_oversized_stdin_refused_before_activation(self):
        with patch('sys.stdin',io.StringIO('x'*4097)),contextlib.redirect_stderr(io.StringIO()),patch.object(entitlement_cli,'activate') as activate:
            with self.assertRaises(SystemExit):entitlement_cli.main(['activate','--stdin'])
        activate.assert_not_called()

    def test_stdin_not_allowed_on_status(self):
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):entitlement_cli.main(['status','--stdin'])

if __name__=='__main__':unittest.main()
