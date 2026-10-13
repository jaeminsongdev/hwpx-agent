"""Only158 whole original controller with explicit lossless physical inputs.

Original engine/worker/whole preflight and historical validators survive.
New immutable DATA and CODE qualification are mandatory before GO. This module
does not accept a runtime candidate or advance the official queue.
"""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import re
import sys
from types import FunctionType,SimpleNamespace as NS
# Limit this process before loading the existing namespace graph.
_k=ctypes.WinDLL("kernel32",use_last_error=True)
_k.GetCurrentProcess.restype=ctypes.c_void_p
_k.SetPriorityClass.argtypes=[ctypes.c_void_p,ctypes.c_uint32]
_k.SetProcessAffinityMask.argtypes=[ctypes.c_void_p,ctypes.c_size_t]
_p=_k.GetCurrentProcess()
if not (_k.SetPriorityClass(_p,0x4000) and _k.SetProcessAffinityMask(_p,1)):
    raise SystemExit("LOCAL_LIMITS_NOT_APPLIED")
import flat_current_queue_product_window_runtime_v18 as prior
import runtime_envelope_parent_connection_v1 as parent
import runtime_envelope_worker_connection_v1 as worker_policy
import runtime_envelope_full_oracle_connection_v1 as full_oracle
import runtime_envelope_source_manifest_v2 as manifest
import strict_product_window_acceptance_connection_v2 as window_acceptance

SELF="tools/p09/flat_current_queue_envelope_runtime_v19.py"
TEST="tools/p09/tests/test_flat_current_queue_envelope_runtime_v19.py"
DATA="implementation/p09/evidence/p09-361-case158-envelope-controller-data020.v1.json"
QUAL="implementation/p09/evidence/p09-361-case158-envelope-controller-code7-r655.v1.json"
QUAL_STATE="PASS_CURRENT158_ENVELOPE_CONTROLLER_CODE7_NOT_PRODUCT_OR_GO"
SCHEMA="hwpx-agent.p09-envelope-current-controller/v19"
CAPSULE=dict(path="implementation/p09/evidence/p09-361-case158-worker-policy-capsule001.v1.json",
    bytes=6383,sha256="37279afffea965613e416cb951d17da4c2c1ec7656bd28d9c58ef8042930b04c")
SUPPORT=["implementation/p09/evidence/"+name for name in (
    "p09-361-case158-raw-live-access-policy-code10-r640.v1.json",
    "p09-361-case158-full-oracle-connection-code9-r642.v1.json",
    "p09-361-case158-parent-connection-code9-r651.v1.json",
    "p09-361-case158-worker-policy-code12-actual11-capsule-r645.v1.json",
    "p09-361-case158-owned-worker-policy-diagnostic-r647.v1.json")]
PRIOR_MARKER_QUAL="implementation/p09/evidence/p09-361-case157-window-acceptance-marker-code5-r612.v1.json"
base=prior.M.base;a=prior.M.a;c=prior.M.c
_binding=None;_checkpoint=None
PARENT_STATES=[]


def require(ok,label):
    if not ok:raise ValueError("ENVELOPE_V19_"+label)


def only158():
    require(base.CONFIG is not None and base.CONFIG.index==158 and base.CONFIG.before==151,
        "EXACT_CURRENT158_CONFIG")


def binding_value():
    global _binding
    if _binding is None:
        prior.lean.base.stable.stable.prior.build.direct_path(c.ROOT/CAPSULE["path"],file_required=True)
        with (c.ROOT/CAPSULE["path"]).open("rb") as stream:data=stream.read(worker_policy.MAX_BYTES+1)
        _binding,_=worker_policy.decode(data,{k:CAPSULE[k] for k in ("bytes","sha256")},lambda:None)
    return _binding


def validate_data(row):
    only158()
    require(type(row) is dict and set(row)=={"schema_version","index","before","run","base_step_pin",
        "manifest_pin","capsule_pin","qualification_pin","controller_code_pins"},"CLOSED_DATA019")
    a.fields(row,dict(schema_version=SCHEMA,index=158,before=151,run=1,
        base_step_pin=base.CONFIG.pin,capsule_pin=CAPSULE),"EXACT_DATA_CONTEXT")
    a.exact(row["manifest_pin"]["path"],manifest.PATH,"EXPLICIT_SOURCE_MANIFEST")
    a.exact(row["qualification_pin"]["path"],QUAL,"NEW_CONTROLLER_QUALIFICATION")
    require(set(base.scope.pins(row["controller_code_pins"],2))=={SELF,TEST},"BOTH_CONTROLLER_SOURCES")
    return row


def own_inputs(q):
    global _checkpoint
    only158();_checkpoint=q.checkpoint
    row=validate_data(q.json(DATA))
    code=a.read_exact(q,row["qualification_pin"])
    a.fields(code,dict(state=QUAL_STATE,contracts=dict(run=7,errors=0,failures=0,skipped=0),
        cleanup_confirmed=True,actual_product_or_Native_executed=False),"QUALIFIED_CODE7_ONLY")
    a.exact(code["new_code_pins"],row["controller_code_pins"],"EXACT_QUALIFIED_CONTROLLER")
    for pin in row["controller_code_pins"]:a.exact(q.pin(pin["path"]),pin,"CURRENT_CODE")
    live,_,_=manifest.load(q,row["manifest_pin"],a)
    a.exact(live.descriptors(),binding_value().descriptors(),"BOOTSTRAP_AND_RUNTIME_SAME11_BINDINGS")
    a.exact(dict(live.manifest_pin),dict(binding_value().manifest_pin),"SAME_MANIFEST")
    a.exact(q.pin(CAPSULE["path"]),CAPSULE,"CAPSULE_IN_WHOLE_SCOPE")
    for filename in SUPPORT:
        record=q.json(filename)
        require(record["state"].startswith("PASS_") and record["cleanup_confirmed"] is True,"EXACT_SUPPORT_NOT_PRODUCT")
        for pin in record.get("new_code_pins",[])+record.get("source_pins",[]):
            a.exact(q.pin(pin["path"]),pin,"CURRENT_CONNECTION_CODE")
    for pin in prior.COMPONENT_PINS:a.exact(q.pin(pin["path"]),pin,"ALL_ORIGINAL_NATIVE_WINDOW_CODE")
    q.pin(prior.SELF);q.pin(prior.TEST)
    marker=q.json(PRIOR_MARKER_QUAL)
    require(marker["state"].startswith("PASS_") and marker["cleanup_confirmed"] is True,"PRIOR_ACCEPTED_MARKER_QUAL")
    a.exact(marker["contracts"],dict(run=5,errors=0,failures=0,skipped=0),"ORIGINAL_MARKER_CODE5")
    for pin in marker["new_code_pins"]:a.exact(q.pin(pin["path"]),pin,"UNCHANGED_ACCEPTED_MARKER_SOURCE")
    return row


def binding(q):
    own_inputs(q)
    pin,data=q._read(prior.M.V3.OLD.API.BASE_PIN["path"],parse=True);q._bind(pin["path"],pin)
    a.exact(pin,prior.M.V3.OLD.API.BASE_PIN,"ORIGINAL_WHOLE_BINDING_BYTES")
    fn,_=prior.M.V3.OLD.API.binding_projection(bytes(data),replacement=previous_validation)
    required,rust=fn(q)
    return base.scope.extend(required,q.snapshots),rust


def binding_attempt(q,run):
    require(type(run) is int and run==1,"NO_UNREVIEWED_RETRY")
    return binding(q)


def template():
    only158();engine,proof=prior.template()
    engine.run_owned.__globals__.update(SELF=SELF,TEST=TEST)
    engine.worker.__globals__.update(SELF=SELF,TEST=TEST)
    connected,state=parent.connect_engine(engine,binding_value());PARENT_STATES.append(state)
    return connected,dict(proof,explicit_parent_physical_Frame_connected=True,
        complete_worker_transport_and_product_qualification_not_claimed=True)


def worker(task):
    only158();a.exact(task,worker_policy.TASK,"EXACT_SINGLE_WORKER")
    # Parent performs full admission/locks before its original GO. Worker reads
    # only the bounded pinned capsule, not the historical receipts again.
    engine,_=prior.template()
    policy=worker_policy.raw_policy.Policy(c.ROOT,binding_value(),lambda:True,lambda:None)
    execute,state=worker_policy.connect_worker(engine.worker,policy)
    return execute(task)


def context(step):
    return NS(**{**vars(prior.context(step)),"SELF":SELF,"TEST":TEST})


ACCEPTED_DIRECT=window_acceptance.direct_oracle(prior.OLD17.DIRECT,prior.NATIVE)
_accepted_validator=prior.LINK.clone(prior.validator,DIRECT=ACCEPTED_DIRECT)
_accepted_candidate=prior.LINK.clone(prior.validate_candidate,validator=_accepted_validator)
_accepted_project=prior.LINK.clone(prior.CURRENT_SOURCE.prepare_projection,validate_candidate=_accepted_candidate)
_accepted_prepare=prior.LINK.clone(prior.CURRENT_SOURCE.prepare,prepare_projection=_accepted_project)
ACCEPTED_SOURCE=NS(**{**vars(prior.CURRENT_SOURCE),"prepare_projection":_accepted_project,
    "prepare":_accepted_prepare,"validate_candidate":_accepted_candidate})


def previous_validation(q,row,listing,oldbody,fresh,ctx,flat=True):
    if ctx.INDEX<=156:return prior.previous_validation(q,row,listing,oldbody,fresh,ctx,flat)
    require(ctx.INDEX==157 and base.CONFIG.index==158,"ONLY_ACCEPTED157_PREDECESSOR")
    original=prior.previous_function(157)
    fn=prior.LINK.clone(original,source=ACCEPTED_SOURCE,validator=_accepted_validator,context=prior.context)
    return fn(q,row,listing,oldbody,fresh,ctx,flat)


def validator(raw,ctx,flat=True):
    if ctx.INDEX<=157:return _accepted_validator(raw,ctx,flat)
    require(ctx.INDEX==158 and callable(_checkpoint),"EXPLICIT_CURRENT_ORACLE_GUARD")
    generator,proof=prior.OLD17.validator(raw,ctx,flat)
    generator=prior.LINK.projector(generator,ACCEPTED_DIRECT,158)
    generator.__globals__["CONTROLLERS"]=tuple(dict.fromkeys(generator.__globals__["CONTROLLERS"]+
        (SELF,TEST,parent.SELF,parent.TEST,worker_policy.SELF,worker_policy.TEST,full_oracle.SELF,full_oracle.TEST)))
    projected,_=full_oracle.projector(generator,binding_value(),prior.DIRECT.runtime_budget,_checkpoint)
    return projected,dict(proof,explicit_semantic_physical_full_oracle_connection=True)


def validate_candidate(q,row,listing,oldbody,fresh,ctx,flat=True):
    global _checkpoint
    if ctx.INDEX<=157:return prior.validate_candidate(q,row,listing,oldbody,fresh,ctx,flat)
    _checkpoint=q.checkpoint
    original_budget=prior.DIRECT.runtime_budget
    def budget(required,requests):
        return binding_value().runtime_budget(required,requests,original_budget,q.checkpoint)
    direct=NS(**{**vars(prior.DIRECT),"runtime_budget":budget,
        "cost":prior.LINK.clone(prior.DIRECT.cost,runtime_budget=budget),
        "retained_evidence":prior.LINK.clone(prior.DIRECT.retained_evidence,runtime_budget=budget)})
    linked,_=prior.OLD17.OLD16.ORACLE.connect_full(prior.OLD17.OLD16._original_source.validate_candidate,
        prior.NEW_CANDIDATE,direct)
    check=prior.LINK.clone(linked,validator=validator)
    result,proof=check(q,row,listing,oldbody,fresh,ctx,flat)
    proof.update(prior.OLD17.OLD16.metadata_identity_evidence(row))
    proof.update(prior.LINK.evidence(row,prior.M.a))
    # All strict-window predicates remain; only the explicitly qualified case
    # metadata changes from157 to158. Real timing must pass on the candidate.
    original=prior.WINDOW_LINK.check_evidence;code=original.__code__
    require(sum(type(x) is int and x==157 for x in code.co_consts)==1,"ONE_WINDOW_CASE_LITERAL")
    changed=code.replace(co_consts=tuple(158 if type(x) is int and x==157 else x for x in code.co_consts))
    require(changed.replace(co_consts=code.co_consts)==code,"ALL_STRICT_WINDOW_PREDICATES_RETAINED")
    window=FunctionType(changed,original.__globals__,argdefs=original.__defaults__,closure=original.__closure__)
    proof.update(window(row,a));return result,proof


_project=prior.LINK.clone(prior.CURRENT_SOURCE.prepare_projection,
    validate_candidate=validate_candidate,runtime=NS(context=context))
_prepare=prior.LINK.clone(prior.CURRENT_SOURCE.prepare,prepare_projection=_project)
CURRENT_SOURCE=NS(**{**vars(prior.CURRENT_SOURCE),"prepare_projection":_project,
    "prepare":_prepare,"validate_candidate":validate_candidate})
_family=prior._full_prepare.__globals__;_env=dict(_family)
for _name,_fn in tuple(_env.items()):
    if type(_fn) is FunctionType and _fn.__globals__ is _family:
        _env[_name]=FunctionType(_fn.__code__,_env,argdefs=_fn.__defaults__,closure=_fn.__closure__)
_env.update(SELF=SELF,TEST=TEST,FILES=(SELF,TEST),QUAL_PATH=QUAL,source=CURRENT_SOURCE,
    own_inputs=own_inputs,validator=validator,context=context,template=template,binding=binding,
    binding_attempt=binding_attempt,previous_validation=previous_validation)
API=NS(**_env)


def run_owned(run):
    only158();require(type(run) is int and run==1,"ONE_PRODUCT_ATTEMPT")
    require(not (c.ROOT/prior.RETRY.root_path(base.CONFIG)).exists(),"NO_SUCCESSFUL_OR_FAILED_ROOT_OVERWRITE")
    execute,state=prior.CONNECTION.connect_run(API.run_owned,prior.BACKEND)
    return execute(run)


def preflight_data(q):return own_inputs(q)


def preflight_projection(raw,leaf):
    old=prior.preflight_projection(raw,leaf);code=old.__code__
    before="-product-window-preflight019.v1.json";after="-envelope-controller-preflight021.v1.json"
    require(sum(type(x) is str and x==before for x in code.co_consts)==1,"ONE_NEW_PREFLIGHT_DESTINATION")
    changed=code.replace(co_consts=tuple(after if type(x) is str and x==before else x for x in code.co_consts))
    require(changed.replace(co_consts=code.co_consts)==code,"FULL_ORIGINAL_PREFLIGHT_CODE_RETAINED")
    def budget(required,requests):
        require(callable(_checkpoint),"CURRENT_FULL_PREFLIGHT_GUARD")
        return binding_value().runtime_budget(required,requests,prior.DIRECT.runtime_budget,_checkpoint)
    prebase=NS(**{**vars(old.__globals__["base"]),"native":prior.NATIVE,
        "stable":NS(**{**vars(old.__globals__["base"].stable),"runtime_budget":budget})})
    return FunctionType(changed,dict(old.__globals__,SELF=SELF,TEST=TEST,template=template,
        binding_attempt=binding_attempt,connection_data=preflight_data,own_inputs=own_inputs,
        data_path=lambda index:DATA,base=prebase),argdefs=old.__defaults__,closure=old.__closure__)


def preflight():
    return prior.LINK.clone(prior.preflight,preflight_projection=preflight_projection)()


if __name__=="__main__":
    try:
        if len(sys.argv)==4 and sys.argv[1:3]==["--owned-worker","--task"]:
            base.configure(base.task_index(sys.argv[3]));raise SystemExit(worker(sys.argv[3]))
        p=argparse.ArgumentParser();p.add_argument("--case",type=int,required=True)
        p.add_argument("--run",type=int);p.add_argument("--preflight",action="store_true")
        args=p.parse_args();base.configure(args.case);only158()
        require((args.run is not None)!=args.preflight,"ONE_MODE")
        raise SystemExit(preflight() if args.preflight else run_owned(args.run))
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        code=str(error) if isinstance(error,ValueError) and re.fullmatch("[A-Za-z0-9_]{1,256}",str(error)) else "REDACTED_V19_FAILURE"
        print(json.dumps(dict(state="FAILED_NOT_ACCEPTED",error_code=code)))
        raise SystemExit(2) from None
