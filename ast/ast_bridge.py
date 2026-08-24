"""
AST Bridge

Compatibility wrapper for the canonical PREFIX for Python AST authority module.
"""

from prefix_python.ast_bridge import (
    PYTHON_VERSION_PIN,
    AstAuthority,
    AstValidationResult,
    diff_ast,
    parse_to_ast,
    validate_source_text,
)

__all__ = [
    "PYTHON_VERSION_PIN",
    "AstAuthority",
    "AstValidationResult",
    "diff_ast",
    "parse_to_ast",
    "validate_source_text",
]
