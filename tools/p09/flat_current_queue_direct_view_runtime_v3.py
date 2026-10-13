"""Exact direct-view backend/full oracle connection; preflight before actual134.

Old v2, view and oracle definitions load from exact fresh raw namespaces, not
CLI/module imports. No imported helper is hidden; every raw source remains in
the whole input scope. Old retained predecessors keep their original checker.
All engine/Job/GO/byte/resource statements and physical ceilings are unchanged.
"""
import argparse
import ast
import copy
import ctypes
from ctypes import wintypes as w
from contextlib import contextmanager
import hashlib
import json
import re
import sys
from types import FunctionType, MappingProxyType, SimpleNamespace as NS

import flat_preserved129_lean_connection_v2 as lean

source, base, a, c = lean.source, lean.base, lean.a, lean.c
SELF = "tools/p09/flat_current_queue_direct_view_runtime_v3.py"
TEST = "tools/p09/tests/test_flat_current_queue_direct_view_runtime_v3.py"
QUAL_PATH = "implementation/p09/evidence/p09-361-case134-direct-view-connection-code-r369.v1.json"
NAMESPACE_PINS = (
    dict(path="tools/p09/flat_current_queue_inherited_scope_runtime_v2.py", bytes=9759,
         sha256="88d28b34b2920f3f987b45a4cc32a980ef8d44123abcd633a1947ee91ee56288"),
    dict(path="tools/p09/held_native_read_views_v1.py", bytes=13370,
         sha256="3aeb0c2ae50f2de0aeeba3c992aac5c0797367eac09c7693a5b3a7d5782e0584"),
    dict(path="tools/p09/held_native_view_oracle_v1.py", bytes=9527,
         sha256="831152fa350e2f743a6c9788bf7b6f8f5d8e2e212544874bc8361a865589a979"))
VIEW_QUAL = dict(path="implementation/p09/evidence/p09-361-case134-direct-view23-focused-native3-qualification-r363.v1.json",
    bytes=18718, sha256="b028ce6120a4123b4df709daaee2de4846e544b85bd3495811b7ff7e7a3a40ee")
ORACLE_QUAL = dict(path="implementation/p09/evidence/p09-361-case134-direct-oracle19-focused-native3-old133-qualification-r365.v1.json",
    bytes=6113, sha256="ed2e87493e5778c7ab74ab09b42c0729e608161b7a4f2f04d12f5c2b72d8686d")
FAILED134 = dict(path="implementation/p09/evidence/p09-361-case134-inherited-namespace-preflight002.v1.json",
    bytes=52385, sha256="c72bf7084ccb0424b66165dcb8d2ce07c8f9e424ea358dc1f8bc2a8edca692c7")
CODE_PASS = "PASS_DIRECT_VIEW_RUNTIME_NAMESPACE_CONNECTION_AND_FULL_OLD133_ORACLE_NOT_ACTUAL134"
OLD = VIEW = ORACLE = NATIVE = API = PROOF = None


def require(ok, code):
    if not ok:
        raise ValueError("DIRECT_CONNECTION_" + code)


def definitions(raw, pin, environment):
    require(type(raw) is bytes and len(raw) == pin["bytes"]
            and hashlib.sha256(raw).hexdigest() == pin["sha256"], "EXACT_NAMESPACE_RAW")
    tree = ast.parse(raw.decode("utf-8"))
    nodes = [copy.deepcopy(n) for n in tree.body
             if isinstance(n, (ast.Assign, ast.FunctionDef, ast.ClassDef))]
    original = [ast.dump(n, include_attributes=False) for n in tree.body
                if isinstance(n, (ast.Assign, ast.FunctionDef, ast.ClassDef))]
    require(nodes and [ast.dump(n, include_attributes=False) for n in nodes] == original,
            "ALL_ORIGINAL_FUNCTION_CLASS_CONSTANT_AST_UNCHANGED")
    env = dict(environment, __name__="p09_exact_direct_namespace", __file__=pin["path"])
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[])),
                 pin["path"], "exec"), env)
    return NS(**env), dict(source_pin=pin, all_function_class_constant_AST_unchanged=True,
        full_module_or_CLI_import_executed=False, imported_modules_hidden_or_removed=False)


def namespaces(raws):
    require(type(raws) is list and len(raws) == 3, "THREE_EXACT_NAMESPACES")
    old, p1 = definitions(raws[0], NAMESPACE_PINS[0], dict(lean=lean, argparse=argparse,
        ast=ast, copy=copy, hashlib=hashlib, json=json, re=re, sys=sys, FunctionType=FunctionType, NS=NS))
    retained = base.native
    view, p2 = definitions(raws[1], NAMESPACE_PINS[1], dict(ctypes=ctypes, w=w,
        contextmanager=contextmanager, MappingProxyType=MappingProxyType, NS=NS, original=retained))
    oracle, p3 = definitions(raws[2], NAMESPACE_PINS[2], dict(ast=ast, copy=copy,
        FunctionType=FunctionType, NS=NS, views=view))
    native = NS(**{**vars(view), "SOURCES": retained.SOURCES, "frames": retained.frames,
        "definitions": retained.definitions})
    return old, view, oracle, native, dict(exact_namespace_proofs=[p1,p2,p3],
        original_v2_and_all_view_oracle_definitions_retained=True,
        helper_ceiling_raised=False, source_scope_exclusions_added=False,
        parsed_file_byte_hash_or_JSON_cache=False, original_default_modules_mutated=False)


def bootstrap():
    raw = []
    for pin in NAMESPACE_PINS:
        base.stable.stable.prior.build.direct_path(c.ROOT / pin["path"], file_required=True)
        with (c.ROOT / pin["path"]).open("rb") as stream:
            raw.append(stream.read(pin["bytes"]+1))
    return namespaces(raw)


def rebind(q):
    raw = []
    for pin in NAMESPACE_PINS:
        actual, buffer = q._read(pin["path"], parse=True)
        q._bind(pin["path"], actual);a.exact(actual, pin, "FRESH_NAMESPACE_SOURCE")
        raw.append(bytes(buffer))
    old, view, oracle, native, proof = namespaces(raw)
    for current, fresh, names in ((VIEW, view, ("load", "model", "locks_type")),
            (ORACLE, oracle, ("mechanics_projection", "project_checker", "retained_evidence", "runtime_budget"))):
        for name in names:
            a.exact(getattr(current,name).__code__ == getattr(fresh,name).__code__,
                    True, "FRESH_SAME_QUALIFIED_FUNCTION_CODE")
    return proof


def data_path(index):
    require(type(index) is int and 134 <= index <= 249, "CURRENT_SUCCESSOR_RANGE")
    return f"implementation/p09/evidence/p09-361-case{index}-direct-view-connection-data003.v1.json"


def validate_data(row, step):
    require(type(row) is dict and set(row) == {"schema_version", "index", "before", "run",
        "base_step_pin", "prior_source_data_pin", "original_base_runtime_pin",
        "parent_qualification_pin", "lean_qualification_pin", "connection_qualification_pin",
        "connection_code_pins", "prior_v2_data_pin", "namespace_source_pins",
        "view_qualification_pin", "oracle_qualification_pin", "failed134_preflight_pin"}, "CLOSED_V3_DATA")
    a.fields(row, dict(schema_version="hwpx-agent.p09-direct-held-view-connection/v3",
        index=step.index, before=step.before, run=1, base_step_pin=step.pin,
        original_base_runtime_pin=OLD.PRISTINE.BASE_PIN, parent_qualification_pin=OLD.PRISTINE.PARENT_QUAL,
        lean_qualification_pin=OLD.PRISTINE.LEAN_QUAL, namespace_source_pins=list(NAMESPACE_PINS),
        view_qualification_pin=VIEW_QUAL, oracle_qualification_pin=ORACLE_QUAL,
        failed134_preflight_pin=FAILED134), "EXACT_V3_LINEAGE")
    a.exact(row["prior_v2_data_pin"]["path"], OLD.data_path(step.index), "OLD_V2_DATA_PATH")
    a.exact(row["prior_source_data_pin"]["path"], source.data_path(step.index), "ORIGINAL_SOURCE_DATA_PATH")
    require(set(base.scope.pins(row["connection_code_pins"],6)) == set(FILES), "ALL_NEW_CODE6")
    require(set(base.scope.pins([row["connection_qualification_pin"]],1)) == {QUAL_PATH}, "V3_QUAL_PATH")
    data_path(step.index)
    return row


def own_inputs(q):
    require(base.CONFIG is not None, "CONFIG_REQUIRED")
    text = q.text(data_path(base.CONFIG.index))
    require(0 < len(text.encode("utf-8")) <= 16384, "BOUNDED_V3_DATA")
    row = validate_data(json.loads(text, object_pairs_hook=base.unique), base.CONFIG)
    rebind(q);OLD.own_inputs(q)  # Entire qualified v2/v1 code25/20 and DATA predicates.
    a.exact(q.snapshots[OLD.data_path(base.CONFIG.index)], row["prior_v2_data_pin"], "FRESH_OLD_V2_DATA")
    a.exact(q.pin(source.data_path(base.CONFIG.index)), row["prior_source_data_pin"], "FRESH_ORIGINAL_SOURCE_DATA")
    view = a.read_exact(q, VIEW_QUAL);oracle = a.read_exact(q, ORACLE_QUAL)
    a.fields(view, dict(state="PASS_DIRECT_VIEW23_AND_FOCUSED_REAL_NATIVE3_NOT_RUNTIME134_OR_GATE",
        contracts=dict(run=23,errors=0,failures=0,skipped=0),focused_frame_final_state="CLOSED",
        focused_Frame_COMMITTED_claimed=False,full134_scope_qualified=False,GO_authorized=False,
        cleanup_confirmed=True,focused_frame_cleanup_confirmed=True), "REAL_VIEW23_COMPONENT_ONLY")
    a.fields(oracle, dict(state="PASS_DIRECT_ORACLE19_FOCUSED3_MECHANICS_AND_UNCHANGED_ACTUAL133_FULL_ORACLE_NOT_RUNTIME134",
        contracts=dict(run=19,errors=0,failures=0,skipped=0),old_candidate_rejection_code="CURRENT_EPOCH_ACCEPT_BORROWED_STREAMS",
        full134_scope_qualified=False,actual_direct134_candidate_oracle_qualified=False,
        GO_authorized=False,cleanup_confirmed=True), "REAL_ORACLE19_COMPONENT_ONLY")
    backend = view["new_code_pins"] + oracle["new_code_pins"]
    a.exact(row["connection_code_pins"][2:], backend, "TESTED_BACKEND4_ORDER")
    a.exact(oracle["qualified_direct_view_code_pins"], view["new_code_pins"], "SAME_VIEW_CODE")
    code = a.read_exact(q, row["connection_qualification_pin"])
    a.fields(code, dict(state=CODE_PASS, cleanup_confirmed=True, accepted_count_after=127,
        accepted_count_delta=0, actual134_product_or_Native_executed=False,
        original_whole_previous133_oracle_checked=True), "CONNECTION_QUAL_NOT_PRODUCT")
    a.exact(code["contracts"], dict(run=12,errors=0,failures=0,skipped=0), "CONNECTION12")
    a.exact(code["new_code_pins"], row["connection_code_pins"], "ALL_TESTED_CURRENT_CODE6")
    for p in row["connection_code_pins"]:
        a.exact(q.pin(p["path"]), p, "CURRENT_V3_CODE")
        directory = ("p361-case134-direct-view-connection-qualified-code/" if p["path"] in (SELF,TEST)
                     else "p361-case134-direct-view-qualified-code/")
        archive = "implementation/p09/evidence/" + directory + p["path"]
        a.exact(q.pin(archive), dict(p,path=archive), "EXACT_QUALIFIED_ARCHIVE")
    failed = a.read_exact(q, FAILED134)
    a.fields(failed, dict(state="FAILED_NOT_ACCEPTED",error_code="RETAINED_READ_WHOLE_CLOSURE_INSIDE_UNCHANGED600",
        product_worker_or_Native_frame_executed=False,accepted_count_delta=0,cleanup_confirmed=True), "FAILED134_PRESERVED")
    return row


def validator(raw, ctx, flat=True):
    project, proof = OLD.API.validator(raw, ctx, flat)
    project = ORACLE.project_checker(project, project.__globals__["ORACLE_SCOPE"])
    project.__globals__["CONTROLLERS"] = tuple(dict.fromkeys(project.__globals__["CONTROLLERS"] + FILES))
    return project, dict(proof, exact_direct_mechanics_and_complete_cost_projection=True,
        all_original_nonphysical_oracle_predicates_retained=True)


def candidate_connection(function):
    """Copy all six original wrapper codes; change only explicit dependencies."""
    env = dict(function.__globals__)
    for name in ("prior", "accepted", "metadata", "original"):
        obj = env.get(name)
        if name in function.__code__.co_names and hasattr(obj, "validate_candidate"):
            child = candidate_connection(obj.validate_candidate)
            env[name] = NS(**{**vars(obj), "validate_candidate": child})
    env["validator"] = validator
    if "candidate" in function.__code__.co_names:
        original = env["candidate"]
        env["candidate"] = NS(**{**vars(original),
            "retained_evidence": lambda row: ORACLE.retained_evidence(row, original)})
    return FunctionType(function.__code__, env, argdefs=function.__defaults__, closure=function.__closure__)


def previous_validation(q, row, listing, oldbody, fresh, oldctx, flat=True):
    if oldctx.INDEX <= 133:
        return OLD.API.previous_validation(q,row,listing,oldbody,fresh,oldctx,flat)
    original = OLD.API.previous_validation
    env = dict(original.__globals__, source=CONNECTED_SOURCE, validator=validator, context=context)
    return FunctionType(original.__code__, env, argdefs=original.__defaults__)(q,row,listing,oldbody,fresh,oldctx,flat)


def context(step):
    return NS(**{**vars(source.context(step)), "SELF":SELF, "TEST":TEST})


def template():
    engine, proof = OLD.API.template()
    env = engine.run_owned.__globals__
    env.update(SELF=SELF, TEST=TEST, native=NATIVE, runtime_budget=ORACLE.runtime_budget)
    engine.worker.__globals__.update(SELF=SELF, TEST=TEST, native=NATIVE)
    return engine, dict(proof, direct_read_backend_and_budget_explicitly_bound=True,
        original_engine_bytecode_unchanged=True, all_original_GO_Job_byte_identity_resource_guards_retained=True)


def binding(q):
    pin,raw = q._read(OLD.API.BASE_PIN["path"],parse=True);q._bind(pin["path"],pin)
    a.exact(pin,OLD.API.BASE_PIN,"ORIGINAL_BINDING_PIN")
    fn,_ = OLD.API.binding_projection(bytes(raw), replacement=previous_validation)
    return fn(q)


def preflight_projection(raw, leaf):
    old = OLD.preflight_projection(raw, leaf)
    constants = tuple("-direct-view-preflight003.v1.json" if type(x) is str
        and x == "-inherited-namespace-preflight002.v1.json" else x for x in old.__code__.co_consts)
    require(sum(type(x) is str and x == "-inherited-namespace-preflight002.v1.json"
        for x in old.__code__.co_consts) == 1, "ONE_NEW_PREFLIGHT003_DESTINATION")
    code = old.__code__.replace(co_consts=constants)
    require(code.replace(co_consts=old.__code__.co_consts) == old.__code__, "ALL_PREFLIGHT_STATEMENTS_UNCHANGED")
    prebase = NS(**{**vars(base), "native":NATIVE,
        "stable":NS(**{**vars(base.stable), "runtime_budget":ORACLE.runtime_budget})})
    return FunctionType(code, dict(old.__globals__,SELF=SELF,TEST=TEST,base=prebase,
        template=template,binding_attempt=API.binding_attempt,data_path=data_path,
        connection_data=lambda q:own_inputs(q)), argdefs=old.__defaults__)


def preflight():
    return FunctionType(OLD.API.preflight.__code__,dict(OLD.API.preflight.__globals__,
        preflight_projection=preflight_projection),argdefs=OLD.API.preflight.__defaults__)()


OLD, VIEW, ORACLE, NATIVE, PROOF = bootstrap()
FILES = (SELF, TEST, VIEW.SELF, VIEW.TEST, ORACLE.SELF, ORACLE.TEST)
CONNECTED_SOURCE = NS(**{**vars(source), "validate_candidate":candidate_connection(source.validate_candidate)})
# Clone the original v1 family as one isolated globals dictionary. Defaults and
# historical predecessor functions remain qualified; explicit dispatch handles
# newly executed direct-view predecessors without changing any old receipt.
_original = OLD.API.own_inputs.__globals__
# OLD.API.own_inputs is v2 code, whereas original family functions share this env.
_family = OLD.API.prepare.__globals__
_env = dict(_family)
for _name, _fn in tuple(_env.items()):
    if type(_fn) is FunctionType and _fn.__globals__ is _family:
        _env[_name] = FunctionType(_fn.__code__, _env, argdefs=_fn.__defaults__, closure=_fn.__closure__)
_env.update(SELF=SELF,TEST=TEST,FILES=FILES,QUAL_PATH=QUAL_PATH,source=CONNECTED_SOURCE,
    own_inputs=own_inputs,validate_data=validate_data,data_path=data_path,validator=validator,
    previous_validation=previous_validation,template=template,binding=binding,context=context)
API = NS(**_env)

if __name__ == "__main__":
    try:
        if len(sys.argv)==4 and sys.argv[1:3]==["--owned-worker","--task"]:
            base.configure(base.task_index(sys.argv[3]));raise SystemExit(API.worker(sys.argv[3]))
        parser=argparse.ArgumentParser();parser.add_argument("--case",type=int,required=True)
        parser.add_argument("--run",type=int);parser.add_argument("--preflight",action="store_true")
        parser.add_argument("--accept",action="store_true");parser.add_argument("--root-bytes",type=int)
        parser.add_argument("--root-sha256");args=parser.parse_args();data_path(args.case);base.configure(args.case)
        require(sum((args.run is not None,args.preflight,args.accept))==1,"ONE_MODE")
        if args.accept:
            pin=dict(path=source.root_path(base.CONFIG),bytes=args.root_bytes,sha256=args.root_sha256)
            base.scope.pins([pin],1);raise SystemExit(API.accept(pin))
        require(args.root_bytes is None and args.root_sha256 is None,"ACCEPT_ARGUMENTS_ONLY")
        raise SystemExit(preflight() if args.preflight else API.run_owned(args.run))
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as e:
        code=str(e) if isinstance(e,ValueError) else "REDACTED_DIRECT_CONNECTION_FAILURE"
        print(json.dumps(dict(state="FAILED_NOT_ACCEPTED",error_code=code if re.fullmatch("[A-Z0-9_]{1,256}",code)
            else "REDACTED_DIRECT_CONNECTION_FAILURE")))
        raise SystemExit(2) from None
