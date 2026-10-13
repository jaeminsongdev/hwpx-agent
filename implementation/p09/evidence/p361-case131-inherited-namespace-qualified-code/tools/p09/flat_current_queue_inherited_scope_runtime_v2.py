"""Exact validation-only v1 namespaces; no full accept130/v1 runner import.

Original family/functions/constants and all Native/product/resource oracles are
preserved at their pinned bytes. Fresh raw rebinding precedes each connection.
Helper64, scope, rates, original guards/deadlines/costs are NEVER relaxed.
"""
import argparse
import ast
import copy
import hashlib
import json
import re
import sys
from types import FunctionType, SimpleNamespace as NS

import flat_preserved129_lean_connection_v2 as lean

source,base,a,c=lean.source,lean.base,lean.a,lean.c
SELF="tools/p09/flat_current_queue_inherited_scope_runtime_v2.py"
TEST="tools/p09/tests/test_flat_current_queue_inherited_scope_v2.py"
QUAL_PATH="implementation/p09/evidence/p09-361-case131-inherited-namespace-code-r339.v1.json"
NAMESPACE_PINS=(
    dict(path="tools/p09/accept_flat_lean130_compound_parent_v1.py",bytes=7323,
        sha256="d409e9e63b2a13b9f54de5d8531e1051eab9024282e459072cb0b7880ef2d200"),
    dict(path="tools/p09/flat_current_queue_inherited_scope_runtime_v1.py",bytes=15271,
        sha256="63f1ebe88082f6a4fb506b3f129970123783f4022b201ee7c343db2094c02934"))
OLD_TEST_PIN=dict(path="tools/p09/tests/test_flat_current_queue_inherited_scope_v1.py",bytes=5711,
    sha256="ceb60d0910797a091796e4598d97b05ae2b57c0340f47c22b404bbd89ef7bc15")
OLD_QUAL=dict(path="implementation/p09/evidence/p09-361-case131-inherited-scope-code-r334.v1.json",
    bytes=4155,sha256="bc5eb9af811fe709cac0faca85646d63ce2b6c4e4f9132e56bbe80e1069ad079")
FAILED_PREFLIGHT=dict(path="implementation/p09/evidence/p09-361-case131-inherited-scope-preflight001.v1.json",
    bytes=41653,sha256="de8e49ffddad7d7a63f54ad106a0d631dffc1dee8c49cf3a8c38e6727bf5e09b")
PREVIOUS_FUNCTIONS=("require","qualify","scoped_validator")
API=PRISTINE=PROOF=None


def require(ok,code):
    if not ok:raise ValueError("INHERITED_NAMESPACE_"+code)


def data_path(index):
    require(type(index) is int and 131<=index<=249,"SUCCESSOR_RANGE")
    return f"implementation/p09/evidence/p09-361-case{index}-inherited-scope-data002.v1.json"


def project_namespaces(parent_raw,family_raw):
    previous,p1=lean.project(parent_raw,NAMESPACE_PINS[0],dict(lean=lean,FunctionType=FunctionType,NS=NS),PREVIOUS_FUNCTIONS)
    env=dict(previous=previous,argparse=argparse,ast=ast,copy=copy,hashlib=hashlib,
        json=json,re=re,sys=sys,FunctionType=FunctionType,NS=NS)
    pristine,p2=lean.project(family_raw,NAMESPACE_PINS[1],env)
    connected,p3=lean.project(family_raw,NAMESPACE_PINS[1],env)
    current=connected.own_inputs.__globals__
    current.update(SELF=SELF,TEST=TEST,FILES=pristine.FILES+(SELF,TEST),QUAL_PATH=QUAL_PATH,
        data_path=data_path,validate_data=validate_data,own_inputs=own_inputs)
    connected=NS(**current)
    return connected,pristine,dict(original_exact_AST_proofs=[p1,p2,p3],
        original_all_v1_functions_and_constants_retained=True,
        full_module_or_CLI_import_executed=False,original_default_modules_mutated=False,
        original_v1_qualification_and_DATA_validation_isolated=True,
        imported_modules_hidden_or_removed=False,helper_ceiling_raised=False)


def bootstrap():
    raw=[]
    for pin in NAMESPACE_PINS:
        base.stable.stable.prior.build.direct_path(c.ROOT/pin["path"],file_required=True)
        with (c.ROOT/pin["path"]).open("rb") as stream:raw.append(stream.read(pin["bytes"]+1))
    return project_namespaces(*raw)


def rebind_namespaces(q):
    raw=[]
    for expected in NAMESPACE_PINS:
        pin,buffer=q._read(expected["path"],parse=True);q._bind(pin["path"],pin)
        a.exact(pin,expected,"CURRENT_RAW_NAMESPACE_SOURCE")
        raw.append(bytes(buffer))
    fresh,original,proof=project_namespaces(*raw)
    # Compiled code (not file data) may be reused just like the original Native
    # definition factory. All exact raw sources are freshly rebound first.
    for name in fresh.__dict__:
        fn=getattr(fresh,name)
        if type(fn) is FunctionType and fn.__code__.co_filename==NAMESPACE_PINS[1]["path"]:
            a.exact(fn.__code__==getattr(API,name).__code__,True,"FRESH_SAME_ORIGINAL_FUNCTION_CODE")
    return fresh,original,proof


def validate_data(row,step):
    require(type(row) is dict and set(row)=={"schema_version","index","before","run","base_step_pin",
        "prior_source_data_pin","original_base_runtime_pin","parent_qualification_pin","lean_qualification_pin",
        "connection_qualification_pin","connection_code_pins","prior_connection_data_pin",
        "prior_connection_qualification_pin","namespace_source_pins","failed_preflight_pin"},"CLOSED_V2_DATA")
    a.fields(row,dict(schema_version="hwpx-agent.p09-fixed-inherited-scope-connection/v2",index=step.index,
        before=step.before,run=1,base_step_pin=step.pin,original_base_runtime_pin=PRISTINE.BASE_PIN,
        parent_qualification_pin=PRISTINE.PARENT_QUAL,lean_qualification_pin=PRISTINE.LEAN_QUAL,
        prior_connection_qualification_pin=OLD_QUAL,namespace_source_pins=list(NAMESPACE_PINS),
        failed_preflight_pin=FAILED_PREFLIGHT if step.index==131 else None),"EXACT_V2_LINEAGE_AND_CURSOR")
    require(set(base.scope.pins(row["connection_code_pins"],2))=={SELF,TEST},"ALL_NEW_V2_CODE")
    require(set(base.scope.pins([row["connection_qualification_pin"]],1))=={QUAL_PATH},"V2_QUAL_PATH")
    require(set(base.scope.pins([row["prior_connection_data_pin"]],1))=={PRISTINE.data_path(step.index)},"OLD_DATA_PATH")
    require(set(base.scope.pins([row["prior_source_data_pin"]],1))=={source.data_path(step.index)},"ORIGINAL_SOURCE_DATA_PATH")
    data_path(step.index)
    return row


def own_inputs(q):
    step=base.CONFIG;require(step is not None,"CONFIG_REQUIRED")
    text=q.text(data_path(step.index));require(0<len(text.encode("utf-8"))<=16384,"BOUNDED_V2_DATA")
    row=validate_data(json.loads(text,object_pairs_hook=base.unique),step)
    fresh,original,_=rebind_namespaces(q)
    original.own_inputs(q)  # Unchanged complete OLD code20/DATA001 predicates.
    a.exact(q.snapshots[original.data_path(step.index)],row["prior_connection_data_pin"],"OLD_DATA_FRESH_UNCHANGED")
    a.exact(q.pin(source.data_path(step.index)),row["prior_source_data_pin"],"SOURCE_DATA_FRESH")
    old=a.read_exact(q,OLD_QUAL)
    a.fields(old,dict(contracts=dict(run=20,errors=0,failures=0,skipped=0),cleanup_confirmed=True),"ORIGINAL20_RETAINED")
    code=a.read_exact(q,row["connection_qualification_pin"])
    a.fields(code,dict(state="PASS_EXACT_NAMESPACED_FAMILY25_AND_ACTUAL130_ORACLE_NOT_RUNTIME131",
        contracts=dict(run=25,errors=0,failures=0,skipped=0),accepted_count_after=124,accepted_count_delta=0,
        original_whole_previous130_oracle_checked=True,body_or_Native_replayed=False,cleanup_confirmed=True),"REAL_NAMESPACE_CODE25")
    a.exact(code["new_code_pins"],row["connection_code_pins"],"TESTED_CURRENT_V2_CODE")
    for pin in row["connection_code_pins"]:a.exact(q.pin(pin["path"]),pin,"CURRENT_V2_CODE")
    a.exact(q.pin(OLD_TEST_PIN["path"]),OLD_TEST_PIN,"ORIGINAL20_TESTS_PIN")
    if row["failed_preflight_pin"] is not None:
        failed=a.read_exact(q,row["failed_preflight_pin"])
        a.fields(failed,dict(state="FAILED_NOT_ACCEPTED",error_code="METADATA_CONNECTION_ORIGINAL_HELPER_BOUND",
            cleanup_confirmed=True,synthetic_connection_contracts_passed=10,
            product_worker_or_Native_frame_executed=False,accepted_count_delta=0,final_fresh_hashes=0),"FAILED001_NEVER_PROMOTED")
    return row


def preflight_projection(raw,leaf):
    old=API.preflight_projection(raw,leaf);code=old.__code__
    prior="-inherited-scope-preflight001.v1.json";new="-inherited-namespace-preflight002.v1.json"
    require(sum(type(x) is str and x==prior for x in code.co_consts)==1,"ONE_NEW_PREFLIGHT002_DESTINATION")
    constants=tuple(new if type(x) is str and x==prior else x for x in code.co_consts)
    fixed=code.replace(co_consts=constants)
    require(fixed.replace(co_consts=code.co_consts)==code,"ALL_ORIGINAL_PREFLIGHT_CODE_RETAINED")
    return FunctionType(fixed,dict(old.__globals__),argdefs=old.__defaults__)


def preflight():
    return FunctionType(API.preflight.__code__,dict(API.preflight.__globals__,preflight_projection=preflight_projection),
        argdefs=API.preflight.__defaults__)()


API,PRISTINE,PROOF=bootstrap()

if __name__=="__main__":
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
        code=str(e) if isinstance(e,ValueError) else "REDACTED_NAMESPACE_CONNECTION_FAILURE"
        print(json.dumps(dict(state="FAILED_NOT_ACCEPTED",error_code=code if re.fullmatch("[A-Z0-9_]{1,256}",code) else "REDACTED_NAMESPACE_CONNECTION_FAILURE")))
        raise SystemExit(2) from None
