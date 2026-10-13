"""Acceptance-only fresh metadata snapshot for the original Rust inventory.

Only three link/file predicate expressions are projected. Ordinary Windows
paths use one no-follow stat instead of two/three pathname metadata queries.
Every uncertain/reparse/error case retains the exact original predicates.
No inventory/path/stat cache, extra observer, input omission or hash shortcut.
"""
import ast
import copy
import hashlib
import os
import stat
from types import FunctionType, SimpleNamespace as NS

SELF = "tools/p09/rust_inventory_single_snapshot_v1.py"
TEST = "tools/p09/tests/test_rust_inventory_single_snapshot_v1.py"
ORIGINAL_PIN = dict(path="tools/p09/current_issuer_build_inputs.py", bytes=18791,
    sha256="7034d77e17c2d6b460d8de753039398adc7c08913f63db203982844ac3e1bd38")

def require(ok, code):
    if not ok:
        raise ValueError("RUST_INVENTORY_SNAPSHOT_" + code)

class Counters:
    def __init__(self):
        self.requests = self.attempts = self.ordinary = self.fallbacks = 0
        self.file_requests = self.directory_requests = 0

    def summary(self):
        return dict(predicate_requests=self.requests, fresh_no_follow_stat_attempts=self.attempts,
            ordinary_decisions=self.ordinary, exact_original_fallbacks=self.fallbacks,
            file_requests=self.file_requests, directory_requests=self.directory_requests,
            cached_stat_or_inventory=False, original_walk_and_checkpoint_order_retained=True,
            complete_source_byte_reads_and_final_hashes_retained=True,
            additional_sampler_thread_or_process=False, PC_freeze_resolved=False)

def predicate(path, kind, counters, *, query=os.stat):
    require(kind in ("file", "directory"), "PREDICATE_KIND")
    counters.requests += 1
    counters.file_requests += kind == "file"
    counters.directory_requests += kind == "directory"
    counters.attempts += 1
    value = None
    try:
        value = query(path, follow_symlinks=False)
    except OSError:
        pass
    attrs = getattr(value, "st_file_attributes", None)
    tag = getattr(value, "st_reparse_tag", None)
    mode = getattr(value, "st_mode", None)
    ordinary = (type(attrs) is int and 0 <= attrs <= 0xffffffff
        and type(tag) is int and tag == 0 and type(mode) is int and mode >= 0
        and not attrs & (0x400 | 0x40)
        and bool(attrs & 0x10) == stat.S_ISDIR(mode))
    if ordinary:
        counters.ordinary += 1
        # The original directory expression checks links only, not is_dir.
        return stat.S_ISREG(mode) if kind == "file" else True
    counters.fallbacks += 1
    if kind == "file":
        return path.is_file() and not path.is_symlink() and not path.is_junction()
    return not path.is_symlink() and not path.is_junction()

def projection(original, raw, *, query=os.stat):
    require(type(raw) is bytes and len(raw) == ORIGINAL_PIN["bytes"]
        and hashlib.sha256(raw).hexdigest() == ORIGINAL_PIN["sha256"], "EXACT_SOURCE_PIN")
    require(type(original) is FunctionType and original.__name__ == "rust_inputs"
        and original.__defaults__ is None and original.__closure__ is None, "ORIGINAL_FUNCTION")
    nodes = [n for n in ast.parse(raw.decode("utf-8")).body
        if isinstance(n, ast.FunctionDef) and n.name == "rust_inputs"]
    require(len(nodes) == 1, "ONE_INVENTORY_FUNCTION")
    node = copy.deepcopy(nodes[0])
    env = dict(original.__globals__)
    exec(compile(ast.Module(body=[copy.deepcopy(node)], type_ignores=[]),
        original.__code__.co_filename, "exec", dont_inherit=True), env)
    require(env["rust_inputs"].__code__ == original.__code__, "EXACT_ORIGINAL_METHOD_CODE")
    before = ast.dump(node, include_attributes=False)
    patterns = {}
    for expression, replacement in (
        ("not parent.is_symlink() and not parent.is_junction()", "_inventory_directory(parent)"),
        ("not child.is_symlink() and not child.is_junction()", "_inventory_directory(child)"),
        ("child.is_file() and not child.is_symlink() and not child.is_junction()", "_inventory_file(child)")):
        patterns[ast.dump(ast.parse(expression, mode="eval").body, include_attributes=False)] = replacement
    changed = []
    class Project(ast.NodeTransformer):
        def visit_BoolOp(self, n):
            key = ast.dump(n, include_attributes=False)
            if key in patterns:
                value = ast.parse(patterns[key], mode="eval").body
                value._inventory_original = copy.deepcopy(n)
                changed.append(key)
                return ast.copy_location(value, n)
            return self.generic_visit(n)
    node = Project().visit(node)
    require(len(changed) == 3 and set(changed) == set(patterns), "EXACT_THREE_PREDICATES")
    class Undo(ast.NodeTransformer):
        def visit(self, n):
            if hasattr(n, "_inventory_original"):
                return copy.deepcopy(n._inventory_original)
            return super().visit(n)
    require(ast.dump(Undo().visit(copy.deepcopy(node)), include_attributes=False) == before,
        "ALL_ORIGINAL_LOOPS_REQUIREMENTS_AND_CHECKPOINTS_RESTORED")
    counters = Counters()
    env = dict(original.__globals__,
        _inventory_directory=lambda path: predicate(path, "directory", counters, query=query),
        _inventory_file=lambda path: predicate(path, "file", counters, query=query))
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])),
        original.__code__.co_filename, "exec", dont_inherit=True), env)
    return env["rust_inputs"], counters

def runtime(original, raw):
    native = original.a.native
    original_definitions = native.definitions
    counters = []
    def definitions(text, names, namespace):
        result = original_definitions(text, names, namespace)
        if names != ("rust_inputs",):
            return result
        require(text == raw.decode("utf-8").replace("\r\n", "\n"), "EXACT_NORMALIZED_INVENTORY_TEXT")
        function, trace = projection(result.rust_inputs, raw)
        counters.append(trace)
        return NS(rust_inputs=function)
    private_native = NS(**{**vars(native), "definitions": definitions})
    private_a = NS(**{**vars(original.a), "native": private_native})
    return NS(**{**vars(original), "a": private_a}), counters
