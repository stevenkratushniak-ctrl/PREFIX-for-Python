import sys
from .cli import main as correction_main
from .entitlement_cli import main as license_main
from .entitlement_gate import gate
if __name__ == '__main__':
    if len(sys.argv)>1 and sys.argv[1]=='license': raise SystemExit(license_main(sys.argv[2:]))
    blocked=gate(sys.argv[1:])
    if blocked is not None: raise SystemExit(blocked)
    raise SystemExit(correction_main())
