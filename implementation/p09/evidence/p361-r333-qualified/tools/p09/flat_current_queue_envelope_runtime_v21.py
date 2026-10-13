"""Only158/run003 whole original controller with explicit lossless physical inputs.

Original engine/worker/whole preflight and historical validators survive.
New immutable DATA and CODE qualification are mandatory before GO. This module
does not accept a runtime candidate or advance the official queue.
"""
import argparse
import ast
import copy
import importlib
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
import flat_current_queue_source_stat_runtime_v2 as _base_source
BUNDLE_PIN=dict(path="tools/p09/runtime_envelope_namespace_bundle_v1.py",bytes=3320,
    sha256="385778d26e0c5d99ac6d38ccaeb6afd24bb4029e01b4a6e91683cb80e5e2da62")
with (_base_source.c.ROOT/BUNDLE_PIN["path"]).open("rb") as _stream:_bundle_raw=_stream.read(BUNDLE_PIN["bytes"]+1)
if len(_bundle_raw)!=BUNDLE_PIN["bytes"] or hashlib.sha256(_bundle_raw).hexdigest()!=BUNDLE_PIN["sha256"]:
    raise SystemExit("EXACT_NAMESPACE_BOOTSTRAP_SOURCE_REQUIRED")
_tree=ast.parse(_bundle_raw.decode("utf-8"));_nodes=copy.deepcopy([n for n in _tree.body if not isinstance(n,(ast.Import,ast.ImportFrom))])
_bundle_env=dict(ast=ast,copy=copy,hashlib=hashlib,importlib=importlib,NS=NS,
    __name__="p09_exact_namespace_bootstrap",__file__=BUNDLE_PIN["path"])
if [ast.dump(n,include_attributes=False) for n in _nodes]!=[ast.dump(n,include_attributes=False) for n in _tree.body if not isinstance(n,(ast.Import,ast.ImportFrom))]:
    raise SystemExit("ALL_NAMESPACE_BOOTSTRAP_DEFINITIONS_REQUIRED")
exec(compile(ast.fix_missing_locations(ast.Module(body=_nodes,type_ignores=[])),BUNDLE_PIN["path"],"exec"),_bundle_env)
namespace_bundle=NS(**_bundle_env)
LEAN_PIN={"path":"tools/p09/flat_preserved129_lean_connection_v2.py","bytes":12154,"sha256":"db26576ee889b94cf47035e80d5057876e29dfeb5991f043bafa3706cc079294"}
_lean,_lean_proof=namespace_bundle.load(_base_source.c.ROOT,[LEAN_PIN],{
    "flat_current_queue_source_stat_runtime_v2":_base_source})
lean=_lean.flat_preserved129_lean_connection_v2
PRIOR_WINDOW_PIN={"path":"tools/p09/flat_current_queue_product_window_runtime_v18.py","bytes":17491,"sha256":"1285a5cd5483cf4fb1057df1e6a2c35d656930b7ec4edd8297fe34d93c74db14"}
_window,_window_proof=namespace_bundle.load(lean.c.ROOT,[PRIOR_WINDOW_PIN],{
    "flat_preserved129_lean_connection_v2":lean})
prior=_window.flat_current_queue_product_window_runtime_v18
NAMESPACE_SOURCE_PINS=[{"path":"tools/p09/runtime_record_envelope_v1.py","bytes":3596,"sha256":"59f4a0bc32f7c03dd1651b5e31f45ad7311fb4b8a36d6490b9b39242895337e5"},{"path":"tools/p09/runtime_record_envelope_v2.py","bytes":2891,"sha256":"9a97c8c9c9a6281992430bfc224bbfea036da6d780389ac2777fbb403d62960f"},{"path":"tools/p09/runtime_envelope_source_projection_v1.py","bytes":6401,"sha256":"728ffdbac1a4b0edb44a8f34f26f912ac79d9c3bad0b5eb26c19b5102f788d5b"},{"path":"tools/p09/runtime_envelope_physical_io_v1.py","bytes":7214,"sha256":"b3bf5637c1f5d13bf9090236274826440e4c6c543b6db219a95b0869919c324c"},{"path":"tools/p09/held_envelope_boundary_guard_v1.py","bytes":1809,"sha256":"a65cd3c4c091e4e94b27b4d0474b2eafaf3fe2c4ac0682d7d95fa11c4d32e884"},{"path":"tools/p09/runtime_envelope_scope_binding_v1.py","bytes":10750,"sha256":"0105881d365213e70bd047b5c7fa8de6fda842f3103b71870c8f2224b3e4db3b"},{"path":"tools/p09/runtime_envelope_frame_connection_v1.py","bytes":3065,"sha256":"579aa5fb2e0d479077cf965c1dd449ab9fc48305bff9ea52a37bfb0f2688b4e5"},{"path":"tools/p09/runtime_envelope_raw_access_policy_v1.py","bytes":4423,"sha256":"74eff97e55402e5e08798ce03a122218b1047844caaf9f61cca92287601bb535"},{"path":"tools/p09/runtime_envelope_parent_connection_v1.py","bytes":6385,"sha256":"24c08ee3ebfa5898aba7f7548471f4bb4c30f05c7a35bff22923fa0e6563db19"},{"path":"tools/p09/runtime_envelope_worker_connection_v1.py","bytes":4745,"sha256":"4730608693080a9492dee36c14cbc606e69f5ec4d5aa2ea4c14a90475110bd92"},{"path":"tools/p09/runtime_envelope_full_oracle_connection_v1.py","bytes":4080,"sha256":"570dd57f96234991e5762689d11c404a64279d0a1fbf8ba38297680932a61863"},{"path":"tools/p09/runtime_envelope_source_manifest_v1.py","bytes":5616,"sha256":"67a1c6033abf6ff15ffa793bb549b7eff762c1bc921b87d1d51b6c5ad897df51"},{"path":"tools/p09/runtime_envelope_source_manifest_v2.py","bytes":3002,"sha256":"9bbc6a478f5d4a3d69f88d1bc35a20a68ec0ff7a48b1d6a7184b2a16c6693856"},{"path":"tools/p09/strict_product_window_acceptance_connection_v2.py","bytes":2592,"sha256":"37baf67827bbd7ed9780b5340707935dde4469154f05b00a007e54518bd1768e"}]
NAMESPACE_SOURCE_PINS=NAMESPACE_SOURCE_PINS+[{"path":"tools/p09/runtime_envelope_raw_access_policy_v2.py","bytes":1810,"sha256":"4070a0b1c7e717220fe2513398e1fa135eca4b1f40c11ab449cc6dce918d6bdf"},{"path":"tools/p09/runtime_envelope_parent_connection_v2.py","bytes":768,"sha256":"12360108843c71f4be058059470f26797a50c4e500fbe75d7d289f33c59dfeab"}]
_namespaces,NAMESPACE_PROOF=namespace_bundle.load(prior.M.c.ROOT,NAMESPACE_SOURCE_PINS,{
    "current_stored_runtime_scope":prior.M.base.scope,
    "owned_source_read_pressure":sys.modules["owned_source_read_pressure"],
    "strict_product_window_connection_v1":prior.WINDOW_LINK})
parent=_namespaces.runtime_envelope_parent_connection_v2
worker_policy=_namespaces.runtime_envelope_worker_connection_v1
full_oracle=_namespaces.runtime_envelope_full_oracle_connection_v1
manifest=_namespaces.runtime_envelope_source_manifest_v2
window_acceptance=_namespaces.strict_product_window_acceptance_connection_v2
ADMISSION_PIN={"path":"tools/p09/same_reader_source_admission_once_v1.py","bytes":1844,"sha256":"923ff5c4ce4d1b5fc58f0564ad852920881f0728570d4f1dd694bdd9171b1544"}
_admission,_admission_proof=namespace_bundle.load(prior.M.c.ROOT,[ADMISSION_PIN],{})
admission_once=_admission.same_reader_source_admission_once_v1
ATTEMPT_PINS=[{"path":"tools/p09/reviewed_case158_attempt_v3.py","bytes":3241,"sha256":"3b1b05141b47aaa8798733ed83fc6fc4232763e9bd8d29a168f3a614bb1b6bdd"},{"path":"tools/p09/reviewed_case158_attempt_v4.py","bytes":1984,"sha256":"9567a847d0def48b5ba5a69262ab7d12d05ce7902cac4c5998dd0f9290f18223"},{"path":"tools/p09/reviewed_case158_attempt_v5.py","bytes":3899,"sha256":"1c19a320d9abe6e6e8f00ba9dd85883d8df91da02cc1c6d9f0225339d4f920f8"}]
_attempt,_attempt_proof=namespace_bundle.load(prior.M.c.ROOT,ATTEMPT_PINS,{})
attempt=_attempt.reviewed_case158_attempt_v5
DISTINCT_TEMPLATE,RETRY,ATTEMPT_PROOF=attempt.connect_template(prior)
ATTEMPT_QUAL="implementation/p09/evidence/p09-361-case158-distinct-physical-run002-code7-r668.v1.json"

SELF="tools/p09/flat_current_queue_envelope_runtime_v21.py"
TEST="tools/p09/tests/test_flat_current_queue_envelope_runtime_v21.py"
DATA="implementation/p09/evidence/p09-361-case158-envelope-controller-data027.v1.json"
QUAL="implementation/p09/evidence/p09-361-case158-envelope-controller-run003-code22-r678.v1.json"
QUAL_STATE="PASS_CURRENT158_RUN003_ENVELOPE_CONTROLLER_CODE22_NOT_PRODUCT_OR_GO"
SCHEMA="hwpx-agent.p09-envelope-current-controller/v21"
CAPSULE=dict(path="implementation/p09/evidence/p09-361-case158-worker-policy-capsule001.v1.json",
    bytes=6383,sha256="37279afffea965613e416cb951d17da4c2c1ec7656bd28d9c58ef8042930b04c")
SUPPORT=["implementation/p09/evidence/"+name for name in (
    "p09-361-case158-raw-live-access-policy-code10-r640.v1.json",
    "p09-361-case158-full-oracle-connection-code9-r642.v1.json",
    "p09-361-case158-parent-connection-code9-r651.v1.json",
    "p09-361-case158-worker-policy-code12-actual11-capsule-r645.v1.json",
    "p09-361-case158-owned-worker-policy-diagnostic-r647.v1.json",
    "p09-361-case158-receipt-safe-policy-code4-r661.v1.json",
    "p09-361-case158-same-reader-admission-code7-r664.v1.json")]
PRIOR_MARKER_QUAL="implementation/p09/evidence/p09-361-case157-window-acceptance-marker-code5-r612.v1.json"
base=prior.M.base;a=prior.M.a;c=prior.M.c
_binding=None;_checkpoint=None
PARENT_STATES=[]


def require(ok,label):
    if not ok:raise ValueError("ENVELOPE_V21_"+label)


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
        "manifest_pin","capsule_pin","qualification_pin","controller_code_pins","physical_product_run","failed_attempt_pin","failed002_pin","failed002_review_pin"},"CLOSED_DATA019")
    a.fields(row,dict(schema_version=SCHEMA,index=158,before=151,run=1,
        base_step_pin=base.CONFIG.pin,capsule_pin=CAPSULE,physical_product_run=3,failed002_pin=attempt.STOPPED),"EXACT_DATA_CONTEXT")
    a.exact(row["manifest_pin"]["path"],manifest.PATH,"EXPLICIT_SOURCE_MANIFEST")
    a.exact(row["qualification_pin"]["path"],QUAL,"NEW_CONTROLLER_QUALIFICATION")
    require(set(base.scope.pins(row["controller_code_pins"],2))=={SELF,TEST},"BOTH_CONTROLLER_SOURCES")
    a.exact(row["failed_attempt_pin"]["path"],attempt.FAILED,"PRESERVED_FAILED_ATTEMPT_PATH")
    a.exact(row["failed002_review_pin"]["path"],attempt.REVIEW_PATH,"REVIEWED_STOP002_PIN_PATH")
    return row


def own_inputs(q):
    global _checkpoint
    only158();_checkpoint=q.checkpoint
    row=validate_data(q.json(DATA))
    code=a.read_exact(q,row["qualification_pin"])
    a.fields(code,dict(state=QUAL_STATE,contracts=dict(run=22,errors=0,failures=0,skipped=0),
        cleanup_confirmed=True,actual_product_or_Native_executed=False),"QUALIFIED_CODE7_ONLY")
    a.exact(code["new_code_pins"],row["controller_code_pins"],"EXACT_QUALIFIED_CONTROLLER")
    for pin in code["source_pins"]:a.exact(q.pin(pin["path"]),pin,"ALL_CONTROLLER_QUALIFIED_DEPENDENCIES")
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
    a.exact(q.pin(PRIOR_WINDOW_PIN["path"]),PRIOR_WINDOW_PIN,"RAW_ORIGINAL_V18_SOURCE_RETAINED")
    a.exact(q.pin(namespace_bundle.SELF),BUNDLE_PIN,"EXACT_NAMESPACE_BOOTSTRAP_SOURCE")
    a.exact(q.pin(LEAN_PIN["path"]),LEAN_PIN,"ORIGINAL_LEAN_SOURCE_RETAINED")
    for pin in NAMESPACE_SOURCE_PINS:a.exact(q.pin(pin["path"]),pin,"ALL_EXACT_RAW_NAMESPACE_SOURCES_IN_SCOPE")
    a.exact(q.pin(ADMISSION_PIN["path"]),ADMISSION_PIN,"EXACT_SAME_READER_ADMISSION_SOURCE")
    for pin in ATTEMPT_PINS:a.exact(q.pin(pin["path"]),pin,"ALL_DISTINCT_ATTEMPT_SOURCE_BYTES")
    attempt_code=q.json(ATTEMPT_QUAL)
    a.fields(attempt_code,dict(state="PASS_REVIEWED158_RUN002_TEMPLATE_DEPENDENCY_CODE7_NOT_ACTUAL_PRODUCT",
        contracts=dict(run=7,errors=0,failures=0,skipped=0),cleanup_confirmed=True),"QUALIFIED_DISTINCT_TEMPLATE_COMPONENT")
    for pin in attempt_code["new_code_pins"]:a.exact(q.pin(pin["path"]),pin,"ORIGINAL_DISTINCT_COMPONENT_SOURCES")
    attempt.reviewed_failure(q,a,row["failed002_review_pin"])
    a.exact(q.snapshots[attempt.FAILED],row["failed_attempt_pin"],"EXACT_FAILURE_HISTORY_IN_SCOPE")
    marker=q.json(PRIOR_MARKER_QUAL)
    require(marker["state"].startswith("PASS_") and marker["cleanup_confirmed"] is True,"PRIOR_ACCEPTED_MARKER_QUAL")
    a.exact(marker["contracts"],dict(run=5,errors=0,failures=0,skipped=0),"ORIGINAL_MARKER_CODE5")
    for pin in marker["new_code_pins"]:a.exact(q.pin(pin["path"]),pin,"UNCHANGED_ACCEPTED_MARKER_SOURCE")
    return row


_original_own_inputs=own_inputs
own_inputs,ADMISSION_COUNTS=admission_once.connect(_original_own_inputs)


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
    only158();engine,proof=DISTINCT_TEMPLATE()
    engine.run_owned.__globals__.update(SELF=SELF,TEST=TEST)
    engine.worker.__globals__.update(SELF=SELF,TEST=TEST)
    connected,state=parent.connect_engine(engine,binding_value());PARENT_STATES.append(state)
    return connected,dict(proof,explicit_parent_physical_Frame_connected=True,
        complete_worker_transport_and_product_qualification_not_claimed=True,
        distinct_physical_attempt=ATTEMPT_PROOF)


def worker(task):
    only158();a.exact(task,RETRY.task(158),"EXACT_SINGLE_WORKER")
    # Parent performs full admission/locks before its original GO. Worker reads
    # only the bounded pinned capsule, not the historical receipts again.
    engine,_=prior.template()
    policy=worker_policy.raw_policy.Policy(c.ROOT,binding_value(),lambda:True,lambda:None)
    execute,state=attempt.connect_worker(worker_policy.connect_worker,engine.worker,policy)
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
    RETRY.validate_actual(row,base.CONFIG,dict(path=RETRY.root_path(base.CONFIG)))
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
    root_path=RETRY.root_path,validate_candidate=validate_candidate,runtime=NS(context=context))
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
    only158();logical=RETRY.public_run(158,run)
    require(not (c.ROOT/RETRY.root_path(base.CONFIG)).exists(),"NO_SUCCESSFUL_OR_FAILED_ROOT_OVERWRITE")
    execute,state=prior.CONNECTION.connect_run(API.run_owned,prior.BACKEND)
    before=len(prior.ATTEMPT_STATES)
    result=execute(logical)
    observed=prior.ATTEMPT_STATES[before:]
    require(len(observed)==1 and observed[0].physical_product_run==3 and observed[0].actual_engine_calls==1,
        "ONE_ACTUAL_DISTINCT_ENGINE_CALL")
    require(state["actual_local_bindings"]==1,"ONE_ORIGINAL_NATIVE_DIAGNOSTIC_CONNECTION")
    return result


def preflight_data(q):return own_inputs(q)


def preflight_projection(raw,leaf):
    old=prior.preflight_projection(raw,leaf);code=old.__code__
    before="-product-window-preflight019.v1.json";after="-envelope-controller-run003-preflight028.v1.json"
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
        code=str(error) if isinstance(error,ValueError) and re.fullmatch("[A-Za-z0-9_]{1,256}",str(error)) else "REDACTED_V21_FAILURE"
        print(json.dumps(dict(state="FAILED_NOT_ACCEPTED",error_code=code)))
        raise SystemExit(2) from None
