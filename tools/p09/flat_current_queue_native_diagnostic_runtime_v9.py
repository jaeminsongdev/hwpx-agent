"""Full current/previous native observer-format connection for cases148+.

Original run/prepare/candidate bytecodes, old147 executed context, all DATA004
postchecks, sole sampler/limits/two byte passes/cleanup and historical failures
remain. Old controllers/receipts are immutable. No successful147 replay.
"""
import argparse
import ast
import copy
import ctypes
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

SELF="tools/p09/flat_current_queue_native_diagnostic_runtime_v9.py"
TEST="tools/p09/tests/test_flat_current_queue_native_diagnostic_runtime_v9.py"
QUAL_PATH="implementation/p09/evidence/p09-361-case148-native-both-observer-controller-code6-r464.v1.json"
OLD8_PIN=dict(path="tools/p09/flat_current_queue_native_diagnostic_runtime_v8.py",bytes=12047,
 sha256="4e344292b6b8d09d0be7507f52b38f30a2d7ca65fa874c2f92462f0833c41a6d")
OLD8_TEST_PIN=dict(path="tools/p09/tests/test_flat_current_queue_native_diagnostic_runtime_v8.py",bytes=2954,
 sha256="9eb91eddc3a9e72d5cc9c9d958e16344f0c3220d13bd6b0a3b1ad70529ba854f")
ADDITIONAL_PINS=[{"path":"tools/p09/native_additional_observer_connection_v1.py","bytes":4825,"sha256":"eb827d590e423895c2d774193a6a1582178a60c2de75b5c982e662f40b33eab3"},{"path":"tools/p09/tests/test_native_additional_observer_connection_v1.py","bytes":3669,"sha256":"f77ad3bcffe19fe59444e5f14590cdca706cf91a2e49ed3f1752e2d26d1d98b4"}]
ADDITIONAL_QUAL=dict(path="implementation/p09/evidence/p09-361-case147-native-additional-observer-code5-r461.v1.json",
 bytes=4325,sha256="4a600e095578b669501ca21da2ad77ceac64db489b9456125d07787fb3f72226")
ACTUAL147_PIN=dict(path="implementation/p09/evidence/p09-361-case147-current-runtime-run001.v1.json",
 bytes=2930573,sha256="fe467b595196410f6ab628d57f945740299cffa5f3b625e436925508823c8112")
ACTUAL141_PIN=dict(path="implementation/p09/evidence/p09-361-case147-current-epoch-accept001.v1.json",
 bytes=321278,sha256="336b086e7e09c59317c4edf558f458912c838814848356a3b5bf42e89aab052c")


def require(ok,code):
    if not ok:raise ValueError("NATIVE_BOTH_OBSERVER_V9_"+code)


def raw(pin):
    lean.base.stable.stable.prior.build.direct_path(lean.c.ROOT/pin["path"],file_required=True)
    with (lean.c.ROOT/pin["path"]).open("rb") as stream:data=stream.read(pin["bytes"]+1)
    require(len(data)==pin["bytes"] and hashlib.sha256(data).hexdigest()==pin["sha256"],"EXACT_NAMESPACE_BYTES")
    return data


def load_old8():
    source=raw(OLD8_PIN);tree=ast.parse(source.decode("utf-8"))
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
     __name__="p09_exact_old8_namespace",__file__=OLD8_PIN["path"])
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),OLD8_PIN["path"],"exec"),env)
    return NS(**env)


OLD8=load_old8()
M=OLD8.M
CONNECTION=OLD8.CONNECTION
BACKEND=OLD8.BACKEND
ADDITIONAL=OLD8.BASE.namespace(raw(ADDITIONAL_PINS[0]),ADDITIONAL_PINS[0],
                             dict(FunctionType=FunctionType,NS=NS))
original_source=OLD8._full_prepare.__globals__["source"]
linked_candidate,ADDITIONAL_PROOF=ADDITIONAL.connect_candidate(original_source.validate_candidate,
 M.source.prior.accepted.original.candidate,M.V3.ORACLE,CONNECTION)
CURRENT_SOURCE=NS(**{**vars(original_source),"validate_candidate":linked_candidate})


def data_path(index):
    require(type(index) is int and 148<=index<=249,"NO_SUCCESSFUL_CASE_REPLAY")
    return f"implementation/p09/evidence/p09-361-case{index}-native-diagnostic-data009.v1.json"


def validate_data(row,step):
    require(type(row) is dict and set(row)=={"schema_version","index","before","run","base_step_pin",
     "prior_v8_data_pin","qualification_pin","controller_code_pins","additional_observer_code_pins",
     "additional_observer_qualification_pin","actual147_pin","actual141_pin"},"CLOSED_DATA009")
    M.a.fields(row,dict(schema_version="hwpx-agent.p09-native-diagnostic-controller/v9",
     index=step.index,before=step.before,run=1,base_step_pin=step.pin,additional_observer_code_pins=ADDITIONAL_PINS,
     additional_observer_qualification_pin=ADDITIONAL_QUAL,actual147_pin=ACTUAL147_PIN,
     actual141_pin=ACTUAL141_PIN),"EXACT_CURRENT_STEP_AND_PASSED147")
    M.a.exact(row["prior_v8_data_pin"]["path"],OLD8.data_path(step.index),"ORIGINAL_DATA008")
    M.a.exact(row["qualification_pin"]["path"],QUAL_PATH,"EXACT_CODE6")
    require(set(M.base.scope.pins(row["controller_code_pins"],2))=={SELF,TEST},"CONTROLLER_CODE2")
    data_path(step.index)
    return row


def own_inputs(q):
    OLD8.own_inputs(q)
    row=validate_data(json.loads(q.text(data_path(M.base.CONFIG.index)),object_pairs_hook=M.base.unique),M.base.CONFIG)
    M.a.exact(q.snapshots[OLD8.data_path(M.base.CONFIG.index)],row["prior_v8_data_pin"],"ORIGINAL_DATA008_BYTES")
    additional=M.a.read_exact(q,ADDITIONAL_QUAL)
    M.a.fields(additional,dict(state="PASS_NATIVE_ADDITIONAL_OBSERVER_CODE5_AND_ACTUAL147_ORIGINAL_GUARDS_NOT_ACCEPTANCE",
     contracts=dict(run=5,errors=0,failures=0,skipped=0),cleanup_confirmed=True,
     Native_product_or_acceptance_executed=False),"ACTUAL_CODE5_NOT_NATIVE_INPUT")
    M.a.exact(additional["new_code_pins"],ADDITIONAL_PINS,"EXACT_ADDITIONAL_CODE2")
    qual=M.a.read_exact(q,row["qualification_pin"])
    M.a.fields(qual,dict(state="PASS_NATIVE_V9_CURRENT_PREVIOUS_OBSERVER_CONNECTION_CODE6_NOT_PRODUCT",
     contracts=dict(run=6,errors=0,failures=0,skipped=0),cleanup_confirmed=True,
     Native_product_or_acceptance_executed=False),"CODE6_NOT_PRODUCT")
    M.a.exact(qual["new_code_pins"],row["controller_code_pins"],"EXACT_CURRENT_TESTED_CONTROLLER2")
    for pin in row["controller_code_pins"]+ADDITIONAL_PINS+[OLD8_PIN,OLD8_TEST_PIN]:
        M.a.exact(q.pin(pin["path"]),pin,"ALL_NAMESPACE_SOURCES_CURRENT")
    ar=M.a.read_exact(q,ACTUAL141_PIN)
    M.a.fields(ar,dict(accepted_count_after=141,next_runtime_index=148,accepted_test_indices=[147],
      resource_cleanup_confirmed=True,P09_gate="OPEN"),"TRUE147_ACCEPTED_ONCE_NOT_GATE")
    M.a.exact(ar["runtime_candidate_pin"],ACTUAL147_PIN,"SAME_EXECUTED147")
    return row


def validator(source,ctx,flat=True):
    fn,proof=OLD8.validator(source,ctx,flat)
    fn.__globals__["CONTROLLERS"]=tuple(dict.fromkeys(fn.__globals__["CONTROLLERS"]+(SELF,TEST)))
    return fn,dict(proof,both_observer_connections_inside_whole_source_scope=True)


def context(step):
    return NS(**{**vars(OLD8.context(step)),"SELF":SELF,"TEST":TEST})


def template():
    engine,proof=OLD8.template()
    engine.run_owned.__globals__.update(SELF=SELF,TEST=TEST)
    engine.worker.__globals__.update(SELF=SELF,TEST=TEST)
    return engine,dict(proof,original_engine_unchanged_with_both_diagnostic_connections=True)


def previous_function(index):
    fn=M.V3.OLD.API.previous_validation
    require(type(index) is int and index>=147,"NATIVE_PREDECESSOR_INDEX")
    use_validator=OLD8.validator if index==147 else validator
    use_context=OLD8.context if index==147 else context
    return FunctionType(fn.__code__,dict(fn.__globals__,source=CURRENT_SOURCE,
      validator=use_validator,context=use_context),argdefs=fn.__defaults__,closure=fn.__closure__)


def previous_validation(q,row,listing,oldbody,fresh,oldctx,flat=True):
    if oldctx.INDEX<=146:return OLD8.previous_validation(q,row,listing,oldbody,fresh,oldctx,flat)
    if oldctx.INDEX==147:
        require(M.base.CONFIG.index==148,"ONLY_NEXT148_AFTER_REAL147")
        M.a.exact(M.base.CONFIG.prior_candidate_pin,ACTUAL147_PIN,"EXACT_147_PREDECESSOR_PIN")
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
    for required in [pin,value["qualification_pin"],ADDITIONAL_QUAL,OLD8_PIN,OLD8_TEST_PIN,
                     ACTUAL147_PIN,ACTUAL141_PIN]+value["controller_code_pins"]+ADDITIONAL_PINS:
        M.a.exact(expected.get(required["path"]),required,"ALL_NEW_DATA_SOURCE_AND_CUTOVER_PINS_IN_NATIVE")
    return expected


_family=OLD8._full_prepare.__globals__;_env=dict(_family)
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
    code=execute(run)
    require(state["actual_local_bindings"]==1,"ONE_ACTUAL_NATIVE_LOCAL_CONNECTION")
    return code


def preflight_projection(data,leaf):
    fn=OLD8.preflight_projection(data,leaf);old=fn.__code__
    require(sum(type(x) is str and x=="-native-diagnostic-preflight008.v1.json" for x in old.co_consts)==1,
      "ONE_NEW_PREFLIGHT_DESTINATION")
    constants=tuple("-native-diagnostic-preflight009.v1.json" if type(x) is str and
      x=="-native-diagnostic-preflight008.v1.json" else x for x in old.co_consts)
    code=old.replace(co_consts=constants)
    require(code.replace(co_consts=old.co_consts)==old,"ALL_ORIGINAL_PREFLIGHT_CODE_AND_TEST10")
    return FunctionType(code,dict(fn.__globals__,SELF=SELF,TEST=TEST,template=template,
      binding_attempt=API.binding_attempt,connection_data=own_inputs,own_inputs=own_inputs,data_path=data_path),
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
        value=str(error) if isinstance(error,ValueError) and re.fullmatch("[A-Z0-9_]{1,256}",str(error)) else "REDACTED_V9_FAILURE"
        print(json.dumps(dict(state="FAILED_NOT_ACCEPTED",error_code=value)))
        raise SystemExit(2) from None
