"""Exact159/run001 controller using original whole engine and worker bodies.

Immutable CODE/DATA and current whole preflight are mandatory. Preserve the
original single physical adapter, Native timing, CPU/RAM/600 guards, fifteen
second window, full input binding and independent predecessor158 oracle.
"""
import argparse
import json
import re
import sys
from types import FunctionType,SimpleNamespace as NS

import flat_current_queue_envelope_runtime_v25 as old
import successor_current_binding_v1 as current_binding
import successor_bounded_graph_bootstrap_v1 as bootstrap
import successor_strict_window_v1 as window

base=old.base;a=old.a;c=old.c;prior=old.prior
SELF="tools/p09/flat_current_queue_envelope_runtime_v26.py"
TEST="tools/p09/tests/test_flat_current_queue_envelope_runtime_v26.py"
DATA="implementation/p09/evidence/p09-361-case159-envelope-controller-data034.v1.json"
QUAL="implementation/p09/evidence/p09-361-case159-envelope-controller-code14-r746.v1.json"
QUAL_STATE="PASS_CURRENT159_CONTROLLER_CODE14_PRIVATE_ENGINE_WORKER_CONNECTION_NOT_NATIVE_OR_GO"
SCHEMA="hwpx-agent.p09-envelope-current-controller/v26"
PREFLIGHT="implementation/p09/evidence/p09-361-case159-envelope-controller-preflight034.v1.json"
CAPSULE=current_binding.graph_factory.CAPSULE
MANIFEST=bootstrap.MANIFEST
BINDING_CODE="implementation/p09/evidence/p09-361-case159-original-current-binding-code8-r744.v1.json"
NATIVE=old.NATIVE;RETRY=prior.RETRY
_graph=None;_checkpoint=None;_execution_requested=False
PARENT_STATES=[]


def require(ok,label):
    if not ok:raise ValueError("ENVELOPE_V26_"+label)


def only159():
    require(base.CONFIG is not None and type(base.CONFIG.index) is int and base.CONFIG.index==159 and
        type(base.CONFIG.before) is int and base.CONFIG.before==152,"ONLY_EXACT159_BEFORE152")


def graph_value():
    global _graph
    only159()
    if _graph is None:_graph,_=bootstrap.load(old,lambda:None)
    return _graph


def binding_value():return graph_value().binding


def validate_data(row):
    only159()
    require(type(row) is dict and set(row)=={"schema_version","index","before","run","physical_product_run",
        "base_step_pin","authority_pin","prior_runtime_pin","manifest_pin","capsule_pin",
        "qualification_pin","controller_code_pins","binding_code_pin"},"CLOSED_CURRENT159_DATA")
    a.fields(row,dict(schema_version=SCHEMA,index=159,before=152,run=1,physical_product_run=1,
        base_step_pin=base.CONFIG.pin,authority_pin=current_binding.successor.AUTHORITY,
        prior_runtime_pin=current_binding.successor.ROOT,manifest_pin=MANIFEST,capsule_pin=CAPSULE),"EXACT_CURRENT159_DATA")
    require(set(base.scope.pins(row["controller_code_pins"],2))=={SELF,TEST},"EXACT_CURRENT_CONTROLLER_PAIR")
    require(row["qualification_pin"]["path"]==QUAL and row["binding_code_pin"]["path"]==BINDING_CODE,"EXACT_CURRENT_CODE_PATHS")
    base.scope.pins([row["qualification_pin"],row["binding_code_pin"]],2)
    return row


def own_inputs(q):
    global _checkpoint
    only159();_checkpoint=q.checkpoint
    row=validate_data(q.json(DATA))
    code=a.read_exact(q,row["qualification_pin"])
    a.fields(code,dict(state=QUAL_STATE,contracts=dict(run=14,errors=0,failures=0,skipped=0),
        actual159_product_or_Native_executed=False,actual159_GO_authorized=False,cleanup_confirmed=True),"EXACT_CONTROLLER_CODE14_NOT_PRODUCT")
    a.exact(code["new_code_pins"],row["controller_code_pins"],"EXACT_QUALIFIED_CONTROLLER_BYTES")
    for pin in code["source_pins"]+row["controller_code_pins"]:a.exact(q.pin(pin["path"]),pin,"CURRENT_CONTROLLER_DEPENDENCIES")
    bound_code=a.read_exact(q,row["binding_code_pin"])
    a.fields(bound_code,dict(state="PASS_SUCCESSOR159_ORIGINAL_CURRENT_BINDING_RUST787_WHOLE_PRIOR158_CODE8_NOT_COMPLETE_CONTROLLER_OR_GO",
        contracts=dict(run=8,errors=0,failures=0,skipped=0),rust_inputs=787,source_pairs=20,cleanup_confirmed=True),"ORIGINAL_BINDING_NOT_PRODUCT")
    for pin in bound_code["source_pins"]:a.exact(q.pin(pin["path"]),pin,"CURRENT_ORIGINAL_BINDING_SOURCES")
    current_binding.qualify(q,old)
    for pin in old.TIMING_PINS+old.NAMESPACE_SOURCE_PINS+old.ROLE_PINS+[old.ROLE_ONCE_PIN]:
        a.exact(q.pin(pin["path"]),pin,"ORIGINAL_TIMING_CORE_FAILURE_SOURCES")
    for filename in old.SUPPORT:
        support=q.json(filename)
        require(support["state"].startswith("PASS_") and support["cleanup_confirmed"] is True,"EXACT_ORIGINAL_SUPPORT")
        for pin in support.get("source_pins",[])+support.get("new_code_pins",[]):a.exact(q.pin(pin["path"]),pin,"ORIGINAL_SUPPORT_SOURCE")
    for path in (bootstrap.SELF,window.SELF,window.TEST):q.pin(path)
    a.exact(q.pin(MANIFEST["path"]),MANIFEST,"EXACT_CURRENT159_MANIFEST")
    a.exact(q.pin(CAPSULE["path"]),CAPSULE,"EXACT_CURRENT159_CAPSULE")
    return row


_original_own_inputs=own_inputs
own_inputs,ADMISSION_COUNTS=old.admission_once.connect(_original_own_inputs)


def binding(q):
    own_inputs(q)
    complete,rust,fresh,live,_=current_binding.bind(q,old)
    current=graph_value()
    a.exact(live.descriptors(),current.binding.descriptors(),"FRESH_AND_ENGINE_SAME_TWENTY_PAIRS")
    a.exact(dict(live.manifest_pin),dict(current.binding.manifest_pin),"FRESH_AND_ENGINE_SAME_MANIFEST")
    a.exact(fresh.lineage,current.lineage,"FRESH_AND_ENGINE_SAME_FAILURE_LINEAGE")
    if _execution_requested:
        checked=q.json(PREFLIGHT)
        a.fields(checked,dict(state="PASS_REVIEWED_METADATA_CONNECTION_PREFLIGHT_NOT_NATIVE_OR_PRODUCT_OR_ACCEPTANCE",
            index=159,product_worker_or_Native_frame_executed=False,cleanup_confirmed=True,
            runtime_connection_qualified=False,accepted_count_delta=0),"WHOLE_PREFLIGHT_REQUIRED_BEFORE_ACTUAL159")
        # The original runtime independently recomputes complete cost including
        # this new receipt before Native acquisition and GO.
        a.exact(checked["connection_data_pin"],q.snapshots[DATA],"SAME_CLOSED_CONTROLLER_DATA_AS_WHOLE_PREFLIGHT")
        require(type(checked["fresh_inputs"]) is int and checked["fresh_inputs"]>0 and
            type(checked["final_fresh_hashes"]) is int and checked["final_fresh_hashes"]==checked["fresh_inputs"],
            "ALL_WHOLE_PREFLIGHT_FINAL_HASHES")
        require(checked.get("synthetic_fixture_only_not_evidence",False) is False,"NO_SYNTHETIC_PREFLIGHT")
        a.resource_history(checked["resource_samples"])
    return base.scope.extend(complete,q.snapshots),rust


def binding_attempt(q,run):
    require(type(run) is int and run==1,"EXACT_FIRST_CURRENT159_RUN_ONLY")
    return binding(q)


def template():
    only159();engine,proof=prior.template()
    engine.run_owned.__globals__.update(SELF=SELF,TEST=TEST,native=NATIVE)
    engine.worker.__globals__.update(SELF=SELF,TEST=TEST,native=NATIVE)
    connected,state=graph_value().parent.connect_engine(engine,binding_value());PARENT_STATES.append(state)
    return connected,dict(proof,current159_parent_worker_oracle_binding_shared=True,
        original_single_physical_adapter_and_engine_worker_bodies_retained=True)


def worker(task):
    only159();a.exact(task,"case159-current-r001-tests","EXACT_CURRENT159_WORKER_TASK")
    graph=graph_value();engine,_=prior.template()
    policy=graph.worker.raw_policy.Policy(c.ROOT,graph.binding,lambda:True,lambda:None)
    execute,_=graph.worker.connect_worker(engine.worker,policy)
    return execute(task)


def context(step):return NS(**{**vars(prior.context(step)),"SELF":SELF,"TEST":TEST})


def validator(raw,ctx,flat=True):
    require(ctx.INDEX==159 and callable(_checkpoint),"EXACT_CURRENT159_FULL_ORACLE_GUARD")
    generator,proof=prior.OLD17.validator(raw,ctx,flat)
    generator=prior.LINK.projector(generator,old.ACCEPTED_DIRECT,159)
    graph=graph_value()
    generator.__globals__["CONTROLLERS"]=tuple(dict.fromkeys(generator.__globals__["CONTROLLERS"]+
        (SELF,TEST,graph.parent.SELF,graph.parent.TEST,graph.worker.SELF,graph.worker.TEST,
         graph.full_oracle.SELF,graph.full_oracle.TEST)))
    projected,_=graph.full_oracle.projector(generator,graph.binding,prior.DIRECT.runtime_budget,_checkpoint)
    return projected,dict(proof,explicit_current159_semantic_and_physical_full_oracle=True)


def validate_candidate(q,row,listing,oldbody,fresh,ctx,flat=True):
    global _checkpoint
    only159();require(ctx.INDEX==159,"ONLY_CURRENT159_CANDIDATE")
    _checkpoint=q.checkpoint;RETRY.validate_actual(row,base.CONFIG,dict(path=RETRY.root_path(base.CONFIG)))
    def budget(required,requests):return binding_value().runtime_budget(required,requests,prior.DIRECT.runtime_budget,q.checkpoint)
    direct=NS(**{**vars(prior.DIRECT),"runtime_budget":budget,
        "cost":prior.LINK.clone(prior.DIRECT.cost,runtime_budget=budget),
        "retained_evidence":prior.LINK.clone(prior.DIRECT.retained_evidence,runtime_budget=budget)})
    linked,_=prior.OLD17.OLD16.ORACLE.connect_full(prior.OLD17.OLD16._original_source.validate_candidate,
        prior.NEW_CANDIDATE,direct)
    result,proof=prior.LINK.clone(linked,validator=validator)(q,row,listing,oldbody,fresh,ctx,flat)
    proof.update(prior.OLD17.OLD16.metadata_identity_evidence(row))
    proof.update(prior.LINK.evidence(row,a))
    check,_=window.connect(prior.WINDOW_LINK.check_evidence);proof.update(check(row,a))
    return result,proof


_project=prior.LINK.clone(prior.CURRENT_SOURCE.prepare_projection,root_path=RETRY.root_path,
    validate_candidate=validate_candidate,runtime=NS(context=context))
CURRENT_SOURCE=NS(**{**vars(prior.CURRENT_SOURCE),"prepare_projection":_project,"validate_candidate":validate_candidate})
_family=prior._full_prepare.__globals__;_env=dict(_family)
for _name,_fn in tuple(_env.items()):
    if type(_fn) is FunctionType and _fn.__globals__ is _family:
        _new=FunctionType(_fn.__code__,_env,argdefs=_fn.__defaults__,closure=_fn.__closure__)
        _new.__kwdefaults__=_fn.__kwdefaults__;_env[_name]=_new
_env.update(SELF=SELF,TEST=TEST,FILES=(SELF,TEST),QUAL_PATH=QUAL,source=CURRENT_SOURCE,
    own_inputs=own_inputs,validator=validator,context=context,template=template,binding=binding,
    binding_attempt=binding_attempt,previous_validation=current_binding.previous_callback(old))
API=NS(**_env)


def independent_prepare_not_qualified(*args,**kwargs):
    require(False,"CURRENT159_INDEPENDENT_PREPARE_NOT_YET_QUALIFIED")
API.prepare=independent_prepare_not_qualified
API.accept=independent_prepare_not_qualified


def run_owned(run):
    global _execution_requested
    only159();require(type(run) is int and run==1,"FIRST_CURRENT159_PHYSICAL_RUN_ONLY")
    require(not (c.ROOT/RETRY.root_path(base.CONFIG)).exists(),"NO_EXISTING159_RUNTIME_OVERWRITE")
    require((c.ROOT/PREFLIGHT).is_file(),"CURRENT159_WHOLE_PREFLIGHT_MISSING")
    require(not _execution_requested,"NO_AUTOMATIC_CURRENT159_RETRY")
    _execution_requested=True
    execute,state=prior.CONNECTION.connect_run(API.run_owned,prior.BACKEND)
    before=len(prior.ATTEMPT_STATES);result=execute(1)
    observed=prior.ATTEMPT_STATES[before:]
    require(len(observed)==1 and observed[0].physical_product_run==1 and observed[0].actual_engine_calls==1,
        "ONE_ORIGINAL_CURRENT159_ENGINE_CALL")
    require(state["actual_local_bindings"]==1,"ONE_ORIGINAL_NATIVE_DIAGNOSTIC_BINDING")
    return result


def preflight_data(q):return own_inputs(q)


def preflight_projection(raw,leaf):
    original=prior.preflight_projection(raw,leaf);code=original.__code__
    before="-product-window-preflight019.v1.json";after="-envelope-controller-preflight034.v1.json"
    require(sum(type(x) is str and x==before for x in code.co_consts)==1,"ONE_CURRENT159_PREFLIGHT_DESTINATION")
    changed=code.replace(co_consts=tuple(after if type(x) is str and x==before else x for x in code.co_consts))
    require(changed.replace(co_consts=code.co_consts)==code,"ENTIRE_ORIGINAL_WHOLE_PREFLIGHT_CODE")
    def budget(required,requests):
        require(callable(_checkpoint),"CURRENT159_PREFLIGHT_GUARD")
        return binding_value().runtime_budget(required,requests,prior.DIRECT.runtime_budget,_checkpoint)
    prebase=NS(**{**vars(original.__globals__["base"]),"native":NATIVE,
        "stable":NS(**{**vars(original.__globals__["base"].stable),"runtime_budget":budget})})
    return FunctionType(changed,dict(original.__globals__,SELF=SELF,TEST=TEST,template=template,
        binding_attempt=binding_attempt,connection_data=preflight_data,own_inputs=own_inputs,
        data_path=lambda index:DATA,base=prebase),argdefs=original.__defaults__,closure=original.__closure__)


def preflight():return prior.LINK.clone(prior.preflight,preflight_projection=preflight_projection)()


if __name__=="__main__":
    try:
        if len(sys.argv)==4 and sys.argv[1:3]==["--owned-worker","--task"]:
            base.configure(base.task_index(sys.argv[3]));raise SystemExit(worker(sys.argv[3]))
        p=argparse.ArgumentParser();p.add_argument("--case",type=int,required=True)
        p.add_argument("--run",type=int);p.add_argument("--preflight",action="store_true")
        args=p.parse_args();base.configure(args.case);only159()
        require((args.run is not None)!=args.preflight,"EXACTLY_ONE_MODE")
        raise SystemExit(preflight() if args.preflight else run_owned(args.run))
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        label=str(error) if isinstance(error,ValueError) and re.fullmatch("[A-Za-z0-9_]{1,256}",str(error)) else "REDACTED_V26_FAILURE"
        print(json.dumps(dict(state="FAILED_NOT_ACCEPTED",error_code=label)))
        raise SystemExit(2) from None
