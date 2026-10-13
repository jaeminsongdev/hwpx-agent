"""Exact same-case failed-receipt alias, never a historical product PASS.

The source and binding namespaces must be freshly loaded private AST copies.
Keep their class/method code; extend only descriptor admission and explicit
representation provenance. Original modules/receipts remain unchanged.
"""
from types import MappingProxyType,SimpleNamespace as NS

SELF="tools/p09/runtime_failed_receipt_projection_v1.py"
TEST="tools/p09/tests/test_runtime_failed_receipt_projection_v1.py"
ROOT=dict(path="implementation/p09/evidence/p09-361-case158-current-runtime-run003.v1.json",
    bytes=2209026,sha256="e93a86080ad9fce059fe8eba26aa4d0c0f343d0c2530677dd86340d52334e609")
REVIEW=dict(path="implementation/p09/evidence/p09-361-case158-run003-native-stop-review-code8-r688.v1.json",
    bytes=1260,sha256="ddab10e467cbf260364ac2d4f73517861538f10557bd7b94df27b090d7ed0838")
PHYSICAL="implementation/p09/evidence/p361-lossless-runtime-inputs/case158-runtime-run003.failed.envelope.v1.json"
ROLE="preserved_same_case_pre_product_failure_not_prior_product"
ADMISSION_SCHEMA="hwpx-agent.p09-exact-failed-receipt-alias-admission/v1"


def require(ok,code):
    if not ok:raise ValueError("FAILED_RECEIPT_PROJECTION_"+code)


def admission(q,a):
    root=a.read_exact(q,ROOT);review=a.read_exact(q,REVIEW)
    a.fields(root,dict(state="DEFERRED_NOT_STARTED",task="case158-current-r003-tests",selected_test_index=158,
        stop_reason="STOP_NATIVE_OPEN_AFTER_HOST_SATURATION",product_body_observed=False,worker_created=False,
        actual_product_child_executed=False,job_assigned=False,Native_source_frame_qualified=False,
        current_generation_runtime_candidate_qualified=False,source_freeze=[],cleanup_confirmed=True,
        owned_tree_empty=True,accepted_count_delta=0),"EXACT_SAME_CASE_STOP_NOT_PRODUCT")
    a.fields(root["source_frame"],dict(frame_state="CLOSED",registered_live_frame=False,actual_byte_boundaries=[]),
        "FAILED_NOT_COMMITTED")
    a.fields(review,dict(state="PASS_EXACT158_RUN003_CLOSED_NATIVE_ACQUISITION_STOP_REVIEW_NOT_GO_OR_PRODUCT",
        contracts=dict(run=8,errors=0,failures=0,skipped=0),original_runtime_pin=ROOT,
        actual_product_executed=False,accepted_count_delta=0,cleanup_confirmed=True),"EXACT_INDEPENDENT_STOP_REVIEW")
    a.fields(review["actual_stop_review"],dict(opened=854,closed=854,remaining=0,actual_byte_boundaries=0,
        source_frame_committed=False,automatic_retry_or_GO_authorized=False),"REVIEWED_FAILURE_NEVER_GO")
    for p in review["new_code_pins"]:a.exact(q.pin(p["path"]),p,"CURRENT_STOP_REVIEW_CODE")
    return dict(schema_version=ADMISSION_SCHEMA,source_role=ROLE,failed_runtime_pin=dict(ROOT),
        independent_review_pin=dict(REVIEW),current_case=158,original_failure_promoted=False,
        current_product_or_GO_qualified=False)


def connect(source,binding,admitted):
    expected=dict(schema_version=ADMISSION_SCHEMA,source_role=ROLE,failed_runtime_pin=ROOT,
        independent_review_pin=REVIEW,current_case=158,original_failure_promoted=False,current_product_or_GO_qualified=False)
    require(type(admitted) is dict and admitted==expected,"EXACT_ADMITTED_FAILURE_CONTEXT")
    require(type(source) is NS and type(binding) is NS and binding.source is source,"ONE_PRIVATE_SOURCE_GRAPH")
    binding.exact(admitted,expected,"EXACT_TYPED_FAILED_ROLE_CONTEXT")
    env=source.Projection.__init__.__globals__
    require(str(env.get("__name__","")).startswith("p09_exact_")
        and env.get("descriptor") is source.descriptor,"FRESH_PRIVATE_DESCRIPTOR_DEPENDENCY")
    require(not hasattr(source,"failed_receipt_extension"),"ONE_EXTENSION_NOT_REINSTALLED")
    original=source.descriptor;old_representation=binding.Binding.representation
    def descriptor(old,new,*,next_case):
        if type(old) is not dict or old.get("path")!=ROOT["path"]:
            return original(old,new,next_case=next_case)
        require(type(next_case) is int and next_case==158,"ONLY_CURRENT158_FAILED003")
        old=source.copy_pin(old);new=source.copy_pin(new)
        require(old==ROOT and new["path"]==PHYSICAL and 0<new["bytes"]<=source.codec.MAX_BYTES,
            "EXACT_FAILED_ORIGINAL_AND_DISTINCT_PHYSICAL_PATH")
        return dict(schema_version=source.SCHEMA,semantic_original_pin=old,physical_envelope_pin=new,next_case=next_case)
    provenance=MappingProxyType(dict(admitted,
        failed_runtime_pin=MappingProxyType(dict(ROOT)),independent_review_pin=MappingProxyType(dict(REVIEW))))
    def representation(self,projection):
        require(ROOT["path"] in self.originals,"FAILED_ALIAS_MUST_BE_EXPLICITLY_PRESENT")
        result=old_representation(self,projection)
        result["same_case_failed_receipt_provenance"]=dict(provenance,
            failed_runtime_pin=dict(provenance["failed_runtime_pin"]),
            independent_review_pin=dict(provenance["independent_review_pin"]))
        return result
    # Only this newly constructed private graph is changed. All original
    # projection/validator/codec methods still use their original bytecode.
    env["descriptor"]=descriptor;source.descriptor=descriptor
    source.failed_receipt_extension=provenance
    binding.Binding.representation=representation
    return dict(exact_failed_role_exposed_in_representation=True,original_projection_and_codec_methods_and_binding_constructor_retained=True,
        original_descriptor_all_other_paths_delegated=True,only_private_fresh_graph_dependencies_changed=True,
        original_receipts_rewritten=False,actual_physical_scope_or_product_adopted=False,GO_authorized=False)
