"""Fixed full inherited-scope connection after real lean130 authority124.

No recursive runner import, receipt rewrite, scope exclusion or successful-body
replay. The exact original flat binding AST changes ONE validator dependency;
all original Native/product/resource/cleanup checks and costs remain.
"""
import argparse
import ast
import copy
import hashlib
import json
import re
import sys
from types import FunctionType, SimpleNamespace as NS

import accept_flat_lean130_compound_parent_v1 as previous

lean, source, base, a, c = previous.lean, previous.source, previous.base, previous.a, previous.c
SELF = "tools/p09/flat_current_queue_inherited_scope_runtime_v1.py"
TEST = "tools/p09/tests/test_flat_current_queue_inherited_scope_v1.py"
FILES = (SELF, TEST)
QUAL_PATH = "implementation/p09/evidence/p09-361-case131-inherited-scope-code-r334.v1.json"
BASE_PIN = dict(path="tools/p09/flat_current_queue_runtime.py", bytes=11527,
    sha256="f67172dc0eedb965b67bde07d494ec8f1f1edd95573b58660bf2826d21baac1d")
PARENT_QUAL = dict(path="implementation/p09/evidence/p09-361-case130-compound-parent-selector-code-r330.v1.json",
    bytes=4363, sha256="4574841cc37694bad2161f525efe27bec1d81d5508649f493947ea8b0c979d15")
LEAN_QUAL = dict(path="implementation/p09/evidence/p09-361-case130-lean-namespace-code-r328.v1.json",
    bytes=8377, sha256="e1ee9a41eadc348d5bd127415f348f5132db62db3357862b0c5d6f8e140d4f6b")


def require(ok, code):
    if not ok: raise ValueError("INHERITED_SCOPE_" + code)


def data_path(index):
    require(type(index) is int and 131 <= index <= 249, "ONLY_CURRENT_SUCCESSORS")
    return f"implementation/p09/evidence/p09-361-case{index}-inherited-scope-data001.v1.json"


def validate_data(row, step):
    require(type(row) is dict and set(row) == {"schema_version", "index", "before", "run",
        "base_step_pin", "prior_source_data_pin", "original_base_runtime_pin", "parent_qualification_pin",
        "lean_qualification_pin", "connection_qualification_pin", "connection_code_pins"}, "CLOSED_DATA")
    a.fields(row, dict(schema_version="hwpx-agent.p09-fixed-inherited-scope-connection/v1",
        index=step.index, before=step.before, run=1, base_step_pin=step.pin,
        original_base_runtime_pin=BASE_PIN, parent_qualification_pin=PARENT_QUAL,
        lean_qualification_pin=LEAN_QUAL), "EXACT_DATA_CURSOR_AND_LINEAGE")
    a.exact(row["prior_source_data_pin"]["path"], source.data_path(step.index), "SOURCE_DATA_PATH")
    base.scope.pins([row["prior_source_data_pin"]], 1)
    a.exact(row["connection_qualification_pin"]["path"], QUAL_PATH, "CURRENT_QUAL_PATH")
    base.scope.pins([row["connection_qualification_pin"]], 1)
    require(set(base.scope.pins(row["connection_code_pins"], 2)) == set(FILES), "ALL_NEW_CODE")
    data_path(step.index)
    return row


def own_inputs(q):
    step = base.CONFIG
    require(step is not None, "CONFIG_REQUIRED")
    text = q.text(data_path(step.index))
    require(0 < len(text.encode("utf-8")) <= 16384, "BOUNDED_DATA")
    row = validate_data(json.loads(text, object_pairs_hook=base.unique), step)
    a.exact(q.pin(source.data_path(step.index)), row["prior_source_data_pin"], "EXACT_ORIGINAL_SOURCE_DATA")
    code = a.read_exact(q, row["connection_qualification_pin"])
    a.fields(code, dict(state="PASS_FIXED_INHERITED_SCOPE_CODE_AND_ACTUAL130_ORACLE_NOT_RUNTIME131",
        accepted_count_after=124, accepted_count_delta=0, cleanup_confirmed=True,
        original_whole_previous130_oracle_checked=True, body_or_Native_replayed=False), "ACTUAL_BOUND_CODE_QUAL")
    a.exact(code["contracts"], dict(run=20, errors=0, failures=0, skipped=0), "CONTRACT20")
    a.exact(code["new_code_pins"], row["connection_code_pins"], "TESTED_CODE_LIST")
    for pin in row["connection_code_pins"]: a.exact(q.pin(pin["path"]), pin, "CURRENT_TESTED_CODE")
    previous.qualify(q, PARENT_QUAL)
    a.exact(q.pin(lean.QUAL_PATH), LEAN_QUAL, "CURRENT_LEAN24_QUAL")
    a.exact(q.pin(BASE_PIN["path"]), BASE_PIN, "CURRENT_ORIGINAL_FLAT_BINDING")
    return row


def inherited_for_step(q, step, api=None):
    """Derive expectations from independent exact predecessor receipts only."""
    parent = a.read_exact(q, step.prior_queue_pin)
    if step.index == 130:
        require(api is not None, "EXPLICIT_COMPOUND_API_REQUIRED")
        fresh = api.parent_header(parent, step)
        doc, _, _, required, candidate = api.documents(q)
        a.exact(parent["actual_compound_evidence_validation"], candidate, "ALL_COMPOUND_BODY_SOURCE_OBSERVER_CHECKS")
        return base.scope.extend(required, fresh)
    require(131 <= step.index <= 249, "ORDINARY_PARENT_RANGE")
    a.fields(parent, dict(state="PASS_EXACT_FLAT_CURRENT_EPOCH_ACCEPTED_ONCE_NOT_FULL249_OR_GATE",
        accepted_count_after=step.before, accepted_count_delta=1, next_runtime_index=step.index,
        accepted_test_indices=[step.index-1], runtime_candidate_pin=step.prior_candidate_pin,
        resource_cleanup_confirmed=True, full249_current_qualified=False, signed16_current_qualified=False,
        P09_gate="OPEN", A12_gate="OPEN", A13_gate="OPEN", P10_started=False), "EXACT_ORDINARY_PARENT")
    require(parent.get("synthetic_fixture_only_not_evidence",False) is False, "NO_SYNTHETIC_PARENT")
    root = a.read_exact(q, step.prior_candidate_pin)
    require(root.get("synthetic_fixture_only_not_evidence",False) is False, "NO_SYNTHETIC_PREDECESSOR")
    required = base.scope.pins(root["source_freeze"])
    fresh = base.scope.pins(parent["fresh_input_pins"])
    n = len(fresh)
    require(type(parent["fresh_read_passes"]) is int and parent["fresh_read_passes"] >= 2*n and
        type(parent["fresh_bytes_read"]) is int and parent["fresh_bytes_read"] >= 2*sum(p["bytes"] for p in fresh.values()),
        "ALL_PRIOR_FRESH_READS")
    a.exact(parent["final_fresh_hashes"], n, "ALL_PRIOR_FINAL_HASHES")
    a.resource_history(parent["resource_samples"])
    return base.scope.extend(required, fresh)


def previous_validation(q, row, listing, oldbody, fresh, oldctx, flat=True):
    current = base.CONFIG
    require(current is not None and 131 <= current.index <= 249, "CONFIGURED_SUCCESSOR")
    a.fields(vars(oldctx), dict(INDEX=current.index-1, BEFORE=current.before-1,
        CASE=listing["source_test_names"][current.index-2]), "EXACT_PREVIOUS_CONTEXT")
    step = base.load_config(current.index-1)
    a.exact(q.pin(step.path), step.pin, "REAL_IMMUTABLE_PREVIOUS_STEP")
    if step.index == 130:
        # Isolated explicit old step; NEVER mutate the process's current CONFIG.
        previous.qualify(q, PARENT_QUAL)
        old_base = NS(**{**vars(base), "CONFIG": step})
        own = FunctionType(lean.own_inputs.__code__, dict(lean.own_inputs.__globals__, base=old_base),
            argdefs=lean.own_inputs.__defaults__)
        own(q)
        api, _ = lean.namespace(q)
        inherited = inherited_for_step(q, step, api)
        original = FunctionType(api.validator.__code__, dict(api.validator.__globals__), argdefs=api.validator.__defaults__)
        validate = FunctionType(api.validate_candidate.__code__,
            dict(api.validate_candidate.__globals__, validator=previous.scoped_validator(original, inherited)),
            argdefs=api.validate_candidate.__defaults__)
        ctx = lean.context(step)
    else:
        inherited = inherited_for_step(q, step)
        validate = FunctionType(source.validate_candidate.__code__, dict(source.validate_candidate.__globals__,
            validator=previous.scoped_validator(validator, inherited)), argdefs=source.validate_candidate.__defaults__)
        ctx = context(step)
    result = validate(q,row,listing,oldbody,fresh,ctx,flat)
    result[1].update(previous_actual_full_oracle_retained=True,previous_runtime_context_bound_to_executed_code=True,
        current_CONFIG_mutated=False,expected_scope_not_copied_from_candidate_observations=True)
    return result


def binding_projection(raw, replacement=previous_validation):
    require(type(raw) is bytes and len(raw)==BASE_PIN["bytes"] and
        hashlib.sha256(raw).hexdigest()==BASE_PIN["sha256"], "EXACT_ORIGINAL_BINDING_RAW")
    nodes=[n for n in ast.parse(raw.decode("utf-8")).body if isinstance(n,ast.FunctionDef) and n.name=="binding"]
    require(len(nodes)==1, "ONE_ORIGINAL_BINDING")
    node=copy.deepcopy(nodes[0]);before=ast.dump(node,include_attributes=False)
    target=ast.dump(ast.parse("acceptance.validate_candidate(q,row,listing,oldbody,fresh,previous,flat=CONFIG.index>116)",mode="eval").body,include_attributes=False)
    changes=0
    class Project(ast.NodeTransformer):
        def visit_Call(self,n):
            nonlocal changes
            if ast.dump(n,include_attributes=False)==target:
                old=copy.deepcopy(n);n.func=ast.Name(id="_validate_previous",ctx=ast.Load());n._old=old;changes+=1
                return n
            return self.generic_visit(n)
    node=Project().visit(node)
    require(changes==1, "ONE_STRONGER_VALIDATOR_DEPENDENCY")
    class Undo(ast.NodeTransformer):
        def visit(self,n):
            if hasattr(n,"_old"):return copy.deepcopy(n._old)
            return super().visit(n)
    require(ast.dump(Undo().visit(copy.deepcopy(node)),include_attributes=False)==before,"ALL_ORIGINAL_BINDING_AST_RETAINED")
    env=dict(vars(base),_validate_previous=replacement)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),BASE_PIN["path"],"exec"),env)
    return env["binding"],dict(original_binding_AST_restored_exactly=True,changed_validator_dependencies=1,
        original_parent_current_compiled_Rust_bootstrap_archive_fresh_read_checks_retained=True,
        original_function_code_or_default_modules_mutated=False)


def binding(q):
    pin,raw=q._read(BASE_PIN["path"],parse=True);q._bind(pin["path"],pin)
    a.exact(pin,BASE_PIN,"ORIGINAL_BINDING_PIN")
    fn,_=binding_projection(bytes(raw))
    return fn(q)


def binding_attempt(q, run):
    a.exact(run,1,"FIRST_EXPLICIT_RUN_ONLY")
    own_inputs(q)
    source.reviewed_inputs(q,run)
    return binding(q)


def context(step):
    return NS(**{**vars(source.context(step)),"SELF":SELF,"TEST":TEST})


def template():
    engine,proof=source.template()
    require(engine.run_owned.__globals__["SELF"]==source.SELF,"UNCHANGED_SOURCE_TEMPLATE")
    engine.run_owned.__globals__.update(SELF=SELF,TEST=TEST)
    engine.worker.__globals__.update(SELF=SELF,TEST=TEST)
    return engine,dict(proof,fixed_inherited_scope_controller=True,original_engine_bytecode_unchanged=True,
        original_CPU_RAM_deadlines_and_costs_retained=True,new_sampler_or_query=False)


def worker(task):
    a.exact(base.run_for(task),1,"FIRST_WORKER")
    engine,_=template();return engine.worker(task)


def run_owned(run):
    a.exact(run,1,"ONE_EXPLICIT_PRODUCT_ATTEMPT")
    return FunctionType(source.run_owned.__code__,dict(source.run_owned.__globals__,
        template=template,binding_attempt=binding_attempt),argdefs=source.run_owned.__defaults__)(run)


def preflight_projection(raw, leaf):
    old=source.preflight_projection(raw,leaf);code=old.__code__
    prior="-source-stat-ancestor-preflight001.v1.json";new="-inherited-scope-preflight001.v1.json"
    require(sum(type(x) is str and x==prior for x in code.co_consts)==1,"ONE_NEW_PREFLIGHT_DESTINATION")
    constants=tuple(new if type(x) is str and x==prior else x for x in code.co_consts)
    fixed=code.replace(co_consts=constants)
    require(fixed.replace(co_consts=code.co_consts)==code,"ALL_ORIGINAL_PREFLIGHT_CODE_AND_TESTS")
    return FunctionType(fixed,dict(old.__globals__,SELF=SELF,TEST=TEST,template=template,
        binding_attempt=binding_attempt),argdefs=old.__defaults__)


def preflight():
    return FunctionType(source.preflight.__code__,dict(source.preflight.__globals__,
        preflight_projection=preflight_projection),argdefs=source.preflight.__defaults__)()


def validator(raw, ctx, flat=True):
    fn,proof=source.validator(raw,ctx,flat)
    fn.__globals__["CONTROLLERS"]=tuple(dict.fromkeys(fn.__globals__["CONTROLLERS"]+FILES))
    return fn,dict(proof,inherited_controller_inside_whole_Native_scope=True)


def prepare(q, root_pin):
    own_inputs(q)
    inherited=inherited_for_step(q,base.CONFIG)
    def full(q,row,listing,oldbody,fresh,ctx,flat=True):
        original=FunctionType(source.validate_candidate.__code__,dict(source.validate_candidate.__globals__,
            validator=previous.scoped_validator(validator,inherited)),argdefs=source.validate_candidate.__defaults__)
        return original(q,row,listing,oldbody,fresh,ctx,flat)
    def project(raw):
        fn=source.prepare_projection(raw)
        fn.__globals__.update(validate_candidate=full,
            r=NS(**{**vars(fn.__globals__["r"]),"context":context}))
        return fn
    fn=FunctionType(source.prepare.__code__,dict(source.prepare.__globals__,prepare_projection=project),
        argdefs=source.prepare.__defaults__)
    row,listing,evidence,proof=fn(q,root_pin)
    expected=base.scope.pins(row["source_freeze"])
    data=validate_data(json.loads(q.text(data_path(base.CONFIG.index)),object_pairs_hook=base.unique),base.CONFIG)
    for pin in data["connection_code_pins"]+[data["connection_qualification_pin"],BASE_PIN,PARENT_QUAL,LEAN_QUAL]:
        a.exact(expected.get(pin["path"]),pin,"ALL_NEW_CODE_QUAL_AND_LINEAGE_INSIDE_NATIVE")
    a.exact(expected.get(data_path(base.CONFIG.index)),q.snapshots[data_path(base.CONFIG.index)],"DATA_INSIDE_NATIVE")
    return row,listing,evidence,dict(proof,complete_independent_inherited_scope_retained=True)


def accept(root_pin):
    return FunctionType(source.accept.__code__,dict(source.accept.__globals__,SELF=SELF,TEST=TEST,
        CONTROLLERS=tuple(dict.fromkeys(source.CONTROLLERS+FILES)),context=context,prepare=prepare),
        argdefs=source.accept.__defaults__)(root_pin)


if __name__=="__main__":
    try:
        if len(sys.argv)==4 and sys.argv[1:3]==["--owned-worker","--task"]:
            base.configure(base.task_index(sys.argv[3]));raise SystemExit(worker(sys.argv[3]))
        parser=argparse.ArgumentParser();parser.add_argument("--case",type=int,required=True)
        parser.add_argument("--run",type=int);parser.add_argument("--preflight",action="store_true")
        parser.add_argument("--accept",action="store_true");parser.add_argument("--root-bytes",type=int)
        parser.add_argument("--root-sha256");args=parser.parse_args();data_path(args.case);base.configure(args.case)
        require(sum((args.run is not None,args.preflight,args.accept))==1,"ONE_MODE")
        if args.accept:
            pin=dict(path=source.root_path(base.CONFIG),bytes=args.root_bytes,sha256=args.root_sha256)
            base.scope.pins([pin],1);raise SystemExit(accept(pin))
        require(args.root_bytes is None and args.root_sha256 is None,"ACCEPT_ARGUMENTS_ONLY")
        raise SystemExit(preflight() if args.preflight else run_owned(args.run))
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as e:
        code=str(e) if isinstance(e,ValueError) else "REDACTED_INHERITED_CONNECTION_FAILURE"
        print(json.dumps(dict(state="FAILED_NOT_ACCEPTED",error_code=code if re.fullmatch("[A-Z0-9_]{1,256}",code) else "REDACTED_INHERITED_CONNECTION_FAILURE")))
        raise SystemExit(2) from None
