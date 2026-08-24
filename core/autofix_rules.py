"""
Legacy rule identifiers retained for documentation compatibility.
"""

AUTO_FIX_RULES = {
    "MISSING_COLON": "Append a single block colon.",
    "AUTO_INDENT": "Indent the first block statement by one deterministic level.",
    "INSERT_PASS": "Insert `pass` into an empty required block.",
    "CLOSE_DELIMITER": "Append the missing closing delimiter at line end.",
    "REMOVE_EXTRA_DELIMITER": "Remove a singular extra closing delimiter when one parse-valid repair exists.",
    "ELIF_TO_IF_CANDIDATE": "Surface orphaned `elif` to `if` as a candidate-only repair, never an automatic mutation.",
}
