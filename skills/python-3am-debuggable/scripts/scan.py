#!/usr/bin/env python3
"""Heuristic scanner for Python 3AM-debuggability review.

Findings are advisory. The script exits 0 when it finds suspicious patterns.
"""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


SKIP_DIRS = {".git", ".hg", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".venv", "venv", "__pycache__"}
GEN_HINTS = ("generated", "auto-generated", "do not edit")
MUTATING_METHODS = {
    "add",
    "append",
    "clear",
    "discard",
    "extend",
    "insert",
    "pop",
    "remove",
    "reverse",
    "setdefault",
    "sort",
    "update",
}
SIDE_EFFECT_CALLS = {"open", "print", "write_file"}
SIDE_EFFECT_PREFIXES = ("os.environ", "requests.", "httpx.", "subprocess.")
PROCESS_STATE_PREFIXES = ("time.", "random.")


SECTIONS = [
    ("A", "Silent/collapsed failure paths (T1)"),
    ("B", "Hidden async/background boundaries (T1/Inspect)"),
    ("C", "Callback/lambda inversion across lifecycle boundary (T1)"),
    ("D", "Mutable shared state and late-bound capture (T1/T2)"),
    ("E", "Test-only seams / fake call indirection (T1)"),
    ("F", "Dynamic dispatch hiding real callable (T1/Inspect)"),
    ("G", "Opaque public contracts (T2)"),
    ("H", "Local closure/lambda chains (T2 -> T1?)"),
    ("I", "Single-caller wrappers and generic abstractions (T2)"),
    ("J", "Long/deep mixed-responsibility functions (Inspect/T2)"),
    ("K", "Hidden side effects/config checkpoints (T1/Inspect)"),
]


@dataclass
class Finding:
    section: str
    path: Path
    line: int
    message: str
    snippet: str


def line_at(lines: list[str], lineno: int) -> str:
    if 1 <= lineno <= len(lines):
        return lines[lineno - 1].strip()
    return ""


def unparse(node: ast.AST | None) -> str:
    if node is None:
        return ""
    try:
        return ast.unparse(node)
    except Exception:
        return node.__class__.__name__


def call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = call_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    if isinstance(node, ast.Call):
        return f"{call_name(node.func)}()"
    if isinstance(node, ast.Subscript):
        return f"{call_name(node.value)}[]"
    return ""


def is_public_name(name: str) -> bool:
    return not name.startswith("_")


def is_mutable_literal(node: ast.AST) -> bool:
    return isinstance(node, (ast.List, ast.Dict, ast.Set))


def is_fallback_return(node: ast.AST) -> bool:
    if not isinstance(node, ast.Return):
        return False
    value = node.value
    if value is None:
        return True
    if isinstance(value, ast.Constant):
        return value.value in (None, False)
    return isinstance(value, (ast.List, ast.Dict, ast.Set, ast.Tuple)) and len(getattr(value, "elts", getattr(value, "keys", []))) == 0


def has_reraise_or_chained_raise(nodes: list[ast.stmt]) -> bool:
    for node in ast.walk(ast.Module(body=nodes, type_ignores=[])):
        if isinstance(node, ast.Raise):
            if node.exc is None:
                return True
            if node.cause is not None and not isinstance(node.cause, ast.Constant):
                return True
    return False


def contains_background_call(node: ast.AST) -> bool:
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            name = call_name(child.func)
            if name in {"asyncio.create_task", "asyncio.ensure_future"}:
                return True
            if name in {"threading.Thread", "Thread"}:
                return True
            if name.endswith(".submit") or name.endswith(".apply_async") or name.endswith(".delay"):
                return True
    return False


def is_background_call(node: ast.Call) -> bool:
    name = call_name(node.func)
    return (
        name in {"asyncio.create_task", "asyncio.ensure_future", "threading.Thread", "Thread"}
        or name.endswith(".submit")
        or name.endswith(".apply_async")
        or name.endswith(".delay")
    )


def has_side_effect_call(node: ast.AST) -> bool:
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            if is_side_effect_checkpoint(child):
                return True
    return False


def is_side_effect_checkpoint(node: ast.Call) -> bool:
    name = call_name(node.func)
    if name in SIDE_EFFECT_CALLS or any(name.startswith(prefix) for prefix in SIDE_EFFECT_PREFIXES):
        return True
    if any(name.startswith(prefix) for prefix in PROCESS_STATE_PREFIXES):
        return True
    if name == "Path" and node.args and is_hardcoded_resource(node.args[0]):
        return True
    return any(is_hardcoded_resource(arg) for arg in list(node.args) + [kw.value for kw in node.keywords])


def is_hardcoded_resource(node: ast.AST) -> bool:
    if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
        return False
    value = node.value
    return (
        value.startswith(("/", "~/"))
        or value.startswith(("http://", "https://"))
        or value.endswith((".json", ".yaml", ".yml", ".db", ".sqlite", ".csv", ".log"))
    )


def nesting_depth(node: ast.AST, depth: int = 0) -> int:
    max_depth = depth
    block_nodes = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.With, ast.AsyncWith, ast.Try, ast.Match)
    for child in ast.iter_child_nodes(node):
        child_depth = depth + 1 if isinstance(child, block_nodes) else depth
        max_depth = max(max_depth, nesting_depth(child, child_depth))
    return max_depth


def annotate_parents(tree: ast.AST) -> None:
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            setattr(child, "_parent", parent)


def walk_without_nested_functions(node: ast.AST) -> Iterable[ast.AST]:
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            continue
        yield child
        yield from walk_without_nested_functions(child)


def bound_names(node: ast.AST) -> set[str]:
    names: set[str] = set()

    def add_target(target: ast.AST) -> None:
        if isinstance(target, ast.Name):
            names.add(target.id)
        elif isinstance(target, (ast.Tuple, ast.List)):
            for elt in target.elts:
                add_target(elt)

    for child in ast.walk(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)) and child is not node:
            continue
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            names.update(arg.arg for arg in child.args.args + child.args.kwonlyargs)
            names.update(arg.arg for arg in child.args.posonlyargs)
            if child.args.vararg:
                names.add(child.args.vararg.arg)
            if child.args.kwarg:
                names.add(child.args.kwarg.arg)
        elif isinstance(child, ast.Assign):
            for target in child.targets:
                add_target(target)
        elif isinstance(child, ast.AnnAssign):
            add_target(child.target)
        elif isinstance(child, ast.AugAssign):
            add_target(child.target)
        elif isinstance(child, ast.For):
            add_target(child.target)
        elif isinstance(child, ast.With):
            for item in child.items:
                if item.optional_vars is not None:
                    add_target(item.optional_vars)
    return names


def loaded_names(node: ast.AST) -> set[str]:
    names: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
            names.add(child.id)
    return names


def first_loaded_name(node: ast.AST, names: set[str]) -> ast.AST | None:
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load) and child.id in names:
            return child
    return None


def root_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, (ast.Attribute, ast.Subscript)):
        return root_name(node.value)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        return root_name(node.func.value)
    return ""


def local_functions(node: ast.AST) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    found: list[ast.FunctionDef | ast.AsyncFunctionDef] = []
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            found.append(child)
            continue
        if isinstance(child, ast.Lambda):
            continue
        found.extend(local_functions(child))
    return found


def has_wraps_decorator(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for decorator in node.decorator_list:
        target = decorator.func if isinstance(decorator, ast.Call) else decorator
        if call_name(target) in {"wraps", "functools.wraps"}:
            return True
    return False


def function_arg_names(node: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    args = node.args.posonlyargs + node.args.args + node.args.kwonlyargs
    names = {arg.arg for arg in args}
    if node.args.vararg:
        names.add(node.args.vararg.arg)
    if node.args.kwarg:
        names.add(node.args.kwarg.arg)
    return names - {"self", "cls"}


class Scanner(ast.NodeVisitor):
    def __init__(self, path: Path, lines: list[str]) -> None:
        self.path = path
        self.lines = lines
        self.findings: list[Finding] = []
        self.stack: list[ast.FunctionDef | ast.AsyncFunctionDef] = []
        self.function_defs: dict[str, ast.FunctionDef | ast.AsyncFunctionDef] = {}
        self.calls: dict[str, int] = {}

    def add(self, section: str, node: ast.AST, message: str, lineno: int | None = None) -> None:
        line = lineno or getattr(node, "lineno", 1)
        self.findings.append(Finding(section, self.path, line, message, line_at(self.lines, line)))

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function(node)

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        self.function_defs.setdefault(node.name, node)

        for default in list(node.args.defaults) + list(node.args.kw_defaults):
            if default is not None and is_mutable_literal(default):
                self.add("D", node, f"mutable default argument in `{node.name}`", node.lineno)

        if is_public_name(node.name):
            self._check_public_contract(node)
            self._check_argument_mutation(node)

        callback_args = []
        for arg in list(node.args.args) + list(node.args.kwonlyargs):
            annotation = unparse(arg.annotation)
            if "Callable" in annotation or arg.arg in {"callback", "cb", "fn", "func"} or arg.arg.startswith(("build_", "make_", "factory")):
                callback_args.append(arg.arg)
        if callback_args and contains_background_call(node):
            self.add("C", node, f"callback argument(s) {', '.join(callback_args)} cross a lifecycle boundary", node.lineno)

        nested_funcs = local_functions(node)
        self._check_mutable_capture(node, nested_funcs)
        self._check_dynamic_callable_alias(node)
        for nested in nested_funcs:
            if has_wraps_decorator(nested):
                continue
            self.add("H", nested, f"local function `{nested.name}` hides a traceback frame inside `{node.name}`")
        for child in ast.walk(node):
            if isinstance(child, ast.Lambda) and not self._allowed_lambda(child):
                self.add("H", child, f"lambda inside `{node.name}` may obscure traceback or captured state")

        if len(node.body) >= 35 or nesting_depth(node) >= 4:
            if has_side_effect_call(node) or any(isinstance(child, (ast.Try, ast.Global)) for child in ast.walk(node)):
                self.add("J", node, f"`{node.name}` is long/deep with side effects or error/state ownership to inspect", node.lineno)

        self.stack.append(node)
        self.generic_visit(node)
        self.stack.pop()

    def _check_mutable_capture(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        nested_funcs: list[ast.FunctionDef | ast.AsyncFunctionDef],
    ) -> None:
        if not nested_funcs:
            return
        mutable_names = self._outer_mutable_names(node)
        if not mutable_names:
            return
        nested_names = {nested.name for nested in nested_funcs}
        scheduled = self._scheduled_nested_functions(node, nested_names)
        if not scheduled:
            return
        for nested in nested_funcs:
            if nested.name not in scheduled:
                continue
            local_names = bound_names(nested)
            captured = (loaded_names(nested) - local_names) & mutable_names
            if not captured:
                continue
            blame = first_loaded_name(nested, captured) or nested
            self.add(
                "D",
                blame,
                f"scheduled `{nested.name}` captures mutable state: {', '.join(sorted(captured))}",
                getattr(blame, "lineno", nested.lineno),
            )

    def _check_argument_mutation(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        args = function_arg_names(node)
        if not args:
            return
        seen: set[tuple[str, int]] = set()

        def report(arg: str, child: ast.AST) -> None:
            line = getattr(child, "lineno", node.lineno)
            key = (arg, line)
            if key in seen:
                return
            seen.add(key)
            self.add("K", child, f"`{node.name}` mutates argument `{arg}`; make side effect explicit", line)

        def check_target(target: ast.AST, child: ast.AST) -> None:
            if isinstance(target, (ast.Subscript, ast.Attribute)):
                base = root_name(target)
                if base in args:
                    report(base, child)
            elif isinstance(target, (ast.Tuple, ast.List)):
                for elt in target.elts:
                    check_target(elt, child)

        for child in walk_without_nested_functions(node):
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    check_target(target, child)
            elif isinstance(child, (ast.AnnAssign, ast.AugAssign)):
                check_target(child.target, child)
            elif isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute):
                base = root_name(child.func.value)
                if base in args and child.func.attr in MUTATING_METHODS:
                    report(base, child)

    def _check_dynamic_callable_alias(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        dynamic_targets: dict[str, ast.AST] = {}
        for child in walk_without_nested_functions(node):
            if isinstance(child, ast.Assign) and isinstance(child.value, ast.Call):
                name = call_name(child.value.func)
                if name in {"getattr", "importlib.import_module"}:
                    for target in child.targets:
                        if isinstance(target, ast.Name):
                            dynamic_targets[target.id] = child
            elif isinstance(child, ast.Call) and isinstance(child.func, ast.Name):
                source = dynamic_targets.get(child.func.id)
                if source is not None:
                    self.add("F", source, f"`{child.func.id}` is assigned from dynamic dispatch then called", getattr(source, "lineno", node.lineno))

    def _outer_mutable_names(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
        names: set[str] = set()

        def add_target(target: ast.AST) -> None:
            if isinstance(target, ast.Name):
                names.add(target.id)
            elif isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name):
                names.add(target.value.id)
            elif isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name):
                names.add(target.value.id)
            elif isinstance(target, (ast.Tuple, ast.List)):
                for elt in target.elts:
                    add_target(elt)

        for child in walk_without_nested_functions(node):
            if isinstance(child, ast.Assign) and is_mutable_literal(child.value):
                for target in child.targets:
                    add_target(target)
            elif isinstance(child, ast.AnnAssign):
                if child.value is not None and is_mutable_literal(child.value):
                    add_target(child.target)
                elif isinstance(child.target, ast.Subscript):
                    add_target(child.target)
            elif isinstance(child, (ast.Assign, ast.AugAssign)):
                targets = child.targets if isinstance(child, ast.Assign) else [child.target]
                for target in targets:
                    if isinstance(target, (ast.Subscript, ast.Attribute)):
                        add_target(target)
            elif isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute):
                if child.func.attr in MUTATING_METHODS and isinstance(child.func.value, ast.Name):
                    names.add(child.func.value.id)
        return names

    def _scheduled_nested_functions(self, node: ast.FunctionDef | ast.AsyncFunctionDef, nested_names: set[str]) -> set[str]:
        scheduled: set[str] = set()
        for child in walk_without_nested_functions(node):
            if isinstance(child, ast.Call) and is_background_call(child):
                scheduled.update(loaded_names(child) & nested_names)
        return scheduled

    def _allowed_lambda(self, node: ast.Lambda) -> bool:
        parent = getattr(node, "_parent", None)
        if isinstance(parent, ast.keyword) and parent.arg in {"key", "default_factory"}:
            return True
        return False

    def _check_public_contract(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        annotations = [unparse(node.returns)]
        annotations.extend(unparse(arg.annotation) for arg in list(node.args.args) + list(node.args.kwonlyargs))
        broad = [ann for ann in annotations if ann in {"dict", "list", "tuple", "Any"} or "dict[str, Any]" in ann or "Any" in ann]
        mixed_returns = set()
        for child in ast.walk(node):
            if isinstance(child, ast.Return):
                value = child.value
                if value is None:
                    mixed_returns.add("None")
                elif isinstance(value, ast.Constant):
                    mixed_returns.add(type(value.value).__name__)
                elif isinstance(value, ast.Dict):
                    mixed_returns.add("dict")
                elif isinstance(value, ast.List):
                    mixed_returns.add("list")
                elif isinstance(value, ast.Tuple):
                    mixed_returns.add("tuple")
                else:
                    mixed_returns.add("value")
        if broad:
            self.add("G", node, f"public contract uses broad shape `{broad[0]}`", node.lineno)
        elif len(mixed_returns) > 1 and "None" in mixed_returns:
            self.add("G", node, f"public contract has mixed return shapes: {', '.join(sorted(mixed_returns))}", node.lineno)

    def visit_Try(self, node: ast.Try) -> None:
        for handler in node.handlers:
            broad = handler.type is None or unparse(handler.type) in {"Exception", "BaseException"}
            if not broad:
                continue
            if has_reraise_or_chained_raise(handler.body):
                continue
            if any(isinstance(stmt, ast.Pass) or is_fallback_return(stmt) for stmt in handler.body):
                self.add("A", handler, "broad exception handler collapses failure meaning", handler.lineno)
        self.generic_visit(node)

    def visit_Raise(self, node: ast.Raise) -> None:
        if isinstance(node.cause, ast.Constant) and node.cause.value is None:
            self.add("A", node, "raise ... from None hides the original traceback cause", node.lineno)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        name = call_name(node.func)
        if name in {"asyncio.create_task", "asyncio.ensure_future"}:
            self.add("B", node, f"{name} creates background work; verify owner/cancel/error path", node.lineno)
        elif name in {"threading.Thread", "Thread"} or name.endswith(".submit") or name.endswith(".apply_async") or name.endswith(".delay"):
            self.add("B", node, f"{name} starts background work; verify lifecycle ownership", node.lineno)

        if isinstance(node.func, ast.Subscript):
            base = call_name(node.func.value)
            if base in {"globals()", "locals()"}:
                self.add("F", node, f"{base} dynamic dispatch hides the real callable", node.lineno)
        if isinstance(node.func, ast.Call) and call_name(node.func.func) == "getattr":
            self.add("F", node, "getattr(...)(...) dynamic dispatch hides the real callable", node.lineno)
        if name in {"eval", "exec"}:
            self.add("F", node, f"{name} hides execution target", node.lineno)
        if is_side_effect_checkpoint(node):
            self.add("K", node, f"{name or 'call'} is a side-effect/config checkpoint to inspect", node.lineno)

        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        if not self.stack:
            for target in node.targets:
                if isinstance(target, ast.Name) and self._looks_like_fake_seam(target.id, node.value):
                    self.add("E", node, f"module-level `{target.id}` looks like fake call indirection", node.lineno)
        self.generic_visit(node)

    def visit_Global(self, node: ast.Global) -> None:
        self.add("D", node, f"global mutation for {', '.join(node.names)} needs ownership review", node.lineno)

    def _looks_like_fake_seam(self, name: str, value: ast.AST) -> bool:
        suffix = name.endswith(("_func", "_fn", "_call", "_client"))
        prefix = name.startswith(("_", "mock_"))
        targetish = isinstance(value, (ast.Name, ast.Attribute))
        return targetish and (suffix or prefix)


class CallCounter(ast.NodeVisitor):
    def __init__(self) -> None:
        self.calls: dict[str, int] = {}

    def visit_Call(self, node: ast.Call) -> None:
        name = call_name(node.func)
        if name:
            short = name.rsplit(".", 1)[-1]
            self.calls[short] = self.calls.get(short, 0) + 1
        self.generic_visit(node)


class PostScanner:
    def __init__(self, scanner: Scanner, calls: dict[str, int]) -> None:
        self.scanner = scanner
        self.calls = calls

    def run(self, tree: ast.AST) -> None:
        for name, node in self.scanner.function_defs.items():
            if not name.startswith("_"):
                continue
            if self.calls.get(name, 0) == 1 and self._thin_function(node):
                self.scanner.add("I", node, f"`{name}` is a thin single-caller wrapper", node.lineno)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                self._check_class(node)

    def _thin_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
        meaningful = [stmt for stmt in node.body if not isinstance(stmt, (ast.Expr, ast.Pass))]
        return 1 <= len(meaningful) <= 3

    def _check_class(self, node: ast.ClassDef) -> None:
        generic_suffixes = ("Manager", "Processor", "Handler", "Service", "Helper")
        methods = [child for child in node.body if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))]
        if node.name.endswith(generic_suffixes) and len(methods) >= 3:
            self.scanner.add("I", node, f"`{node.name}` is a broad generic class; verify one coherent responsibility", node.lineno)


def scan_file(path: Path) -> list[Finding]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if any(hint in "\n".join(lines[:5]).lower() for hint in GEN_HINTS):
        return []
    tree = ast.parse(text, filename=str(path))
    annotate_parents(tree)
    scanner = Scanner(path, lines)
    scanner.visit(tree)
    counter = CallCounter()
    counter.visit(tree)
    PostScanner(scanner, counter.calls).run(tree)
    return scanner.findings


def iter_py_files(paths: Iterable[Path], include_tests: bool) -> Iterable[Path]:
    for path in paths:
        if path.is_file():
            if path.suffix == ".py" and (include_tests or not is_test_path(path)):
                yield path
            continue
        for child in path.rglob("*.py"):
            if any(part in SKIP_DIRS for part in child.parts):
                continue
            if not include_tests and is_test_path(child):
                continue
            yield child


def is_test_path(path: Path) -> bool:
    parts = set(path.parts)
    return path.name.startswith("test_") or path.name.endswith("_test.py") or "tests" in parts or "test" in parts


def print_report(findings: list[Finding]) -> None:
    by_section: dict[str, list[Finding]] = {key: [] for key, _ in SECTIONS}
    for finding in findings:
        by_section.setdefault(finding.section, []).append(finding)

    total = 0
    for key, title in SECTIONS:
        print()
        print(f"── {key}. {title} ──")
        items = by_section.get(key, [])
        if not items:
            print("  ok: no hits")
            continue
        total += len(items)
        for item in items[:30]:
            print(f"  {item.path}:{item.line}: {item.message}")
            if item.snippet:
                print(f"    {item.snippet}")
        if len(items) > 30:
            print(f"  ... {len(items) - 30} more")

    print()
    print("═══ Summary ═══")
    if total == 0:
        print("  no suspicious patterns found")
    else:
        print(f"  {total} suspicious patterns. Fix T1 first; treat Inspect/T2 output as review anchors.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Heuristically scan Python for 3AM-debuggability risks.")
    parser.add_argument("paths", nargs="*", default=["."], help="Python files or directories to scan")
    parser.add_argument("--include-tests", action="store_true", help="Include tests in the scan")
    args = parser.parse_args(argv)

    roots = [Path(path) for path in args.paths]
    missing = [str(path) for path in roots if not path.exists()]
    if missing:
        parser.error(f"path not found: {', '.join(missing)}")

    findings: list[Finding] = []
    for path in iter_py_files(roots, args.include_tests):
        try:
            findings.extend(scan_file(path))
        except (SyntaxError, UnicodeDecodeError) as exc:
            findings.append(Finding("K", path, getattr(exc, "lineno", 1) or 1, f"could not parse file: {exc}", ""))

    print_report(sorted(findings, key=lambda item: (str(item.path), item.line, item.section)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
