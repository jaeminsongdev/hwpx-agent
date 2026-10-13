"""Exact160 captured-product but incomplete-source failure, not accepted PASS."""
from types import CodeType,FunctionType,SimpleNamespace as NS
import reviewed_case160_attempt_v1 as attempt
import runtime_failed_receipt_projection_v2 as original

SELF="tools/p09/runtime_failed160_partial_projection_v1.py"
TEST="tools/p09/tests/test_runtime_failed160_partial_projection_v1.py"
ROOT=attempt.STOPPED
REVIEW={"path":"implementation/p09/evidence/p09-361-case160-run001-shared-metadata-stop-review-r770.v1.json","bytes":1433,"sha256":"d36c1b159359c58f5caa0fe03da383f9b95c51047e87c63005ef6fc5ebe159af"}
PHYSICAL="implementation/p09/evidence/p361-lossless-runtime-inputs/case160-runtime-run001.failed.envelope.v1.json"
ROLE="preserved_same_case_partial_post_product_source_failure_not_accepted_product"
ADMISSION_SCHEMA="hwpx-agent.p09-exact-partial-failed-receipt-alias-admission/v2"
CODE="implementation/p09/evidence/p09-361-case160-run002-identity-template-code12-r780.v1.json"
MAPPING={158:160,"failed004_receipt_extension":"failed160_partial_receipt_extension",
    "same_case_failed004_receipt_provenance":"same_case_failed160_partial_receipt_provenance"}


def declaration():
    return dict(schema_version=ADMISSION_SCHEMA,source_role=ROLE,failed_runtime_pin=ROOT,
        independent_review_pin=REVIEW,current_case=160,original_failure_promoted=False,
        current_product_or_GO_qualified=False)


def admission(q,a):
    reviewed=attempt.reviewed_failure(q,a)
    a.exact(q.snapshots[REVIEW["path"]],REVIEW,"EXACT_PARTIAL160_REVIEW_BYTES")
    code=q.json(CODE)
    a.fields(code,dict(state="PASS_REVIEWED160_RUN002_IDENTITY_CODE12_ACTUAL_SINGLE_TEMPLATE_NOT_NATIVE_OR_GO",
        contracts=dict(run=12,errors=0,failures=0,skipped=0),cleanup_confirmed=True,
        actual_engine_calls=0,actual_worker_calls=0,accepted_count_delta=0),"QUALIFIED_FAILURE_IDENTITY_REVIEW")
    a.exact(code["failure_admission"],reviewed,"SAME_ACTUAL_PARTIAL160_FAILURE")
    for pin in code["source_pins"]:a.exact(q.pin(pin["path"]),pin,"CURRENT_PARTIAL160_REVIEW_SOURCES")
    return declaration()


def project(code,mapping):
    return code.replace(co_consts=tuple(project(x,mapping) if type(x) is CodeType else
        mapping.get(x,x) if type(x) in (int,str) else x for x in code.co_consts))


def connect(source,binding,admitted):
    code=original.connect.__code__;changed=project(code,MAPPING)
    original.require(project(changed,{v:k for k,v in MAPPING.items()})==code,
        "PARTIAL160_ENTIRE_ORIGINAL_ROLE_CODE_INVERSE")
    env=dict(original.connect.__globals__,ROOT=ROOT,REVIEW=REVIEW,PHYSICAL=PHYSICAL,
        ROLE=ROLE,ADMISSION_SCHEMA=ADMISSION_SCHEMA)
    fn=FunctionType(changed,env,argdefs=original.connect.__defaults__,closure=original.connect.__closure__)
    fn.__kwdefaults__=original.connect.__kwdefaults__
    proof=fn(source,binding,admitted)
    return dict(proof,original_failed_role_whole_code_inverse_equal=True,
        explicit_partial_post_product_failure_not_pre_product_role=True,
        original_prior_failed_roles_delegated_unchanged=True,current160_runtime_or_GO_qualified=False)
