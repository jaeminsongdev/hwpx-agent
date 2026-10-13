"""NO_PDH product controller; full original v4 statements and helper ceiling retained.

No full v4/new-diagnostic module import, sys.modules hiding, source omission,
legacy provenance forgery, deadline/rate extension, body replay or queue write.
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

SELF = "tools/p09/flat_current_queue_native_diagnostic_runtime_v5.py"
TEST = "tools/p09/tests/test_flat_current_queue_native_diagnostic_runtime_v5.py"
QUAL_PATH = "implementation/p09/evidence/p09-361-case146-native-controller-code-r443.v1.json"
FIXED_PINS = [{"path":"tools/p09/flat_current_queue_direct_view_runtime_v4.py","bytes":13522,"sha256":"8a47181b47f67667aecd3456207003ef1a4159778f88736940e86f74bf1f656f"},{"path":"tools/p09/native_diagnostic_connection_v1.py","bytes":14705,"sha256":"8bcc39efed0f396fc0fd9063efaad31bff5aa26aefba21d150408841af988d2c"},{"path":"tools/p09/tests/test_native_diagnostic_connection_v1.py","bytes":8380,"sha256":"6e4d776d7c1d163eb5d5e287257000ec1feec44ff94c2ed2f851c8995af980c7"},{"path":"tools/p09/native_diagnostic_oracle_connection_v1.py","bytes":2968,"sha256":"12cfd1a1854843389fbe1346bc20021e181dac6ec9840bb7a099c589458ff189"},{"path":"tools/p09/tests/test_native_diagnostic_oracle_connection_v1.py","bytes":3838,"sha256":"99ff6946ee2c18f2bf0802159d90043046d1a3cde7db501ece811fdc9318e27b"},{"path":"tools/p09/native_process_cpu_attribution_v2.py","bytes":1995,"sha256":"d5b96c013f1a938e53c92982a3e45a55eca91456d3c1bb9b7e1400820407dfd9"},{"path":"tools/p09/tests/test_native_process_cpu_attribution_v2.py","bytes":2664,"sha256":"e8c0fc99e76c1cf34240d60ddd8b64b57e3be230d49f91209a2228518ba27fcd"},{"path":"tools/p09/native_process_cpu_attribution_v1.py","bytes":8147,"sha256":"0dab3c419566dafb4678b6fcacde82c8d6484ef811e97ba84e48b8eed7851b5c"},{"path":"tools/p09/tests/test_native_process_cpu_attribution_v1.py","bytes":4983,"sha256":"b1fc80f8abe8d73dbbd5517e53c39ed17d2bf3a27dd2d8732f3f59a4f14ac372"},{"path":"tools/p09/bounded_cpu_attribution_probe_v1.py","bytes":7944,"sha256":"784e55884f10673fbbe7e12611be821b4cee255773b89972b3144473c6e2f9dc"},{"path":"tools/p09/tests/test_bounded_cpu_attribution_probe_v1.py","bytes":2800,"sha256":"b03ebc6594d2b24e490c1d64f88d5c56f08226119a3e18feb2e7d8a489385d46"}]
PINS = {pin["path"]:pin for pin in FIXED_PINS}
M = CONNECTION = ORACLE = BACKEND = API = None


def require(ok, code):
    if not ok:
        raise ValueError("NATIVE_CONTROLLER_V5_" + code)


def raw(pin):
    lean.base.stable.stable.prior.build.direct_path(lean.c.ROOT/pin["path"],file_required=True)
    with (lean.c.ROOT/pin["path"]).open("rb") as stream:
        data=stream.read(pin["bytes"]+1)
    require(len(data)==pin["bytes"] and hashlib.sha256(data).hexdigest()==pin["sha256"],"EXACT_BOOTSTRAP_BYTES")
    return data


def namespace(data, pin, environment, initialize=False):
    require(type(data) is bytes and len(data)==pin["bytes"] and hashlib.sha256(data).hexdigest()==pin["sha256"],"EXACT_NAMESPACE_BYTES")
    tree=ast.parse(data.decode("utf-8"))
    def selected(node):
        return isinstance(node,(ast.Assign,ast.FunctionDef,ast.ClassDef)) or (
            initialize and (isinstance(node,ast.For) or isinstance(node,ast.Expr) and isinstance(node.value,ast.Call)
            and isinstance(node.value.func,ast.Attribute) and isinstance(node.value.func.value,ast.Name)
            and node.value.func.value.id=="_env" and node.value.func.attr=="update"))
    source=[n for n in tree.body if selected(n)];nodes=copy.deepcopy(source)
    require([ast.dump(n,include_attributes=False) for n in nodes]==[ast.dump(n,include_attributes=False) for n in source],"ALL_NAMESPACE_AST_RETAINED")
    env={**environment,"__name__":"p09_exact_native_v5_namespace","__file__":pin["path"]}
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),pin["path"],"exec"),env)
    return NS(**env)


def bootstrap():
    env=dict(lean=lean,argparse=argparse,ast=ast,copy=copy,ctypes=ctypes,w=w,contextmanager=contextmanager,
             hashlib=hashlib,json=json,re=re,sys=sys,threading=threading,FunctionType=FunctionType,
             MappingProxyType=MappingProxyType,NS=NS,unittest=unittest)
    v4pin=PINS["tools/p09/flat_current_queue_direct_view_runtime_v4.py"]
    v4=namespace(raw(v4pin),v4pin,env,True)
    cp=PINS["tools/p09/native_diagnostic_connection_v1.py"]
    connection=namespace(raw(cp),cp,dict(ast=ast,copy=copy,hashlib=hashlib,math=math,Path=Path,FunctionType=FunctionType,NS=NS))
    hp=PINS["tools/p09/bounded_cpu_attribution_probe_v1.py"]
    helper=namespace(raw(hp),hp,dict(ctypes=ctypes,w=w,json=json,math=math,os=os,time=time,runtime=v4))
    bp=PINS["tools/p09/native_process_cpu_attribution_v1.py"]
    # Existing original observer module is already a dependency; never construct its PDH probe.
    legacy_observer=v4.source.prior.prior.prior.connection.original
    native1=namespace(raw(bp),bp,dict(math=math,os=os,threading=threading,time=time,native=helper,prior=legacy_observer))
    vp=PINS["tools/p09/native_process_cpu_attribution_v2.py"]
    backend=namespace(raw(vp),vp,dict(prior=native1))
    op=PINS["tools/p09/native_diagnostic_oracle_connection_v1.py"]
    oracle=namespace(raw(op),op,dict(Path=Path,FunctionType=FunctionType,NS=NS,diagnostic=connection))
    return v4,connection,oracle,backend


def data_path(index):
    require(type(index) is int and 146<=index<=249,"EXACT_SUCCESSOR_RANGE")
    return f"implementation/p09/evidence/p09-361-case{index}-native-diagnostic-data005.v1.json"


def validate_data(row,step):
    require(type(row) is dict and set(row)=={"schema_version","index","before","run","base_step_pin",
            "prior_v4_data_pin","qualification_pin","controller_code_pins","native_component_pins"},"CLOSED_DATA")
    M.a.fields(row,dict(schema_version="hwpx-agent.p09-native-diagnostic-controller/v5",index=step.index,
                       before=step.before,run=1,base_step_pin=step.pin),"EXACT_STEP")
    M.a.exact(row["prior_v4_data_pin"]["path"],M.data_path(step.index),"ALL_ORIGINAL_V4_DATA")
    M.a.exact(row["qualification_pin"]["path"],QUAL_PATH,"EXACT_CONTROLLER_QUAL")
    require(set(M.base.scope.pins(row["controller_code_pins"],2))=={SELF,TEST},"BOTH_NEW_CONTROLLER_FILES")
    M.a.exact(row["native_component_pins"],FIXED_PINS,"ALL_EXACT_TESTED_NAMESPACE_SOURCES")
    return row


def own_inputs(q):
    M.own_inputs(q)  # Original DATA10, qualification, code, archives and failed evidence checks.
    value=validate_data(json.loads(q.text(data_path(M.base.CONFIG.index)),object_pairs_hook=M.base.unique),M.base.CONFIG)
    M.a.exact(q.snapshots[M.data_path(M.base.CONFIG.index)],value["prior_v4_data_pin"],"ORIGINAL_V4_PIN")
    qual=M.a.read_exact(q,value["qualification_pin"])
    M.a.fields(qual,dict(state="PASS_NATIVE_V5_CONTROLLER_AND_FULL_NAMESPACE_CONTRACTS_NOT_PRODUCT",
                         cleanup_confirmed=True,actual_Native_product_controller_executed=False),"CONTROLLER_CODE_NOT_PRODUCT")
    M.a.exact(qual["new_code_pins"],value["controller_code_pins"],"QUALIFIED_CONTROLLER2")
    for pin in value["controller_code_pins"]+FIXED_PINS:
        M.a.exact(q.pin(pin["path"]),pin,"ALL_TESTED_NATIVE_CONTROLLER_SOURCES")
    return value


def validator(data,ctx,flat=True):
    result,proof=M.validator(data,ctx,flat)
    result.__globals__["CONTROLLERS"]=tuple(dict.fromkeys(result.__globals__["CONTROLLERS"]+(SELF,TEST)))
    return result,dict(proof,native_diagnostic_controller_inside_full_scope=True)


def context(step):
    return NS(**{**vars(M.context(step)),"SELF":SELF,"TEST":TEST})


def template():
    engine,proof=M.template()
    engine.run_owned.__globals__.update(SELF=SELF,TEST=TEST)
    engine.worker.__globals__.update(SELF=SELF,TEST=TEST)
    return engine,dict(proof,original_engine_and_direct_view_backend_unchanged=True,
                       native_diagnostic_optional_dependency_only=True)


def previous_validation(q,row,listing,oldbody,fresh,oldctx,flat=True):
    if oldctx.INDEX<=145:
        return M.previous_validation(q,row,listing,oldbody,fresh,oldctx,flat)
    # Same original scoped predecessor function, new diagnostic format dispatch only.
    original=M.V3.OLD.API.previous_validation
    connected=NS(**{**vars(M.source),"validate_candidate":ORACLE.connect_candidate(M.source.validate_candidate)[0]})
    env=dict(original.__globals__,source=connected,validator=validator,context=context)
    return FunctionType(original.__code__,env,argdefs=original.__defaults__)(q,row,listing,oldbody,fresh,oldctx,flat)


def binding(q):
    pin,value=q._read(M.V3.OLD.API.BASE_PIN["path"],parse=True);q._bind(pin["path"],pin)
    M.a.exact(pin,M.V3.OLD.API.BASE_PIN,"ORIGINAL_BINDING_CODE")
    fn,_=M.V3.OLD.API.binding_projection(bytes(value),replacement=previous_validation)
    return fn(q)


def run_owned(run):
    require(run==1,"FIRST_EXPLICIT_RUN_ONLY")
    execute,state=CONNECTION.connect_run(API.original_run_owned,BACKEND)
    code=execute(run)
    require(state["actual_local_bindings"]==1,"REAL_NATIVE_LOCAL_CONNECTION")
    return code


def preflight_projection(data,leaf):
    original=M.preflight_projection(data,leaf)
    old=original.__code__
    require(sum(type(item) is str and item=="-direct-view-preflight004.v1.json" for item in old.co_consts)==1,"ONE_PREFLIGHT_DESTINATION")
    constants=tuple("-native-diagnostic-preflight005.v1.json" if type(item) is str and item=="-direct-view-preflight004.v1.json" else item for item in old.co_consts)
    updated=old.replace(co_consts=constants)
    require(updated.replace(co_consts=old.co_consts)==old,"ALL_ORIGINAL_PREFLIGHT_TESTS_AND_BYTECODE")
    env=dict(original.__globals__,SELF=SELF,TEST=TEST,template=template,binding_attempt=API.binding_attempt,
             connection_data=own_inputs,own_inputs=own_inputs,data_path=data_path)
    return FunctionType(updated,env,argdefs=original.__defaults__)


def preflight():
    fn=M.V3.OLD.API.preflight
    return FunctionType(fn.__code__,dict(fn.__globals__,preflight_projection=preflight_projection),
                        argdefs=fn.__defaults__)()


M,CONNECTION,ORACLE,BACKEND=bootstrap()
_family=M.API.prepare.__globals__
_env=dict(_family)
for _name,_fn in tuple(_env.items()):
    if type(_fn) is FunctionType and _fn.__globals__ is _family:
        _env[_name]=FunctionType(_fn.__code__,_env,argdefs=_fn.__defaults__,closure=_fn.__closure__)
connected_source=NS(**{**vars(M.API.prepare.__globals__["source"]),
    "validate_candidate":ORACLE.connect_candidate(M.API.prepare.__globals__["source"].validate_candidate)[0]})
_env.update(SELF=SELF,TEST=TEST,FILES=(SELF,TEST),QUAL_PATH=QUAL_PATH,source=connected_source,
            own_inputs=own_inputs,validate_data=validate_data,data_path=data_path,validator=validator,
            context=context,template=template,binding=binding,previous_validation=previous_validation)
API=NS(**_env)
API.original_run_owned=API.run_owned

if __name__=="__main__":
    try:
        if len(sys.argv)==4 and sys.argv[1:3]==["--owned-worker","--task"]:
            M.base.configure(M.base.task_index(sys.argv[3]));raise SystemExit(API.worker(sys.argv[3]))
        parser=argparse.ArgumentParser()
        parser.add_argument("--case",type=int,required=True)
        parser.add_argument("--run",type=int)
        parser.add_argument("--preflight",action="store_true")
        args=parser.parse_args();data_path(args.case);M.base.configure(args.case)
        require((args.run is not None)!=args.preflight,"ONE_MODE")
        raise SystemExit(preflight() if args.preflight else run_owned(args.run))
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        value=str(error) if isinstance(error,ValueError) and re.fullmatch("[A-Z0-9_]{1,256}",str(error)) else "REDACTED_NATIVE_CONTROLLER_FAILURE"
        print(json.dumps(dict(state="FAILED_NOT_ACCEPTED",error_code=value)))
        raise SystemExit(2) from None
