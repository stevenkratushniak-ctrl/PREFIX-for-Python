import ast
import unittest

from prefix_python import (
    ACCEPT_FIXED,
    ACCEPT_VALID,
    LANE_ADVISE,
    LANE_ANALYZE,
    LANE_APPLY,
    LANE_ROADMAP,
    REFUSE_INVALID,
    REFUSE_UNMAPPED,
    STATE_ADVISED,
    STATE_APPLIED,
    STATE_REFUSED,
    correct_source,
)


class PrefixPythonEngineTests(unittest.TestCase):
    def test_missing_colon_and_indent_are_corrected(self):
        result = correct_source('if ready\nprint("launch")\n')
        self.assertEqual(result.status, ACCEPT_FIXED)
        self.assertEqual(result.state, STATE_APPLIED)
        self.assertEqual(result.lane, LANE_APPLY)
        self.assertEqual(result.source, 'if ready:\n    print("launch")\n')
        self.assertEqual([event.rule_id for event in result.events], ["MISSING_COLON", "AUTO_INDENT"])
        self.assertTrue(result.parse_reparse_validated)
        self.assertEqual(result.structural_context["governing_law"], "single_lawful_continuation")
        self.assertEqual(result.continuation_graph["successor_count"], 1)
        self.assertGreaterEqual(result.legality_score["score"], 98)

    def test_async_function_missing_colon_is_corrected(self):
        result = correct_source("async def build()\n    return 'ok'\n")
        self.assertEqual(result.status, ACCEPT_FIXED)
        self.assertEqual(result.lane, LANE_APPLY)
        self.assertEqual(result.source, "async def build():\n    return 'ok'\n")
        self.assertEqual(result.events[-1].rule_id, "MISSING_COLON")

    def test_async_with_missing_colon_inside_async_function_is_corrected(self):
        result = correct_source("async def build():\n    async with lock\n        return 'ok'\n")
        self.assertEqual(result.status, ACCEPT_FIXED)
        self.assertEqual(result.lane, LANE_APPLY)
        self.assertEqual(result.source, "async def build():\n    async with lock:\n        return 'ok'\n")
        self.assertIn("MISSING_COLON", [event.rule_id for event in result.events])
        self.assertTrue(result.parse_reparse_validated)

    def test_except_star_missing_colon_is_corrected(self):
        result = correct_source("try:\n    raise ValueError()\nexcept* ValueError\n    pass\n")
        self.assertEqual(result.status, ACCEPT_FIXED)
        self.assertEqual(result.lane, LANE_APPLY)
        self.assertEqual(result.source, "try:\n    raise ValueError()\nexcept* ValueError:\n    pass\n")
        self.assertIn("MISSING_COLON", [event.rule_id for event in result.events])

    def test_empty_function_gets_pass(self):
        result = correct_source("def build():\n")
        self.assertEqual(result.status, ACCEPT_FIXED)
        self.assertEqual(result.lane, LANE_APPLY)
        self.assertEqual(result.source, "def build():\n    pass\n")
        self.assertEqual(result.events[-1].rule_id, "INSERT_PASS")

    def test_unmatched_delimiter_is_closed(self):
        result = correct_source('print("launch"\n')
        self.assertEqual(result.status, ACCEPT_FIXED)
        self.assertEqual(result.lane, LANE_APPLY)
        self.assertEqual(result.source, 'print("launch")\n')
        self.assertEqual(result.events[-1].rule_id, "CLOSE_DELIMITER")

    def test_extra_closing_delimiter_is_removed(self):
        result = correct_source('print("launch"))\n')
        self.assertEqual(result.status, ACCEPT_FIXED)
        self.assertEqual(result.lane, LANE_APPLY)
        self.assertEqual(result.source, 'print("launch")\n')
        self.assertEqual(result.events[-1].rule_id, "REMOVE_EXTRA_DELIMITER")

    def test_tabs_are_normalized_with_evidence(self):
        result = correct_source("if ready:\n\tprint('x')\n")
        self.assertEqual(result.status, ACCEPT_FIXED)
        self.assertEqual(result.lane, LANE_APPLY)
        self.assertEqual(result.source, "if ready:\n    print('x')\n")
        self.assertEqual(result.events[0].rule_id, "NORMALIZE_TABS")

    def test_windows_newlines_are_preserved(self):
        result = correct_source("if ready\r\nprint('x')\r\n")
        self.assertEqual(result.status, ACCEPT_FIXED)
        self.assertEqual(result.lane, LANE_APPLY)
        self.assertEqual(result.source, "if ready:\r\n    print('x')\r\n")

    def test_valid_source_is_left_alone(self):
        result = correct_source('print("launch")\n')
        self.assertEqual(result.status, ACCEPT_VALID)
        self.assertEqual(result.state, STATE_APPLIED)
        self.assertEqual(result.lane, LANE_APPLY)
        self.assertEqual(result.source, 'print("launch")\n')
        self.assertEqual(result.events, ())
        self.assertEqual(result.rounds, 0)
        self.assertFalse(result.to_dict()["changed"])

    def test_valid_async_source_is_left_alone(self):
        result = correct_source("async def build():\n    return 'ok'\n")
        self.assertEqual(result.status, ACCEPT_VALID)
        self.assertEqual(result.lane, LANE_APPLY)
        self.assertEqual(result.source, "async def build():\n    return 'ok'\n")

    def test_return_outside_function_is_analyze_lane(self):
        result = correct_source("return 1\n")
        self.assertEqual(result.status, REFUSE_INVALID)
        self.assertEqual(result.state, STATE_REFUSED)
        self.assertEqual(result.lane, LANE_ANALYZE)
        self.assertIn("return", result.refusal_reason.lower())
        self.assertEqual(result.refusal_code, "return_outside_function")
        self.assertFalse(result.mutation_performed)

    def test_orphaned_else_is_analyze_lane(self):
        result = correct_source("else:\n    print('x')\n")
        self.assertEqual(result.status, REFUSE_INVALID)
        self.assertEqual(result.lane, LANE_ANALYZE)
        self.assertIn("orphaned `else`", result.refusal_reason)
        self.assertFalse(result.mutation_performed)

    def test_orphaned_elif_is_advice_lane(self):
        result = correct_source("elif ready:\n    print('x')\n")
        self.assertEqual(result.status, REFUSE_UNMAPPED)
        self.assertEqual(result.state, STATE_ADVISED)
        self.assertEqual(result.lane, LANE_ADVISE)
        self.assertEqual(result.refusal_code, "elif_requires_explicit_authority")
        self.assertEqual(result.candidates[0].rule_id, "ELIF_TO_IF_CANDIDATE")
        self.assertEqual(result.candidates[0].rank, 1)
        self.assertGreater(result.candidates[0].score, 0)
        self.assertIsNotNone(result.recommendation_packet)
        self.assertEqual(result.recommendation_packet.recommended_rule_id, "ELIF_TO_IF_CANDIDATE")
        self.assertEqual(result.structural_context["governing_law"], "multiple_lawful_continuations")
        self.assertEqual(result.continuation_graph["successor_count"], 1)
        self.assertFalse(result.mutation_performed)

    def test_assignment_rhs_is_analyze_lane_not_guessed(self):
        result = correct_source("value =\n")
        self.assertEqual(result.status, REFUSE_UNMAPPED)
        self.assertEqual(result.state, STATE_REFUSED)
        self.assertEqual(result.lane, LANE_ANALYZE)
        self.assertEqual(result.refusal_code, "assignment_rhs_unmapped")
        self.assertIsNone(result.recommendation_packet)
        self.assertEqual(result.structural_context["surface_class"], "incomplete_expression")
        self.assertEqual(result.transition_governance["local_mutation_boundary"], "no_mutation")
        self.assertFalse(result.mutation_performed)

    def test_trailing_operator_is_analyze_lane_not_guessed(self):
        result = correct_source("value = 1 +\n")
        self.assertEqual(result.status, REFUSE_UNMAPPED)
        self.assertEqual(result.state, STATE_REFUSED)
        self.assertEqual(result.lane, LANE_ANALYZE)
        self.assertEqual(result.refusal_code, "trailing_operator_unmapped")
        self.assertFalse(result.mutation_performed)

    def test_partial_async_signature_is_completed_deterministically(self):
        result = correct_source("async def build(\n")
        self.assertEqual(result.status, ACCEPT_FIXED)
        self.assertEqual(result.lane, LANE_APPLY)
        self.assertEqual(result.source, "async def build():\n    pass\n")
        self.assertEqual([event.rule_id for event in result.events], ["CLOSE_DELIMITER", "MISSING_COLON", "INSERT_PASS"])

    def test_undefined_name_is_analyze_lane(self):
        result = correct_source("print(missing_name)\n")
        self.assertEqual(result.status, REFUSE_UNMAPPED)
        self.assertEqual(result.lane, LANE_ANALYZE)
        self.assertEqual(result.refusal_code, "undefined_name_unmapped")

    def test_nul_bytes_are_refused(self):
        result = correct_source("print('x')\x00")
        self.assertEqual(result.status, REFUSE_INVALID)
        self.assertEqual(result.lane, LANE_ANALYZE)
        self.assertEqual(result.refusal_code, "input_contains_nul")

    def test_oversized_input_is_refused(self):
        result = correct_source("x" * 1_048_577)
        self.assertEqual(result.status, REFUSE_INVALID)
        self.assertEqual(result.lane, LANE_ANALYZE)
        self.assertEqual(result.refusal_code, "input_too_large")

    def test_unshipped_surface_is_roadmap_lane(self):
        result = correct_source("print('x')))\n")
        self.assertEqual(result.status, REFUSE_UNMAPPED)
        self.assertEqual(result.state, STATE_REFUSED)
        self.assertEqual(result.lane, LANE_ROADMAP)
        self.assertEqual(result.refusal_code, "unsupported_syntax_state")
        self.assertEqual(result.structural_context["governing_law"], "unmapped_surface")
        self.assertFalse(result.mutation_performed)

    def test_repeatability_is_deterministic(self):
        first = correct_source('if ready\nprint("launch")\n').to_dict()
        second = correct_source('if ready\nprint("launch")\n').to_dict()
        self.assertEqual(first, second)

    def test_advice_repeatability_is_deterministic(self):
        first = correct_source("elif ready:\n    print('x')\n").to_dict()
        second = correct_source("elif ready:\n    print('x')\n").to_dict()
        self.assertEqual(first, second)

    def test_idempotency_holds_after_fix(self):
        first = correct_source('if ready\nprint("launch")\n')
        second = correct_source(first.source)
        self.assertEqual(first.status, ACCEPT_FIXED)
        self.assertEqual(second.status, ACCEPT_VALID)
        self.assertEqual(first.source, second.source)

    def test_idempotency_holds_after_async_fix(self):
        first = correct_source("async def build()\n    return 'ok'\n")
        second = correct_source(first.source)
        self.assertEqual(first.status, ACCEPT_FIXED)
        self.assertEqual(second.status, ACCEPT_VALID)
        self.assertEqual(first.source, second.source)

    def test_no_invalid_ast_is_committed_on_accept(self):
        result = correct_source('if ready\nprint("launch")\n')
        self.assertIn(result.status, {ACCEPT_VALID, ACCEPT_FIXED})
        ast.parse(result.source)

    def test_unicode_identifier_is_accepted(self):
        result = correct_source("def café():\n    return 'ok'\n")
        self.assertEqual(result.status, ACCEPT_VALID)


if __name__ == "__main__":
    unittest.main()
