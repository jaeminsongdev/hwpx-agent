"""Successor uses fixed namespace connection; recorded legacy146 is never replayed.

V6 remains immutable/FAILED as a NO_PDH product connection. Full original
run/prepare/oracle bytecodes, DATA004 postchecks and all current DATA pins stay.
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
from types import FunctionType, MappingProxyType, SimpleNamespace as NS
import unittest

import flat_preserved129_lean_connection_v2 as lean

SELF="tools/p09/flat_current_queue_native_diagnostic_runtime_v8.py"
TEST="tools/p09/tests/test_flat_current_queue_native_diagnostic_runtime_v8.py"
QUAL_PATH="implementation/p09/evidence/p09-361-case147-native-namespace-controller-code2-r454b.v1.json"
BASE_PIN=dict(path="tools/p09/flat_current_queue_native_diagnostic_runtime_v6.py",bytes=13024,
 sha256="7714307688dc7aac46179f5eaedb702ec9e6fdccf169bde6260979190d520099")
FIX_PINS=[dict(path="tools/p09/native_diagnostic_connection_v2.py",bytes=4302,
 sha256="ed575f0e2dd261711bbf1e3ead228583cccb26316b22046a4db2db7a707a2f1b"),
 dict(path="tools/p09/tests/test_native_diagnostic_connection_v2.py",bytes=5477,
 sha256="879b758218f55f8302207b198b7fdda639dae33aaf1ed42436657e220e41a348")]
FIX_QUAL=dict(path="implementation/p09/evidence/p09-361-case146-native-namespace-regression9-r448.v1.json",
 bytes=3057,sha256="50e534d0716f27d1b420d0a62a8f5d0702ea207aef80594970385fc382c7504d")
LEGACY146_PIN=dict(path="implementation/p09/evidence/p09-361-case146-current-runtime-run001.v1.json",
 bytes=2714708,sha256="4cd6e3e67e157521b7353af62a3d09503813acd80cbb614d3189ac3ef1dd3234")
LEGACY146_AUTH=dict(path="implementation/p09/evidence/p09-361-case146-current-epoch-accept001.v1.json",
 bytes=321292,sha256="a099d2c03b48353e5b7c64ff46e664a6d3ec0127d73990a98a73854ba191162a")


def require(ok,code):
    if not ok:raise ValueError("NATIVE_NAMESPACE_CONTROLLER_V8_"+code)


def exact_raw(pin):
    lean.base.stable.stable.prior.build.direct_path(lean.c.ROOT/pin["path"],file_required=True)
    with (lean.c.ROOT/pin["path"]).open("rb") as stream:raw=stream.read(pin["bytes"]+1)
    require(len(raw)==pin["bytes"] and hashlib.sha256(raw).hexdigest()==pin["sha256"],"EXACT_NAMESPACE_SOURCE")
    return raw


def load_base():
    raw=exact_raw(BASE_PIN);tree=ast.parse(raw.decode("utf-8"))
    def selected(node):
        return isinstance(node,(ast.Assign,ast.FunctionDef,ast.ClassDef,ast.For)) or (
         isinstance(node,ast.Expr) and isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Attribute)
         and isinstance(node.value.func.value,ast.Name) and node.value.func.value.id=="_env")
    originals=[n for n in tree.body if selected(n)];nodes=copy.deepcopy(originals)
    require([ast.dump(n,include_attributes=False) for n in nodes]==
            [ast.dump(n,include_attributes=False) for n in originals],"ALL_BASE_DEFINITIONS_AND_INITIALIZATION")
    env=dict(lean=lean,argparse=argparse,ast=ast,copy=copy,ctypes=ctypes,w=w,contextmanager=contextmanager,
     hashlib=hashlib,json=json,math=math,os=os,Path=Path,re=re,sys=sys,threading=threading,time=time,
     FunctionType=FunctionType,MappingProxyType=MappingProxyType,NS=NS,unittest=unittest,
     __name__="p09_exact_v6_for_v7",__file__=BASE_PIN["path"])
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),BASE_PIN["path"],"exec"),env)
    return NS(**env)


BASE=load_base()
M=BASE.M
CONNECTION=BASE.namespace(exact_raw(FIX_PINS[0]),FIX_PINS[0],
                         dict(prior=BASE.CONNECTION,Path=Path,FunctionType=FunctionType,NS=NS))
BACKEND=BASE.BACKEND


def data_path(index):
    require(type(index) is int and 147<=index<=249,"NO_SUCCESSFUL146_REPLAY")
    return f"implementation/p09/evidence/p09-361-case{index}-native-diagnostic-data008.v1.json"


def validate_data(row,step):
    require(type(row) is dict and set(row)=={"schema_version","index","before","run","base_step_pin",
     "prior_v6_data_pin","qualification_pin","controller_code_pins","namespace_fix_code_pins","namespace_fix_qualification_pin",
     "recorded_legacy146_pin","recorded_legacy146_authority_pin"},"CLOSED_DATA007")
    M.a.fields(row,dict(schema_version="hwpx-agent.p09-native-diagnostic-controller/v8",index=step.index,
     before=step.before,run=1,base_step_pin=step.pin,namespace_fix_code_pins=FIX_PINS,
     namespace_fix_qualification_pin=FIX_QUAL,recorded_legacy146_pin=LEGACY146_PIN,
     recorded_legacy146_authority_pin=LEGACY146_AUTH),"EXACT_CURRENT_STEP_AND_RECORDED_CUTOVER")
    M.a.exact(row["prior_v6_data_pin"]["path"],BASE.data_path(step.index),"ENTIRE_BASE_DATA006")
    M.a.exact(row["qualification_pin"]["path"],QUAL_PATH,"EXACT_CODE9")
    require(set(M.base.scope.pins(row["controller_code_pins"],2))=={SELF,TEST},"CODE2")
    data_path(step.index)
    return row


def own_inputs(q):
    BASE.own_inputs(q)
    row=validate_data(json.loads(q.text(data_path(M.base.CONFIG.index)),object_pairs_hook=M.base.unique),M.base.CONFIG)
    M.a.exact(q.snapshots[BASE.data_path(M.base.CONFIG.index)],row["prior_v6_data_pin"],"ALL_ORIGINAL_DATA006")
    fix=M.a.read_exact(q,FIX_QUAL)
    M.a.fields(fix,dict(state="PASS_NATIVE_NAMESPACE_V2_REGRESSION9_REAL_WRAPPERS_WITH_INTERCEPTED_ENTRY_NOT_PRODUCT",
      contracts=dict(run=9,errors=0,failures=0,skipped=0),cleanup_confirmed=True,
      actual_Native_or_product_or_PDH_observer_executed=False),"REAL_NAMESPACE_REGRESSION9")
    qual=M.a.read_exact(q,row["qualification_pin"])
    M.a.fields(qual,dict(state="PASS_NATIVE_V8_NO_EXTRA_ROOT_ACQUISITION_CODE2_NOT_PRODUCT",
      contracts=dict(run=2,errors=0,failures=0,skipped=0),cleanup_confirmed=True,
      actual_Native_product_controller_executed=False),"CODE9_NOT_PRODUCT")
    M.a.exact(qual["new_code_pins"],row["controller_code_pins"],"CURRENT_QUALIFIED_CONTROLLER2")
    for pin in row["controller_code_pins"]+FIX_PINS+[BASE_PIN]:
        M.a.exact(q.pin(pin["path"]),pin,"ALL_CURRENT_SOURCE_BYTES")
    old=M.a.read_exact(q,LEGACY146_AUTH)
    M.a.fields(old,dict(accepted_count_after=140,next_runtime_index=147,accepted_test_indices=[146],
      resource_cleanup_confirmed=True,P09_gate="OPEN"),"TRUE_LEGACY146_ACCEPTANCE_NOT_NEW_BACKEND")
    M.a.exact(old["runtime_candidate_pin"],LEGACY146_PIN,"SAME_LEGACY146_ROOT")
    return row


def validator(raw,ctx,flat=True):
    fn,proof=BASE.validator(raw,ctx,flat)
    fn.__globals__["CONTROLLERS"]=tuple(dict.fromkeys(fn.__globals__["CONTROLLERS"]+(SELF,TEST)))
    return fn,dict(proof,v7_namespace_source_pins_inside_whole_scope=True)


def context(step):
    return NS(**{**vars(BASE.context(step)),"SELF":SELF,"TEST":TEST})


def template():
    engine,proof=BASE.template()
    engine.run_owned.__globals__.update(SELF=SELF,TEST=TEST)
    engine.worker.__globals__.update(SELF=SELF,TEST=TEST)
    return engine,dict(proof,namespace_fix_connection_required_before_product=True)


def legacy146_previous_function():
    fn=M.V3.OLD.API.previous_validation
    return FunctionType(fn.__code__,dict(fn.__globals__,
      source=M.API.prepare.__globals__["source"],validator=BASE.validator,context=BASE.context),
      argdefs=fn.__defaults__,closure=fn.__closure__)


def previous_validation(q,row,listing,oldbody,fresh,oldctx,flat=True):
    if oldctx.INDEX<=145:return BASE.previous_validation(q,row,listing,oldbody,fresh,oldctx,flat)
    if oldctx.INDEX==146:
        require(M.base.CONFIG.index==147,"ONLY_EXACT_LEGACY146_PREDECESSOR")
        M.a.exact(M.base.CONFIG.prior_candidate_pin,LEGACY146_PIN,"EXACT_LEGACY_PREDECESSOR_PIN")
        M.a.exact(row,M.a.read_exact(q,LEGACY146_PIN),"ORIGINAL_LEGACY_ROW_NOT_REBASED")
        require(row["serial_CPU_attribution"].get("backend") is None,"ACTUAL_LEGACY_FORMAT")
        return legacy146_previous_function()(q,row,listing,oldbody,fresh,oldctx,flat)
    original=M.V3.OLD.API.previous_validation
    source=BASE.API.prepare.__globals__["source"]
    return FunctionType(original.__code__,dict(original.__globals__,source=source,validator=validator,context=context),
      argdefs=original.__defaults__,closure=original.__closure__)(q,row,listing,oldbody,fresh,oldctx,flat)


def binding(q):
    pin,raw=q._read(M.V3.OLD.API.BASE_PIN["path"],parse=True);q._bind(pin["path"],pin)
    M.a.exact(pin,M.V3.OLD.API.BASE_PIN,"ORIGINAL_BINDING_CODE")
    fn,_=M.V3.OLD.API.binding_projection(bytes(raw),replacement=previous_validation)
    return fn(q)


def native_scope(q,row):
    pin=q.snapshots[data_path(M.base.CONFIG.index)]
    value=validate_data(M.a.read_exact(q,pin),M.base.CONFIG)
    expected=M.base.scope.pins(row["source_freeze"])
    for required in [pin,value["qualification_pin"],FIX_QUAL,BASE_PIN,LEGACY146_PIN,LEGACY146_AUTH]+value["controller_code_pins"]+FIX_PINS:
        M.a.exact(expected.get(required["path"]),required,"ALL_NEW_COMPONENT_DATA_AND_CUTOVER_IN_NATIVE")
    return expected


_family=BASE.API.prepare.__globals__;_env=dict(_family)
for _name,_fn in tuple(_env.items()):
    if type(_fn) is FunctionType and _fn.__globals__ is _family:
        _env[_name]=FunctionType(_fn.__code__,_env,argdefs=_fn.__defaults__,closure=_fn.__closure__)
_env.update(SELF=SELF,TEST=TEST,FILES=(SELF,TEST),QUAL_PATH=QUAL_PATH,own_inputs=own_inputs,
 template=template,validator=validator,context=context,binding=binding,previous_validation=previous_validation,
 data_path=M.data_path,validate_data=M.validate_data)
API=NS(**_env)
_full_prepare=API.prepare


def prepare(q,pin):
    result=_full_prepare(q,pin)
    native_scope(q,result[0])
    return result


API.prepare=prepare
API.original_run_owned=API.run_owned


def run_owned(run):
    data_path(M.base.CONFIG.index);require(run==1,"FIRST_EXPLICIT_ONLY")
    execute,state=CONNECTION.connect_run(API.original_run_owned,BACKEND)
    code=execute(run)
    require(state["actual_local_bindings"]==1,"ACTUAL_ONE_NATIVE_LOCAL_CONNECTION")
    return code


def preflight_projection(raw,leaf):
    fn=BASE.preflight_projection(raw,leaf);old=fn.__code__
    require(sum(type(x) is str and x=="-native-diagnostic-preflight006.v1.json" for x in old.co_consts)==1,
      "ONE_PREFLIGHT_DESTINATION")
    constants=tuple("-native-diagnostic-preflight008.v1.json" if type(x) is str and
      x=="-native-diagnostic-preflight006.v1.json" else x for x in old.co_consts)
    code=old.replace(co_consts=constants)
    require(code.replace(co_consts=old.co_consts)==old,"ALL_ORIGINAL_PREFLIGHT_BYTECODE_AND_TEST10")
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
        value=str(error) if isinstance(error,ValueError) and re.fullmatch("[A-Z0-9_]{1,256}",str(error)) else "REDACTED_V7_FAILURE"
        print(json.dumps(dict(state="FAILED_NOT_ACCEPTED",error_code=value)))
        raise SystemExit(2) from None

