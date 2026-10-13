"""Exact160 controller with original engine, worker and whole oracle bodies.

All prior/current raw namespaces remain real source inputs. The helper ceiling,
Native600, window15, both byte boundaries and independent159 oracle survive.
"""
import argparse
import json
import re
import sys
from types import CodeType,FunctionType,SimpleNamespace as NS
import flat_current_queue_envelope_runtime_v25 as old

SELF="tools/p09/flat_current_queue_envelope_runtime_v28.py"
TEST="tools/p09/tests/test_flat_current_queue_envelope_runtime_v28.py"
PRIOR_PIN={"sha256":"55f2afbc6a8fb5641cb6392335925b3f52008330f22db261646bbb61973ac290","bytes":6189,"path":"tools/p09/flat_current_queue_envelope_runtime_v27.py"}
NEXT_PINS=[{"sha256":"761b7e635c87ccd715b13a362295b260e12f85983e8b594fc0f1454a8db528f5","bytes":5737,"path":"tools/p09/isolated_predecessor159_prepare_v1.py"},{"sha256":"d6c319a799e7adde609c24b5f8ea3def6a84724ecbb44062acfb74241de50058","bytes":2902,"path":"tools/p09/current_successor_acceptance_prepare_v1.py"},{"sha256":"453e33b3289ce59520626df429be906f8facbba5944c9d868aec777f6defbd94","bytes":4948,"path":"tools/p09/runtime_successor_binding_v2.py"},{"sha256":"28ceb78b8fd2e2ef2a8c56e16734ea45e9ac464bf351779c0021c6bfeff7d164","bytes":4405,"path":"tools/p09/runtime_successor_manifest_v2.py"},{"sha256":"b980270b55af17928cfb204dc811f3c65635ba72c13353cfc982ce1e8a596500","bytes":3108,"path":"tools/p09/runtime_successor_worker_capsule_v2.py"},{"sha256":"743c0d06355831ff49ae563f4280e218fb7fd2848cd6f426351ec3fd5200d5fc","bytes":2506,"path":"tools/p09/successor_runtime_graph_v2.py"},{"sha256":"43e14d5aa049f550c13e4da053d59731f0f3e95b287acff4907b068712a378b4","bytes":4989,"path":"tools/p09/successor_current_binding_v2.py"},{"sha256":"8c03f979c7a90b476a808fdbdc08d674e60dd6d84a5002b992e585a719346558","bytes":1601,"path":"tools/p09/successor_bounded_graph_bootstrap_v2.py"},{"sha256":"f1b69bd5afd5aa531304954e600115eb38c3ab402884451b57f4c80eced1f56c","bytes":1213,"path":"tools/p09/successor_strict_window_v2.py"}]
_predecessor,_prior_proof=old.namespace_bundle.load(old.c.ROOT,[PRIOR_PIN],
    {"flat_current_queue_envelope_runtime_v25":old})
PRIOR159=_predecessor.flat_current_queue_envelope_runtime_v27
_reuse={**vars(PRIOR159.SOURCE_NAMESPACES),"flat_current_queue_envelope_runtime_v25":old}
NEXT,NEXT_PROOFS=old.namespace_bundle.load(old.c.ROOT,NEXT_PINS,_reuse)
RAW_PINS=PRIOR159.RAW_PINS+[PRIOR_PIN]+NEXT_PINS
RAW_TEST_PIN=PRIOR159.RAW_TEST_PIN
SOURCE_PROOFS=PRIOR159.SOURCE_PROOFS+_prior_proof+NEXT_PROOFS
_family=PRIOR159.M.only159.__globals__;_env=dict(_family)
META={159:160,152:153,"case159-current-r001-tests":"case160-current-r001-tests",
    "-envelope-controller-preflight035.v1.json":"-envelope-controller-preflight036.v1.json"}
CODE_PROOFS={}


def project_code(code,mapping):
    values=tuple(project_code(x,mapping) if type(x) is CodeType else
        mapping.get(x,x) if type(x) in (int,str) else x for x in code.co_consts)
    return code.replace(co_consts=values)


for _name,_fn in tuple(_family.items()):
    if type(_fn) is FunctionType and _fn.__globals__ is _family:
        _changed=project_code(_fn.__code__,META)
        old.a.require(project_code(_changed,{v:k for k,v in META.items()})==_fn.__code__,
            "WHOLE_ORIGINAL159_CONTROLLER_METADATA_INVERSE")
        _new=FunctionType(_changed,_env,argdefs=_fn.__defaults__,closure=_fn.__closure__)
        _new.__kwdefaults__=_fn.__kwdefaults__;_env[_name]=_new
        CODE_PROOFS[_name]=dict(original_full_code_restored_by_metadata_inverse=True,
            original_defaults_closure_kwdefaults_retained=True)

DATA="implementation/p09/evidence/p09-361-case160-envelope-controller-data036.v1.json"
QUAL="implementation/p09/evidence/p09-361-case160-namespace-controller-code16-r768.v1.json"
QUAL_STATE="PASS_CURRENT160_NAMESPACE_CONTROLLER_CODE16_ORIGINAL_BOUND64_NOT_NATIVE_OR_GO"
SCHEMA="hwpx-agent.p09-envelope-current-controller/v28"
PREFLIGHT="implementation/p09/evidence/p09-361-case160-envelope-controller-preflight036.v1.json"
BINDING_CODE="implementation/p09/evidence/p09-361-case160-full-binding-r765.v1.json"
bootstrap=NEXT.successor_bounded_graph_bootstrap_v2
window=NEXT.successor_strict_window_v2
full_binding=NEXT.successor_current_binding_v2
CAPSULE=NEXT.successor_runtime_graph_v2.CAPSULE
MANIFEST=bootstrap.MANIFEST
_env.update(SELF=SELF,TEST=TEST,DATA=DATA,QUAL=QUAL,QUAL_STATE=QUAL_STATE,SCHEMA=SCHEMA,
    PREFLIGHT=PREFLIGHT,BINDING_CODE=BINDING_CODE,bootstrap=bootstrap,window=window,
    CAPSULE=CAPSULE,MANIFEST=MANIFEST,_graph=None,_checkpoint=None,
    _execution_requested=False,PARENT_STATES=[])
_env["only160"]=_env["only159"]


def own_inputs(q):
    _env["only160"]();_env["_checkpoint"]=q.checkpoint
    row=_env["validate_data"](q.json(DATA))
    code=old.a.read_exact(q,row["qualification_pin"])
    old.a.fields(code,dict(state=QUAL_STATE,contracts=dict(run=16,errors=0,failures=0,skipped=0),
        actual160_product_or_Native_executed=False,actual160_GO_authorized=False,
        cleanup_confirmed=True),"EXACT160_CONTROLLER_CODE16_NOT_PRODUCT")
    old.a.exact(code["new_code_pins"],row["controller_code_pins"],"EXACT_QUALIFIED160_CONTROLLER_BYTES")
    for pin in code["source_pins"]+row["controller_code_pins"]+RAW_PINS+[RAW_TEST_PIN]:
        old.a.exact(q.pin(pin["path"]),pin,"ALL_ORIGINAL_AND_CURRENT160_RAW_SOURCES")
    bound=old.a.read_exact(q,row["binding_code_pin"])
    old.a.fields(bound,dict(state="PASS_ACTUAL160_FULL_BINDING_PRIVATE159_WHOLE_ORACLE_NOT_CONTROLLER_PREFLIGHT_NATIVE_OR_GO",
        rust_source_count=787,source_pairs=24,cleanup_confirmed=True,
        default_current160_CONFIG_mutated=False,current160_product_or_Native_executed=False,
        queue_acceptance_called=False),"EXACT_ORIGINAL160_FULL_BINDING_NOT_PRODUCT")
    for pin in bound["source_pins"]:old.a.exact(q.pin(pin["path"]),pin,"QUALIFIED160_FULL_BINDING_SOURCES")
    for pin in old.TIMING_PINS+old.NAMESPACE_SOURCE_PINS+old.ROLE_PINS+[old.ROLE_ONCE_PIN]:
        old.a.exact(q.pin(pin["path"]),pin,"ORIGINAL_TIMING_CORE_FAILURE_SOURCES")
    for filename in old.SUPPORT:
        support=q.json(filename)
        old.a.require(support["state"].startswith("PASS_") and support["cleanup_confirmed"] is True,
            "EXACT_ORIGINAL_SUPPORT")
        for pin in support.get("source_pins",[])+support.get("new_code_pins",[]):
            old.a.exact(q.pin(pin["path"]),pin,"ORIGINAL_SUPPORT_SOURCE")
    old.a.exact(q.pin(MANIFEST["path"]),MANIFEST,"EXACT_CURRENT160_MANIFEST")
    old.a.exact(q.pin(CAPSULE["path"]),CAPSULE,"EXACT_CURRENT160_CAPSULE")
    return row


_owned,ADMISSION_COUNTS=old.admission_once.connect(own_inputs)
_env["own_inputs"]=_owned


def binding(q):
    _owned(q)
    complete,rust,fresh,live,_=full_binding.bind(q,PRIOR159)
    current=_env["graph_value"]()
    old.a.exact(live.descriptors(),current.binding.descriptors(),"FRESH_AND_ENGINE_SAME_TWENTY_FOUR_PAIRS")
    old.a.exact(dict(live.manifest_pin),dict(current.binding.manifest_pin),"FRESH_AND_ENGINE_SAME160_MANIFEST")
    old.a.exact(fresh.context,current.context,"FRESH_AND_ENGINE_SAME160_CONTEXT")
    if _env["_execution_requested"]:
        checked=q.json(PREFLIGHT)
        old.a.fields(checked,dict(state="PASS_REVIEWED_METADATA_CONNECTION_PREFLIGHT_NOT_NATIVE_OR_PRODUCT_OR_ACCEPTANCE",
            index=160,product_worker_or_Native_frame_executed=False,cleanup_confirmed=True,
            runtime_connection_qualified=False,accepted_count_delta=0),"WHOLE_PREFLIGHT_BEFORE_ACTUAL160")
        old.a.exact(checked["connection_data_pin"],q.snapshots[DATA],"SAME_CLOSED160_DATA_AS_WHOLE_PREFLIGHT")
        old.a.require(type(checked["fresh_inputs"]) is int and checked["fresh_inputs"]>0 and
            type(checked["final_fresh_hashes"]) is int and checked["final_fresh_hashes"]==checked["fresh_inputs"],
            "ALL_WHOLE160_PREFLIGHT_FINAL_HASHES")
        old.a.require(checked.get("synthetic_fixture_only_not_evidence",False) is False,"NO_SYNTHETIC_PREFLIGHT")
        old.a.resource_history(checked["resource_samples"])
    return old.base.scope.extend(complete,q.snapshots),rust


_env["binding"]=binding
_env["current_binding"]=NS(**{**vars(full_binding),"successor":NEXT.runtime_successor_binding_v2})
prior=old.prior
_project=prior.LINK.clone(prior.CURRENT_SOURCE.prepare_projection,root_path=prior.RETRY.root_path,
    validate_candidate=_env["validate_candidate"],runtime=NS(context=_env["context"]))
source=NS(**{**vars(prior.CURRENT_SOURCE),"prepare_projection":_project,
    "validate_candidate":_env["validate_candidate"]})
_env["CURRENT_SOURCE"]=source
_api_family=prior._full_prepare.__globals__;_api_env=dict(_api_family)
for _name,_fn in tuple(_api_family.items()):
    if type(_fn) is FunctionType and _fn.__globals__ is _api_family:
        _new=FunctionType(_fn.__code__,_api_env,argdefs=_fn.__defaults__,closure=_fn.__closure__)
        _new.__kwdefaults__=_fn.__kwdefaults__;_api_env[_name]=_new
_api_env.update(SELF=SELF,TEST=TEST,FILES=(SELF,TEST),QUAL_PATH=QUAL,source=source,
    own_inputs=_owned,validator=_env["validator"],context=_env["context"],template=_env["template"],
    binding=binding,binding_attempt=_env["binding_attempt"],
    previous_validation=full_binding.previous_callback(PRIOR159))
API=NS(**_api_env)
API.prepare=_env["independent_prepare_not_qualified"];API.accept=API.prepare
_env["API"]=API
M=NS(**_env)


def test_namespace():
    ns,proof=old.namespace_bundle.load(old.c.ROOT,[RAW_TEST_PIN],
        {"flat_current_queue_envelope_runtime_v26":M})
    module=ns.test_flat_current_queue_envelope_runtime_v26
    mapping={159:160,152:153,20:24,
        "-envelope-controller-preflight034.v1.json":"-envelope-controller-preflight036.v1.json",
        "case159-current-r001-tests":"case160-current-r001-tests",
        "case158-current-r005-tests":"case159-current-r005-tests",
        "case159-current-r002-tests":"case160-current-r002-tests"}
    original_data=module.data
    changed_data=project_code(original_data.__code__,mapping)
    old.a.require(project_code(changed_data,{v:k for k,v in mapping.items()})==original_data.__code__,
        "ENTIRE_ORIGINAL_CONTROLLER_TEST_DATA_METADATA_INVERSE")
    new_data=FunctionType(changed_data,original_data.__globals__,argdefs=original_data.__defaults__,
        closure=original_data.__closure__)
    new_data.__kwdefaults__=original_data.__kwdefaults__
    original_data.__globals__["data"]=new_data;module.data=new_data
    for name,fn in tuple(vars(module.Tests).items()):
        target=fn.__func__ if type(fn) is classmethod else fn
        if type(target) is FunctionType:
            changed=project_code(target.__code__,mapping)
            old.a.require(project_code(changed,{v:k for k,v in mapping.items()})==target.__code__,
                "ENTIRE_ORIGINAL14_CONTROLLER_TEST_METADATA_INVERSE")
            new=FunctionType(changed,target.__globals__,argdefs=target.__defaults__,closure=target.__closure__)
            new.__kwdefaults__=target.__kwdefaults__
            setattr(module.Tests,name,classmethod(new) if type(fn) is classmethod else new)
    return module,proof


if __name__=="__main__":
    try:
        if len(sys.argv)==4 and sys.argv[1:3]==["--owned-worker","--task"]:
            M.base.configure(M.base.task_index(sys.argv[3]));raise SystemExit(M.worker(sys.argv[3]))
        p=argparse.ArgumentParser();p.add_argument("--case",type=int,required=True)
        p.add_argument("--run",type=int);p.add_argument("--preflight",action="store_true")
        args=p.parse_args();M.base.configure(args.case);M.only160()
        M.require((args.run is not None)!=args.preflight,"EXACTLY_ONE_MODE")
        raise SystemExit(M.preflight() if args.preflight else M.run_owned(args.run))
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        label=str(error) if isinstance(error,ValueError) and re.fullmatch("[A-Za-z0-9_]{1,256}",str(error)) else "REDACTED_V28_FAILURE"
        print(json.dumps(dict(state="FAILED_NOT_ACCEPTED",error_code=label)));raise SystemExit(2) from None
