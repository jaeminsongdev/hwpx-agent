"""156+ whole CLI with qualified terminal Native pressure,old155 preserved.

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

SELF="tools/p09/flat_current_queue_native_pressure_runtime_v17.py"
TEST="tools/p09/tests/test_flat_current_queue_native_pressure_runtime_v17.py"
QUAL_PATH="implementation/p09/evidence/p09-361-case156-native-pressure-whole-controller-code6-r568.v1.json"
QUAL_STATE="PASS_NATIVE_V17_TERMINAL_PRESSURE_WHOLE_CONTROLLER_CODE6_NOT_PRODUCT"
OLD16_PIN=dict(path="tools/p09/flat_current_queue_native_diagnostic_runtime_v16.py",bytes=22268,
    sha256="22c289db689c9e6909f61db50a4e828df32c012bc938fbd338ebd29f57257116")
OLD16_TEST_PIN=dict(path="tools/p09/tests/test_flat_current_queue_native_diagnostic_runtime_v16.py",bytes=6335,
    sha256="92f4256a43001fceac1203eece74a8350d4479413487a30a942ded9a0ae3ced9")
NEW_COMPONENT_PINS=[
    dict(path="tools/p09/native_pressure_failfast_v1.py",bytes=10185,sha256="661c4a690947464ee588a8edd7b12ca8d0d0f4d91a4ea6e1c53aa51151b3fa03"),
    dict(path="tools/p09/tests/test_native_pressure_failfast_v1.py",bytes=11219,sha256="f0cbcf517e98cab2249df9b1700afa5a50f7ade65b55335ea24071e8d2d8bbcb"),
    dict(path="tools/p09/native_pressure_full_connection_v1.py",bytes=10169,sha256="72054929bf952192bd5720df954ef5becbc7ab1c8f7650eaff44bc434756b1f8"),
    dict(path="tools/p09/tests/test_native_pressure_full_connection_v1.py",bytes=7848,sha256="71cc7c549a1016110f3bb1e7f20398b54f872c057a2fa2e918127aeeb57b0675")]
NEW_QUAL_PINS=[
    dict(path="implementation/p09/evidence/p09-361-case156-native-pressure-failfast-explicit-checkpoint-code16-r563.v1.json",bytes=1794,sha256="da95e10c461008b434ac6546bad3151061493f4b066245699b225ae0ab22f59d"),
    dict(path="implementation/p09/evidence/p09-361-case156-native-pressure-failfast-explicit-focused3-r564.v1.json",bytes=18756,sha256="041fc07b5a76f973dec33cc5d33a42baba859b9a1d6381f9c99738061fb70a5c"),
    dict(path="implementation/p09/evidence/p09-361-case156-full-native-pressure-connection-code10-r567.v1.json",bytes=1050,sha256="26f78bbb7df0b7b1e6cc7eea26731382065c20951236b38a1193ad295652b596")]
ACTUAL155_PIN=dict(path="implementation/p09/evidence/p09-361-case155-current-runtime-run001.v1.json",bytes=2437055,
    sha256="1966af42d86a3a1327d974806d5989d2d77d74c14e8a1936ab295a3167ead081")
ACTUAL149_PIN=dict(path="implementation/p09/evidence/p09-361-case155-current-epoch-accept001.v1.json",bytes=458195,
    sha256="613a91514a9a1c350b2a90ae7800ad35d0a1222aff842f2cb6612a326bccd41f")
FAILED_PREFLIGHT_PIN=dict(path="implementation/p09/evidence/p09-361-case156-native-diagnostic-preflight017.v1.json",bytes=107385,
    sha256="1042dc0277f052520dd2ad33876803653e99badfbdf44de04fa02dbbf063d5e4")

def require(ok,code):
    if not ok:raise ValueError("NATIVE_V17_"+code)

def raw(pin):
    lean.base.stable.stable.prior.build.direct_path(lean.c.ROOT/pin["path"],file_required=True)
    with (lean.c.ROOT/pin["path"]).open("rb") as stream:data=stream.read(pin["bytes"]+1)
    require(len(data)==pin["bytes"] and hashlib.sha256(data).hexdigest()==pin["sha256"],"EXACT_NAMESPACE_BYTES")
    return data

def load_old16():
    tree=ast.parse(raw(OLD16_PIN).decode("utf-8"))
    def selected(n):
        return isinstance(n,(ast.Assign,ast.FunctionDef,ast.ClassDef,ast.For)) or (
            isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Attribute)
            and isinstance(n.value.func.value,ast.Name) and n.value.func.value.id=="_env")
    original=[n for n in tree.body if selected(n)];nodes=copy.deepcopy(original)
    require([ast.dump(n,include_attributes=False) for n in nodes]==[ast.dump(n,include_attributes=False) for n in original],
        "ALL_OLD16_DEFINITIONS_AND_INITIALIZATION")
    env=dict(lean=lean,argparse=argparse,ast=ast,copy=copy,ctypes=ctypes,w=w,contextmanager=contextmanager,
        hashlib=hashlib,json=json,math=math,os=os,Path=Path,re=re,sys=sys,threading=threading,time=time,
        dis=dis,FunctionType=FunctionType,MappingProxyType=MappingProxyType,NS=NS,unittest=unittest,
        __name__="p09_exact_old16_namespace",__file__=OLD16_PIN["path"])
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),OLD16_PIN["path"],"exec"),env)
    return NS(**env)

OLD16=load_old16()
M=OLD16.M
COMPONENT_PINS=OLD16.COMPONENT_PINS+[OLD16_PIN,OLD16_TEST_PIN]+NEW_COMPONENT_PINS
COMPONENT_QUAL_PINS=OLD16.COMPONENT_QUAL_PINS+[
    dict(path=OLD16.QUAL_PATH,bytes=10427,sha256="5ff3d034ff43e8db9c3a382d2792b157425e512211cde973e57adb1b24f8d4d8")]+NEW_QUAL_PINS

def component(pin,env):
    load=OLD16.OLD15.OLD14.OLD12.OLD11.OLD10.OLD9.OLD8.BASE.namespace
    return load(raw(pin),pin,env)

POLICY=component(NEW_COMPONENT_PINS[0],dict(ast=ast,copy=copy,hashlib=hashlib,FunctionType=FunctionType,NS=NS))
LINK=component(NEW_COMPONENT_PINS[2],dict(ast=ast,copy=copy,FunctionType=FunctionType,NS=NS))
NATIVE=LINK.native_namespace(OLD16.NATIVE,POLICY,raw,M.base.scope)
DIRECT=LINK.direct_oracle(M.V3.ORACLE,NATIVE)
original_candidate=M.source.prior.accepted.original.candidate
new_additional=LINK.additional_checker(original_candidate.original.additional_observer_evidence,
    raw(original_candidate.ACCEPTOR_PIN))
NEW_CANDIDATE=LINK.candidate_namespace(original_candidate,new_additional)
linked,ORACLE_PROOF=OLD16.ORACLE.connect_full(OLD16._original_source.validate_candidate,NEW_CANDIDATE,DIRECT)
BACKEND=OLD16.BACKEND
CONNECTION=OLD16.CONNECTION
RETRY=OLD16.RETRY
FORMAT_STATES=[]
ATTEMPT_STATES=[]

def validator(source,ctx,flat=True):
    fn,proof=OLD16.validator(source,ctx,flat)
    fn=LINK.projector(fn,DIRECT,ctx.INDEX)
    if ctx.INDEX>=156:
        fn.__globals__["CONTROLLERS"]=tuple(dict.fromkeys(fn.__globals__["CONTROLLERS"]+(SELF,TEST)
            +tuple(p["path"] for p in NEW_COMPONENT_PINS)))
    return fn,dict(proof,explicit_terminal_pressure_context=ctx.INDEX>=156)

def context(step):
    return NS(**{**vars(OLD16.context(step)),"SELF":SELF,"TEST":TEST})

def validate_candidate(q,row,listing,oldbody,fresh,ctx,flat=True):
    fn=LINK.clone(linked,validator=validator)
    result,proof=fn(q,row,listing,oldbody,fresh,ctx,flat)
    proof.update(OLD16.metadata_identity_evidence(row))
    proof.update(LINK.evidence(row,M.a))
    return result,proof

_prepare_projection=LINK.clone(OLD16.CURRENT_SOURCE.prepare_projection,
    root_path=RETRY.root_path,validate_candidate=validate_candidate)
_source_prepare=LINK.clone(OLD16.CURRENT_SOURCE.prepare,prepare_projection=_prepare_projection)
CURRENT_SOURCE=NS(**{**vars(OLD16.CURRENT_SOURCE),"validate_candidate":validate_candidate,
    "prepare_projection":_prepare_projection,"prepare":_source_prepare})

def data_path(index):
    require(type(index) is int and 156<=index<=249,"NO_SUCCESSFUL_REPLAY")
    return f"implementation/p09/evidence/p09-361-case{index}-native-pressure-data017.v1.json"

def validate_data(row,step):
    require(type(row) is dict and set(row)=={"schema_version","index","before","qualification_run",
        "physical_product_run","base_step_pin","prior_v16_data_pin","qualification_pin","controller_code_pins",
        "component_pins","component_qualification_pins","actual155_pin","actual149_pin","failed_preflight_pin"},"CLOSED_DATA017")
    M.a.fields(row,dict(schema_version="hwpx-agent.p09-native-pressure-controller/v17",index=step.index,
        before=step.before,qualification_run=1,physical_product_run=1,base_step_pin=step.pin,
        component_pins=COMPONENT_PINS,component_qualification_pins=COMPONENT_QUAL_PINS,
        actual155_pin=ACTUAL155_PIN,actual149_pin=ACTUAL149_PIN,failed_preflight_pin=FAILED_PREFLIGHT_PIN),"EXACT_NEW_CONTEXT")
    M.a.exact(row["prior_v16_data_pin"]["path"],OLD16.data_path(step.index),"ORIGINAL_DATA016_PATH")
    M.a.exact(row["qualification_pin"]["path"],QUAL_PATH,"CURRENT_CODE6_PATH")
    require(set(M.base.scope.pins(row["controller_code_pins"],2))=={SELF,TEST},"CONTROLLER_CODE2")
    data_path(step.index);return row

def own_inputs(q):
    OLD16.own_inputs(q)
    row=validate_data(json.loads(q.text(data_path(M.base.CONFIG.index)),object_pairs_hook=M.base.unique),M.base.CONFIG)
    M.a.exact(q.snapshots[OLD16.data_path(M.base.CONFIG.index)],row["prior_v16_data_pin"],"PRIOR_DATA016_BYTES")
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
    return row

def template():
    engine,proof=OLD16.template()
    engine.run_owned.__globals__.update(SELF=SELF,TEST=TEST,native=NATIVE,runtime_budget=DIRECT.runtime_budget)
    engine.worker.__globals__.update(SELF=SELF,TEST=TEST,native=NATIVE)
    FORMAT_STATES.append(OLD16.FORMAT_STATES[-1]);ATTEMPT_STATES.append(OLD16.ATTEMPT_STATES[-1])
    return engine,dict(proof,terminal_native_pressure_and_complete_cost_locally_connected=True,
        original_engine_and_worker_code_unchanged=True,no_additional_physical_adapter=True)

def previous_function(index):
    require(type(index) is int and 147<=index<=249,"EXACT_PREDECESSOR")
    if index<=155:return OLD16.previous_function(index)
    fn=M.V3.OLD.API.previous_validation
    return LINK.clone(fn,source=CURRENT_SOURCE,validator=validator,context=context)

def previous_validation(q,row,listing,oldbody,fresh,oldctx,flat=True):
    if oldctx.INDEX<=155:return OLD16.previous_validation(q,row,listing,oldbody,fresh,oldctx,flat)
    return previous_function(oldctx.INDEX)(q,row,listing,oldbody,fresh,oldctx,flat)

def binding(q):
    pin,data=q._read(M.V3.OLD.API.BASE_PIN["path"],parse=True);q._bind(pin["path"],pin)
    M.a.exact(pin,M.V3.OLD.API.BASE_PIN,"ORIGINAL_BINDING_SOURCE")
    fn,_=M.V3.OLD.API.binding_projection(bytes(data),replacement=previous_validation)
    return fn(q)

def native_scope(q,row):
    p=q.snapshots[data_path(M.base.CONFIG.index)];value=validate_data(M.a.read_exact(q,p),M.base.CONFIG)
    expected=M.base.scope.pins(row["source_freeze"])
    for pin in [p,value["qualification_pin"],ACTUAL155_PIN,ACTUAL149_PIN,FAILED_PREFLIGHT_PIN]+\
        value["controller_code_pins"]+COMPONENT_PINS+COMPONENT_QUAL_PINS:
        M.a.exact(expected.get(pin["path"]),pin,"FULL_NEW_NATIVE_SOURCE_SCOPE")
    return expected

_family=OLD16._full_prepare.__globals__;_env=dict(_family)
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
    return code

def preflight_data(q):
    row=own_inputs(q);require("run" not in row,"IMMUTABLE_QUALIFICATION_ALIAS")
    return dict(row,run=row["qualification_run"])

def preflight_projection(data,leaf):
    fn=OLD16.preflight_projection(data,leaf);code=fn.__code__
    old="-native-diagnostic-preflight016.v1.json";new="-native-pressure-preflight018.v1.json"
    require(sum(type(x) is str and x==old for x in code.co_consts)==1,"ONE_FRESH_PREFLIGHT_DESTINATION")
    revised=code.replace(co_consts=tuple(new if type(x) is str and x==old else x for x in code.co_consts))
    require(revised.replace(co_consts=code.co_consts)==code,"ORIGINAL_FULL_PREFLIGHT10_CODE")
    return FunctionType(revised,dict(fn.__globals__,SELF=SELF,TEST=TEST,template=template,
        binding_attempt=API.binding_attempt,connection_data=preflight_data,own_inputs=own_inputs,data_path=data_path,
        base=NS(**{**vars(fn.__globals__["base"]),"native":NATIVE,"stable":NS(**{**vars(fn.__globals__["base"].stable),"runtime_budget":DIRECT.runtime_budget})})),
        argdefs=fn.__defaults__,closure=fn.__closure__)

def preflight():
    fn=OLD16.preflight
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
        code=str(error) if isinstance(error,ValueError) and re.fullmatch("[A-Z0-9_]{1,256}",str(error)) else "REDACTED_V17_FAILURE"
        print(json.dumps(dict(state="FAILED_NOT_ACCEPTED",error_code=code)));raise SystemExit(2) from None
