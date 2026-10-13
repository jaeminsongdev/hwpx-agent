"""Compact final runtime JSON for151+; historical150 full context unchanged.

Original run/prepare/candidate bytecodes, old149 executed context, all DATA004
postchecks, sole sampler/limits/two byte passes/cleanup and historical failures
remain. Old controllers/receipts are immutable. No successful149 replay.
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

SELF="tools/p09/flat_current_queue_native_diagnostic_runtime_v12.py"
TEST="tools/p09/tests/test_flat_current_queue_native_diagnostic_runtime_v12.py"
QUAL_PATH="implementation/p09/evidence/p09-361-case151-compact-controller-code6-r497.v1.json"
OLD11_PIN=dict(path="tools/p09/flat_current_queue_native_diagnostic_runtime_v11.py",bytes=13939,
 sha256="a5728bf6cac0e9b0d92e42ee6fe68599b16581e63ffd4b7c49cf9de64ae2b9d5")
OLD11_TEST_PIN=dict(path="tools/p09/tests/test_flat_current_queue_native_diagnostic_runtime_v11.py",bytes=4795,
 sha256="e97da15d2bd4d15dc9dc87dbbe9b3409d5f92e336c7ac878d920e07c0f8cdcc5")
COMPONENT_PINS=[{"path":"tools/p09/compact_runtime_record_v1.py","bytes":3349,"sha256":"54821823bde2a76c416116ac4b3560fcd7d0083fea8466c0ee9517b3d0e09e74"},{"path":"tools/p09/tests/test_compact_runtime_record_v1.py","bytes":4740,"sha256":"42a9fe01b633b898c4b47524ee3925d3a309bce8b9700a12a7065242be3fb695"}]
COMPONENT_QUAL_PINS=[{"path":"implementation/p09/evidence/p09-361-case151-compact-runtime-code6-r496.v1.json","bytes":3677,"sha256":"f0634044504ccafb06504003eafe5c06ccbb545a962aac0dee210f579747f4ed"}]
ACTUAL150_PIN={"path":"implementation/p09/evidence/p09-361-case150-current-runtime-run001.v1.json","bytes":2889343,"sha256":"0dabddedff0a12f5c637ba48df921f0368fb00b494d732b016c90c1cf3d2545a"}
ACTUAL144_PIN={"path":"implementation/p09/evidence/p09-361-case150-current-epoch-accept001.v1.json","bytes":331621,"sha256":"e7dac223298ba60b1016db16cf517db671dc218eab6f6ea0c2e0a5e67a8725d2"}
QUAL_STATE="PASS_NATIVE_V12_FULL_COMPACT_CONTROLLER_CODE6_NOT_PRODUCT"


def require(ok,code):
    if not ok:raise ValueError("NATIVE_BOTH_OBSERVER_V12_"+code)


def raw(pin):
    lean.base.stable.stable.prior.build.direct_path(lean.c.ROOT/pin["path"],file_required=True)
    with (lean.c.ROOT/pin["path"]).open("rb") as stream:data=stream.read(pin["bytes"]+1)
    require(len(data)==pin["bytes"] and hashlib.sha256(data).hexdigest()==pin["sha256"],"EXACT_NAMESPACE_BYTES")
    return data


def load_old11():
    source=raw(OLD11_PIN);tree=ast.parse(source.decode("utf-8"))
    def selected(n):
        return isinstance(n,(ast.Assign,ast.FunctionDef,ast.ClassDef,ast.For)) or (
         isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Attribute)
         and isinstance(n.value.func.value,ast.Name) and n.value.func.value.id=="_env")
    originals=[n for n in tree.body if selected(n)];nodes=copy.deepcopy(originals)
    require([ast.dump(n,include_attributes=False) for n in nodes]==
            [ast.dump(n,include_attributes=False) for n in originals],"ALL_OLD_DEFINITIONS_AND_INITIALIZATION")
    env=dict(lean=lean,argparse=argparse,ast=ast,copy=copy,ctypes=ctypes,w=w,contextmanager=contextmanager,
     hashlib=hashlib,json=json,math=math,os=os,Path=Path,re=re,sys=sys,threading=threading,time=time,
     FunctionType=FunctionType,MappingProxyType=MappingProxyType,NS=NS,unittest=unittest,
     __name__="p09_exact_old11_namespace",__file__=OLD11_PIN["path"])
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),OLD11_PIN["path"],"exec"),env)
    return NS(**env)


OLD11=load_old11()
M=OLD11.M
pin=COMPONENT_PINS[0]
COMPACT=OLD11.OLD10.OLD9.OLD8.BASE.namespace(raw(pin),pin,dict(dis=dis,FunctionType=FunctionType,NS=NS))
FORMAT_STATES=[]
NATIVE=OLD11.NATIVE
NATIVE_PROOF=OLD11.NATIVE_PROOF
BACKEND=OLD11.BACKEND
CONNECTION=OLD11.CONNECTION
ORACLE=OLD11.ORACLE
ORACLE_PROOF=OLD11.ORACLE_PROOF
CURRENT_SOURCE=OLD11.CURRENT_SOURCE


def data_path(index):
    require(type(index) is int and 151<=index<=249,"NO_SUCCESSFUL_CASE_REPLAY")
    return f"implementation/p09/evidence/p09-361-case{index}-native-diagnostic-data012.v1.json"


def validate_data(row,step):
    require(type(row) is dict and set(row)=={"schema_version","index","before","run","base_step_pin",
     "prior_v11_data_pin","qualification_pin","controller_code_pins","component_pins","component_qualification_pins",
     "actual150_pin","actual144_pin"},"CLOSED_DATA012")
    M.a.fields(row,dict(schema_version="hwpx-agent.p09-native-diagnostic-controller/v12",
     index=step.index,before=step.before,run=1,base_step_pin=step.pin,component_pins=COMPONENT_PINS,
     component_qualification_pins=COMPONENT_QUAL_PINS,actual150_pin=ACTUAL150_PIN,actual144_pin=ACTUAL144_PIN),
     "EXACT_CURRENT_STEP_AND_PASSED148")
    M.a.exact(row["prior_v11_data_pin"]["path"],OLD11.data_path(step.index),"ORIGINAL_DATA011")
    M.a.exact(row["qualification_pin"]["path"],QUAL_PATH,"EXACT_CODE6")
    require(set(M.base.scope.pins(row["controller_code_pins"],2))=={SELF,TEST},"CONTROLLER_CODE2")
    data_path(step.index)
    return row


def own_inputs(q):
    OLD11.own_inputs(q)
    row=validate_data(json.loads(q.text(data_path(M.base.CONFIG.index)),object_pairs_hook=M.base.unique),M.base.CONFIG)
    M.a.exact(q.snapshots[OLD11.data_path(M.base.CONFIG.index)],row["prior_v11_data_pin"],"ORIGINAL_DATA011_BYTES")
    for pin in COMPONENT_QUAL_PINS:
        qualified=M.a.read_exact(q,pin)
        require(qualified["state"].startswith("PASS_") and qualified["cleanup_confirmed"] is True,"QUALIFIED_COMPONENT")
    qual=M.a.read_exact(q,row["qualification_pin"])
    M.a.fields(qual,dict(state=QUAL_STATE,contracts=dict(run=6,errors=0,failures=0,skipped=0),
     cleanup_confirmed=True,Native_product_or_acceptance_executed=False),"CODE6_NOT_PRODUCT")
    M.a.exact(qual["new_code_pins"],row["controller_code_pins"],"EXACT_CURRENT_TESTED_CONTROLLER2")
    M.a.exact(qual["component_pins"],COMPONENT_PINS,"ALL_QUALIFIED_COMPONENTS")
    for pin in row["controller_code_pins"]+COMPONENT_PINS+[OLD11_PIN,OLD11_TEST_PIN]:
        M.a.exact(q.pin(pin["path"]),pin,"ALL_NAMESPACE_SOURCES_CURRENT")
    ar=M.a.read_exact(q,ACTUAL144_PIN)
    M.a.fields(ar,dict(accepted_count_after=144,next_runtime_index=151,accepted_test_indices=[150],
      resource_cleanup_confirmed=True,P09_gate="OPEN"),"TRUE148_ACCEPTED_ONCE_NOT_GATE")
    M.a.exact(ar["runtime_candidate_pin"],ACTUAL150_PIN,"SAME_EXECUTED148")
    return row


def validator(source,ctx,flat=True):
    fn,proof=OLD11.validator(source,ctx,flat)
    fn.__globals__["CONTROLLERS"]=tuple(dict.fromkeys(fn.__globals__["CONTROLLERS"]+(SELF,TEST)))
    return fn,dict(proof,both_observer_connections_inside_whole_source_scope=True)


def context(step):
    return NS(**{**vars(OLD11.context(step)),"SELF":SELF,"TEST":TEST})


def template():
    engine,proof=OLD11.template()
    engine.run_owned.__globals__.update(SELF=SELF,TEST=TEST,native=NATIVE)
    engine.worker.__globals__.update(SELF=SELF,TEST=TEST,native=NATIVE)
    engine.run_owned,state,format_proof=COMPACT.connect(engine.run_owned)
    FORMAT_STATES.append(state)
    return engine,dict(proof,original_engine_bytecode_unchanged=False,
      all_original_engine_code_except_one_raw_dump_lookup_retained=True,compact_record_projection=format_proof)


def previous_function(index):
    fn=M.V3.OLD.API.previous_validation
    require(type(index) is int and index>=147,"NATIVE_PREDECESSOR_INDEX")
    use_validator=OLD11.OLD10.OLD9.OLD8.validator if index==147 else OLD11.OLD10.OLD9.validator if index==148 else OLD11.OLD10.validator if index==149 else OLD11.validator if index==150 else validator
    use_context=OLD11.OLD10.OLD9.OLD8.context if index==147 else OLD11.OLD10.OLD9.context if index==148 else OLD11.OLD10.context if index==149 else OLD11.context if index==150 else context
    return FunctionType(fn.__code__,dict(fn.__globals__,source=CURRENT_SOURCE,
      validator=use_validator,context=use_context),argdefs=fn.__defaults__,closure=fn.__closure__)


def previous_validation(q,row,listing,oldbody,fresh,oldctx,flat=True):
    if oldctx.INDEX<=146:return OLD11.previous_validation(q,row,listing,oldbody,fresh,oldctx,flat)
    if oldctx.INDEX==150:
        require(M.base.CONFIG.index==151,"ONLY_NEXT151_AFTER_REAL150")
        M.a.exact(M.base.CONFIG.prior_candidate_pin,ACTUAL150_PIN,"EXACT_150_PREDECESSOR_PIN")
    return previous_function(oldctx.INDEX)(q,row,listing,oldbody,fresh,oldctx,flat)


def binding(q):
    pin,data=q._read(M.V3.OLD.API.BASE_PIN["path"],parse=True);q._bind(pin["path"],pin)
    M.a.exact(pin,M.V3.OLD.API.BASE_PIN,"ORIGINAL_BINDING_SOURCE")
    fn,_=M.V3.OLD.API.binding_projection(bytes(data),replacement=previous_validation)
    return fn(q)


def native_scope(q,row):
    pin=q.snapshots[data_path(M.base.CONFIG.index)]
    value=validate_data(M.a.read_exact(q,pin),M.base.CONFIG)
    expected=M.base.scope.pins(row["source_freeze"])
    for required in [pin,value["qualification_pin"],OLD11_PIN,OLD11_TEST_PIN,
                     ACTUAL150_PIN,ACTUAL144_PIN]+value["controller_code_pins"]+COMPONENT_PINS+COMPONENT_QUAL_PINS:
        M.a.exact(expected.get(required["path"]),required,"ALL_NEW_DATA_SOURCE_AND_CUTOVER_PINS_IN_NATIVE")
    return expected


_family=OLD11._full_prepare.__globals__;_env=dict(_family)
for _name,_fn in tuple(_env.items()):
    if type(_fn) is FunctionType and _fn.__globals__ is _family:
        _env[_name]=FunctionType(_fn.__code__,_env,argdefs=_fn.__defaults__,closure=_fn.__closure__)
_env.update(SELF=SELF,TEST=TEST,FILES=(SELF,TEST),QUAL_PATH=QUAL_PATH,source=CURRENT_SOURCE,
 own_inputs=own_inputs,validator=validator,context=context,template=template,binding=binding,
 previous_validation=previous_validation,data_path=M.data_path,validate_data=M.validate_data)
API=NS(**_env)
_full_prepare=API.prepare


def prepare(q,pin):
    result=_full_prepare(q,pin);native_scope(q,result[0]);return result


API.prepare=prepare
API.original_run_owned=API.run_owned


def run_owned(run):
    data_path(M.base.CONFIG.index);require(run==1,"FIRST_EXPLICIT_RUN_ONLY")
    execute,state=CONNECTION.connect_run(API.original_run_owned,BACKEND)
    before=len(FORMAT_STATES)
    code=execute(run)
    if code==0:
        observed=FORMAT_STATES[before:]
        require(sum(s.actual_capture_count for s in observed)==1 and sum(s.actual_dump_calls for s in observed)==1
                and all(s.writer_errors_propagated==0 for s in observed),"ONE_ACTUAL_COMPACT_RECORD_CAPTURE_AND_DUMP")
    require(state["actual_local_bindings"]==1,"ONE_ACTUAL_NATIVE_LOCAL_CONNECTION")
    return code


def preflight_projection(data,leaf):
    fn=OLD11.preflight_projection(data,leaf);old=fn.__code__
    require(sum(type(x) is str and x=="-native-diagnostic-preflight011.v1.json" for x in old.co_consts)==1,
      "ONE_NEW_PREFLIGHT_DESTINATION")
    constants=tuple("-native-diagnostic-preflight012.v1.json" if type(x) is str and
      x=="-native-diagnostic-preflight011.v1.json" else x for x in old.co_consts)
    code=old.replace(co_consts=constants)
    require(code.replace(co_consts=old.co_consts)==old,"ALL_ORIGINAL_PREFLIGHT_CODE_AND_TEST10")
    return FunctionType(code,dict(fn.__globals__,SELF=SELF,TEST=TEST,template=template,
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
            raise SystemExit(API.worker(sys.argv[3]))
        parser=argparse.ArgumentParser();parser.add_argument("--case",type=int,required=True)
        parser.add_argument("--run",type=int);parser.add_argument("--preflight",action="store_true")
        args=parser.parse_args();data_path(args.case);M.base.configure(args.case)
        require((args.run is not None)!=args.preflight,"ONE_MODE")
        raise SystemExit(preflight() if args.preflight else run_owned(args.run))
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        value=str(error) if isinstance(error,ValueError) and re.fullmatch("[A-Z0-9_]{1,256}",str(error)) else "REDACTED_V12_FAILURE"
        print(json.dumps(dict(state="FAILED_NOT_ACCEPTED",error_code=value)))
        raise SystemExit(2) from None
