"""Canonical scoped-validator forwarding with qualified identity guard reuse.
Old153 V14 context/diagnostic and failed154run001 remain immutable.
No extra sampler, guard/rate/deadline relaxation, source cache or product replay.
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



SELF="tools/p09/flat_current_queue_native_diagnostic_runtime_v16.py"
TEST="tools/p09/tests/test_flat_current_queue_native_diagnostic_runtime_v16.py"
QUAL_PATH="implementation/p09/evidence/p09-361-case155-scoped-identity-controller-code6-r540.v1.json"
QUAL_STATE="PASS_NATIVE_V16_SCOPED_IDENTITY_CONTROLLER_CODE6_NOT_PRODUCT"
OLD15_PIN={"path":"tools/p09/flat_current_queue_native_diagnostic_runtime_v15.py","bytes":21060,"sha256":"5cd1ee92eefaa4991d9e8ce62010b50921243113d4cbc6b474f6accf985b571f"}
OLD15_TEST_PIN={"path":"tools/p09/tests/test_flat_current_queue_native_diagnostic_runtime_v15.py","bytes":6687,"sha256":"66ca8d0d482c24995afc44fe418ec218a0a3734afd979c43f66cbcc9b5a2d2fa"}
COMPONENT_PINS=[{"path":"tools/p09/native_process_cpu_attribution_v4.py","bytes":2309,"sha256":"a2007fb8fcd5c3790fd79c036aa00bffb37bbee4e883552d8784fa822ab285b9"},{"path":"tools/p09/tests/test_native_process_cpu_attribution_v4.py","bytes":3472,"sha256":"3ceeacfe7cacc120fce254b1463ba88a620c1971fe91983b1f896cc080520706"},{"path":"tools/p09/native_diagnostic_connection_v4.py","bytes":4194,"sha256":"53dc3615f5fe340961e44faecb65a915d17497ea32169ff7efb15607f14abf45"},{"path":"tools/p09/tests/test_native_diagnostic_connection_v4.py","bytes":4093,"sha256":"1aa758dfdf33d8e02196b0a380b05fce2bcde4e4d9bb6a6c2d747d8e5909b91b"},{"path":"tools/p09/native_diagnostic_oracle_connection_v3.py","bytes":2508,"sha256":"104d8b8d83205f5370657e293a43307684e76d7735ba788df13befc3efd7d106"},{"path":"tools/p09/tests/test_native_diagnostic_oracle_connection_v3.py","bytes":2847,"sha256":"1a38821c4cd4436f2d0ad6e604171190435b895bde4549e52b45122020f30376"},{"path":"tools/p09/reviewed_runtime_attempt_v1.py","bytes":4634,"sha256":"3818faa42ff155a44a35fa83514407d712a29166c242b0975a290e9272f5a8e7"},{"path":"tools/p09/tests/test_reviewed_runtime_attempt_v1.py","bytes":5031,"sha256":"91289367797a2f6760b98097721b4344c757cecf87668af5f4fef77786c13b3c"},{"path":"tools/p09/flat_current_queue_native_diagnostic_runtime_v13.py","bytes":16750,"sha256":"db42aba986c97ccc48f2728134e448e67181bc9d4c63c6409f0a12da5a98541d"},{"path":"tools/p09/tests/test_flat_current_queue_native_diagnostic_runtime_v13.py","bytes":7609,"sha256":"13ce88cb12bab63725a71c6358c77d84323c1afe8a30360f6596834eb2e125fb"},{"path":"tools/p09/flat_current_queue_native_diagnostic_runtime_v14.py","bytes":18390,"sha256":"693d2ec414b2cf90b1fa283e8a9f477ebf446b9c079e20d95c6eadda702ef621"},{"path":"tools/p09/tests/test_flat_current_queue_native_diagnostic_runtime_v14.py","bytes":8197,"sha256":"7043ed38900e68fc1909aeef7ca443cca4b44ec40e5c8a150f558fd38d36691f"},{"path":"tools/p09/metadata_guard_identity_dedup_v1.py","bytes":5692,"sha256":"dab41e12f390292b6d9908d2b90a812b8927f497964e0fd9cf3f36c72981c8e4"},{"path":"tools/p09/tests/test_metadata_guard_identity_dedup_v1.py","bytes":4143,"sha256":"ef77587f0171852aab051794b4a38a9261a3b0f27fe4e569625b96a011b4c867"},{"path":"tools/p09/metadata_guard_identity_connection_v1.py","bytes":4296,"sha256":"08a538f3267f506eb6926c96b3cd8e1746a7644c87dfdb67ed0c5bfbb07bfaeb"},{"path":"tools/p09/tests/test_metadata_guard_identity_connection_v1.py","bytes":4877,"sha256":"9c98c406746f0fb3c4b01944f5fa039da164adba7ed233cc27675315421aff22"},{"path":"tools/p09/reviewed_runtime_attempt_v2.py","bytes":2313,"sha256":"6759dea3898070192f3c32f9b9abdb769c2ecd39eaecb213d4cbeff41d3f6d94"},{"path":"tools/p09/tests/test_reviewed_runtime_attempt_v2.py","bytes":4315,"sha256":"0ec73517d815b540371a802f909eeb2ce07baab186c4577d541d788e964ebedf"},{"path":"tools/p09/metadata_pressure_failfast.py","bytes":2942,"sha256":"c61ae620fe63cda94b029efe29fb252612c941c6f47ca4265a5c6c8491ce0c9c"},{"path":"tools/p09/flat_current_queue_native_diagnostic_runtime_v15.py","bytes":21060,"sha256":"5cd1ee92eefaa4991d9e8ce62010b50921243113d4cbc6b474f6accf985b571f"},{"path":"tools/p09/tests/test_flat_current_queue_native_diagnostic_runtime_v15.py","bytes":6687,"sha256":"66ca8d0d482c24995afc44fe418ec218a0a3734afd979c43f66cbcc9b5a2d2fa"},{"path":"tools/p09/metadata_identity_acceptance_bridge_v1.py","bytes":3059,"sha256":"33560a5a03eefeede9a0db8b680d80e1827527264f7c9aed006a89190be164a4"},{"path":"tools/p09/tests/test_metadata_identity_acceptance_bridge_v1.py","bytes":4268,"sha256":"7a86d87b4675642b8ae59c8f4c287f19398a88f123cae40a82dc9ecc5888b928"}]
COMPONENT_QUAL_PINS=[{"path":"implementation/p09/evidence/p09-361-case153-native4-warning-suppression-code6-r513.v1.json","bytes":3222,"sha256":"f1d11ad25451dfbc330dfc62d69a06860ec9db8f0804848970e0a6c49c51a599"},{"path":"implementation/p09/evidence/p09-361-case153-native4-connection-schema-code6-r516.v1.json","bytes":3259,"sha256":"d79f56467cea47ee1ce8fb5b883b2160042ab0cbcb0618639be7c6248735d968"},{"path":"implementation/p09/evidence/p09-361-case153-native4-version-oracle-code6-r517.v1.json","bytes":3265,"sha256":"cb445d6a048a190c21a789c2c58615676fbed43088cc29d67c82b4d0d0b2fa7f"},{"path":"implementation/p09/evidence/p09-361-case153-native4-actual-local-observer-r518.v1.json","bytes":6849,"sha256":"56cd2a0651f1787fc8edcb7971c2c92b31becc286639a0e005ac8712b6d5c59f"},{"path":"implementation/p09/evidence/p09-361-case153-reviewed-retry-code6-r520.v1.json","bytes":3502,"sha256":"99d561943c24d0e636cdad1d7474361ab7d906dd3dd028f1408115b00ca8fb1b"},{"path":"implementation/p09/evidence/p09-361-case153-native4-retry-controller-code6-r521.v1.json","bytes":6432,"sha256":"c7eee54c0a88285e07b7a78eccb98ca7c76afcf70f16b43c60c714f719b39398"},{"sha256":"2b1bef888f3eec53a82166fe4ba4759c58a087a3fbc090b433f5e4b0de1309e8","path":"implementation/p09/evidence/p09-361-case153-native4-retry-controller-code6-r524.v1.json","bytes":7003},{"path":"implementation/p09/evidence/p09-361-case154-metadata-guard-dedup-code6-r529.v1.json","bytes":4806,"sha256":"42276a0aa5f7dafd27960f3e953f1ed0993e74faa71e3f8e32ac790edd9e7d7b"},{"path":"implementation/p09/evidence/p09-361-case154-metadata-guard-connection-code6-r531.v1.json","bytes":5751,"sha256":"cb004ae492331971763975a682ee9373a66894bdec7f0f28bf380bc58f43baef"},{"path":"implementation/p09/evidence/p09-361-case154-metadata-guard-full-summary-local20-r532.v1.json","bytes":8962,"sha256":"768830cc174dd628587acfb4a8a9ecba11dc4cd1af247ad4bb724958e9cdbf42"},{"bytes":4829,"sha256":"f09b5015a1378d17dda5318176dcd7d07dc5f43fb09eae8584dfa04f1a1c0d37","path":"implementation/p09/evidence/p09-361-case154-reviewed-run002-code6-r534.v1.json"},{"path":"implementation/p09/evidence/p09-361-case154-metadata-guard-whole-controller-code6-r535.v1.json","bytes":9405,"sha256":"375e308cd7ee24ddb7931c9aae6ad3ab73bb0604cb106347aa1c6fc81f72938f"},{"path":"implementation/p09/evidence/p09-361-case154-acceptance-scoped-bridge-code6-r537.v1.json","bytes":4510,"sha256":"451ce1bd8d1cfa2b5f2821d20ae5a78854ef0905a14dc938faf84085add4b846"}]
ACTUAL154_PIN={"path":"implementation/p09/evidence/p09-361-case154-current-runtime-run002.v1.json","sha256":"ab9d13010e6ee18689d6f02ec7b06a66a14beba4bc6a83841abd921e799996f1","bytes":2398252}
ACTUAL148_PIN={"path":"implementation/p09/evidence/p09-361-case154-current-epoch-accept001.v1.json","bytes":462952,"sha256":"d01d743cbd0216a0ce3ff05990129017472df30f81cb0630bafd249b056d75d2"}

def require(ok,code):
    if not ok:raise ValueError("NATIVE_V16_"+code)

def raw(pin):
    lean.base.stable.stable.prior.build.direct_path(lean.c.ROOT/pin["path"],file_required=True)
    with (lean.c.ROOT/pin["path"]).open("rb") as stream:data=stream.read(pin["bytes"]+1)
    require(len(data)==pin["bytes"] and hashlib.sha256(data).hexdigest()==pin["sha256"],"EXACT_NAMESPACE_BYTES")
    return data


def load_old15():
    source=raw(OLD15_PIN);tree=ast.parse(source.decode("utf-8"))
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
     __name__="p09_exact_old15_namespace",__file__=OLD15_PIN["path"])
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),OLD15_PIN["path"],"exec"),env)
    return NS(**env)




OLD15=load_old15()
M=OLD15.M
def component(name,env):
    p=next(p for p in COMPONENT_PINS if p["path"].endswith("/"+name))
    return OLD15.OLD14.OLD12.OLD11.OLD10.OLD9.OLD8.BASE.namespace(raw(p),p,env)
DEDUP=component("metadata_guard_identity_dedup_v1.py",dict(ast=ast,copy=copy,FunctionType=FunctionType))
META_CONNECTION=component("metadata_guard_identity_connection_v1.py",
 dict(FunctionType=FunctionType,NS=NS,optimization=DEDUP))
RETRY=component("reviewed_runtime_attempt_v2.py",dict(FunctionType=FunctionType,prior=OLD15.RETRY))
NATIVE=OLD15.NATIVE
NATIVE_PROOF=OLD15.NATIVE_PROOF
BACKEND=OLD15.BACKEND
CONNECTION=OLD15.CONNECTION
ORACLE=OLD15.ORACLE
ORACLE_PROOF=OLD15.ORACLE_PROOF
BRIDGE=component("metadata_identity_acceptance_bridge_v1.py",dict(FunctionType=FunctionType,NS=NS))
PRIOR154,PRIOR154_PROOF=BRIDGE.connect(OLD15)
FORMAT_STATES=[]
ATTEMPT_STATES=[]

def metadata_identity_evidence(row):
    require(type(row["selected_test_index"]) is int and row["selected_test_index"]>=154,"NEW_METADATA_INDEX")
    failfast=row["bootstrap_metadata"]["early_pressure"]["metadata_failfast_connection"]
    value=failfast["identity_duplicate_guard"]
    expected=dict(source=DEDUP.SELF,original_callback_is_hard=True,
      calls_avoided=failfast["checks"],original_hard_guard_called_first=True,distinct_callback_path_unchanged=True,
      original_warning_latch_validation_and_restore_retained=True,source_reads_rates_deadlines_or_guards_weakened=False,
      added_sampler_thread_or_native_query=False,PC_freeze_resolved=False)
    require(type(value) is dict and set(value)==set(expected),"CLOSED_ACTUAL_IDENTITY_PROOF")
    for k,x in expected.items():require(type(value.get(k)) is type(x) and value[k]==x,"EXACT_ACTUAL_IDENTITY_VALUE")
    require(type(failfast["checks"]) is int and failfast["checks"]>0,"ACTUAL_METADATA_CALLS_NOT_IMPORT_ONLY")
    M.a.fields(failfast,dict(active=False,original_checkpoint_restored=True,warning_stops=0,latched=False,
      automatic_retry_or_resume=False,complete_source_reads_or_deadlines_weakened=False),"ACTUAL_RESTORED_METADATA")
    return dict(actual_metadata_identity_duplicate_calls_avoided=value["calls_avoided"],
      all_original_full_source_product_resource_predicates_retained=True)

_original_source=OLD15._original_source
def validate_candidate(q,row,listing,oldbody,fresh,ctx,flat=True):
    fn=FunctionType(_original_source.validate_candidate.__code__,
      dict(_original_source.validate_candidate.__globals__,validator=validator),
      argdefs=_original_source.validate_candidate.__defaults__,closure=_original_source.validate_candidate.__closure__)
    result,proof=fn(q,row,listing,oldbody,fresh,ctx,flat)
    proof.update(metadata_identity_evidence(row))
    return result,proof
_prepare_projection=FunctionType(_original_source.prepare_projection.__code__,
 dict(_original_source.prepare_projection.__globals__,root_path=RETRY.root_path),
 argdefs=_original_source.prepare_projection.__defaults__,closure=_original_source.prepare_projection.__closure__)
_source_prepare=FunctionType(_original_source.prepare.__code__,
 dict(_original_source.prepare.__globals__,prepare_projection=_prepare_projection),
 argdefs=_original_source.prepare.__defaults__,closure=_original_source.prepare.__closure__)
CURRENT_SOURCE=NS(**{**vars(_original_source),"validate_candidate":validate_candidate,
 "root_path":RETRY.root_path,"prepare_projection":_prepare_projection,"prepare":_source_prepare})

def data_path(index):
    require(type(index) is int and 155<=index<=249,"NO_SUCCESSFUL_REPLAY")
    return f"implementation/p09/evidence/p09-361-case{index}-native-diagnostic-data016.v1.json"

def validate_data(row,step):
    require(type(row) is dict and set(row)=={"schema_version","index","before","qualification_run",
     "physical_product_run","base_step_pin","prior_v15_data_pin","qualification_pin","controller_code_pins",
     "component_pins","component_qualification_pins","actual154_pin","actual148_pin","reviewed_failure_pins"},"CLOSED_DATA016")
    M.a.fields(row,dict(schema_version="hwpx-agent.p09-native-diagnostic-controller/v16",index=step.index,
      before=step.before,qualification_run=1,physical_product_run=RETRY.physical_run(step.index),base_step_pin=step.pin,
      component_pins=COMPONENT_PINS,component_qualification_pins=COMPONENT_QUAL_PINS,
      actual154_pin=ACTUAL154_PIN,actual148_pin=ACTUAL148_PIN,reviewed_failure_pins=RETRY.HISTORY),
      "EXPLICIT_QUALIFICATION_AND_PHYSICAL_RUN")
    M.a.exact(row["prior_v15_data_pin"]["path"],OLD15.data_path(step.index),"ORIGINAL_DATA014")
    M.a.exact(row["qualification_pin"]["path"],QUAL_PATH,"EXACT_NEW_CODE6")
    require(set(M.base.scope.pins(row["controller_code_pins"],2))=={SELF,TEST},"CONTROLLER_CODE2")
    data_path(step.index)
    return row

def own_inputs(q):
    OLD15.own_inputs(q)
    row=validate_data(json.loads(q.text(data_path(M.base.CONFIG.index)),object_pairs_hook=M.base.unique),M.base.CONFIG)
    M.a.exact(q.snapshots[OLD15.data_path(M.base.CONFIG.index)],row["prior_v15_data_pin"],"ORIGINAL_DATA014_BYTES")
    RETRY.reviewed_failure(q,M.a.read_exact,M.a.fields)
    for p in COMPONENT_QUAL_PINS:
        qualified=M.a.read_exact(q,p)
        require(qualified["state"].startswith("PASS_") and qualified["cleanup_confirmed"] is True,"QUALIFIED_COMPONENT")
    qual=M.a.read_exact(q,row["qualification_pin"])
    M.a.fields(qual,dict(state=QUAL_STATE,contracts=dict(run=6,errors=0,failures=0,skipped=0),
      cleanup_confirmed=True,Native_product_or_acceptance_executed=False),"CODE6_NOT_PRODUCT")
    M.a.exact(qual["new_code_pins"],row["controller_code_pins"],"EXACT_CURRENT_TESTED_CODE2")
    M.a.exact(qual["component_pins"],COMPONENT_PINS,"ALL_QUALIFIED_COMPONENTS")
    for p in row["controller_code_pins"]+COMPONENT_PINS+[OLD15_PIN,OLD15_TEST_PIN]:
        M.a.exact(q.pin(p["path"]),p,"ALL_NAMESPACE_SOURCES_CURRENT")
    ar=M.a.read_exact(q,ACTUAL148_PIN)
    M.a.fields(ar,dict(accepted_count_after=148,next_runtime_index=155,accepted_test_indices=[154],
      resource_cleanup_confirmed=True,P09_gate="OPEN"),"ORIGINAL147_CUTOVER_AUTHORITY")
    M.a.exact(ar["runtime_candidate_pin"],ACTUAL154_PIN,"SAME_EXECUTED153_RUN002")
    return row

def validator(source,ctx,flat=True):
    fn,proof=OLD15.validator(source,ctx,flat)
    fn.__globals__["CONTROLLERS"]=tuple(dict.fromkeys(fn.__globals__["CONTROLLERS"]+(SELF,TEST)))
    return fn,dict(proof,metadata_identity_and_reviewed_physical_attempt_in_whole_scope=True)

def context(step):
    return NS(**{**vars(OLD15.context(step)),"SELF":SELF,"TEST":TEST})

def template():
    engine,proof=OLD15.template()
    engine.run_owned.__globals__.update(SELF=SELF,TEST=TEST)
    engine.worker.__globals__.update(SELF=SELF,TEST=TEST)
    FORMAT_STATES.append(OLD15.FORMAT_STATES[-1]);ATTEMPT_STATES.append(OLD15.ATTEMPT_STATES[-1])
    return engine,dict(proof,qualified_metadata_and_one_physical_adapter_reused=True,
      original_engine_and_worker_code_unchanged=True)

def previous_function(index):
    require(type(index) is int and 147<=index<=249,"EXACT_PREDECESSOR")
    if index<=153:return OLD15.previous_function(index)
    if index==154:
        fn=OLD15.previous_function(index)
        return FunctionType(fn.__code__,dict(fn.__globals__,source=PRIOR154.source),
          argdefs=fn.__defaults__,closure=fn.__closure__)
    fn=M.V3.OLD.API.previous_validation
    return FunctionType(fn.__code__,dict(fn.__globals__,source=CURRENT_SOURCE,validator=validator,context=context),
      argdefs=fn.__defaults__,closure=fn.__closure__)

def previous_validation(q,row,listing,oldbody,fresh,oldctx,flat=True):
    if oldctx.INDEX<=146:return OLD15.previous_validation(q,row,listing,oldbody,fresh,oldctx,flat)
    if oldctx.INDEX==154:
        require(M.base.CONFIG.index==155,"ONLY_NEXT155_AFTER_REAL154")
        M.a.exact(M.base.CONFIG.prior_candidate_pin,ACTUAL154_PIN,"EXACT153_PREDECESSOR")
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
    for required in [p,value["qualification_pin"],OLD15_PIN,OLD15_TEST_PIN,ACTUAL154_PIN,ACTUAL148_PIN]+\
      value["controller_code_pins"]+COMPONENT_PINS+COMPONENT_QUAL_PINS+RETRY.HISTORY:
        M.a.exact(expected.get(required["path"]),required,"ALL_NEW_DATA_CODE_AND_REVIEW_PINS_IN_NATIVE")
    return expected

_family=OLD15._full_prepare.__globals__;_env=dict(_family)
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
    data_path(M.base.CONFIG.index);M.a.exact(task,RETRY.task(M.base.CONFIG.index),"EXACT_ACTUAL_PHYSICAL_WORKER")
    engine,_=template();return engine.worker(task)
API.worker=worker

def run_owned(run):
    index=M.base.CONFIG.index;logical=RETRY.public_run(index,run);data_path(index)
    require(not (M.c.ROOT/RETRY.root_path(M.base.CONFIG)).exists(),"FRESH_PHYSICAL_RECEIPT")
    execute,state=CONNECTION.connect_run(API.original_run_owned,BACKEND)
    before=len(FORMAT_STATES);ab=len(ATTEMPT_STATES)
    code=execute(logical);observed=ATTEMPT_STATES[ab:]
    require(len(observed)==1 and observed[0].actual_engine_calls==1 and observed[0].physical_product_run==run,
      "ONE_ACTUAL_PHYSICAL_ENGINE_CALL")
    if code==0:
        formatted=FORMAT_STATES[before:]
        require(sum(s.actual_capture_count for s in formatted)==1 and sum(s.actual_dump_calls for s in formatted)==1
          and all(s.writer_errors_propagated==0 for s in formatted),"ONE_ACTUAL_COMPACT_CAPTURE_DUMP")
    require(state["actual_local_bindings"]==1,"ONE_ACTUAL_NATIVE4_CONNECTION")
    return code

def preflight_data(q):
    row=own_inputs(q)
    require("run" not in row and type(row["qualification_run"]) is int and row["qualification_run"]==1,"IMMUTABLE_ALIAS")
    return dict(row,run=row["qualification_run"])

def preflight_projection(data,leaf):
    fn=OLD15.preflight_projection(data,leaf);old=fn.__code__
    require(sum(type(x) is str and x=="-native-diagnostic-preflight015.v1.json" for x in old.co_consts)==1,
      "ONE_NEW_PREFLIGHT_DESTINATION")
    code=old.replace(co_consts=tuple("-native-diagnostic-preflight016.v1.json" if type(x) is str and
      x=="-native-diagnostic-preflight015.v1.json" else x for x in old.co_consts))
    require(code.replace(co_consts=old.co_consts)==old,"ALL_ORIGINAL_PREFLIGHT_CODE_TEST10")
    return FunctionType(code,dict(fn.__globals__,SELF=SELF,TEST=TEST,template=template,
      binding_attempt=API.binding_attempt,connection_data=preflight_data,own_inputs=own_inputs,data_path=data_path,
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
        code=str(error) if isinstance(error,ValueError) and re.fullmatch("[A-Z0-9_]{1,256}",str(error)) else "REDACTED_V16_FAILURE"
        print(json.dumps(dict(state="FAILED_NOT_ACCEPTED",error_code=code)))
        raise SystemExit(2) from None
