import sys
from pathlib import Path

PRODUCT_ROOT = Path(__file__).resolve().parent.parent
if str(PRODUCT_ROOT) not in sys.path:
    sys.path.insert(0, str(PRODUCT_ROOT))

from prefix_python.engine import correct_source


def main() -> None:
    demo_path = PRODUCT_ROOT / "examples" / "broken_missing_colon.txt"
    source = demo_path.read_text(encoding="utf-8")
    result = correct_source(source)

    print("PREFIX for Python Demo")
    print("=" * 32)
    print("Status:", result.status)
    print("")
    print("Input:")
    print(source)
    print("Output:")
    print(result.source)
    if result.refusal_reason:
        print("Refusal:", result.refusal_reason)
    for event in result.events:
        print(f"- {event.rule_id} line {event.line}: {event.reason}")


if __name__ == "__main__":
    main()
