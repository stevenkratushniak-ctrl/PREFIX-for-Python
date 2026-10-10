"""Commercial entry wrapper; preserve the qualified operator implementation."""
import sys

from .entitlement_gate import gate
from .operator_console import main as operator_main


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    refusal = gate(arguments)
    return refusal if refusal is not None else operator_main(arguments)


if __name__ == '__main__':
    raise SystemExit(main())
