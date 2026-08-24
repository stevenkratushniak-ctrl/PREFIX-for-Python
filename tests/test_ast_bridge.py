import ast
import unittest

from prefix_python.ast_bridge import (
    PYTHON_VERSION_PIN,
    build_ast_construction_signature,
    diff_ast,
    parse_to_ast,
    validate_ast_legality,
    validate_source_text,
)


class PrefixPythonAstBridgeTests(unittest.TestCase):
    def test_parse_to_ast_returns_module(self):
        tree = parse_to_ast("print('x')\n")
        self.assertIsInstance(tree, ast.Module)

    def test_validate_source_text_accepts_parseable_source(self):
        result = validate_source_text("print('x')\n")
        self.assertTrue(result.is_valid)
        self.assertIsNotNone(result.authority)
        self.assertEqual(result.authority.python_version_pin, PYTHON_VERSION_PIN)
        self.assertIn("signature_sha256", result.authority.construction_signature)

    def test_validate_source_text_rejects_unparseable_source(self):
        result = validate_source_text("if ready\nprint('x')\n")
        self.assertFalse(result.is_valid)
        self.assertIsNotNone(result.syntax_error)

    def test_diff_ast_changes_when_structure_changes(self):
        before = parse_to_ast("print('x')\n")
        after = parse_to_ast("print('y')\n")
        diff = diff_ast(before, after)
        self.assertTrue(diff["changed"])
        self.assertNotEqual(diff["before_sha256"], diff["after_sha256"])

    def test_validate_source_text_accepts_python_3_12_type_alias(self):
        result = validate_source_text("type UserId = int\n")
        self.assertTrue(result.is_valid)
        self.assertEqual(result.authority.python_version_pin, PYTHON_VERSION_PIN)

    def test_validate_ast_legality_rejects_empty_function_body(self):
        tree = ast.Module(
            body=[
                ast.FunctionDef(
                    name="build",
                    args=ast.arguments(
                        posonlyargs=[],
                        args=[],
                        vararg=None,
                        kwonlyargs=[],
                        kw_defaults=[],
                        kwarg=None,
                        defaults=[],
                    ),
                    body=[],
                    decorator_list=[],
                    returns=None,
                    type_comment=None,
                )
            ],
            type_ignores=[],
        )
        report = validate_ast_legality(tree, "def build():\n    pass\n")
        self.assertGreater(report.violation_count, 0)
        self.assertEqual(report.violations[0].code, "BLOCK_BODY")

    def test_validate_ast_legality_rejects_compare_arity_mismatch(self):
        tree = ast.parse("print(x)\n")
        compare = ast.Compare(left=ast.Name(id="x", ctx=ast.Load()), ops=[ast.Eq()], comparators=[])
        tree.body[0].value = compare
        report = validate_ast_legality(tree, "print(x)\n")
        self.assertTrue(any(violation.code == "COMPARE_ARITY" for violation in report.violations))

    def test_build_ast_construction_signature_counts_blocks_and_async(self):
        tree = ast.parse("async def build():\n    async with lock:\n        return 1\n")
        signature = build_ast_construction_signature(tree)
        self.assertGreaterEqual(signature["async_node_count"], 2)
        self.assertGreaterEqual(signature["block_node_count"], 2)
        self.assertIn("signature_sha256", signature)


if __name__ == "__main__":
    unittest.main()
