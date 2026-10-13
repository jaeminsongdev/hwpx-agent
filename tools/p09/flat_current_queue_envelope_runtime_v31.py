"""Actual160/run002 controller; whole original engine and oracle retained."""
import argparse
import json
import re
import sys
from types import CodeType,FunctionType,SimpleNamespace as NS
import flat_current_queue_envelope_runtime_v25 as old

SELF="tools/p09/flat_current_queue_envelope_runtime_v31.py"
TEST="tools/p09/tests/test_flat_current_queue_envelope_runtime_v31.py"
PRIOR_PIN={"path":"tools/p09/flat_current_queue_envelope_runtime_v30.py","bytes":13368,"sha256":"68299c21e702a49afe82986c66ddfd18422ac2225159425da8c4b956cd1adb4b"}
NEXT_PINS=[{"path":"tools/p09/runtime_successor_manifest_v6.py","bytes":3311,"sha256":"2e188f844e93555bfdfdd5601d34c1058f37b07d7ea4ed017041a67b5cb4bf4b"},{"path":"tools/p09/runtime_successor_worker_capsule_v5.py","bytes":1047,"sha256":"d4b09e41683d02f6165bbb62aa47a03cea845b69950baf6505d139a36f951479"},{"path":"tools/p09/successor_runtime_graph_v5.py","bytes":1097,"sha256":"70eceb2cbc86f1a6f621ea2491747eac5466ff153eac21435d565bca0b316fe9"},{"path":"tools/p09/successor_bounded_graph_bootstrap_v5.py","bytes":2392,"sha256":"4e80486c209c6d5138e52fe600e28fd49b17fc311356faf12fcf2c3f477b0673"},{"path":"tools/p09/successor_current_binding_v5.py","bytes":1118,"sha256":"d04454c473544157a9aa4a70c66e639e43d4d06466a36481b8014fff91f29b6b"},{"path":"tools/p09/reviewed_case160_attempt_v2.py","bytes":3894,"sha256":"f1b37676c7b23c17e58762a1c3cc889f19506501c82e188199a582703b805fb4"},{"path":"tools/p09/same_reader_failure_review_once_v1.py","bytes":3180,"sha256":"f9a962fb97db785c22c419640bfb79c4f5a3ded293db141a4b325481328516ab"},{"path":"tools/p09/same_reader_history_declaration_once_v1.py","bytes":2461,"sha256":"5bf2309acbedfe130b7de8225997cc78c640588e757b5bc79e12c36d3eaea3cf"}]
prior_bundle,prior_proof=old.namespace_bundle.load(old.c.ROOT,[PRIOR_PIN],
    {"flat_current_queue_envelope_runtime_v25":old})
PRIOR160=prior_bundle.flat_current_queue_envelope_runtime_v30
reuse={**vars(PRIOR160.PRIOR160.PRIOR160.PRIOR159.SOURCE_NAMESPACES),**vars(PRIOR160.PRIOR160.NEXT),**vars(PRIOR160.NEXT),
    **vars(old._attempt),**vars(old._roles),"flat_current_queue_envelope_runtime_v25":old}
NEXT,NEXT_PROOFS=old.namespace_bundle.load(old.c.ROOT,NEXT_PINS,reuse)
RAW_PINS=PRIOR160.RAW_PINS+[PRIOR_PIN]+NEXT_PINS
RAW_TEST_PIN=PRIOR160.RAW_TEST_PIN
SOURCE_PROOFS=PRIOR160.SOURCE_PROOFS+prior_proof+NEXT_PROOFS
_family=PRIOR160.M.only160.__globals__;_env=dict(_family)
META={"case160-current-r002-tests":"case160-current-r003-tests",
    "-envelope-controller-preflight038.v1.json":"-envelope-controller-preflight039.v1.json"}
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

DATA="implementation/p09/evidence/p09-361-case160-envelope-controller-data039.v1.json"
QUAL="implementation/p09/evidence/p09-361-case160-run003-controller-code18-r826.v1.json"
QUAL_STATE="PASS_CURRENT160_RUN003_CONTROLLER_CODE18_ORIGINAL_BOUND64_NOT_NATIVE_OR_GO"
SCHEMA="hwpx-agent.p09-envelope-current-controller/v31"
PREFLIGHT="implementation/p09/evidence/p09-361-case160-envelope-controller-preflight039.v1.json"
BINDING_CODE="implementation/p09/evidence/p09-361-case160-run003-whole29-binding-code43-r825.v1.json"
bootstrap=NEXT.successor_bounded_graph_bootstrap_v5
binding_module=NEXT.successor_current_binding_v5
attempt=NEXT.reviewed_case160_attempt_v2
CAPSULE=NEXT.successor_runtime_graph_v5.CAPSULE
MANIFEST=bootstrap.MANIFEST
DISTINCT_TEMPLATE,RETRY,ATTEMPT_PROOF=attempt.connect_template(old.prior)
prior=NS(**{**vars(old.prior),"template":DISTINCT_TEMPLATE})
_env.update(SELF=SELF,TEST=TEST,DATA=DATA,QUAL=QUAL,QUAL_STATE=QUAL_STATE,SCHEMA=SCHEMA,
    PREFLIGHT=PREFLIGHT,BINDING_CODE=BINDING_CODE,bootstrap=bootstrap,CAPSULE=CAPSULE,MANIFEST=MANIFEST,
    RETRY=RETRY,prior=prior,_graph=None,_checkpoint=None,_execution_requested=False,PARENT_STATES=[],
    current_binding=NS(**{**vars(binding_module),"successor":PRIOR160.PRIOR160.PRIOR160.NEXT.runtime_successor_binding_v2}))

def validate_data(row):
    _env["only160"]()
    old.a.require(type(row) is dict and set(row)=={"schema_version","index","before","run","physical_product_run",
        "base_step_pin","authority_pin","prior_runtime_pin","manifest_pin","capsule_pin",
        "qualification_pin","controller_code_pins","binding_code_pin"},"CLOSED_RUN002_DATA")
    old.a.fields(row,dict(schema_version=SCHEMA,index=160,before=153,run=1,physical_product_run=3,
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
    old.a.fields(bound,dict(state="PASS_RUN003_WHOLE29_BINDING_CODE43_BOUNDED21_AND_ORIGINAL600_COST_NOT_CONTROLLER_OR_GO",
        source_pairs=29,rust_source_count=787,
        cleanup_confirmed=True,Native_or_product_executed=False,queue_acceptance_called=False),
        "EXACT_QUALIFIED_WHOLE26_BINDING")
    old.a.require(bound["fresh_inputs"]==bound["final_fresh_hashes"] and bound["fresh_inputs"]>0,
        "ALL_ACTUAL26_BINDING_FINAL_HASHES")
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

FIRST_REVIEW_PIN={"path":"implementation/p09/evidence/p09-361-case160-run001-shared-metadata-stop-review-r770.v1.json","bytes":1433,"sha256":"d36c1b159359c58f5caa0fe03da383f9b95c51047e87c63005ef6fc5ebe159af"}
_old_attempt=PRIOR160.attempt
_old_attempt.reviewed_failure,REVIEW_REUSE_COUNTS=NEXT.same_reader_failure_review_once_v1.connect(
    _old_attempt.reviewed_failure,expected_runtime_pin=_old_attempt.STOPPED,expected_review_pin=FIRST_REVIEW_PIN)
_history=_env["current_binding"].successor.original
_history_expected=_history.declaration([dict(schema_version=f.ADMISSION_SCHEMA,source_role=f.ROLE,
    failed_runtime_pin=f.ROOT,independent_review_pin=f.REVIEW,current_case=158,
    original_failure_promoted=False,current_product_or_GO_qualified=False)
    for f in (old.failed_role,old.failed004_role)])
_history.admission,HISTORY_REUSE_COUNTS=NEXT.same_reader_history_declaration_once_v1.connect(_history.admission,_history_expected)
owned,ADMISSION_COUNTS=old.admission_once.connect(own_inputs)
_env.update(own_inputs=owned,validate_data=validate_data)
def binding(q):
    owned(q)
    complete,rust,fresh,live,_=binding_module.bind(q,PRIOR160.PRIOR160.PRIOR160.PRIOR159)
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
    old.a.require(type(public_run) is int and public_run==3,"EXACT_REVIEWED160_PHYSICAL_RUN002")
    old.a.require(not (old.c.ROOT/RETRY.root_path(old.base.CONFIG)).exists(),"REFUSE_EXISTING_RUN002_ROOT")
    old.a.require((old.c.ROOT/PREFLIGHT).is_file(),"WHOLE_RUN002_PREFLIGHT_REQUIRED")
    old.a.require(not _env["_execution_requested"],"NO_AUTOMATIC_RETRY")
    _env["_execution_requested"]=True
    execute,state=prior.CONNECTION.connect_run(API.run_owned,prior.BACKEND)
    before=len(prior.ATTEMPT_STATES);result=execute(RETRY.public_run(160,public_run))
    observed=prior.ATTEMPT_STATES[before:]
    old.a.require(len(observed)==1 and observed[0].physical_product_run==3 and
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
    previous_validation=PRIOR160.PRIOR160.PRIOR160.NEXT.successor_current_binding_v2.previous_callback(PRIOR160.PRIOR160.PRIOR160.PRIOR159))
API=NS(**_api_env);API.prepare=_env["independent_prepare_not_qualified"];API.accept=API.prepare
_env["API"]=API;M=NS(**_env)

def test_namespace():
    ns,proof=old.namespace_bundle.load(old.c.ROOT,[RAW_TEST_PIN],{"flat_current_queue_envelope_runtime_v26":M})
    module=ns.test_flat_current_queue_envelope_runtime_v26
    mapping={159:160,152:153,20:29,
        "-envelope-controller-preflight034.v1.json":"-envelope-controller-preflight039.v1.json",
        "case159-current-r001-tests":"case160-current-r003-tests",
        "case159-current-r002-tests":"case160-current-r004-tests"}
    original_data=module.data
    def data():
        row=original_data();row.update(index=160,before=153,physical_product_run=3);return row
    original_data.__globals__["data"]=data;module.data=data
    for name,fn in tuple(vars(module.Tests).items()):
        target=fn.__func__ if type(fn) is classmethod else fn
        if type(target) is FunctionType:
            specific=dict(mapping)
            if name=="test_actual_original_engine_and_worker_connected_not_executed":specific[1]=3
            if name in ("test_existing_runtime_never_overwritten","test_missing_whole_pref_denied_before_engine"):specific[1]=3
            if name=="test_wrong_physical_run_never_starts_engine":specific[2]=1; specific[3]=2
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
        label=str(error) if isinstance(error,ValueError) and re.fullmatch("[A-Za-z0-9_]{1,256}",str(error)) else "REDACTED_V31_FAILURE"
        print(json.dumps(dict(state="FAILED_NOT_ACCEPTED",error_code=label)));raise SystemExit(2) from None
