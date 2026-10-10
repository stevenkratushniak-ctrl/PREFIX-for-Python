"""Run regression tests using an isolated synthetic cache, never a provider key."""
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import unittest

source = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(source))
from prefix_python.entitlement import fp, write, PRODUCTION_AUTHORITY

with tempfile.TemporaryDirectory(prefix='prefix-distribution-tests-') as temporary:
    root = Path(temporary) / 'synthetic-entitlement'
    key = 'SYNTHETIC-TEST-FIXTURE-NO-PROVIDER-ACTIVATION'
    write(root, {'schema': 1, 'policy_version': 1, 'instance_id': 'synthetic-instance',
                'install_id': 'synthetic-install', 'license_fingerprint': fp(key),
                'store_id': PRODUCTION_AUTHORITY.store_id,
                'product_id': PRODUCTION_AUTHORITY.product_id,
                'variant_id': PRODUCTION_AUTHORITY.variant_id,
                'last_validated_at': int(time.time())}, key)
    os.environ['PREFIX_ENTITLEMENT_ROOT'] = str(root)
    os.chdir(source)
    suite = unittest.defaultTestLoader.discover(str(source / 'tests'))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    summary = {'fixture': 'Isolated synthetic signed cache only; no provider/network activation.',
               'tests': result.testsRun, 'passed': result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped),
               'failures': len(result.failures), 'errors': len(result.errors),
               'skipped': len(result.skipped), 'success': result.wasSuccessful(),
               'python': sys.version, 'platform': sys.platform}
    destination = os.environ.get('PREFIX_TEST_RESULT_JSON')
    if destination:
        Path(destination).write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(summary))
    sys.exit(0 if result.wasSuccessful() else 1)
