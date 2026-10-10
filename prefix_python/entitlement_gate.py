from __future__ import annotations

import hashlib
import json
import sys

from .engine import MAX_SOURCE_BYTES
from .entitlement import require


def gate(argv: list[str]) -> int | None:
    if '--version' in argv or '--help' in argv or '-h' in argv:
        return None
    status = require()
    if status.entitled:
        return None

    # Bind denied editor requests to their unchanged input. Allowed requests
    # retain the qualified CLI input path and its bounds and custody checks.
    source = ''
    input_error = None
    if '--stdin' in argv and '--json' in argv:
        try:
            stream = getattr(sys.stdin, 'buffer', sys.stdin)
            raw = stream.read(MAX_SOURCE_BYTES + 1)
            encoded = raw.encode('utf-8') if isinstance(raw, str) else raw
            if len(encoded) > MAX_SOURCE_BYTES:
                input_error = 'source_too_large'
            else:
                source = encoded.decode('utf-8')
        except (OSError, UnicodeError):
            input_error = 'input_decode_or_read_error'
    digest = hashlib.sha256(source.encode('utf-8')).hexdigest()
    payload = {
        'accepted': False, 'changed': False, 'mutation_performed': False,
        'wrote': False, 'status': 'REFUSE_INVALID', 'state': 'REFUSED',
        'lane': 'ANALYZE', 'refusal_code': 'entitlement_required',
        'refusal_reason': status.message, 'entitlement': status.to_dict(),
        'source': source, 'input_sha256': digest, 'output_sha256': digest,
        'events': [], 'candidates': [], 'receipt_path': None,
    }
    if input_error:
        payload['input_error'] = input_error
    if '--json' in argv:
        sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True) + '\n')
    else:
        sys.stdout.write('PREFIX activation required.\n' + status.message + '\n'
                         'Run `prefix-python license status` or activate a purchased license.\n')
    return 3
