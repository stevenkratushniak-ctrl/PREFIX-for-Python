"""
Editor Adapter

Receives text from the editor and delegates it to the canonical engine.
"""

from prefix_python.engine import CorrectionResult

from core.constraint_engine import enforce_transition


def handle_transition(source: str) -> CorrectionResult:
    return enforce_transition(source)
