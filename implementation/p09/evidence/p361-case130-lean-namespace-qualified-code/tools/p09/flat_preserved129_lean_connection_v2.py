"""Validation-only exact namespaces, not top-level source/authority runners.

모든 실제 imported module과 원 fixed 항목은 그대로64 상한에 센다. source,
body, compound 검증의 원 함수/상수는 별도 exact raw pin으로 읽고 원 AST를
그대로 컴파일한다. 실행기/CLI를 import하지 않을 뿐 검증을 제거하지 않는다.
전체 원1913 입력·두 byte 경계·권위129·실패preflight001을 보존한다.
"""
import argparse
import ast
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import threading
import time
from types import FunctionType, SimpleNamespace as NS

import flat_current_queue_source_stat_runtime_v2 as source

base, a, c = source.base, source.a, source.c
SELF = "tools/p09/flat_preserved129_lean_connection_v2.py"
TEST = "tools/p09/tests/test_flat_preserved129_lean_connection_v2.py"
QUAL_PATH = "implementation/p09/evidence/p09-361-case130-lean-namespace-code-r328.v1.json"
DATA_PATH = "implementation/p09/evidence/p09-361-case130-lean-namespace-data001.v1.json"
CODE_PASS = "PASS_LEAN_FULL_COMPOUND_NAMESPACE_AND_RUNTIME_CODE_NOT_ACTUAL130"
LEGACY_QUAL = dict(path="implementation/p09/evidence/p09-361-case129-compound-connection-code-r324.v1.json",
    bytes=2713, sha256="06b03d3ad41aa2fd178d8eb514f0b6f981032d041d8c5c2b4bf3a936988ab211")
FAILED_PREFLIGHT = dict(path="implementation/p09/evidence/p09-361-case130-source-stat-ancestor-preflight001.v1.json",
    bytes=39470, sha256="6255dcf087bbe541d362829f75672272a33c762091952ae260ff57d7107d1941")
SOURCES = (
    dict(path="tools/p09/review_flat_completed_body_stop_v1.py", bytes=9738,
        sha256="030e8cdcc6c39982d7fb00190b7609ad0a5e5da735ac04f7233a0a447a322fe6"),
    dict(path="tools/p09/close_flat_case129_preserved_source_v1.py", bytes=19621,
        sha256="f2d29dfa8cd78294b07619d64fc4f3533b4cc4fdf8a825a332cf50115b29ce82"),
    dict(path="tools/p09/validate_flat_case129_compound_v1.py", bytes=12049,
        sha256="8c26d46f52d0594ea96be53080a7aacdf887cbe7d4524bf3f069860d9a2e156c"),
    dict(path="tools/p09/validate_flat_case129_compound_observer_v2.py", bytes=10568,
        sha256="1354f9ee93d916bdc00f55cbb3117c0641a7829da35beb46cf2552adfcc5db3d"),
    dict(path="tools/p09/flat_preserved129_compound_connection_v1.py", bytes=23775,
        sha256="9901a4ce034609574f1558fa3ea856d80ba0b2272d1e4ee5b96e8efbc97324b9"))
SOURCE_FUNCTIONS = ("require", "source_budget", "validate_frame")
LEGACY_FUNCTIONS = ("require", "qualification", "documents", "parent_header", "predecessor_data_path",
    "predecessor_data", "binding", "binding_attempt", "template", "context", "worker", "run_owned",
    "preflight_projection", "preflight", "validator", "validate_candidate", "prepare_projection",
    "prepare", "accept130", "imported", "scan_future")


def require(ok, code):
    if not ok:
        raise ValueError("LEAN_COMPOUND_" + code)


def project(raw, pin, environment, functions=None):
    require(type(raw) is bytes and len(raw) == pin["bytes"] and
        hashlib.sha256(raw).hexdigest() == pin["sha256"], "EXACT_QUALIFIED_NAMESPACE_RAW")
    tree = ast.parse(raw.decode("utf-8"))
    names = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
    selected = names if functions is None else set(functions)
    require(selected and selected <= names, "ALL_SELECTED_ORIGINAL_FUNCTIONS")
    nodes = [copy.deepcopy(n) for n in tree.body if isinstance(n, ast.Assign) or
        (isinstance(n, ast.FunctionDef) and n.name in selected)]
    original = [ast.dump(n, include_attributes=False) for n in tree.body if isinstance(n, ast.Assign) or
        (isinstance(n, ast.FunctionDef) and n.name in selected)]
    require([ast.dump(n, include_attributes=False) for n in nodes] == original, "UNCHANGED_ALL_FUNCTION_AND_CONSTANT_AST")
    env = dict(environment, __name__="qualified_namespace", __file__=pin["path"])
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])), pin["path"], "exec"), env)
    return NS(**env), dict(source_pin=pin, functions=sorted(selected),
        original_selected_function_and_constant_AST_unchanged=True,
        top_level_imports_or_runner_or_CLI_executed=False)


def namespace(q):
    """Fresh raw pins, no byte/JSON/hash cache, no sys.modules deletion/filter."""
    raw = []
    for pin in SOURCES:
        actual, data = q._read(pin["path"], parse=True)
        q._bind(pin["path"], actual)
        a.exact(actual, pin, "ALL_FIVE_CURRENT_NAMESPACE_SOURCES")
        raw.append(bytes(data))
    common = dict(json=json, math=math, re=re, Path=Path, os=os, sys=sys,
        threading=threading, time=time, FunctionType=FunctionType, NS=NS)
    completed, p1 = project(raw[0], SOURCES[0], common)
    native, p2 = project(raw[1], SOURCES[1], dict(common, runtime=source,
        retained=base.native, completed=completed), SOURCE_FUNCTIONS)
    first, p3 = project(raw[2], SOURCES[2], dict(common, source=native))
    full, p4 = project(raw[3], SOURCES[3], dict(common, prior=first))
    api, p5 = project(raw[4], SOURCES[4], dict(common, contract=full), LEGACY_FUNCTIONS)
    env = api.binding.__globals__
    # Keep the old qualification's EXPECTED code kind/paths in an isolated
    # function. New runtime command metadata must never rewrite old authority.
    old_qualification = FunctionType(api.qualification.__code__, dict(env),
        argdefs=api.qualification.__defaults__)
    files = tuple(dict.fromkeys(api.FILES + (SELF, TEST)))
    env.update(SELF=SELF, TEST=TEST, FILES=files,
        CONTROLLERS=tuple(dict.fromkeys(source.CONTROLLERS + files)), qualification=old_qualification)
    api = NS(**env)
    return api, dict(namespace_sources=list(SOURCES), original_AST_proofs=[p1,p2,p3,p4,p5],
        all_original_full_body_source_observer_oracles_retained=True,
        code_sources_freshly_bound_separately_from_imported_module_count=True,
        imported_modules_hidden_or_removed=False, helper64_ceiling_raised=False,
        default_runtime_modules_mutated=False, source_or_product_runner_executed=False)


def own_inputs(q):
    require(base.CONFIG is not None and base.CONFIG.index == 130, "ONLY_CASE130")
    text = q.text(DATA_PATH)
    require(0 < len(text.encode("utf-8")) <= 16384, "BOUNDED_LEAN_DATA")
    row = json.loads(text, object_pairs_hook=base.unique)
    require(type(row) is dict and set(row) == {"schema_version", "index", "before", "base_step_pin",
        "original_connection_qualification_pin", "failed_preflight_pin", "namespace_source_pins",
        "lean_qualification_pin"}, "CLOSED_LEAN_DATA")
    a.fields(row, dict(schema_version="hwpx-agent.p09-lean-compound-validation/v2", index=130,
        before=123, base_step_pin=base.CONFIG.pin, original_connection_qualification_pin=LEGACY_QUAL,
        failed_preflight_pin=FAILED_PREFLIGHT, namespace_source_pins=list(SOURCES)), "EXACT_LEAN_BINDING")
    pin = row["lean_qualification_pin"]
    base.scope.pins([pin], 1)
    require(pin["path"] == QUAL_PATH, "EXACT_LEAN_QUAL_PATH")
    qual = a.read_exact(q, pin)
    a.fields(qual, dict(state=CODE_PASS, accepted_count_after=123, accepted_count_delta=0,
        cleanup_confirmed=True, all_original_full_validation_AST_preserved=True,
        original_helper64_ceiling_retained=True, product_body_replayed=False,
        Native_source_replayed=False), "QUALIFIED_NEW_LEAN_CODE_NOT_PRODUCT")
    a.exact(qual["contracts"], dict(run=24, errors=0, failures=0, skipped=0), "EXACT_LEAN24")
    require(set(base.scope.pins(qual["new_code_pins"],2)) == {SELF,TEST}, "ALL_NEW_LEAN_CODE2")
    for p in qual["new_code_pins"]:
        a.exact(q.pin(p["path"]), p, "CURRENT_TESTED_LEAN_CODE")
    failed = a.read_exact(q, FAILED_PREFLIGHT)
    a.fields(failed, dict(state="FAILED_NOT_ACCEPTED", error_code="METADATA_CONNECTION_ORIGINAL_HELPER_BOUND",
        product_worker_or_Native_frame_executed=False, accepted_count_delta=0,
        synthetic_connection_contracts_passed=10, cleanup_confirmed=True, final_fresh_hashes=0), "PRESERVED_HELPER_FAILURE")
    return row


def binding_attempt(q, run):
    require(type(run) is int and run == 1, "ONE_REVIEWED_PRODUCT_ATTEMPT")
    own_inputs(q)
    api, _ = namespace(q)
    return api.binding_attempt(q, run)


def template():
    engine, proof = source.template()
    require(engine.run_owned.__globals__["SELF"] == source.SELF, "EXACT_SOURCE_STAT_ENGINE")
    engine.run_owned.__globals__.update(SELF=SELF, TEST=TEST)
    engine.worker.__globals__.update(SELF=SELF, TEST=TEST)
    return engine, dict(proof, lean_full_compound_controller=True,
        original_engine_bytecode_unchanged=True, new_sampler_or_guard_relaxation=False)


def worker(task):
    require(base.CONFIG is not None and base.CONFIG.index == 130, "ONLY_WORKER130")
    a.exact(base.run_for(task), 1, "FIRST_OWNED_WORKER")
    engine, _ = template()
    return engine.worker(task)


def run_owned(run):
    require(base.CONFIG is not None and base.CONFIG.index == 130 and type(run) is int and run == 1, "ONE_PRODUCT130")
    return FunctionType(source.run_owned.__code__, dict(source.run_owned.__globals__,
        template=template, binding_attempt=binding_attempt), argdefs=source.run_owned.__defaults__)(run)


def preflight_projection(raw, leaf):
    original = source.preflight_projection(raw, leaf)
    code = original.__code__
    old = "-source-stat-ancestor-preflight001.v1.json"
    new = "-lean-compound-preflight002.v1.json"
    require(sum(type(x) is str and x == old for x in code.co_consts) == 1, "ONE_NEW_PREFLIGHT_DESTINATION")
    constants = tuple(new if type(x) is str and x == old else x for x in code.co_consts)
    fixed = code.replace(co_consts=constants)
    require(fixed.replace(co_consts=code.co_consts) == code, "ALL_ORIGINAL_PREFLIGHT_CODE_AND_TESTS_RETAINED")
    env = dict(original.__globals__, SELF=SELF, TEST=TEST, template=template, binding_attempt=binding_attempt)
    return FunctionType(fixed, env, argdefs=original.__defaults__)


def preflight():
    return FunctionType(source.preflight.__code__, dict(source.preflight.__globals__,
        preflight_projection=preflight_projection), argdefs=source.preflight.__defaults__)()


def prepare(q, root_pin):
    own_inputs(q)
    api, _ = namespace(q)
    row, listing, evidence, proof = api.prepare(q, root_pin)
    expected = base.scope.pins(row["source_freeze"])
    for name in (SELF, TEST, DATA_PATH):
        a.exact(expected.get(name), q.snapshots[name], "LEAN_CODE_AND_DATA_INSIDE_FULL_NATIVE_FRAME")
    return row, listing, evidence, proof


def context(step):
    return NS(**{**vars(source.context(step)), "SELF":SELF,"TEST":TEST})


def accept(root_pin):
    require(base.CONFIG is not None and base.CONFIG.index == 130, "ONLY_ACCEPT130")
    files = (SELF, TEST) + tuple(p["path"] for p in SOURCES)
    env = dict(source.accept.__globals__, SELF=SELF, TEST=TEST,
        CONTROLLERS=tuple(dict.fromkeys(source.CONTROLLERS+files)), context=context, prepare=prepare)
    return FunctionType(source.accept.__code__, env, argdefs=source.accept.__defaults__)(root_pin)


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1:3] == ["--owned-worker", "--task"]:
        base.configure(base.task_index(sys.argv[3])); raise SystemExit(worker(sys.argv[3]))
    parser = argparse.ArgumentParser()
    parser.add_argument("--case",type=int,required=True)
    parser.add_argument("--run",type=int)
    parser.add_argument("--preflight",action="store_true")
    parser.add_argument("--accept",action="store_true")
    parser.add_argument("--root-bytes",type=int)
    parser.add_argument("--root-sha256")
    args=parser.parse_args();require(args.case==130,"EXPLICIT_CASE130");base.configure(130)
    require(sum((args.run is not None,args.preflight,args.accept))==1,"ONE_MODE")
    if args.accept:
        pin=dict(path=source.root_path(base.CONFIG),bytes=args.root_bytes,sha256=args.root_sha256)
        base.scope.pins([pin],1);raise SystemExit(accept(pin))
    require(args.root_bytes is None and args.root_sha256 is None,"ROOT_ARGUMENTS_ACCEPT_ONLY")
    raise SystemExit(preflight() if args.preflight else run_owned(args.run))
