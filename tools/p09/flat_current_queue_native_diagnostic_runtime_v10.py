"""Native V3 bounded measurement and explicit historical V2 controller for149+.

Original run/prepare/candidate bytecodes, old148 executed context, all DATA004
postchecks, sole sampler/limits/two byte passes/cleanup and historical failures
remain. Old controllers/receipts are immutable. No successful147/148 replay.
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

SELF="tools/p09/flat_current_queue_native_diagnostic_runtime_v10.py"
TEST="tools/p09/tests/test_flat_current_queue_native_diagnostic_runtime_v10.py"
QUAL_PATH="implementation/p09/evidence/p09-361-case149-native3-controller-code6-r478.v1.json"
OLD9_PIN=dict(path="tools/p09/flat_current_queue_native_diagnostic_runtime_v9.py",bytes=12462,
 sha256="6a341749c7d530cdb9e5ddc2da6bd29fbfe9780f333a2959ea3e26ffe87a7601")
OLD9_TEST_PIN=dict(path="tools/p09/tests/test_flat_current_queue_native_diagnostic_runtime_v9.py",bytes=4217,
 sha256="08f9c81c82240df532dba8a2da03d92e8503194ce497597dd9c4d2041d74b6f3")
COMPONENT_PINS=[{"path":"tools/p09/bounded_cpu_attribution_probe_v2.py","bytes":3385,"sha256":"4a1d3c2a7d912df5019c9d28df9a43deffff0682d2100682f1b734350114e5c6"},{"path":"tools/p09/tests/test_bounded_cpu_attribution_probe_v2.py","bytes":3450,"sha256":"63781c19ab65fb17773eefdc920ea200abca1090e9d2480005106e9bd15e1d9d"},{"path":"tools/p09/native_process_cpu_attribution_v3.py","bytes":3288,"sha256":"6448d4fdccb0d69d717986d174296ed5b2bd4894b20043c94ec80977fd57ddd3"},{"path":"tools/p09/tests/test_native_process_cpu_attribution_v3.py","bytes":3364,"sha256":"e3e8442b6e0ccb04e791b88abde2905975daa835b5f01552366290c416d027d5"},{"path":"tools/p09/native_diagnostic_connection_v3.py","bytes":3023,"sha256":"566fe3b4732f59410171154e513d608cbabf9b5c500b074d183aa07046f5b1e4"},{"path":"tools/p09/tests/test_native_diagnostic_connection_v3.py","bytes":3730,"sha256":"0d181c33fd6c59ab70c2643ab9d0cde86761ac17d0d7d02fe249c7fb628b175d"},{"path":"tools/p09/native_diagnostic_oracle_connection_v2.py","bytes":2869,"sha256":"b16be1b013dea0a7176e1717a22f05d5b76278cd245da657cf455ad85dee40e6"},{"path":"tools/p09/tests/test_native_diagnostic_oracle_connection_v2.py","bytes":2789,"sha256":"243889a93a78668ef9f287d681a9eb51638bb37f12669cca0b455f6ce5a42ebb"}]
COMPONENT_QUAL_PINS=[{"path":"implementation/p09/evidence/p09-361-case148-capture-midbudget-scratch-code6-r469.v1.json","bytes":2324,"sha256":"01f7fc82246f083a18eed64ef42401142d5825fdcd8f851f0c82f44f78fd0a18"},{"path":"implementation/p09/evidence/p09-361-case149-native-probe3-code6-r473.v1.json","bytes":2525,"sha256":"db6f2b30f8928b11ad12e5cbdc0aa26000c695af6a91de28c0ad7b5261b4b867"},{"path":"implementation/p09/evidence/p09-361-case149-native-connection3-code6-r474.v1.json","bytes":2524,"sha256":"245fe20ecf8e7ebeb571481710298bafbb18e0d4de13ea6e8d5c627da0cd838a"},{"path":"implementation/p09/evidence/p09-361-case149-native3-local-single-observer-live-r475.v1.json","bytes":6544,"sha256":"3329ead222cf5ed65a1c3222e64a860c50df77870c2ec8b460bbe92c596b45e0"},{"path":"implementation/p09/evidence/p09-361-case149-native-versioned-oracle-code6-r476.v1.json","bytes":2528,"sha256":"08c752f1fc132f97e1d36f46f362de1887bfe980628e470d6962fdc9bb78ec5e"}]
ACTUAL148_PIN={"path":"implementation/p09/evidence/p09-361-case148-current-runtime-run001.v1.json","bytes":2872655,"sha256":"652e29e299d3290a7044c77d41ee871d4c23ec1f1566f6f36752b28c2c3ad954"}
ACTUAL142_PIN={"path":"implementation/p09/evidence/p09-361-case148-current-epoch-accept001.v1.json","bytes":323013,"sha256":"0b87d93e9b3794af7b5ecc726f3836a854e5511f629f607923f9a76c8d68d3b7"}
QUAL_STATE="PASS_NATIVE_V10_VERSIONED_FULL_CONTROLLER_CODE6_NOT_PRODUCT"


def require(ok,code):
    if not ok:raise ValueError("NATIVE_BOTH_OBSERVER_V10_"+code)


def raw(pin):
    lean.base.stable.stable.prior.build.direct_path(lean.c.ROOT/pin["path"],file_required=True)
    with (lean.c.ROOT/pin["path"]).open("rb") as stream:data=stream.read(pin["bytes"]+1)
    require(len(data)==pin["bytes"] and hashlib.sha256(data).hexdigest()==pin["sha256"],"EXACT_NAMESPACE_BYTES")
    return data


def load_old9():
    source=raw(OLD9_PIN);tree=ast.parse(source.decode("utf-8"))
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
     __name__="p09_exact_old9_namespace",__file__=OLD9_PIN["path"])
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),OLD9_PIN["path"],"exec"),env)
    return NS(**env)


OLD9=load_old9()
M=OLD9.M
def component(name,env):
    pin=next(p for p in COMPONENT_PINS if p["path"].endswith("/"+name))
    return OLD9.OLD8.BASE.namespace(raw(pin),pin,env)
CAPTURE=component("bounded_cpu_attribution_probe_v2.py",dict(ctypes=ctypes,time=time,prior=OLD9.BACKEND.prior.native))
BACKEND=component("native_process_cpu_attribution_v3.py",dict(math=math,os=os,threading=threading,time=time,
 NS=NS,prior=OLD9.BACKEND,native=CAPTURE))
CONNECTION=component("native_diagnostic_connection_v3.py",dict(math=math,FunctionType=FunctionType,prior=OLD9.CONNECTION))
ORACLE=component("native_diagnostic_oracle_connection_v2.py",dict(FunctionType=FunctionType,NS=NS,
 prior=OLD9.OLD8.BASE.ORACLE,diagnostic=CONNECTION,additional=OLD9.ADDITIONAL))
original_source=OLD9._full_prepare.__globals__["source"]
linked_candidate,ORACLE_PROOF=ORACLE.connect_full(original_source.validate_candidate,
 M.source.prior.accepted.original.candidate,M.V3.ORACLE)
CURRENT_SOURCE=NS(**{**vars(original_source),"validate_candidate":linked_candidate})


def data_path(index):
    require(type(index) is int and 149<=index<=249,"NO_SUCCESSFUL_CASE_REPLAY")
    return f"implementation/p09/evidence/p09-361-case{index}-native-diagnostic-data010.v1.json"


def validate_data(row,step):
    require(type(row) is dict and set(row)=={"schema_version","index","before","run","base_step_pin",
     "prior_v9_data_pin","qualification_pin","controller_code_pins","component_pins","component_qualification_pins",
     "actual148_pin","actual142_pin"},"CLOSED_DATA010")
    M.a.fields(row,dict(schema_version="hwpx-agent.p09-native-diagnostic-controller/v10",
     index=step.index,before=step.before,run=1,base_step_pin=step.pin,component_pins=COMPONENT_PINS,
     component_qualification_pins=COMPONENT_QUAL_PINS,actual148_pin=ACTUAL148_PIN,actual142_pin=ACTUAL142_PIN),
     "EXACT_CURRENT_STEP_AND_PASSED148")
    M.a.exact(row["prior_v9_data_pin"]["path"],OLD9.data_path(step.index),"ORIGINAL_DATA009")
    M.a.exact(row["qualification_pin"]["path"],QUAL_PATH,"EXACT_CODE6")
    require(set(M.base.scope.pins(row["controller_code_pins"],2))=={SELF,TEST},"CONTROLLER_CODE2")
    data_path(step.index)
    return row


def own_inputs(q):
    OLD9.own_inputs(q)
    row=validate_data(json.loads(q.text(data_path(M.base.CONFIG.index)),object_pairs_hook=M.base.unique),M.base.CONFIG)
    M.a.exact(q.snapshots[OLD9.data_path(M.base.CONFIG.index)],row["prior_v9_data_pin"],"ORIGINAL_DATA009_BYTES")
    for pin in COMPONENT_QUAL_PINS:
        qualified=M.a.read_exact(q,pin)
        require(qualified["state"].startswith("PASS_") and qualified["cleanup_confirmed"] is True,"QUALIFIED_COMPONENT")
    qual=M.a.read_exact(q,row["qualification_pin"])
    M.a.fields(qual,dict(state=QUAL_STATE,contracts=dict(run=6,errors=0,failures=0,skipped=0),
     cleanup_confirmed=True,Native_product_or_acceptance_executed=False),"CODE6_NOT_PRODUCT")
    M.a.exact(qual["new_code_pins"],row["controller_code_pins"],"EXACT_CURRENT_TESTED_CONTROLLER2")
    M.a.exact(qual["component_pins"],COMPONENT_PINS,"ALL_QUALIFIED_COMPONENTS")
    for pin in row["controller_code_pins"]+COMPONENT_PINS+[OLD9_PIN,OLD9_TEST_PIN]:
        M.a.exact(q.pin(pin["path"]),pin,"ALL_NAMESPACE_SOURCES_CURRENT")
    ar=M.a.read_exact(q,ACTUAL142_PIN)
    M.a.fields(ar,dict(accepted_count_after=142,next_runtime_index=149,accepted_test_indices=[148],
      resource_cleanup_confirmed=True,P09_gate="OPEN"),"TRUE148_ACCEPTED_ONCE_NOT_GATE")
    M.a.exact(ar["runtime_candidate_pin"],ACTUAL148_PIN,"SAME_EXECUTED148")
    return row


def validator(source,ctx,flat=True):
    fn,proof=OLD9.validator(source,ctx,flat)
    fn.__globals__["CONTROLLERS"]=tuple(dict.fromkeys(fn.__globals__["CONTROLLERS"]+(SELF,TEST)))
    return fn,dict(proof,both_observer_connections_inside_whole_source_scope=True)


def context(step):
    return NS(**{**vars(OLD9.context(step)),"SELF":SELF,"TEST":TEST})


def template():
    engine,proof=OLD9.template()
    engine.run_owned.__globals__.update(SELF=SELF,TEST=TEST)
    engine.worker.__globals__.update(SELF=SELF,TEST=TEST)
    return engine,dict(proof,original_engine_unchanged_with_both_diagnostic_connections=True)


def previous_function(index):
    fn=M.V3.OLD.API.previous_validation
    require(type(index) is int and index>=147,"NATIVE_PREDECESSOR_INDEX")
    use_validator=OLD9.OLD8.validator if index==147 else OLD9.validator if index==148 else validator
    use_context=OLD9.OLD8.context if index==147 else OLD9.context if index==148 else context
    return FunctionType(fn.__code__,dict(fn.__globals__,source=CURRENT_SOURCE,
      validator=use_validator,context=use_context),argdefs=fn.__defaults__,closure=fn.__closure__)


def previous_validation(q,row,listing,oldbody,fresh,oldctx,flat=True):
    if oldctx.INDEX<=146:return OLD9.previous_validation(q,row,listing,oldbody,fresh,oldctx,flat)
    if oldctx.INDEX==148:
        require(M.base.CONFIG.index==149,"ONLY_NEXT149_AFTER_REAL148")
        M.a.exact(M.base.CONFIG.prior_candidate_pin,ACTUAL148_PIN,"EXACT_148_PREDECESSOR_PIN")
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
    for required in [pin,value["qualification_pin"],OLD9_PIN,OLD9_TEST_PIN,
                     ACTUAL148_PIN,ACTUAL142_PIN]+value["controller_code_pins"]+COMPONENT_PINS+COMPONENT_QUAL_PINS:
        M.a.exact(expected.get(required["path"]),required,"ALL_NEW_DATA_SOURCE_AND_CUTOVER_PINS_IN_NATIVE")
    return expected


_family=OLD9._full_prepare.__globals__;_env=dict(_family)
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
    fn=OLD9.preflight_projection(data,leaf);old=fn.__code__
    require(sum(type(x) is str and x=="-native-diagnostic-preflight009.v1.json" for x in old.co_consts)==1,
      "ONE_NEW_PREFLIGHT_DESTINATION")
    constants=tuple("-native-diagnostic-preflight010.v1.json" if type(x) is str and
      x=="-native-diagnostic-preflight009.v1.json" else x for x in old.co_consts)
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
        value=str(error) if isinstance(error,ValueError) and re.fullmatch("[A-Z0-9_]{1,256}",str(error)) else "REDACTED_V10_FAILURE"
        print(json.dumps(dict(state="FAILED_NOT_ACCEPTED",error_code=value)))
        raise SystemExit(2) from None
