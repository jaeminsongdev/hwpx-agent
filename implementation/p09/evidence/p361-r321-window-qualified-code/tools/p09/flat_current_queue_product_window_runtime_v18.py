"""Only157: stricter actual product window, full original Native scope retained.

No accepted product replay,interleaved acquisition/read,scope/rate/deadline
relaxation or default-module mutation. Original full engine and worker code
are reused; only explicit local Native/model/oracle dependencies differ.
"""
import argparse
import ast
import copy
import ctypes
import dis
from ctypes import wintypes as w
from contextlib import contextmanager
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import threading
import time
from types import FunctionType,MappingProxyType,SimpleNamespace as NS
import unittest
import flat_preserved129_lean_connection_v2 as lean

SELF="tools/p09/flat_current_queue_product_window_runtime_v18.py"
TEST="tools/p09/tests/test_flat_current_queue_product_window_runtime_v18.py"
QUAL_PATH="implementation/p09/evidence/p09-361-case157-product-window-whole-controller-code6-r609.v1.json"
QUAL_STATE="PASS_PRODUCT_WINDOW_V18_TERMINAL_PRESSURE_WHOLE_CONTROLLER_CODE6_NOT_PRODUCT"
OLD17_PIN=dict(path="tools/p09/flat_current_queue_native_pressure_runtime_v17.py",bytes=15779,sha256="dea158f8df44080116dffd7a2e5ae8fad081c677e149da35d972b18d826d92a6")
OLD17_TEST_PIN=dict(path="tools/p09/tests/test_flat_current_queue_native_pressure_runtime_v17.py",bytes=6159,sha256="0f92171c106f341a86d286565c85f7f34e6649eb96b23c443db3fbd9a1e2bd45")
NEW_COMPONENT_PINS=[
  {
    "path": "tools/p09/strict_product_window_v1.py",
    "bytes": 4696,
    "sha256": "cd35710cbd11e47cc0a83dd2f28c03772b86267713d52bb8129ed52c670cc701"
  },
  {
    "path": "tools/p09/tests/test_strict_product_window_v1.py",
    "bytes": 5531,
    "sha256": "fd23db3fb9ac61ae61a58c47ee364c599defb463fde98871042efaaa02215cff"
  },
  {
    "path": "tools/p09/strict_product_window_model_v1.py",
    "bytes": 3941,
    "sha256": "91637ab8544f83a5c9c2ca006d8e3ac93bc704aa2460874f2b55f6871626a955"
  },
  {
    "path": "tools/p09/tests/test_strict_product_window_model_v1.py",
    "bytes": 2814,
    "sha256": "64123aacdb690961e2bcaf08028b261ee9fc4f054f755aafa410d342abe3bb88"
  },
  {
    "path": "tools/p09/strict_product_window_connection_v1.py",
    "bytes": 5489,
    "sha256": "f5d6e5c1792464a3699272c62e6175a3607d15f213c6e3444fb2f4a0fe24510c"
  },
  {
    "path": "tools/p09/tests/test_strict_product_window_connection_v1.py",
    "bytes": 5303,
    "sha256": "6fd67d1e3d10496a5dee3fba9ee3a8c045791de1ba73dbddbf6c2b09f7e6362a"
  }
]
NEW_QUAL_PINS=[
  {
    "path": "implementation/p09/evidence/p09-361-case157-strict-window-code19-r601.v1.json",
    "bytes": 1851,
    "sha256": "3c58044f410001751d05421cadffea5903ef7b903116a6f36213605e70df488f"
  },
  {
    "path": "implementation/p09/evidence/p09-361-case157-strict-window-actual-owned-pipe-r606.v1.json",
    "bytes": 2693,
    "sha256": "8a4462607aacab1f7b98020f8aba3adf4f3186905171fdf5dd0c907c2a0806a9"
  },
  {
    "path": "implementation/p09/evidence/p09-361-case157-window-connection-code9-r608.v1.json",
    "bytes": 1328,
    "sha256": "c18e4949bfc7615c76e28546e1433c70a371d32aa45eb88e47ca1dd57e707a58"
  }
]
ACTUAL155_PIN=dict(path="implementation/p09/evidence/p09-361-case155-current-runtime-run001.v1.json",bytes=2437055,
    sha256="1966af42d86a3a1327d974806d5989d2d77d74c14e8a1936ab295a3167ead081")
ACTUAL149_PIN=dict(path="implementation/p09/evidence/p09-361-case155-current-epoch-accept001.v1.json",bytes=458195,
    sha256="613a91514a9a1c350b2a90ae7800ad35d0a1222aff842f2cb6612a326bccd41f")
FAILED_PREFLIGHT_PIN=dict(path="implementation/p09/evidence/p09-361-case156-native-diagnostic-preflight017.v1.json",bytes=107385,
    sha256="1042dc0277f052520dd2ad33876803653e99badfbdf44de04fa02dbbf063d5e4")

def require(ok,code):
    if not ok:raise ValueError("PRODUCT_WINDOW_V18_"+code)

def raw(pin):
    lean.base.stable.stable.prior.build.direct_path(lean.c.ROOT/pin["path"],file_required=True)
    with (lean.c.ROOT/pin["path"]).open("rb") as stream:data=stream.read(pin["bytes"]+1)
    require(len(data)==pin["bytes"] and hashlib.sha256(data).hexdigest()==pin["sha256"],"EXACT_NAMESPACE_BYTES")
    return data

def load_old17():
    tree=ast.parse(raw(OLD17_PIN).decode("utf-8"))
    def selected(n):
        return isinstance(n,(ast.Assign,ast.FunctionDef,ast.ClassDef,ast.For)) or (
            isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Attribute)
            and isinstance(n.value.func.value,ast.Name) and n.value.func.value.id=="_env")
    original=[n for n in tree.body if selected(n)];nodes=copy.deepcopy(original)
    require([ast.dump(n,include_attributes=False) for n in nodes]==[ast.dump(n,include_attributes=False) for n in original],
        "ALL_OLD17_DEFINITIONS_AND_INITIALIZATION")
    env=dict(lean=lean,argparse=argparse,ast=ast,copy=copy,ctypes=ctypes,w=w,contextmanager=contextmanager,
        hashlib=hashlib,json=json,math=math,os=os,Path=Path,re=re,sys=sys,threading=threading,time=time,
        dis=dis,FunctionType=FunctionType,MappingProxyType=MappingProxyType,NS=NS,unittest=unittest,
        __name__="p09_exact_old17_namespace",__file__=OLD17_PIN["path"])
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),OLD17_PIN["path"],"exec"),env)
    return NS(**env)

OLD17=load_old17()
M=OLD17.M
COMPONENT_PINS=OLD17.COMPONENT_PINS+[OLD17_PIN,OLD17_TEST_PIN]+NEW_COMPONENT_PINS
COMPONENT_QUAL_PINS=OLD17.COMPONENT_QUAL_PINS+[
    dict(path=OLD17.QUAL_PATH,bytes=9473,sha256="7488eb12254bb0b6c000c28fd8a81001a270f6dac444045d99934854f132383f")]+NEW_QUAL_PINS

def component(pin,env):
    load=OLD17.OLD16.OLD15.OLD14.OLD12.OLD11.OLD10.OLD9.OLD8.BASE.namespace
    return load(raw(pin),pin,env)

POLICY=OLD17.POLICY
LINK=OLD17.LINK
WINDOW=component(NEW_COMPONENT_PINS[0],dict(math=math,time=time,NS=NS))
MODEL=component(NEW_COMPONENT_PINS[2],dict(ast=ast,copy=copy,NS=NS))
WINDOW_LINK=component(NEW_COMPONENT_PINS[4],dict(math=math,FunctionType=FunctionType,NS=NS,patch=unittest.mock.patch))
_new_model,MODEL_PROOF=MODEL.project(OLD17.NATIVE.model,raw(POLICY.MODEL_PIN),POLICY,M.base.scope)
NATIVE=NS(**{**vars(OLD17.NATIVE),"model":_new_model})
DIRECT=WINDOW_LINK.direct_oracle(OLD17.DIRECT,NATIVE,LINK)
original_candidate=OLD17.original_candidate
NEW_CANDIDATE=OLD17.NEW_CANDIDATE
linked,ORACLE_PROOF=OLD17.OLD16.ORACLE.connect_full(OLD17.OLD16._original_source.validate_candidate,NEW_CANDIDATE,DIRECT)
WINDOW_STATES=[]
ACTUAL156_PIN=dict(path="implementation/p09/evidence/p09-361-case156-current-runtime-run001.v1.json",bytes=2514157,sha256="e5e15b0a4fadc6b402c45d65a20e9bee74f15454750e725acace598342823cf4")
ACTUAL150_PIN=dict(path="implementation/p09/evidence/p09-361-case156-current-epoch-accept001.v1.json",bytes=463784,sha256="bef5e3dbf148a245108f408b761edf02840159032ecd4ae16a5ec125465f934c")
BACKEND=OLD17.BACKEND
CONNECTION=OLD17.CONNECTION
RETRY=OLD17.RETRY
FORMAT_STATES=[]
ATTEMPT_STATES=[]

def validator(source,ctx,flat=True):
    fn,proof=OLD17.validator(source,ctx,flat)
    if ctx.INDEX<=156:return fn,proof
    require(ctx.INDEX==157,"ONLY_QUALIFIED_ORDINARY157")
    fn=LINK.projector(fn,DIRECT,ctx.INDEX)
    if ctx.INDEX==157:
        fn.__globals__["CONTROLLERS"]=tuple(dict.fromkeys(fn.__globals__["CONTROLLERS"]+(SELF,TEST)
            +tuple(p["path"] for p in NEW_COMPONENT_PINS)))
    return fn,dict(proof,explicit_strict_window_context=ctx.INDEX==157)

def context(step):
    return NS(**{**vars(OLD17.context(step)),"SELF":SELF,"TEST":TEST})

def validate_candidate(q,row,listing,oldbody,fresh,ctx,flat=True):
    if ctx.INDEX<=156:return OLD17.validate_candidate(q,row,listing,oldbody,fresh,ctx,flat)
    fn=LINK.clone(linked,validator=validator)
    result,proof=fn(q,row,listing,oldbody,fresh,ctx,flat)
    proof.update(OLD17.OLD16.metadata_identity_evidence(row))
    proof.update(LINK.evidence(row,M.a))
    proof.update(WINDOW_LINK.check_evidence(row,M.a))
    return result,proof

_prepare_projection=LINK.clone(OLD17.CURRENT_SOURCE.prepare_projection,
    root_path=RETRY.root_path,validate_candidate=validate_candidate)
_source_prepare=LINK.clone(OLD17.CURRENT_SOURCE.prepare,prepare_projection=_prepare_projection)
CURRENT_SOURCE=NS(**{**vars(OLD17.CURRENT_SOURCE),"validate_candidate":validate_candidate,
    "prepare_projection":_prepare_projection,"prepare":_source_prepare})

def data_path(index):
    require(type(index) is int and index==157,"NO_SUCCESSFUL_REPLAY")
    return f"implementation/p09/evidence/p09-361-case{index}-product-window-data018.v1.json"

def validate_data(row,step):
    require(type(row) is dict and set(row)=={"schema_version","index","before","qualification_run",
        "physical_product_run","base_step_pin","prior_v17_data_pin","qualification_pin","controller_code_pins",
        "component_pins","component_qualification_pins","actual155_pin","actual149_pin","failed_preflight_pin","actual156_pin","actual150_pin"},"CLOSED_DATA018")
    M.a.fields(row,dict(schema_version="hwpx-agent.p09-product-window-controller/v18",index=step.index,
        before=step.before,qualification_run=1,physical_product_run=1,base_step_pin=step.pin,
        component_pins=COMPONENT_PINS,component_qualification_pins=COMPONENT_QUAL_PINS,
        actual155_pin=ACTUAL155_PIN,actual149_pin=ACTUAL149_PIN,failed_preflight_pin=FAILED_PREFLIGHT_PIN,actual156_pin=ACTUAL156_PIN,actual150_pin=ACTUAL150_PIN),"EXACT_NEW_CONTEXT")
    M.a.exact(row["prior_v17_data_pin"]["path"],OLD17.data_path(step.index),"ORIGINAL_DATA017_PATH")
    M.a.exact(row["qualification_pin"]["path"],QUAL_PATH,"CURRENT_CODE6_PATH")
    require(set(M.base.scope.pins(row["controller_code_pins"],2))=={SELF,TEST},"CONTROLLER_CODE2")
    data_path(step.index);return row

def own_inputs(q):
    OLD17.own_inputs(q)
    row=validate_data(json.loads(q.text(data_path(M.base.CONFIG.index)),object_pairs_hook=M.base.unique),M.base.CONFIG)
    M.a.exact(q.snapshots[OLD17.data_path(M.base.CONFIG.index)],row["prior_v17_data_pin"],"PRIOR_DATA016_BYTES")
    for pin in COMPONENT_QUAL_PINS:
        qual=M.a.read_exact(q,pin)
        require(qual["state"].startswith("PASS_") and qual["cleanup_confirmed"] is True,"QUALIFIED_COMPONENT_ONLY")
    qual=M.a.read_exact(q,row["qualification_pin"])
    M.a.fields(qual,dict(state=QUAL_STATE,contracts=dict(run=6,errors=0,failures=0,skipped=0),
        cleanup_confirmed=True,Native_product_or_acceptance_executed=False),"CODE6_NOT_PRODUCT")
    M.a.exact(qual["new_code_pins"],row["controller_code_pins"],"EXACT_CURRENT_CONTROLLER")
    M.a.exact(qual["component_pins"],COMPONENT_PINS,"ALL_COMPONENTS")
    for pin in row["controller_code_pins"]+COMPONENT_PINS:M.a.exact(q.pin(pin["path"]),pin,"FRESH_NAMESPACE_SOURCES")
    ar=M.a.read_exact(q,ACTUAL149_PIN)
    M.a.fields(ar,dict(accepted_count_after=149,next_runtime_index=156,accepted_test_indices=[155],
        resource_cleanup_confirmed=True,P09_gate="OPEN"),"ACTUAL149_CUTOVER")
    M.a.exact(ar["runtime_candidate_pin"],ACTUAL155_PIN,"SAME_ACCEPTED155")
    failed=M.a.read_exact(q,FAILED_PREFLIGHT_PIN)
    M.a.fields(failed,dict(state="FAILED_NOT_ACCEPTED",error_code="HELD_READ_VIEW_WHOLE_CLOSURE_INSIDE_UNCHANGED600",
        cleanup_confirmed=True,product_worker_or_Native_frame_executed=False),"PRESERVED_FAILED_PREFLIGHT")
    ar150=M.a.read_exact(q,ACTUAL150_PIN)
    M.a.fields(ar150,dict(accepted_count_after=150,next_runtime_index=157,resource_cleanup_confirmed=True),"ACTUAL150_CUTOVER")
    M.a.exact(ar150["runtime_candidate_pin"],ACTUAL156_PIN,"SAME_ACCEPTED156")
    return row

def template():
    engine,proof=OLD17.template()
    engine.run_owned.__globals__.update(SELF=SELF,TEST=TEST,native=NATIVE,runtime_budget=DIRECT.runtime_budget)
    engine.worker.__globals__.update(SELF=SELF,TEST=TEST,native=NATIVE)
    FORMAT_STATES.append(OLD17.FORMAT_STATES[-1]);ATTEMPT_STATES.append(OLD17.ATTEMPT_STATES[-1])
    engine,state=WINDOW_LINK.connect_engine(engine,WINDOW);WINDOW_STATES.append(state)
    return engine,dict(proof,terminal_native_pressure_and_complete_cost_locally_connected=True,
        original_engine_and_worker_code_unchanged=True,no_additional_physical_adapter=True)

def previous_function(index):
    require(type(index) is int and 147<=index<=249,"EXACT_PREDECESSOR")
    if index<=156:return OLD17.previous_function(index)
    fn=M.V3.OLD.API.previous_validation
    return LINK.clone(fn,source=CURRENT_SOURCE,validator=validator,context=context)

def previous_validation(q,row,listing,oldbody,fresh,oldctx,flat=True):
    if oldctx.INDEX<=156:return OLD17.previous_validation(q,row,listing,oldbody,fresh,oldctx,flat)
    return previous_function(oldctx.INDEX)(q,row,listing,oldbody,fresh,oldctx,flat)

def binding(q):
    pin,data=q._read(M.V3.OLD.API.BASE_PIN["path"],parse=True);q._bind(pin["path"],pin)
    M.a.exact(pin,M.V3.OLD.API.BASE_PIN,"ORIGINAL_BINDING_SOURCE")
    fn,_=M.V3.OLD.API.binding_projection(bytes(data),replacement=previous_validation)
    return fn(q)

def native_scope(q,row):
    p=q.snapshots[data_path(M.base.CONFIG.index)];value=validate_data(M.a.read_exact(q,p),M.base.CONFIG)
    expected=M.base.scope.pins(row["source_freeze"])
    for pin in [p,value["qualification_pin"],ACTUAL155_PIN,ACTUAL149_PIN,FAILED_PREFLIGHT_PIN,ACTUAL156_PIN,ACTUAL150_PIN]+\
        value["controller_code_pins"]+COMPONENT_PINS+COMPONENT_QUAL_PINS:
        M.a.exact(expected.get(pin["path"]),pin,"FULL_NEW_NATIVE_SOURCE_SCOPE")
    return expected

_family=OLD17._full_prepare.__globals__;_env=dict(_family)
for _name,_fn in tuple(_env.items()):
    if type(_fn) is FunctionType and _fn.__globals__ is _family:
        _env[_name]=FunctionType(_fn.__code__,_env,argdefs=_fn.__defaults__,closure=_fn.__closure__)
_env.update(SELF=SELF,TEST=TEST,FILES=(SELF,TEST),QUAL_PATH=QUAL_PATH,source=CURRENT_SOURCE,
    own_inputs=own_inputs,validator=validator,context=context,template=template,binding=binding,
    previous_validation=previous_validation,data_path=M.data_path,validate_data=M.validate_data)
API=NS(**_env)
_full_prepare=API.prepare

def prepare(q,p):
    result=_full_prepare(q,p);native_scope(q,result[0]);RETRY.validate_actual(result[0],M.base.CONFIG,p)
    return result
API.prepare=prepare
API.original_run_owned=API.run_owned

def worker(task):
    data_path(M.base.CONFIG.index);M.a.exact(task,RETRY.task(M.base.CONFIG.index),"EXACT_PHYSICAL_WORKER")
    engine,_=template();return engine.worker(task)
API.worker=worker

def run_owned(run):
    index=M.base.CONFIG.index;logical=RETRY.public_run(index,run);data_path(index)
    require(not (M.c.ROOT/RETRY.root_path(M.base.CONFIG)).exists(),"FRESH_PHYSICAL_RECEIPT")
    execute,state=CONNECTION.connect_run(API.original_run_owned,BACKEND)
    before=len(FORMAT_STATES);ab=len(ATTEMPT_STATES);code=execute(logical)
    observed=ATTEMPT_STATES[ab:]
    require(len(observed)==1 and observed[0].actual_engine_calls==1 and observed[0].physical_product_run==run,"ONE_ENGINE_CALL")
    if code==0:
        formatted=FORMAT_STATES[before:]
        require(sum(x.actual_capture_count for x in formatted)==sum(x.actual_dump_calls for x in formatted)==1,"ONE_COMPACT_DUMP")
    require(state["actual_local_bindings"]==1,"ONE_NATIVE_DIAGNOSTIC_CONNECTION")
    require(len(WINDOW_STATES[-1].states)==1,"ONE_ACTUAL_WINDOW_BINDING")
    if code==0:require(WINDOW_STATES[-1].states[0].completed is not None,"COMPLETE_ACTUAL_WINDOW_BEFORE_PASS")
    return code

def preflight_data(q):
    row=own_inputs(q);require("run" not in row,"IMMUTABLE_QUALIFICATION_ALIAS")
    return dict(row,run=row["qualification_run"])

def preflight_projection(data,leaf):
    fn=OLD17.preflight_projection(data,leaf);code=fn.__code__
    old="-native-pressure-preflight018.v1.json";new="-product-window-preflight019.v1.json"
    require(sum(type(x) is str and x==old for x in code.co_consts)==1,"ONE_FRESH_PREFLIGHT_DESTINATION")
    revised=code.replace(co_consts=tuple(new if type(x) is str and x==old else x for x in code.co_consts))
    require(revised.replace(co_consts=code.co_consts)==code,"ORIGINAL_FULL_PREFLIGHT10_CODE")
    return FunctionType(revised,dict(fn.__globals__,SELF=SELF,TEST=TEST,template=template,
        binding_attempt=API.binding_attempt,connection_data=preflight_data,own_inputs=own_inputs,data_path=data_path,
        base=NS(**{**vars(fn.__globals__["base"]),"native":NATIVE,"stable":NS(**{**vars(fn.__globals__["base"].stable),"runtime_budget":DIRECT.runtime_budget})})),
        argdefs=fn.__defaults__,closure=fn.__closure__)

def preflight():
    fn=OLD17.preflight
    return LINK.clone(fn,preflight_projection=preflight_projection)()

if __name__=="__main__":
    try:
        if len(sys.argv)==4 and sys.argv[1:3]==["--owned-worker","--task"]:
            M.base.configure(M.base.task_index(sys.argv[3]));raise SystemExit(worker(sys.argv[3]))
        p=argparse.ArgumentParser();p.add_argument("--case",type=int,required=True);p.add_argument("--run",type=int);p.add_argument("--preflight",action="store_true")
        args=p.parse_args();data_path(args.case);M.base.configure(args.case)
        require((args.run is not None)!=args.preflight,"ONE_MODE")
        raise SystemExit(preflight() if args.preflight else run_owned(args.run))
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        code=str(error) if isinstance(error,ValueError) and re.fullmatch("[A-Z0-9_]{1,256}",str(error)) else "REDACTED_V18_FAILURE"
        print(json.dumps(dict(state="FAILED_NOT_ACCEPTED",error_code=code)));raise SystemExit(2) from None
