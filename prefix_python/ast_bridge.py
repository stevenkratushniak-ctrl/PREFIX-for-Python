from __future__ import annotations

import ast
import hashlib
import io
import sys
import tokenize
from dataclasses import dataclass

PYTHON_VERSION_PIN = "3.12"

PYTHON_3_12_AST_NODES = {
    "Add",
    "And",
    "AnnAssign",
    "Assert",
    "Assign",
    "AsyncFor",
    "AsyncFunctionDef",
    "AsyncWith",
    "Attribute",
    "AugAssign",
    "Await",
    "BinOp",
    "BitAnd",
    "BitOr",
    "BitXor",
    "BoolOp",
    "Break",
    "Call",
    "ClassDef",
    "Compare",
    "Constant",
    "Continue",
    "Del",
    "Delete",
    "Dict",
    "DictComp",
    "Div",
    "Eq",
    "ExceptHandler",
    "Expr",
    "Expression",
    "FloorDiv",
    "For",
    "FormattedValue",
    "FunctionDef",
    "GeneratorExp",
    "Global",
    "Gt",
    "GtE",
    "If",
    "IfExp",
    "Import",
    "ImportFrom",
    "In",
    "Interactive",
    "Invert",
    "Is",
    "IsNot",
    "JoinedStr",
    "LShift",
    "Lambda",
    "List",
    "ListComp",
    "Load",
    "Lt",
    "LtE",
    "Match",
    "MatchAs",
    "MatchClass",
    "MatchMapping",
    "MatchOr",
    "MatchSequence",
    "MatchSingleton",
    "MatchStar",
    "MatchValue",
    "MatMult",
    "Mod",
    "Module",
    "Mult",
    "Name",
    "NamedExpr",
    "Nonlocal",
    "Not",
    "NotEq",
    "NotIn",
    "Or",
    "ParamSpec",
    "Pass",
    "Pow",
    "Raise",
    "Return",
    "RShift",
    "Set",
    "SetComp",
    "Slice",
    "Starred",
    "Store",
    "Sub",
    "Subscript",
    "Try",
    "TryStar",
    "Tuple",
    "TypeAlias",
    "TypeIgnore",
    "TypeVar",
    "TypeVarTuple",
    "UAdd",
    "USub",
    "UnaryOp",
    "While",
    "With",
    "Yield",
    "YieldFrom",
    "alias",
    "arg",
    "arguments",
    "comprehension",
    "keyword",
    "match_case",
    "withitem",
}


@dataclass(frozen=True)
class LegalityViolation:
    code: str
    path: str
    detail: str

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "detail": self.detail,
            "path": self.path,
        }


@dataclass(frozen=True)
class AstLegalityReport:
    ast_sha256: str
    token_sha256: str
    node_count: int
    edge_count: int
    token_count: int
    violation_count: int
    violations: tuple[LegalityViolation, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "ast_sha256": self.ast_sha256,
            "edge_count": self.edge_count,
            "node_count": self.node_count,
            "token_count": self.token_count,
            "token_sha256": self.token_sha256,
            "violation_count": self.violation_count,
            "violations": [violation.to_dict() for violation in self.violations],
        }


@dataclass(frozen=True)
class AstAuthority:
    tree: ast.AST
    ast_sha256: str
    construction_signature: dict[str, object]
    node_count: int
    python_version_pin: str
    roundtrip_sha256: str
    token_sha256: str
    legality_report: AstLegalityReport


@dataclass(frozen=True)
class AstValidationResult:
    is_valid: bool
    authority: AstAuthority | None = None
    syntax_error: SyntaxError | None = None
    failure_reason: str | None = None


def parse_to_ast(code: str) -> ast.AST:
    _assert_python_version_pin()
    return ast.parse(code, mode="exec")


def diff_ast(old_ast: ast.AST, new_ast: ast.AST) -> dict[str, object]:
    old_dump = ast.dump(old_ast, annotate_fields=True, include_attributes=False)
    new_dump = ast.dump(new_ast, annotate_fields=True, include_attributes=False)
    return {
        "before_sha256": _sha256_text(old_dump),
        "after_sha256": _sha256_text(new_dump),
        "changed": old_dump != new_dump,
    }


def validate_source_text(code: str) -> AstValidationResult:
    try:
        tree = parse_to_ast(code)
        compile(code, "<prefix-python>", "exec")
    except RuntimeError as exc:
        return AstValidationResult(is_valid=False, failure_reason=str(exc))
    except SyntaxError as exc:
        return AstValidationResult(is_valid=False, syntax_error=exc, failure_reason=exc.msg or "Syntax error")

    try:
        token_infos, token_sha256 = _tokenize_source(code)
    except tokenize.TokenError as exc:
        return AstValidationResult(is_valid=False, failure_reason=f"Tokenization failed: {exc}")

    legality_report = validate_ast_legality(tree, code, token_infos=token_infos, token_sha256=token_sha256)
    if legality_report.violation_count:
        first = legality_report.violations[0]
        return AstValidationResult(
            is_valid=False,
            failure_reason=f"{first.code} at {first.path}: {first.detail}",
        )

    roundtrip_source = ast.unparse(tree)
    try:
        roundtrip_tree = ast.parse(roundtrip_source, mode="exec")
    except SyntaxError as exc:
        return AstValidationResult(
            is_valid=False,
            syntax_error=exc,
            failure_reason="Roundtrip parse failed after AST unparse.",
        )

    roundtrip_sha256 = _sha256_text(ast.dump(roundtrip_tree, annotate_fields=True, include_attributes=False))
    if legality_report.ast_sha256 != roundtrip_sha256:
        return AstValidationResult(
            is_valid=False,
            failure_reason="Roundtrip AST diverged from the admitted AST authority surface.",
        )

    authority = AstAuthority(
        tree=tree,
        ast_sha256=legality_report.ast_sha256,
        construction_signature=build_ast_construction_signature(tree),
        node_count=legality_report.node_count,
        python_version_pin=PYTHON_VERSION_PIN,
        roundtrip_sha256=roundtrip_sha256,
        token_sha256=token_sha256,
        legality_report=legality_report,
    )
    return AstValidationResult(is_valid=True, authority=authority)


def validate_ast_legality(
    tree: ast.AST,
    source_text: str,
    *,
    token_infos: list[tokenize.TokenInfo] | None = None,
    token_sha256: str | None = None,
) -> AstLegalityReport:
    if token_infos is None or token_sha256 is None:
        token_infos, token_sha256 = _tokenize_source(source_text)

    ast_sha256 = _sha256_text(ast.dump(tree, annotate_fields=True, include_attributes=False))
    lines = source_text.splitlines()
    violations: list[LegalityViolation] = []
    edge_count = 0
    node_count = 0

    def visit(node: ast.AST, path: str) -> None:
        nonlocal edge_count, node_count
        node_count += 1
        node_name = type(node).__name__
        if node_name not in PYTHON_3_12_AST_NODES:
            violations.append(
                LegalityViolation(
                    code="UNKNOWN_NODE",
                    path=path,
                    detail=f"{node_name} is outside the pinned Python {PYTHON_VERSION_PIN} node registry.",
                )
            )
        _validate_positions(node, lines, path, violations)
        _validate_node_contract(node, path, violations)

        for field_name, value in ast.iter_fields(node):
            field_path = f"{path}.{field_name}"
            if isinstance(value, ast.AST):
                edge_count += 1
                _validate_parent_child_edge(node, field_name, value, field_path, violations)
                visit(value, field_path)
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    if isinstance(child, ast.AST):
                        edge_count += 1
                        child_path = f"{field_path}[{index}]"
                        _validate_parent_child_edge(node, field_name, child, child_path, violations)
                        visit(child, child_path)
                    elif child is not None:
                        violations.append(
                            LegalityViolation(
                                code="NON_AST_LIST_ITEM",
                                path=f"{field_path}[{index}]",
                                detail=f"List field contains non-AST value {child!r}.",
                            )
                        )

    visit(tree, "root")
    return AstLegalityReport(
        ast_sha256=ast_sha256,
        token_sha256=token_sha256,
        node_count=node_count,
        edge_count=edge_count,
        token_count=len(token_infos),
        violation_count=len(violations),
        violations=tuple(violations),
    )


def build_ast_construction_signature(tree: ast.AST) -> dict[str, object]:
    block_nodes = 0
    async_nodes = 0
    delimiter_sensitive_nodes = 0
    scope_boundary_nodes = 0
    pattern_nodes = 0

    for node in ast.walk(tree):
        if isinstance(
            node,
            (
                ast.If,
                ast.For,
                ast.AsyncFor,
                ast.While,
                ast.Try,
                ast.TryStar,
                ast.With,
                ast.AsyncWith,
                ast.Match,
                ast.FunctionDef,
                ast.AsyncFunctionDef,
                ast.ClassDef,
            ),
        ):
            block_nodes += 1
        if isinstance(node, (ast.AsyncFunctionDef, ast.AsyncFor, ast.AsyncWith, ast.Await)):
            async_nodes += 1
        if isinstance(node, (ast.Call, ast.Tuple, ast.List, ast.Dict, ast.Set, ast.Subscript)):
            delimiter_sensitive_nodes += 1
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda, ast.Module)):
            scope_boundary_nodes += 1
        if isinstance(node, ast.pattern):
            pattern_nodes += 1

    payload = {
        "async_node_count": async_nodes,
        "block_node_count": block_nodes,
        "delimiter_sensitive_node_count": delimiter_sensitive_nodes,
        "pattern_node_count": pattern_nodes,
        "scope_boundary_node_count": scope_boundary_nodes,
    }
    payload["signature_sha256"] = _sha256_text(repr(sorted(payload.items())))
    return payload


def _tokenize_source(code: str) -> tuple[list[tokenize.TokenInfo], str]:
    token_infos = list(tokenize.generate_tokens(io.StringIO(code).readline))
    canonical = [
        (token.type, token.string, token.start, token.end)
        for token in token_infos
        if token.type != tokenize.ENCODING
    ]
    return token_infos, _sha256_text(repr(canonical))


def _validate_positions(
    node: ast.AST,
    lines: list[str],
    path: str,
    violations: list[LegalityViolation],
) -> None:
    if not hasattr(node, "lineno"):
        return

    lineno = getattr(node, "lineno", None)
    end_lineno = getattr(node, "end_lineno", lineno)
    col_offset = getattr(node, "col_offset", None)
    end_col_offset = getattr(node, "end_col_offset", col_offset)

    if not isinstance(lineno, int) or lineno < 1 or lineno > max(len(lines), 1):
        violations.append(
            LegalityViolation(
                code="POSITION_RANGE",
                path=path,
                detail=f"lineno {lineno!r} is outside the source bounds.",
            )
        )
        return

    if not isinstance(end_lineno, int) or end_lineno < lineno or end_lineno > max(len(lines), 1):
        violations.append(
            LegalityViolation(
                code="POSITION_RANGE",
                path=path,
                detail=f"end_lineno {end_lineno!r} is outside the source bounds.",
            )
        )
        return

    if not isinstance(col_offset, int) or col_offset < 0:
        violations.append(
            LegalityViolation(
                code="COLUMN_RANGE",
                path=path,
                detail=f"col_offset {col_offset!r} is invalid.",
            )
        )

    if not isinstance(end_col_offset, int) or end_col_offset < 0:
        violations.append(
            LegalityViolation(
                code="COLUMN_RANGE",
                path=path,
                detail=f"end_col_offset {end_col_offset!r} is invalid.",
            )
        )

    if isinstance(col_offset, int) and isinstance(end_col_offset, int) and lineno == end_lineno and end_col_offset < col_offset:
        violations.append(
            LegalityViolation(
                code="COLUMN_RANGE",
                path=path,
                detail="end_col_offset precedes col_offset on the same line.",
            )
        )


def _validate_parent_child_edge(
    parent: ast.AST,
    field_name: str,
    child: ast.AST,
    path: str,
    violations: list[LegalityViolation],
) -> None:
    parent_name = type(parent).__name__
    child_name = type(child).__name__

    def require(predicate: bool, code: str, detail: str) -> None:
        if not predicate:
            violations.append(LegalityViolation(code=code, path=path, detail=detail))

    if isinstance(parent, ast.Module):
        if field_name == "body":
            require(isinstance(child, ast.stmt), "PARENT_CHILD_LEGALITY", f"Module.body cannot contain {child_name}.")
        elif field_name == "type_ignores":
            require(isinstance(child, ast.TypeIgnore), "PARENT_CHILD_LEGALITY", f"Module.type_ignores cannot contain {child_name}.")

    if isinstance(parent, ast.Expression) and field_name == "body":
        require(isinstance(child, ast.expr), "PARENT_CHILD_LEGALITY", f"Expression.body cannot contain {child_name}.")

    if isinstance(parent, ast.Interactive) and field_name == "body":
        require(isinstance(child, ast.stmt), "PARENT_CHILD_LEGALITY", f"Interactive.body cannot contain {child_name}.")

    if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        if field_name == "body":
            require(isinstance(child, ast.stmt), "PARENT_CHILD_LEGALITY", f"{parent_name}.body cannot contain {child_name}.")
        if field_name == "decorator_list":
            require(isinstance(child, ast.expr), "PARENT_CHILD_LEGALITY", f"{parent_name}.decorator_list cannot contain {child_name}.")

    if isinstance(parent, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.With, ast.AsyncWith, ast.Match, ast.Try, ast.TryStar, ast.ExceptHandler)):
        if field_name in {"body", "orelse", "finalbody"}:
            require(isinstance(child, ast.stmt), "PARENT_CHILD_LEGALITY", f"{parent_name}.{field_name} cannot contain {child_name}.")
        if field_name == "handlers":
            require(isinstance(child, ast.ExceptHandler), "PARENT_CHILD_LEGALITY", f"{parent_name}.handlers cannot contain {child_name}.")
        if field_name == "items":
            require(isinstance(child, ast.withitem), "PARENT_CHILD_LEGALITY", f"{parent_name}.items cannot contain {child_name}.")
        if field_name == "cases":
            require(isinstance(child, ast.match_case), "PARENT_CHILD_LEGALITY", f"{parent_name}.cases cannot contain {child_name}.")

    if isinstance(parent, ast.match_case):
        if field_name == "pattern":
            require(isinstance(child, ast.pattern), "PARENT_CHILD_LEGALITY", f"match_case.pattern cannot contain {child_name}.")
        if field_name == "guard":
            require(isinstance(child, ast.expr), "PARENT_CHILD_LEGALITY", f"match_case.guard cannot contain {child_name}.")
        if field_name == "body":
            require(isinstance(child, ast.stmt), "PARENT_CHILD_LEGALITY", f"match_case.body cannot contain {child_name}.")

    if isinstance(parent, ast.arguments):
        if field_name in {"posonlyargs", "args", "kwonlyargs"}:
            require(isinstance(child, ast.arg), "PARENT_CHILD_LEGALITY", f"arguments.{field_name} cannot contain {child_name}.")
        if field_name in {"defaults", "kw_defaults"}:
            require(isinstance(child, ast.expr), "PARENT_CHILD_LEGALITY", f"arguments.{field_name} cannot contain {child_name}.")
        if field_name in {"vararg", "kwarg"}:
            require(isinstance(child, ast.arg), "PARENT_CHILD_LEGALITY", f"arguments.{field_name} cannot contain {child_name}.")

    if isinstance(parent, ast.Call):
        if field_name in {"func", "args"}:
            require(isinstance(child, ast.expr), "PARENT_CHILD_LEGALITY", f"Call.{field_name} cannot contain {child_name}.")
        if field_name == "keywords":
            require(isinstance(child, ast.keyword), "PARENT_CHILD_LEGALITY", f"Call.keywords cannot contain {child_name}.")

    if isinstance(parent, ast.Compare):
        if field_name in {"left", "comparators"}:
            require(isinstance(child, ast.expr), "PARENT_CHILD_LEGALITY", f"Compare.{field_name} cannot contain {child_name}.")
        if field_name == "ops":
            require(isinstance(child, ast.cmpop), "PARENT_CHILD_LEGALITY", f"Compare.ops cannot contain {child_name}.")

    if isinstance(parent, ast.BinOp):
        if field_name in {"left", "right"}:
            require(isinstance(child, ast.expr), "PARENT_CHILD_LEGALITY", f"BinOp.{field_name} cannot contain {child_name}.")
        if field_name == "op":
            require(isinstance(child, ast.operator), "PARENT_CHILD_LEGALITY", f"BinOp.op cannot contain {child_name}.")

    if isinstance(parent, ast.BoolOp):
        if field_name == "values":
            require(isinstance(child, ast.expr), "PARENT_CHILD_LEGALITY", f"BoolOp.values cannot contain {child_name}.")
        if field_name == "op":
            require(isinstance(child, ast.boolop), "PARENT_CHILD_LEGALITY", f"BoolOp.op cannot contain {child_name}.")

    if isinstance(parent, ast.UnaryOp):
        if field_name == "operand":
            require(isinstance(child, ast.expr), "PARENT_CHILD_LEGALITY", f"UnaryOp.operand cannot contain {child_name}.")
        if field_name == "op":
            require(isinstance(child, ast.unaryop), "PARENT_CHILD_LEGALITY", f"UnaryOp.op cannot contain {child_name}.")

    if isinstance(parent, ast.comprehension):
        if field_name in {"target", "iter", "ifs"}:
            require(isinstance(child, ast.expr), "PARENT_CHILD_LEGALITY", f"comprehension.{field_name} cannot contain {child_name}.")

    if isinstance(parent, ast.withitem):
        if field_name in {"context_expr", "optional_vars"}:
            require(isinstance(child, ast.expr), "PARENT_CHILD_LEGALITY", f"withitem.{field_name} cannot contain {child_name}.")


def _validate_node_contract(node: ast.AST, path: str, violations: list[LegalityViolation]) -> None:
    def require(predicate: bool, code: str, detail: str) -> None:
        if not predicate:
            violations.append(LegalityViolation(code=code, path=path, detail=detail))

    if isinstance(node, ast.Module):
        require(all(isinstance(item, ast.stmt) for item in node.body), "MODULE_BODY", "Module.body must contain only statements.")
        require(all(isinstance(item, ast.TypeIgnore) for item in node.type_ignores), "MODULE_TYPE_IGNORES", "Module.type_ignores must contain only TypeIgnore nodes.")
    elif isinstance(node, ast.Interactive):
        require(all(isinstance(item, ast.stmt) for item in node.body), "INTERACTIVE_BODY", "Interactive.body must contain only statements.")
    elif isinstance(node, ast.Expression):
        require(isinstance(node.body, ast.expr), "EXPRESSION_BODY", "Expression.body must be an expression.")
    elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        require(bool(node.name) and node.name.isidentifier(), "IDENTIFIER", f"{type(node).__name__}.name must be a valid identifier.")
        require(isinstance(node.args, ast.arguments), "FUNCTION_ARGS", f"{type(node).__name__}.args must be arguments.")
        require(len(node.body) > 0 and all(isinstance(item, ast.stmt) for item in node.body), "BLOCK_BODY", f"{type(node).__name__}.body must contain at least one statement.")
        require(all(isinstance(item, ast.expr) for item in node.decorator_list), "DECORATORS", f"{type(node).__name__}.decorator_list must contain expressions.")
        require(node.returns is None or isinstance(node.returns, ast.expr), "RETURNS", f"{type(node).__name__}.returns must be an expression or None.")
    elif isinstance(node, ast.ClassDef):
        require(bool(node.name) and node.name.isidentifier(), "IDENTIFIER", "ClassDef.name must be a valid identifier.")
        require(len(node.body) > 0 and all(isinstance(item, ast.stmt) for item in node.body), "BLOCK_BODY", "ClassDef.body must contain at least one statement.")
        require(all(isinstance(item, ast.expr) for item in node.bases), "BASES", "ClassDef.bases must contain expressions.")
        require(all(isinstance(item, ast.keyword) for item in node.keywords), "KEYWORDS", "ClassDef.keywords must contain keyword nodes.")
        require(all(isinstance(item, ast.expr) for item in node.decorator_list), "DECORATORS", "ClassDef.decorator_list must contain expressions.")
    elif isinstance(node, ast.If):
        require(isinstance(node.test, ast.expr), "IF_TEST", "If.test must be an expression.")
        require(len(node.body) > 0 and all(isinstance(item, ast.stmt) for item in node.body), "BLOCK_BODY", "If.body must contain at least one statement.")
        require(all(isinstance(item, ast.stmt) for item in node.orelse), "ORELSE", "If.orelse must contain only statements.")
    elif isinstance(node, (ast.For, ast.AsyncFor)):
        require(isinstance(node.target, ast.expr), "FOR_TARGET", f"{type(node).__name__}.target must be an expression.")
        require(isinstance(node.iter, ast.expr), "FOR_ITER", f"{type(node).__name__}.iter must be an expression.")
        require(len(node.body) > 0 and all(isinstance(item, ast.stmt) for item in node.body), "BLOCK_BODY", f"{type(node).__name__}.body must contain at least one statement.")
        require(all(isinstance(item, ast.stmt) for item in node.orelse), "ORELSE", f"{type(node).__name__}.orelse must contain only statements.")
    elif isinstance(node, ast.While):
        require(isinstance(node.test, ast.expr), "WHILE_TEST", "While.test must be an expression.")
        require(len(node.body) > 0 and all(isinstance(item, ast.stmt) for item in node.body), "BLOCK_BODY", "While.body must contain at least one statement.")
        require(all(isinstance(item, ast.stmt) for item in node.orelse), "ORELSE", "While.orelse must contain only statements.")
    elif isinstance(node, (ast.Try, ast.TryStar)):
        require(len(node.body) > 0 and all(isinstance(item, ast.stmt) for item in node.body), "BLOCK_BODY", f"{type(node).__name__}.body must contain at least one statement.")
        require(len(node.handlers) > 0 and all(isinstance(item, ast.ExceptHandler) for item in node.handlers), "HANDLERS", f"{type(node).__name__}.handlers must contain at least one ExceptHandler.")
        require(all(isinstance(item, ast.stmt) for item in node.orelse), "ORELSE", f"{type(node).__name__}.orelse must contain only statements.")
        require(all(isinstance(item, ast.stmt) for item in node.finalbody), "FINALBODY", f"{type(node).__name__}.finalbody must contain only statements.")
    elif isinstance(node, ast.Return):
        require(node.value is None or isinstance(node.value, ast.expr), "RETURN_VALUE", "Return.value must be an expression or None.")
    elif isinstance(node, ast.Assign):
        require(len(node.targets) > 0 and all(isinstance(item, ast.expr) for item in node.targets), "ASSIGN_TARGETS", "Assign.targets must contain at least one expression.")
        require(isinstance(node.value, ast.expr), "ASSIGN_VALUE", "Assign.value must be an expression.")
    elif isinstance(node, ast.Call):
        require(isinstance(node.func, ast.expr), "CALL_FUNC", "Call.func must be an expression.")
        require(all(isinstance(item, ast.expr) for item in node.args), "CALL_ARGS", "Call.args must contain only expressions.")
        require(all(isinstance(item, ast.keyword) for item in node.keywords), "CALL_KEYWORDS", "Call.keywords must contain only keyword nodes.")
    elif isinstance(node, ast.BinOp):
        require(isinstance(node.left, ast.expr), "BINOP_LEFT", "BinOp.left must be an expression.")
        require(isinstance(node.op, ast.operator), "BINOP_OP", "BinOp.op must be an operator.")
        require(isinstance(node.right, ast.expr), "BINOP_RIGHT", "BinOp.right must be an expression.")
    elif isinstance(node, ast.Compare):
        require(isinstance(node.left, ast.expr), "COMPARE_LEFT", "Compare.left must be an expression.")
        require(len(node.ops) == len(node.comparators) and len(node.ops) > 0, "COMPARE_ARITY", "Compare.ops and Compare.comparators must be non-empty and equal length.")
        require(all(isinstance(item, ast.cmpop) for item in node.ops), "COMPARE_OPS", "Compare.ops must contain only comparison operators.")
        require(all(isinstance(item, ast.expr) for item in node.comparators), "COMPARE_COMPARATORS", "Compare.comparators must contain only expressions.")
    elif isinstance(node, ast.Name):
        require(bool(node.id) and node.id.isidentifier(), "IDENTIFIER", "Name.id must be a valid identifier.")
        require(isinstance(node.ctx, (ast.Load, ast.Store, ast.Del)), "NAME_CONTEXT", "Name.ctx must be Load, Store, or Del.")
    elif isinstance(node, ast.Attribute):
        require(isinstance(node.value, ast.expr), "ATTRIBUTE_VALUE", "Attribute.value must be an expression.")
        require(bool(node.attr) and node.attr.isidentifier(), "IDENTIFIER", "Attribute.attr must be a valid identifier.")
        require(isinstance(node.ctx, (ast.Load, ast.Store, ast.Del)), "ATTRIBUTE_CONTEXT", "Attribute.ctx must be Load, Store, or Del.")
    elif isinstance(node, ast.BoolOp):
        require(isinstance(node.op, ast.boolop), "BOOLOP_OP", "BoolOp.op must be a boolean operator.")
        require(len(node.values) >= 2 and all(isinstance(item, ast.expr) for item in node.values), "BOOLOP_VALUES", "BoolOp.values must contain at least two expressions.")
    elif isinstance(node, ast.UnaryOp):
        require(isinstance(node.op, ast.unaryop), "UNARY_OP", "UnaryOp.op must be a unary operator.")
        require(isinstance(node.operand, ast.expr), "UNARY_OPERAND", "UnaryOp.operand must be an expression.")
    elif isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        require(all(isinstance(item, ast.expr) for item in node.elts), "CONTAINER_ELTS", f"{type(node).__name__}.elts must contain only expressions.")
        if hasattr(node, "ctx"):
            require(isinstance(node.ctx, (ast.Load, ast.Store, ast.Del)), "CONTEXT", f"{type(node).__name__}.ctx must be Load, Store, or Del.")
    elif isinstance(node, ast.Starred):
        require(isinstance(node.value, ast.expr), "STARRED_VALUE", "Starred.value must be an expression.")
        require(isinstance(node.ctx, (ast.Load, ast.Store, ast.Del)), "CONTEXT", "Starred.ctx must be Load, Store, or Del.")
    elif isinstance(node, ast.Subscript):
        require(isinstance(node.value, ast.expr), "SUBSCRIPT_VALUE", "Subscript.value must be an expression.")
        require(isinstance(node.slice, ast.AST), "SUBSCRIPT_SLICE", "Subscript.slice must be an AST node.")
        require(isinstance(node.ctx, (ast.Load, ast.Store, ast.Del)), "CONTEXT", "Subscript.ctx must be Load, Store, or Del.")
    elif isinstance(node, ast.Slice):
        for attr in (node.lower, node.upper, node.step):
            require(attr is None or isinstance(attr, ast.expr), "SLICE_COMPONENT", "Slice components must be expressions or None.")
    elif isinstance(node, ast.ExceptHandler):
        require(node.type is None or isinstance(node.type, ast.expr), "EXCEPT_TYPE", "ExceptHandler.type must be an expression or None.")
        require(node.name is None or (isinstance(node.name, str) and node.name.isidentifier()), "IDENTIFIER", "ExceptHandler.name must be an identifier or None.")
        require(len(node.body) > 0 and all(isinstance(item, ast.stmt) for item in node.body), "BLOCK_BODY", "ExceptHandler.body must contain at least one statement.")
    elif isinstance(node, ast.withitem):
        require(isinstance(node.context_expr, ast.expr), "WITH_CONTEXT", "withitem.context_expr must be an expression.")
        require(node.optional_vars is None or isinstance(node.optional_vars, ast.expr), "WITH_OPTIONAL_VARS", "withitem.optional_vars must be an expression or None.")
    elif isinstance(node, ast.arguments):
        require(all(isinstance(item, ast.arg) for item in node.posonlyargs), "ARGUMENTS", "arguments.posonlyargs must contain arg nodes.")
        require(all(isinstance(item, ast.arg) for item in node.args), "ARGUMENTS", "arguments.args must contain arg nodes.")
        require(all(isinstance(item, ast.arg) for item in node.kwonlyargs), "ARGUMENTS", "arguments.kwonlyargs must contain arg nodes.")
        require(all(item is None or isinstance(item, ast.expr) for item in node.kw_defaults), "KW_DEFAULTS", "arguments.kw_defaults must contain expressions or None.")
        require(all(isinstance(item, ast.expr) for item in node.defaults), "DEFAULTS", "arguments.defaults must contain expressions.")
        require(node.vararg is None or isinstance(node.vararg, ast.arg), "VARARG", "arguments.vararg must be arg or None.")
        require(node.kwarg is None or isinstance(node.kwarg, ast.arg), "KWARG", "arguments.kwarg must be arg or None.")
    elif isinstance(node, ast.arg):
        require(bool(node.arg) and node.arg.isidentifier(), "IDENTIFIER", "arg.arg must be a valid identifier.")
        require(node.annotation is None or isinstance(node.annotation, ast.expr), "ANNOTATION", "arg.annotation must be an expression or None.")
    elif isinstance(node, ast.keyword):
        require(node.arg is None or (isinstance(node.arg, str) and node.arg.isidentifier()), "IDENTIFIER", "keyword.arg must be an identifier or None.")
        require(isinstance(node.value, ast.expr), "KEYWORD_VALUE", "keyword.value must be an expression.")
    elif isinstance(node, ast.alias):
        require(bool(node.name), "ALIAS_NAME", "alias.name must be present.")
        require(node.asname is None or node.asname.isidentifier(), "IDENTIFIER", "alias.asname must be an identifier or None.")
    elif isinstance(node, ast.comprehension):
        require(isinstance(node.target, ast.expr), "COMPREHENSION_TARGET", "comprehension.target must be an expression.")
        require(isinstance(node.iter, ast.expr), "COMPREHENSION_ITER", "comprehension.iter must be an expression.")
        require(all(isinstance(item, ast.expr) for item in node.ifs), "COMPREHENSION_IFS", "comprehension.ifs must contain only expressions.")
        require(node.is_async in (0, 1), "COMPREHENSION_ASYNC", "comprehension.is_async must be 0 or 1.")
    elif isinstance(node, ast.Match):
        require(isinstance(node.subject, ast.expr), "MATCH_SUBJECT", "Match.subject must be an expression.")
        require(len(node.cases) > 0 and all(isinstance(item, ast.match_case) for item in node.cases), "MATCH_CASES", "Match.cases must contain at least one match_case.")
    elif isinstance(node, ast.match_case):
        require(isinstance(node.pattern, ast.pattern), "MATCH_PATTERN", "match_case.pattern must be a pattern.")
        require(node.guard is None or isinstance(node.guard, ast.expr), "MATCH_GUARD", "match_case.guard must be an expression or None.")
        require(len(node.body) > 0 and all(isinstance(item, ast.stmt) for item in node.body), "BLOCK_BODY", "match_case.body must contain at least one statement.")
    elif isinstance(node, ast.TypeAlias):
        require(isinstance(node.name, ast.Name), "TYPE_ALIAS_NAME", "TypeAlias.name must be a Name.")
        require(isinstance(node.value, ast.expr), "TYPE_ALIAS_VALUE", "TypeAlias.value must be an expression.")


def _assert_python_version_pin() -> None:
    if sys.version_info[:2] != (3, 12):
        raise RuntimeError(
            f"PREFIX for Python is pinned to Python {PYTHON_VERSION_PIN} AST authority. Runtime was {sys.version_info.major}.{sys.version_info.minor}."
        )


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
