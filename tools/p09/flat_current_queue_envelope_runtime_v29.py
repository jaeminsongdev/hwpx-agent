"""Actual160/run002 controller; whole original engine and oracle retained."""
import argparse
import json
import re
import sys
from types import CodeType,FunctionType,SimpleNamespace as NS
import flat_current_queue_envelope_runtime_v25 as old

SELF="tools/p09/flat_current_queue_envelope_runtime_v29.py"
TEST="tools/p09/tests/test_flat_current_queue_envelope_runtime_v29.py"
PRIOR_PIN={"path":"tools/p09/flat_current_queue_envelope_runtime_v28.py","sha256":"04ed4e1c035fc2782a7cb5281c4df0a30ce0ba8d031867dd1edcd016a7895ccd","bytes":12055}
NEXT_PINS=[{"path":"tools/p09/same_reader_manifest_declaration_once_v1.py","sha256":"4a21470bfbfab8aa2e0949b8f4d1e04ba6bb1cb61031a692666617beb311457f","bytes":3814},{"path":"tools/p09/successor_manifest_shared_admission_v1.py","sha256":"303b26d56d58926be7a1b700b35994770d229a0867ddb6a14e24e8698777caab","bytes":3014},{"path":"tools/p09/reviewed_case160_attempt_v1.py","sha256":"6c803ce19d4e8b3254adf746cf8eca6a4653165c8227694676ccb42d21979a3a","bytes":3691},{"path":"tools/p09/runtime_failed160_partial_projection_v1.py","sha256":"332a73ebe099d24d905a902d7d96c31c16864adba079a7873ac510b7d32862c4","bytes":3113},{"path":"tools/p09/runtime_failed160_partial_projection_v2.py","sha256":"7a22cccdaf3d5189efa8226ea8c43951d47de7db12953ee7c4318f02c1483871","bytes":1626},{"path":"tools/p09/runtime_successor_manifest_v4.py","sha256":"f2778e2e3a130d240fdbaeff87fd89ccd53fd5f3d0c8435be9917ab49fb99ac4","bytes":4327},{"path":"tools/p09/runtime_successor_worker_capsule_v3.py","sha256":"69abba4096b0ffc75250ada632029f72ba39e78176c2855a9ed94b10ae83d7b4","bytes":1051},{"path":"tools/p09/successor_runtime_graph_v3.py","sha256":"396e1d4ac71d755138b3a7139f6299d326a629e2d38756599e7bd80f0b3042ea","bytes":2616},{"path":"tools/p09/successor_bounded_graph_bootstrap_v3.py","sha256":"fefcbf55d100baf404b407f7fa32265ff0cfa1fa1949e978cc681a447c0b2938","bytes":2258},{"path":"tools/p09/successor_current_binding_v3.py","sha256":"4769b3deedfe46df69dcf66cd9b86b26fe342945c515b791703167358a882008","bytes":1837}]
prior_bundle,prior_proof=old.namespace_bundle.load(old.c.ROOT,[PRIOR_PIN],
    {"flat_current_queue_envelope_runtime_v25":old})
PRIOR160=prior_bundle.flat_current_queue_envelope_runtime_v28
reuse={**vars(PRIOR160.PRIOR159.SOURCE_NAMESPACES),**vars(PRIOR160.NEXT),
    **vars(old._attempt),**vars(old._roles),"flat_current_queue_envelope_runtime_v25":old}
NEXT,NEXT_PROOFS=old.namespace_bundle.load(old.c.ROOT,NEXT_PINS,reuse)
RAW_PINS=PRIOR160.RAW_PINS+[PRIOR_PIN]+NEXT_PINS
RAW_TEST_PIN=PRIOR160.RAW_TEST_PIN
SOURCE_PROOFS=PRIOR160.SOURCE_PROOFS+prior_proof+NEXT_PROOFS
_family=PRIOR160.M.only160.__globals__;_env=dict(_family)
META={"case160-current-r001-tests":"case160-current-r002-tests",
    "-envelope-controller-preflight036.v1.json":"-envelope-controller-preflight037.v1.json"}
CODE_PROOFS={}
def project(code,mapping):
    return code.replace(co_consts=tuple(project(x,mapping) if type(x) is CodeType else
        mapping.get(x,x) if type(x) in (int,str) else x for x in code.co_consts))
for name,fn in tuple(_family.items()):
    if type(fn) is FunctionType and fn.__globals__ is _family:
        code=project(fn.__code__,META)
        old.a.require(project(code,{v:k for k,v in META.items()})==fn.__code__,"ENTIRE_ORIGINAL160_CONTROLLER_METADATA_INVERSE")
        new=FunctionType(code,_env,argdefs=fn.__defaults__,closure=fn.__closure__)
        new.__kwdefaults__=fn.__kwdefaults__;_env[name]=new
        CODE_PROOFS[name]=dict(original_entire_code_metadata_inverse=True,defaults_closure_kwdefaults_retained=True)

DATA="implementation/p09/evidence/p09-361-case160-envelope-controller-data037.v1.json"
QUAL="implementation/p09/evidence/p09-361-case160-run002-controller-code18-r798.v1.json"
QUAL_STATE="PASS_CURRENT160_RUN002_CONTROLLER_CODE18_ORIGINAL_BOUND64_NOT_NATIVE_OR_GO"
SCHEMA="hwpx-agent.p09-envelope-current-controller/v29"
PREFLIGHT="implementation/p09/evidence/p09-361-case160-envelope-controller-preflight037.v1.json"
BINDING_CODE="implementation/p09/evidence/p09-361-case160-run002-bootstrap-full-binding-code7-r796.v1.json"
bootstrap=NEXT.successor_bounded_graph_bootstrap_v3
binding_module=NEXT.successor_current_binding_v3
attempt=NEXT.reviewed_case160_attempt_v1
CAPSULE=NEXT.successor_runtime_graph_v3.CAPSULE
MANIFEST=bootstrap.MANIFEST
DISTINCT_TEMPLATE,RETRY,ATTEMPT_PROOF=attempt.connect_template(old.prior)
prior=NS(**{**vars(old.prior),"template":DISTINCT_TEMPLATE})
_env.update(SELF=SELF,TEST=TEST,DATA=DATA,QUAL=QUAL,QUAL_STATE=QUAL_STATE,SCHEMA=SCHEMA,
    PREFLIGHT=PREFLIGHT,BINDING_CODE=BINDING_CODE,bootstrap=bootstrap,CAPSULE=CAPSULE,MANIFEST=MANIFEST,
    RETRY=RETRY,prior=prior,_graph=None,_checkpoint=None,_execution_requested=False,PARENT_STATES=[],
    current_binding=NS(**{**vars(binding_module),"successor":PRIOR160.NEXT.runtime_successor_binding_v2}))

def validate_data(row):
    _env["only160"]()
    old.a.require(type(row) is dict and set(row)=={"schema_version","index","before","run","physical_product_run",
        "base_step_pin","authority_pin","prior_runtime_pin","manifest_pin","capsule_pin",
        "qualification_pin","controller_code_pins","binding_code_pin"},"CLOSED_RUN002_DATA")
    old.a.fields(row,dict(schema_version=SCHEMA,index=160,before=153,run=1,physical_product_run=2,
        base_step_pin=old.base.CONFIG.pin,authority_pin=_env["current_binding"].successor.AUTHORITY,
        prior_runtime_pin=_env["current_binding"].successor.ROOT,manifest_pin=MANIFEST,capsule_pin=CAPSULE),
        "EXACT_CURRENT160_RUN002_DATA")
    old.a.require(set(old.base.scope.pins(row["controller_code_pins"],2))=={SELF,TEST},"EXACT_CONTROLLER_PAIR")
    old.a.require(row["qualification_pin"]["path"]==QUAL and row["binding_code_pin"]["path"]==BINDING_CODE,
        "EXACT_RUN002_CODE_PATHS")
    old.base.scope.pins([row["qualification_pin"],row["binding_code_pin"]],2)
    return row

def own_inputs(q):
    _env["only160"]();_env["_checkpoint"]=q.checkpoint
    row=validate_data(q.json(DATA))
    code=old.a.read_exact(q,row["qualification_pin"])
    old.a.fields(code,dict(state=QUAL_STATE,contracts=dict(run=18,errors=0,failures=0,skipped=0),
        actual160_product_or_Native_executed=False,actual160_GO_authorized=False,cleanup_confirmed=True),
        "EXACT_RUN002_CONTROLLER_CODE18")
    old.a.exact(code["new_code_pins"],row["controller_code_pins"],"SAME_QUALIFIED_CONTROLLER_BYTES")
    for pin in code["source_pins"]+row["controller_code_pins"]+RAW_PINS+[RAW_TEST_PIN]:
        old.a.exact(q.pin(pin["path"]),pin,"ALL_ORIGINAL_AND_CURRENT_RAW_INPUTS")
    bound=old.a.read_exact(q,row["binding_code_pin"])
    old.a.fields(bound,dict(state="PASS_RUN002_BOOTSTRAP_CODE7_ORIGINAL_WHOLE25_BINDING_NOT_CONTROLLER_PREFLIGHT_OR_GO",
        contracts=dict(run=7,errors=0,failures=0,skipped=0),source_pairs=25,rust_source_count=787,
        cleanup_confirmed=True,Native_or_product_executed=False,queue_acceptance_called=False),
        "EXACT_QUALIFIED_WHOLE25_BINDING")
    for pin in bound["source_pins"]:old.a.exact(q.pin(pin["path"]),pin,"CURRENT_WHOLE_BINDING_SOURCES")
    for pin in old.TIMING_PINS+old.NAMESPACE_SOURCE_PINS+old.ROLE_PINS+[old.ROLE_ONCE_PIN]:
        old.a.exact(q.pin(pin["path"]),pin,"ORIGINAL_TIMING_CORE_FAILURE_INPUTS")
    for filename in old.SUPPORT:
        support=q.json(filename)
        old.a.require(support["state"].startswith("PASS_") and support["cleanup_confirmed"] is True,"ORIGINAL_SUPPORT")
        for pin in support.get("source_pins",[])+support.get("new_code_pins",[]):
            old.a.exact(q.pin(pin["path"]),pin,"ORIGINAL_SUPPORT_SOURCE")
    attempt.reviewed_failure(q,old.a)
    old.a.exact(q.pin(MANIFEST["path"]),MANIFEST,"ACTUAL_MANIFEST026")
    old.a.exact(q.pin(CAPSULE["path"]),CAPSULE,"ACTUAL_CAPSULE002")
    return row

owned,ADMISSION_COUNTS=old.admission_once.connect(own_inputs)
_env.update(own_inputs=owned,validate_data=validate_data)
def binding(q):
    owned(q)
    complete,rust,fresh,live,_=binding_module.bind(q,PRIOR160.PRIOR159)
    graph=_env["graph_value"]()
    old.a.exact(live.descriptors(),graph.binding.descriptors(),"SAME_ACTUAL25_BINDING")
    old.a.exact(dict(live.manifest_pin),dict(graph.binding.manifest_pin),"SAME_ACTUAL_MANIFEST026")
    old.a.exact(fresh.context,graph.context,"SAME_CURRENT160_CONTEXT")
    old.a.exact(fresh.partial_admission,graph.partial_admission,"SAME_PARTIAL_FAILURE_ADMISSION")
    if _env["_execution_requested"]:
        checked=q.json(PREFLIGHT)
        old.a.fields(checked,dict(state="PASS_REVIEWED_METADATA_CONNECTION_PREFLIGHT_NOT_NATIVE_OR_PRODUCT_OR_ACCEPTANCE",
            index=160,product_worker_or_Native_frame_executed=False,cleanup_confirmed=True,
            runtime_connection_qualified=False,accepted_count_delta=0),"EXACT_WHOLE_RUN002_PREFLIGHT")
        old.a.exact(checked["connection_data_pin"],q.snapshots[DATA],"SAME_CURRENT_DATA_AS_PREFLIGHT")
        old.a.require(type(checked["fresh_inputs"]) is int and checked["fresh_inputs"]>0 and
            checked["fresh_inputs"]==checked["final_fresh_hashes"],"ALL_PREFLIGHT_FINAL_HASHES")
        old.a.require(not checked.get("synthetic_fixture_only_not_evidence",False),"NO_SYNTHETIC_PREFLIGHT")
        old.a.resource_history(checked["resource_samples"])
    return old.base.scope.extend(complete,q.snapshots),rust
_env["binding"]=binding

def run_owned(public_run):
    _env["only160"]()
    old.a.require(type(public_run) is int and public_run==2,"EXACT_REVIEWED160_PHYSICAL_RUN002")
    old.a.require(not (old.c.ROOT/RETRY.root_path(old.base.CONFIG)).exists(),"REFUSE_EXISTING_RUN002_ROOT")
    old.a.require((old.c.ROOT/PREFLIGHT).is_file(),"WHOLE_RUN002_PREFLIGHT_REQUIRED")
    old.a.require(not _env["_execution_requested"],"NO_AUTOMATIC_RETRY")
    _env["_execution_requested"]=True
    execute,state=prior.CONNECTION.connect_run(API.run_owned,prior.BACKEND)
    before=len(prior.ATTEMPT_STATES);result=execute(RETRY.public_run(160,public_run))
    observed=prior.ATTEMPT_STATES[before:]
    old.a.require(len(observed)==1 and observed[0].physical_product_run==2 and
        observed[0].actual_engine_calls==1,"ONE_ORIGINAL_PHYSICAL2_ENGINE")
    old.a.require(state["actual_local_bindings"]==1,"ONE_NATIVE_DIAGNOSTIC_BINDING")
    return result
_env["run_owned"]=run_owned
source_projection=prior.LINK.clone(prior.CURRENT_SOURCE.prepare_projection,root_path=RETRY.root_path,
    validate_candidate=_env["validate_candidate"],runtime=NS(context=_env["context"]))
source=NS(**{**vars(prior.CURRENT_SOURCE),"prepare_projection":source_projection,
    "validate_candidate":_env["validate_candidate"]})
_env["CURRENT_SOURCE"]=source
_api_family=prior._full_prepare.__globals__;_api_env=dict(_api_family)
for name,fn in tuple(_api_family.items()):
    if type(fn) is FunctionType and fn.__globals__ is _api_family:
        new=FunctionType(fn.__code__,_api_env,argdefs=fn.__defaults__,closure=fn.__closure__)
        new.__kwdefaults__=fn.__kwdefaults__;_api_env[name]=new
_api_env.update(SELF=SELF,TEST=TEST,FILES=(SELF,TEST),QUAL_PATH=QUAL,source=source,
    own_inputs=owned,validator=_env["validator"],context=_env["context"],template=_env["template"],
    binding=binding,binding_attempt=_env["binding_attempt"],
    previous_validation=PRIOR160.NEXT.successor_current_binding_v2.previous_callback(PRIOR160.PRIOR159))
API=NS(**_api_env);API.prepare=_env["independent_prepare_not_qualified"];API.accept=API.prepare
_env["API"]=API;M=NS(**_env)

def test_namespace():
    ns,proof=old.namespace_bundle.load(old.c.ROOT,[RAW_TEST_PIN],{"flat_current_queue_envelope_runtime_v26":M})
    module=ns.test_flat_current_queue_envelope_runtime_v26
    mapping={159:160,152:153,20:25,
        "-envelope-controller-preflight034.v1.json":"-envelope-controller-preflight037.v1.json",
        "case159-current-r001-tests":"case160-current-r002-tests",
        "case159-current-r002-tests":"case160-current-r003-tests"}
    original_data=module.data
    def data():
        row=original_data();row.update(index=160,before=153,physical_product_run=2);return row
    original_data.__globals__["data"]=data;module.data=data
    for name,fn in tuple(vars(module.Tests).items()):
        target=fn.__func__ if type(fn) is classmethod else fn
        if type(target) is FunctionType:
            specific=dict(mapping)
            if name=="test_actual_original_engine_and_worker_connected_not_executed":specific[1]=2
            if name in ("test_existing_runtime_never_overwritten","test_missing_whole_pref_denied_before_engine"):specific[1]=2
            if name=="test_wrong_physical_run_never_starts_engine":specific[2]=1
            revised=project(target.__code__,specific)
            old.a.require(project(revised,{v:k for k,v in specific.items()})==target.__code__,"WHOLE_ORIGINAL_CONTROLLER_TEST_INVERSE")
            new=FunctionType(revised,target.__globals__,argdefs=target.__defaults__,closure=target.__closure__)
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
        label=str(error) if isinstance(error,ValueError) and re.fullmatch("[A-Za-z0-9_]{1,256}",str(error)) else "REDACTED_V29_FAILURE"
        print(json.dumps(dict(state="FAILED_NOT_ACCEPTED",error_code=label)));raise SystemExit(2) from None
