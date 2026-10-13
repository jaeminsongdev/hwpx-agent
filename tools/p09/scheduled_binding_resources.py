"""Cadence scheduling of ONLY proven pressure callbacks during full source IO.

No source/hash/parser check is rate-limited: all original reads and closing hashes
remain. A whole-scope canonical manual guard additionally keeps CPU streaks across
reader boundaries. Neither runtime Job policy nor thresholds are changed.
"""
import ast
import inspect
import math
import textwrap
import time
from types import FunctionType, ModuleType
from unittest.mock import patch

import conservative_maintenance as maintenance
from audit_evidence_io import AuditEvidenceReader, MAX_PARSE_BYTES
from bounded_container_absence import observed_sample
from sql_runtime_supervision import SQLRuntimeResources, finish_watcher

SELF = "tools/p09/scheduled_binding_resources.py"
MODULES = frozenset({"run_optimized_signed_tests", "run_signed_stage_cost",
    "run_stored_signed_continuation", "run_call_local_xml_regression",
    "run_output_stage_profile", "run_readback_buffer_regression",
    "run_xml_roundtrip_regression", "run_source_stage_profile",
    "run_stored_comment_regression"})
MAX_SCOPE_SECONDS = 600


def resolve(node, globals_):
    if isinstance(node, ast.Name):
        return globals_[node.id]
    maintenance.require(isinstance(node, ast.Attribute), "BINDING_UNREVIEWED_CALLBACK_EXPRESSION")
    parent = resolve(node.value, globals_)
    maintenance.require(isinstance(parent, ModuleType), "BINDING_UNREVIEWED_CALLBACK_ATTRIBUTE")
    return getattr(parent, node.attr)


def pressure_body_only(source, globals_):
    """Closed AST grammar: no input/auth/hash/extra call can be silently scheduled."""
    try:
        tree = ast.parse(textwrap.dedent(source))
        maintenance.require(len(tree.body) == 1, "BINDING_CALLBACK_BODY_REQUIRED")
        function = tree.body[0]
        maintenance.require(isinstance(function, ast.FunctionDef) and function.name == "checkpoint"
            and not function.decorator_list and not function.args.posonlyargs
            and not function.args.args and not function.args.kwonlyargs
            and function.args.vararg is None and function.args.kwarg is None and len(function.body) == 3,
            "BINDING_CALLBACK_BODY_REQUIRED")
        nonlocal_, assignment, final = function.body
        maintenance.require(isinstance(nonlocal_, ast.Nonlocal) and nonlocal_.names == ["hot"], "BINDING_CALLBACK_BODY_REQUIRED")
        maintenance.require(isinstance(assignment, ast.Assign) and len(assignment.targets) == 1
            and isinstance(assignment.targets[0], ast.Tuple)
            and [n.id for n in assignment.targets[0].elts if isinstance(n, ast.Name)] == ["hot", "reason"]
            and len(assignment.targets[0].elts) == 2, "BINDING_CALLBACK_BODY_REQUIRED")
        decision = assignment.value
        maintenance.require(isinstance(decision, ast.Call) and not decision.keywords and len(decision.args) == 2
            and resolve(decision.func, globals_) is maintenance.decision
            and isinstance(decision.args[1], ast.Name) and decision.args[1].id == "hot", "BINDING_CALLBACK_BODY_REQUIRED")
        sample = decision.args[0]
        maintenance.require(isinstance(sample, ast.Call) and not sample.keywords and len(sample.args) == 1
            and resolve(sample.func, globals_) is observed_sample
            and isinstance(sample.args[0], ast.Name) and sample.args[0].id == "windows", "BINDING_CALLBACK_BODY_REQUIRED")
        maintenance.require(isinstance(final, ast.Expr) and isinstance(final.value, ast.Call), "BINDING_CALLBACK_BODY_REQUIRED")
        call = final.value
        maintenance.require(not call.keywords and len(call.args) == 2 and resolve(call.func, globals_) is maintenance.require
            and isinstance(call.args[1], ast.Name) and call.args[1].id == "reason", "BINDING_CALLBACK_BODY_REQUIRED")
        predicate = call.args[0]
        maintenance.require(isinstance(predicate, ast.Compare) and isinstance(predicate.left, ast.Name)
            and predicate.left.id == "reason" and len(predicate.ops) == len(predicate.comparators) == 1
            and isinstance(predicate.ops[0], ast.Is) and isinstance(predicate.comparators[0], ast.Constant)
            and predicate.comparators[0].value is None, "BINDING_CALLBACK_BODY_REQUIRED")
        return True
    except (SyntaxError, KeyError, AttributeError, TypeError):
        raise ValueError("BINDING_CALLBACK_BODY_REQUIRED") from None


def validate_pressure_callback(callback, windows):
    maintenance.require(isinstance(callback, FunctionType) and callback.__module__ in MODULES
        and callback.__qualname__ == "load_binding.<locals>.checkpoint", "BINDING_CALLBACK_SCOPE_REQUIRED")
    cells = dict(zip(callback.__code__.co_freevars, (c.cell_contents for c in callback.__closure__ or ())))
    maintenance.require(set(cells) == {"hot", "windows"} and cells["windows"] is windows
        and type(cells["hot"]) is int and cells["hot"] >= 0, "BINDING_CALLBACK_CLOSURE_REQUIRED")
    pressure_body_only(inspect.getsource(callback), callback.__globals__)


class ScheduledBinding:
    def __init__(self, windows, resources=None, clock=time.monotonic):
        self.windows, self.resources, self.clock = windows, resources, clock
        self.started = self.previous = clock()
        self.last_original_at = self.started
        self.readers = []
        self.original_pressure_calls = self.checkpoints = 0
        self.callback_modules = set()
        self.closed = False
        self.cleanup = False
        self.original_init = AuditEvidenceReader.__init__

    def checkpoint(self):
        now = self.clock()
        maintenance.require(not self.closed and type(now) in (int,float) and math.isfinite(now)
            and now >= self.previous and now-self.started <= MAX_SCOPE_SECONDS, "STOP_BINDING_CLOCK_OR_SCOPE_INVALID")
        self.previous = now
        self.resources.checkpoint_io()
        self.checkpoints += 1

    def init_reader(self, reader, root, callback, maximum_parse_bytes=MAX_PARSE_BYTES):
        maintenance.require(root == maintenance.ROOT and maximum_parse_bytes == MAX_PARSE_BYTES,
            "BINDING_READER_SCOPE_REQUIRED")
        validate_pressure_callback(callback, self.windows)
        self.callback_modules.add(callback.__module__)
        def scheduled():
            self.checkpoint()  # canonical fresh 0.5s guard runs at EVERY IO checkpoint
            now = self.clock()
            if now-self.last_original_at >= maintenance.POLICY["sample_seconds"]:
                callback()  # original, unchanged pressure-only body; never a cached sample
                self.last_original_at = self.clock()
                self.original_pressure_calls += 1
        self.original_init(reader, root, scheduled, maximum_parse_bytes)
        self.readers.append(reader)

    def __enter__(self):
        if self.resources is None:
            self.resources = SQLRuntimeResources()  # independent canonical sampler, no watcher thread
        self.resources.admit()
        self.started = self.previous = self.last_original_at = self.clock()
        # A bound method installed on a class is not a reader descriptor. Use a
        # plain function so Python supplies the real AuditEvidenceReader instance.
        def init(reader, root, callback, maximum_parse_bytes=MAX_PARSE_BYTES):
            return self.init_reader(reader, root, callback, maximum_parse_bytes)
        self.context = patch.object(AuditEvidenceReader, "__init__", init)
        self.context.__enter__()
        return self

    def __exit__(self, kind, value, traceback):
        self.context.__exit__(kind, value, traceback)
        status = {}
        self.cleanup = finish_watcher(self.resources, status)
        self.closed = True
        maintenance.require(self.cleanup, "STOP_BINDING_WATCHER_CLEANUP_FAILED")

    def summary(self):
        complete = bool(self.readers) and all(r.final_fresh_hashes == len(r.snapshots) for r in self.readers)
        return {"qualification":"FULL_SOURCE_BINDING_CADENCE_ONLY_NOT_COMPILE_RUNTIME_OR_GATE",
            "callback_modules":sorted(self.callback_modules), "reader_instances":len(self.readers),
            "IO_checkpoints":self.checkpoints, "unchanged_original_pressure_callback_calls":self.original_pressure_calls,
            "canonical_sample_count":len(self.resources.samples), "canonical_host_samples":list(self.resources.samples),
            "original_resource_stop":self.resources.reason, "whole_scope_maximum_seconds":MAX_SCOPE_SECONDS,
            "canonical_sample_interval_seconds":maintenance.POLICY["sample_seconds"],
            "per_IO_sleep_added":False, "source_read_or_final_hash_checks_scheduled_or_removed":False,
            "all_legacy_readers_final_fresh_hash_inventory_exact":complete,
            "read_passes":sum(r.read_passes for r in self.readers),
            "bytes_read":sum(r.bytes_read for r in self.readers),
            "closing_fresh_hashes":sum(r.final_fresh_hashes for r in self.readers),
            "elapsed_binding_seconds":self.previous-self.started,
            "thresholds_or_owned_runtime_policy_changed":False,
            "new_child_or_watcher_thread_started":False,
            "cleanup_confirmed":self.closed and self.cleanup}
