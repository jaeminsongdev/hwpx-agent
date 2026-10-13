"""Native READ scratch connection for150+; historical149 NativeV3 unchanged.

Original run/prepare/candidate bytecodes, old149 executed context, all DATA004
postchecks, sole sampler/limits/two byte passes/cleanup and historical failures
remain. Old controllers/receipts are immutable. No successful149 replay.
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

SELF="tools/p09/flat_current_queue_native_diagnostic_runtime_v11.py"
TEST="tools/p09/tests/test_flat_current_queue_native_diagnostic_runtime_v11.py"
QUAL_PATH="implementation/p09/evidence/p09-361-case150-native-read-scratch-controller-code6-r488.v1.json"
OLD10_PIN=dict(path="tools/p09/flat_current_queue_native_diagnostic_runtime_v10.py",bytes=14516,
 sha256="270e6be4da13c0233fec530b3d534910582bd4de4f5280377312b039cb26fc97")
OLD10_TEST_PIN=dict(path="tools/p09/tests/test_flat_current_queue_native_diagnostic_runtime_v10.py",bytes=4638,
 sha256="abbb1539502448168efd0ae4d3cdecc70f567fc35fc99ead2f5c440e9302be89")
COMPONENT_PINS=[{"path":"tools/p09/native_read_call_scratch_v1.py","bytes":5182,"sha256":"09408f62aa62801259bc9d50fcfdb6b601fdc909b1348dbcfd41475c9d37bd44"},{"path":"tools/p09/tests/test_native_read_call_scratch_v1.py","bytes":4095,"sha256":"f471b991107436800eaa73f7ffbea3f305ea5039808664ee06e2ee93963b77a3"},{"path":"tools/p09/native_read_scratch_connection_v1.py","bytes":5221,"sha256":"33bc429ca8d51118c100a5183c0c2ab682b3cc75771ba84a6150a26e4b9b59bc"},{"path":"tools/p09/tests/test_native_read_scratch_connection_v1.py","bytes":5228,"sha256":"2c3b3e6d18439fc8ea14b5c91c4bbb8984b81f68a09281cf581ab90f2298d1ef"}]
COMPONENT_QUAL_PINS=[{"path":"implementation/p09/evidence/p09-361-case150-native-read-scratch-code6-r483.v1.json","bytes":3616,"sha256":"8ee3a61e2f1d9b46f0530e579c83bcc478cd95bf84ad89779e46cfd39b3f5034"},{"path":"implementation/p09/evidence/p09-361-case150-native-read-scratch-live-r484.v1.json","bytes":3388,"sha256":"63ea31bcb527207e7f380a388a7fc7c4d16c9fb2db9484d04a718b9389a1f576"},{"path":"implementation/p09/evidence/p09-361-case150-native-read-scratch-connection-code6-r487.v1.json","bytes":4347,"sha256":"23a21756d5677eafcee1de54b94f0d48c4faca2da39facaf954364ee762fdfd0"}]
ACTUAL149_PIN={"path":"implementation/p09/evidence/p09-361-case149-current-runtime-run001.v1.json","bytes":2925472,"sha256":"05edda92b932f88284fea5d75e8303a63a3d5b91edc97e2d1db739bde9550c17"}
ACTUAL143_PIN={"path":"implementation/p09/evidence/p09-361-case149-current-epoch-accept001.v1.json","bytes":327648,"sha256":"0cbc98f824dad9756dedaf19dc056d701544dc7c7ff6dae61fd6fb698c343ada"}
QUAL_STATE="PASS_NATIVE_V11_FULL_SCRATCH_CONTROLLER_CODE6_NOT_PRODUCT"


def require(ok,code):
    if not ok:raise ValueError("NATIVE_BOTH_OBSERVER_V11_"+code)


def raw(pin):
    lean.base.stable.stable.prior.build.direct_path(lean.c.ROOT/pin["path"],file_required=True)
    with (lean.c.ROOT/pin["path"]).open("rb") as stream:data=stream.read(pin["bytes"]+1)
    require(len(data)==pin["bytes"] and hashlib.sha256(data).hexdigest()==pin["sha256"],"EXACT_NAMESPACE_BYTES")
    return data


def load_old10():
    source=raw(OLD10_PIN);tree=ast.parse(source.decode("utf-8"))
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
     __name__="p09_exact_old10_namespace",__file__=OLD10_PIN["path"])
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),OLD10_PIN["path"],"exec"),env)
    return NS(**env)


OLD10=load_old10()
M=OLD10.M
def component(name,env):
    pin=next(p for p in COMPONENT_PINS if p["path"].endswith("/"+name))
    return OLD10.OLD9.OLD8.BASE.namespace(raw(pin),pin,env)
SCRATCH=component("native_read_call_scratch_v1.py",dict(ast=ast,copy=copy,ctypes=ctypes,w=w,
 hashlib=hashlib,threading=threading,prior=M.V3.VIEW))
SCRATCH_CONNECTION=component("native_read_scratch_connection_v1.py",
 dict(threading=threading,FunctionType=FunctionType,NS=NS,scratch=SCRATCH))
NATIVE,NATIVE_PROOF=SCRATCH_CONNECTION.connect(M.V3.NATIVE,raw(SCRATCH.ORIGINAL_PIN))
BACKEND=OLD10.BACKEND
CONNECTION=SCRATCH_CONNECTION.diagnostic(OLD10.CONNECTION)
oracle_pin=next(p for p in OLD10.COMPONENT_PINS if p["path"].endswith("/native_diagnostic_oracle_connection_v2.py"))
ORACLE=OLD10.OLD9.OLD8.BASE.namespace(raw(oracle_pin),oracle_pin,dict(FunctionType=FunctionType,NS=NS,
 prior=OLD10.ORACLE.prior,diagnostic=CONNECTION,additional=OLD10.ORACLE.additional))
original_source=OLD10._full_prepare.__globals__["source"]
linked_candidate,ORACLE_PROOF=ORACLE.connect_full(original_source.validate_candidate,
 M.source.prior.accepted.original.candidate,M.V3.ORACLE)
CURRENT_SOURCE=NS(**{**vars(original_source),"validate_candidate":linked_candidate})


def data_path(index):
    require(type(index) is int and 150<=index<=249,"NO_SUCCESSFUL_CASE_REPLAY")
    return f"implementation/p09/evidence/p09-361-case{index}-native-diagnostic-data011.v1.json"


def validate_data(row,step):
    require(type(row) is dict and set(row)=={"schema_version","index","before","run","base_step_pin",
     "prior_v10_data_pin","qualification_pin","controller_code_pins","component_pins","component_qualification_pins",
     "actual149_pin","actual143_pin"},"CLOSED_DATA011")
    M.a.fields(row,dict(schema_version="hwpx-agent.p09-native-diagnostic-controller/v11",
     index=step.index,before=step.before,run=1,base_step_pin=step.pin,component_pins=COMPONENT_PINS,
     component_qualification_pins=COMPONENT_QUAL_PINS,actual149_pin=ACTUAL149_PIN,actual143_pin=ACTUAL143_PIN),
     "EXACT_CURRENT_STEP_AND_PASSED148")
    M.a.exact(row["prior_v10_data_pin"]["path"],OLD10.data_path(step.index),"ORIGINAL_DATA010")
    M.a.exact(row["qualification_pin"]["path"],QUAL_PATH,"EXACT_CODE6")
    require(set(M.base.scope.pins(row["controller_code_pins"],2))=={SELF,TEST},"CONTROLLER_CODE2")
    data_path(step.index)
    return row


def own_inputs(q):
    OLD10.own_inputs(q)
    row=validate_data(json.loads(q.text(data_path(M.base.CONFIG.index)),object_pairs_hook=M.base.unique),M.base.CONFIG)
    M.a.exact(q.snapshots[OLD10.data_path(M.base.CONFIG.index)],row["prior_v10_data_pin"],"ORIGINAL_DATA010_BYTES")
    for pin in COMPONENT_QUAL_PINS:
        qualified=M.a.read_exact(q,pin)
        require(qualified["state"].startswith("PASS_") and qualified["cleanup_confirmed"] is True,"QUALIFIED_COMPONENT")
    qual=M.a.read_exact(q,row["qualification_pin"])
    M.a.fields(qual,dict(state=QUAL_STATE,contracts=dict(run=6,errors=0,failures=0,skipped=0),
     cleanup_confirmed=True,Native_product_or_acceptance_executed=False),"CODE6_NOT_PRODUCT")
    M.a.exact(qual["new_code_pins"],row["controller_code_pins"],"EXACT_CURRENT_TESTED_CONTROLLER2")
    M.a.exact(qual["component_pins"],COMPONENT_PINS,"ALL_QUALIFIED_COMPONENTS")
    for pin in row["controller_code_pins"]+COMPONENT_PINS+[OLD10_PIN,OLD10_TEST_PIN]:
        M.a.exact(q.pin(pin["path"]),pin,"ALL_NAMESPACE_SOURCES_CURRENT")
    ar=M.a.read_exact(q,ACTUAL143_PIN)
    M.a.fields(ar,dict(accepted_count_after=143,next_runtime_index=150,accepted_test_indices=[149],
      resource_cleanup_confirmed=True,P09_gate="OPEN"),"TRUE148_ACCEPTED_ONCE_NOT_GATE")
    M.a.exact(ar["runtime_candidate_pin"],ACTUAL149_PIN,"SAME_EXECUTED148")
    return row


def validator(source,ctx,flat=True):
    fn,proof=OLD10.validator(source,ctx,flat)
    fn.__globals__["CONTROLLERS"]=tuple(dict.fromkeys(fn.__globals__["CONTROLLERS"]+(SELF,TEST)))
    return fn,dict(proof,both_observer_connections_inside_whole_source_scope=True)


def context(step):
    return NS(**{**vars(OLD10.context(step)),"SELF":SELF,"TEST":TEST})


def template():
    engine,proof=OLD10.template()
    engine.run_owned.__globals__.update(SELF=SELF,TEST=TEST,native=NATIVE)
    engine.worker.__globals__.update(SELF=SELF,TEST=TEST,native=NATIVE)
    return engine,dict(proof,original_engine_unchanged_with_both_diagnostic_connections=True)


def previous_function(index):
    fn=M.V3.OLD.API.previous_validation
    require(type(index) is int and index>=147,"NATIVE_PREDECESSOR_INDEX")
    use_validator=OLD10.OLD9.OLD8.validator if index==147 else OLD10.OLD9.validator if index==148 else OLD10.validator if index==149 else validator
    use_context=OLD10.OLD9.OLD8.context if index==147 else OLD10.OLD9.context if index==148 else OLD10.context if index==149 else context
    return FunctionType(fn.__code__,dict(fn.__globals__,source=CURRENT_SOURCE,
      validator=use_validator,context=use_context),argdefs=fn.__defaults__,closure=fn.__closure__)


def previous_validation(q,row,listing,oldbody,fresh,oldctx,flat=True):
    if oldctx.INDEX<=146:return OLD10.previous_validation(q,row,listing,oldbody,fresh,oldctx,flat)
    if oldctx.INDEX==149:
        require(M.base.CONFIG.index==150,"ONLY_NEXT150_AFTER_REAL149")
        M.a.exact(M.base.CONFIG.prior_candidate_pin,ACTUAL149_PIN,"EXACT_149_PREDECESSOR_PIN")
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
    for required in [pin,value["qualification_pin"],OLD10_PIN,OLD10_TEST_PIN,
                     ACTUAL149_PIN,ACTUAL143_PIN]+value["controller_code_pins"]+COMPONENT_PINS+COMPONENT_QUAL_PINS:
        M.a.exact(expected.get(required["path"]),required,"ALL_NEW_DATA_SOURCE_AND_CUTOVER_PINS_IN_NATIVE")
    return expected


_family=OLD10._full_prepare.__globals__;_env=dict(_family)
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
    fn=OLD10.preflight_projection(data,leaf);old=fn.__code__
    require(sum(type(x) is str and x=="-native-diagnostic-preflight010.v1.json" for x in old.co_consts)==1,
      "ONE_NEW_PREFLIGHT_DESTINATION")
    constants=tuple("-native-diagnostic-preflight011.v1.json" if type(x) is str and
      x=="-native-diagnostic-preflight010.v1.json" else x for x in old.co_consts)
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
        value=str(error) if isinstance(error,ValueError) and re.fullmatch("[A-Z0-9_]{1,256}",str(error)) else "REDACTED_V11_FAILURE"
        print(json.dumps(dict(state="FAILED_NOT_ACCEPTED",error_code=value)))
        raise SystemExit(2) from None
