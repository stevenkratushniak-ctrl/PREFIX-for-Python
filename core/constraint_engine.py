"""
Constraint Engine

Compatibility wrappers for the canonical PREFIX for Python engine.
"""

from prefix_python.engine import ACCEPT_OUTCOMES, CorrectionResult, correct_source


def validate_transition(source: str) -> bool:
    return correct_source(source).status in ACCEPT_OUTCOMES


def enforce_transition(source: str) -> CorrectionResult:
    return correct_source(source)
