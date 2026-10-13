"""NativeV4 successor with one reviewed physical153/run002 attempt.
Old152 actual V12/V3 validation context remains exactly historical.
All original full source/product/resource/byte/cleanup predicates remain.
Qualification DATA run=1 and physical product run=2 are explicitly distinct.
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


SELF="tools/p09/flat_current_queue_native_diagnostic_runtime_v13.py"
TEST="tools/p09/tests/test_flat_current_queue_native_diagnostic_runtime_v13.py"
QUAL_PATH="implementation/p09/evidence/p09-361-case153-native4-retry-controller-code6-r521.v1.json"
OLD12_PIN=dict(path="tools/p09/flat_current_queue_native_diagnostic_runtime_v12.py",bytes=12994,
 sha256="d7aa721cc2b24da2a81508a24056d599548668bd9cc2477952907c5e617d9412")
OLD12_TEST_PIN=dict(path="tools/p09/tests/test_flat_current_queue_native_diagnostic_runtime_v12.py",bytes=5140,
 sha256="aeba585d0a55b96523e50dc7c737bc94233fd480c4f175d586c2092dd5332ae9")
COMPONENT_PINS=[{"path":"tools/p09/native_process_cpu_attribution_v4.py","bytes":2309,"sha256":"a2007fb8fcd5c3790fd79c036aa00bffb37bbee4e883552d8784fa822ab285b9"},{"path":"tools/p09/tests/test_native_process_cpu_attribution_v4.py","bytes":3472,"sha256":"3ceeacfe7cacc120fce254b1463ba88a620c1971fe91983b1f896cc080520706"},{"path":"tools/p09/native_diagnostic_connection_v4.py","bytes":4194,"sha256":"53dc3615f5fe340961e44faecb65a915d17497ea32169ff7efb15607f14abf45"},{"path":"tools/p09/tests/test_native_diagnostic_connection_v4.py","bytes":4093,"sha256":"1aa758dfdf33d8e02196b0a380b05fce2bcde4e4d9bb6a6c2d747d8e5909b91b"},{"path":"tools/p09/native_diagnostic_oracle_connection_v3.py","bytes":2508,"sha256":"104d8b8d83205f5370657e293a43307684e76d7735ba788df13befc3efd7d106"},{"path":"tools/p09/tests/test_native_diagnostic_oracle_connection_v3.py","bytes":2847,"sha256":"1a38821c4cd4436f2d0ad6e604171190435b895bde4549e52b45122020f30376"},{"path":"tools/p09/reviewed_runtime_attempt_v1.py","bytes":4634,"sha256":"3818faa42ff155a44a35fa83514407d712a29166c242b0975a290e9272f5a8e7"},{"path":"tools/p09/tests/test_reviewed_runtime_attempt_v1.py","bytes":5031,"sha256":"91289367797a2f6760b98097721b4344c757cecf87668af5f4fef77786c13b3c"}]
COMPONENT_QUAL_PINS=[{"path":"implementation/p09/evidence/p09-361-case153-native4-warning-suppression-code6-r513.v1.json","bytes":3222,"sha256":"f1d11ad25451dfbc330dfc62d69a06860ec9db8f0804848970e0a6c49c51a599"},{"path":"implementation/p09/evidence/p09-361-case153-native4-connection-schema-code6-r516.v1.json","bytes":3259,"sha256":"d79f56467cea47ee1ce8fb5b883b2160042ab0cbcb0618639be7c6248735d968"},{"path":"implementation/p09/evidence/p09-361-case153-native4-version-oracle-code6-r517.v1.json","bytes":3265,"sha256":"cb445d6a048a190c21a789c2c58615676fbed43088cc29d67c82b4d0d0b2fa7f"},{"path":"implementation/p09/evidence/p09-361-case153-native4-actual-local-observer-r518.v1.json","bytes":6849,"sha256":"56cd2a0651f1787fc8edcb7971c2c92b31becc286639a0e005ac8712b6d5c59f"},{"path":"implementation/p09/evidence/p09-361-case153-reviewed-retry-code6-r520.v1.json","bytes":3502,"sha256":"99d561943c24d0e636cdad1d7474361ab7d906dd3dd028f1408115b00ca8fb1b"}]
ACTUAL152_PIN=dict(path="implementation/p09/evidence/p09-361-case152-current-runtime-run001.v1.json",bytes=2374068,
 sha256="31b466f04ff5ce7f6af964ac6f218bef60012502f9c4449bb84b245c01892499")
ACTUAL146_PIN=dict(path="implementation/p09/evidence/p09-361-case152-current-epoch-accept001.v1.json",bytes=430831,
 sha256="9f69f67c464cd78c85db1732109997683b4e2b2d203a0ac290e66b4dceacc29e")
QUAL_STATE="PASS_NATIVE_V13_FULL_WARNING_SUPPRESSION_RETRY_CONTROLLER_CODE6_NOT_PRODUCT"

def require(ok,code):
    if not ok:raise ValueError("NATIVE_V13_"+code)

def raw(pin):
    lean.base.stable.stable.prior.build.direct_path(lean.c.ROOT/pin["path"],file_required=True)
    with (lean.c.ROOT/pin["path"]).open("rb") as stream:data=stream.read(pin["bytes"]+1)
    require(len(data)==pin["bytes"] and hashlib.sha256(data).hexdigest()==pin["sha256"],"EXACT_NAMESPACE_BYTES")
    return data


def load_old12():
    source=raw(OLD12_PIN);tree=ast.parse(source.decode("utf-8"))
    def selected(n):
        return isinstance(n,(ast.Assign,ast.FunctionDef,ast.ClassDef,ast.For)) or (
         isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Attribute)
         and isinstance(n.value.func.value,ast.Name) and n.value.func.value.id=="_env")
    originals=[n for n in tree.body if selected(n)];nodes=copy.deepcopy(originals)
    require([ast.dump(n,include_attributes=False) for n in nodes]==
            [ast.dump(n,include_attributes=False) for n in originals],"ALL_OLD_DEFINITIONS_AND_INITIALIZATION")
    env=dict(lean=lean,argparse=argparse,ast=ast,copy=copy,ctypes=ctypes,w=w,contextmanager=contextmanager,
     hashlib=hashlib,json=json,math=math,os=os,Path=Path,re=re,sys=sys,threading=threading,time=time,
     dis=dis,FunctionType=FunctionType,MappingProxyType=MappingProxyType,NS=NS,unittest=unittest,
     __name__="p09_exact_old12_namespace",__file__=OLD12_PIN["path"])
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),OLD12_PIN["path"],"exec"),env)
    return NS(**env)



OLD12=load_old12()
M=OLD12.M
def component(name,env):
    p=next(p for p in COMPONENT_PINS if p["path"].endswith("/"+name))
    return OLD12.OLD11.OLD10.OLD9.OLD8.BASE.namespace(raw(p),p,env)
RETRY=component("reviewed_runtime_attempt_v1.py",dict(FunctionType=FunctionType,NS=NS))
BACKEND=component("native_process_cpu_attribution_v4.py",dict(math=math,threading=threading,prior=OLD12.BACKEND))
RAW_CONNECTION=component("native_diagnostic_connection_v4.py",
 dict(math=math,FunctionType=FunctionType,prior=OLD12.OLD11.OLD10.CONNECTION,backend=BACKEND))
_scratch_connection=OLD12.OLD11.SCRATCH_CONNECTION.diagnostic(RAW_CONNECTION)
CONNECTION=NS(**{**vars(_scratch_connection),
 "validate_historical_v3":OLD12.CONNECTION.validate,
 "validate_historical_v2":OLD12.OLD11.OLD10.CONNECTION.validate_historical_v2})
ORACLE=component("native_diagnostic_oracle_connection_v3.py",
 dict(FunctionType=FunctionType,NS=NS,prior=OLD12.ORACLE,diagnostic=CONNECTION))
linked,ORACLE_PROOF=ORACLE.connect_full(OLD12.CURRENT_SOURCE.validate_candidate,
 M.source.prior.accepted.original.candidate,M.V3.ORACLE)
NATIVE=OLD12.NATIVE
NATIVE_PROOF=OLD12.NATIVE_PROOF
COMPACT=OLD12.COMPACT
FORMAT_STATES=[]
ATTEMPT_STATES=[]
_original_source=OLD12.CURRENT_SOURCE
_prepare_projection=FunctionType(_original_source.prepare_projection.__code__,
 dict(_original_source.prepare_projection.__globals__,root_path=RETRY.root_path),
 argdefs=_original_source.prepare_projection.__defaults__,closure=_original_source.prepare_projection.__closure__)
_source_prepare=FunctionType(_original_source.prepare.__code__,
 dict(_original_source.prepare.__globals__,prepare_projection=_prepare_projection),
 argdefs=_original_source.prepare.__defaults__,closure=_original_source.prepare.__closure__)
CURRENT_SOURCE=NS(**{**vars(_original_source),"validate_candidate":linked,
 "root_path":RETRY.root_path,"prepare_projection":_prepare_projection,"prepare":_source_prepare})

def data_path(index):
    RETRY.physical_run(index)
    return f"implementation/p09/evidence/p09-361-case{index}-native-diagnostic-data013.v1.json"

def validate_data(row,step):
    require(type(row) is dict and set(row)=={"schema_version","index","before","qualification_run",
     "physical_product_run","base_step_pin","prior_v12_data_pin","qualification_pin","controller_code_pins",
     "component_pins","component_qualification_pins","actual152_pin","actual146_pin","reviewed_failure_pins"},
     "CLOSED_DATA013")
    M.a.fields(row,dict(schema_version="hwpx-agent.p09-native-diagnostic-controller/v13",
     index=step.index,before=step.before,qualification_run=1,physical_product_run=RETRY.physical_run(step.index),
     base_step_pin=step.pin,component_pins=COMPONENT_PINS,component_qualification_pins=COMPONENT_QUAL_PINS,
     actual152_pin=ACTUAL152_PIN,actual146_pin=ACTUAL146_PIN,
     reviewed_failure_pins=[RETRY.STOPPED,RETRY.REVIEW]),"EXPLICIT_PHYSICAL_AND_QUALIFICATION_RUNS")
    M.a.exact(row["prior_v12_data_pin"]["path"],OLD12.data_path(step.index),"ORIGINAL_DATA012")
    M.a.exact(row["qualification_pin"]["path"],QUAL_PATH,"EXACT_NEW_CODE6")
    require(set(M.base.scope.pins(row["controller_code_pins"],2))=={SELF,TEST},"CONTROLLER_CODE2")
    data_path(step.index)
    return row

def own_inputs(q):
    OLD12.own_inputs(q)
    row=validate_data(json.loads(q.text(data_path(M.base.CONFIG.index)),object_pairs_hook=M.base.unique),M.base.CONFIG)
    M.a.exact(q.snapshots[OLD12.data_path(M.base.CONFIG.index)],row["prior_v12_data_pin"],"ORIGINAL_DATA012_BYTES")
    RETRY.reviewed_failure(q,M.a.read_exact,M.a.fields)
    for p in COMPONENT_QUAL_PINS:
        value=M.a.read_exact(q,p)
        require(value["state"].startswith("PASS_") and value["cleanup_confirmed"] is True,"QUALIFIED_COMPONENT")
    qual=M.a.read_exact(q,row["qualification_pin"])
    M.a.fields(qual,dict(state=QUAL_STATE,contracts=dict(run=6,errors=0,failures=0,skipped=0),
     cleanup_confirmed=True,Native_product_or_acceptance_executed=False),"CODE6_NOT_PRODUCT")
    M.a.exact(qual["new_code_pins"],row["controller_code_pins"],"EXACT_CURRENT_TESTED_CONTROLLER2")
    M.a.exact(qual["component_pins"],COMPONENT_PINS,"ALL_QUALIFIED_COMPONENTS")
    for p in row["controller_code_pins"]+COMPONENT_PINS+[OLD12_PIN,OLD12_TEST_PIN]:
        M.a.exact(q.pin(p["path"]),p,"ALL_NAMESPACE_SOURCES_CURRENT")
    ar=M.a.read_exact(q,ACTUAL146_PIN)
    M.a.fields(ar,dict(accepted_count_after=146,next_runtime_index=153,accepted_test_indices=[152],
      resource_cleanup_confirmed=True,P09_gate="OPEN"),"TRUE146_UNCHANGED_AUTHORITY")
    M.a.exact(ar["runtime_candidate_pin"],ACTUAL152_PIN,"SAME_EXECUTED152")
    return row

def validator(source,ctx,flat=True):
    fn,proof=OLD12.validator(source,ctx,flat)
    fn.__globals__["CONTROLLERS"]=tuple(dict.fromkeys(fn.__globals__["CONTROLLERS"]+(SELF,TEST)))
    return fn,dict(proof,both_diagnostics_and_reviewed_physical_attempt_in_whole_scope=True)

def context(step):
    return NS(**{**vars(OLD12.context(step)),"SELF":SELF,"TEST":TEST})

def template():
    # Build FULL prior engine, then keep same private globals for outer binding.
    engine,proof=OLD12.template()
    engine.run_owned.__globals__.update(SELF=SELF,TEST=TEST,native=NATIVE)
    engine.worker.__globals__.update(SELF=SELF,TEST=TEST,native=NATIVE)
    FORMAT_STATES.append(OLD12.FORMAT_STATES[-1])
    result,state,attempt_proof=RETRY.connect_engine(engine,M.base.CONFIG.index)
    ATTEMPT_STATES.append(state)
    return result,dict(proof,reviewed_physical_attempt=attempt_proof,
      full_original_engine_preserved_inside_one_explicit_argument_adapter=True)

def previous_function(index):
    require(type(index) is int and 147<=index<=249,"EXACT_PREDECESSOR_INDEX")
    if index<=152:return OLD12.previous_function(index)
    fn=M.V3.OLD.API.previous_validation
    return FunctionType(fn.__code__,dict(fn.__globals__,source=CURRENT_SOURCE,
      validator=validator,context=context),argdefs=fn.__defaults__,closure=fn.__closure__)

def previous_validation(q,row,listing,oldbody,fresh,oldctx,flat=True):
    if oldctx.INDEX<=146:return OLD12.previous_validation(q,row,listing,oldbody,fresh,oldctx,flat)
    if oldctx.INDEX==152:
        require(M.base.CONFIG.index==153,"ONLY_NEXT153_AFTER_REAL152")
        M.a.exact(M.base.CONFIG.prior_candidate_pin,ACTUAL152_PIN,"EXACT152_PREDECESSOR")
    return previous_function(oldctx.INDEX)(q,row,listing,oldbody,fresh,oldctx,flat)

def binding(q):
    p,data=q._read(M.V3.OLD.API.BASE_PIN["path"],parse=True);q._bind(p["path"],p)
    M.a.exact(p,M.V3.OLD.API.BASE_PIN,"ORIGINAL_BINDING_SOURCE")
    fn,_=M.V3.OLD.API.binding_projection(bytes(data),replacement=previous_validation)
    return fn(q)

def native_scope(q,row):
    p=q.snapshots[data_path(M.base.CONFIG.index)]
    value=validate_data(M.a.read_exact(q,p),M.base.CONFIG)
    expected=M.base.scope.pins(row["source_freeze"])
    for required in [p,value["qualification_pin"],OLD12_PIN,OLD12_TEST_PIN,ACTUAL152_PIN,ACTUAL146_PIN]+\
       value["controller_code_pins"]+COMPONENT_PINS+COMPONENT_QUAL_PINS+[RETRY.STOPPED,RETRY.REVIEW]:
        M.a.exact(expected.get(required["path"]),required,"ALL_NEW_DATA_AND_REVIEW_PINS_IN_NATIVE")
    return expected

_family=OLD12._full_prepare.__globals__;_env=dict(_family)
for _name,_fn in tuple(_env.items()):
    if type(_fn) is FunctionType and _fn.__globals__ is _family:
        _env[_name]=FunctionType(_fn.__code__,_env,argdefs=_fn.__defaults__,closure=_fn.__closure__)
_env.update(SELF=SELF,TEST=TEST,FILES=(SELF,TEST),QUAL_PATH=QUAL_PATH,source=CURRENT_SOURCE,
 own_inputs=own_inputs,validator=validator,context=context,template=template,binding=binding,
 previous_validation=previous_validation,data_path=M.data_path,validate_data=M.validate_data)
API=NS(**_env)
_full_prepare=API.prepare

def prepare(q,p):
    result=_full_prepare(q,p)
    native_scope(q,result[0]);RETRY.validate_actual(result[0],M.base.CONFIG,p)
    return result

API.prepare=prepare
API.original_run_owned=API.run_owned

def worker(task):
    RETRY.physical_run(M.base.CONFIG.index)
    M.a.exact(task,RETRY.task(M.base.CONFIG.index),"EXACT_ACTUAL_PHYSICAL_WORKER_TASK")
    engine,_=template()
    return engine.worker(task)

API.worker=worker

def run_owned(run):
    index=M.base.CONFIG.index;logical=RETRY.public_run(index,run);data_path(index)
    require(not (M.c.ROOT/RETRY.root_path(M.base.CONFIG)).exists(),"FRESH_PHYSICAL_RECEIPT")
    execute,state=CONNECTION.connect_run(API.original_run_owned,BACKEND)
    before=len(FORMAT_STATES);attempt_before=len(ATTEMPT_STATES)
    code=execute(logical)
    observed=ATTEMPT_STATES[attempt_before:]
    require(len(observed)==1 and observed[0].actual_engine_calls==1 and
      observed[0].physical_product_run==run,"ONE_ACTUAL_EXPLICIT_PHYSICAL_ENGINE_CALL")
    if code==0:
        formatted=FORMAT_STATES[before:]
        require(sum(s.actual_capture_count for s in formatted)==1 and sum(s.actual_dump_calls for s in formatted)==1
          and all(s.writer_errors_propagated==0 for s in formatted),"ONE_ACTUAL_COMPACT_CAPTURE_AND_DUMP")
    require(state["actual_local_bindings"]==1,"ONE_ACTUAL_NATIVE4_LOCAL_CONNECTION")
    return code

def preflight_projection(data,leaf):
    fn=OLD12.preflight_projection(data,leaf);old=fn.__code__
    require(sum(type(x) is str and x=="-native-diagnostic-preflight012.v1.json" for x in old.co_consts)==1,
      "ONE_NEW_PREFLIGHT_DESTINATION")
    revised=old.replace(co_consts=tuple("-native-diagnostic-preflight013.v1.json" if type(x) is str and
      x=="-native-diagnostic-preflight012.v1.json" else x for x in old.co_consts))
    require(revised.replace(co_consts=old.co_consts)==old,"ALL_ORIGINAL_PREFLIGHT_CODE_TEST10")
    return FunctionType(revised,dict(fn.__globals__,SELF=SELF,TEST=TEST,template=template,
      binding_attempt=API.binding_attempt,connection_data=own_inputs,own_inputs=own_inputs,data_path=data_path,
      base=NS(**{**vars(fn.__globals__["base"]),"native":NATIVE})),
      argdefs=fn.__defaults__,closure=fn.__closure__)

def preflight():
    fn=M.V3.OLD.API.preflight
    return FunctionType(fn.__code__,dict(fn.__globals__,preflight_projection=preflight_projection),
      argdefs=fn.__defaults__,closure=fn.__closure__)()

if __name__=="__main__":
    try:
        if len(sys.argv)==4 and sys.argv[1:3]==["--owned-worker","--task"]:
            M.base.configure(M.base.task_index(sys.argv[3]));data_path(M.base.CONFIG.index)
            raise SystemExit(worker(sys.argv[3]))
        parser=argparse.ArgumentParser();parser.add_argument("--case",type=int,required=True)
        parser.add_argument("--run",type=int);parser.add_argument("--preflight",action="store_true")
        args=parser.parse_args();data_path(args.case);M.base.configure(args.case)
        require((args.run is not None)!=args.preflight,"ONE_MODE")
        raise SystemExit(preflight() if args.preflight else run_owned(args.run))
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        code=str(error) if isinstance(error,ValueError) and re.fullmatch("[A-Z0-9_]{1,256}",str(error)) else "REDACTED_V13_FAILURE"
        print(json.dumps(dict(state="FAILED_NOT_ACCEPTED",error_code=code)))
        raise SystemExit(2) from None
