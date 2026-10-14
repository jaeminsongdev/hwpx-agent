"""Two exact partial failures extend only a newly built private source graph."""
from types import MappingProxyType,SimpleNamespace as NS
import review_failed_run003_v1 as third
SELF="tools/p09/runtime_failed160_extras_v1.py"
TEST="tools/p09/tests/test_runtime_failed160_extras_v1.py"
SCHEMA="hwpx-agent.p09-failed160-extra-input-admission/v1"
PRODUCER="implementation/p09/evidence/p09-361-case160-failed002003-transport-producer-r844.v1.json"
SECOND=dict(path="implementation/p09/evidence/p09-361-case160-current-runtime-run002.v1.json",bytes=4217213,
    sha256="cec8b6269f552bf9c50fc528d85a1a87bd0a188925d82a0cccbcbf43ab7778c5")
ROOTS=(SECOND,third.ROOT)

def require(ok,label):
    if not ok:raise ValueError("FAILED160_EXTRAS_"+label)

def admission(q,a):
    produced=q.json(PRODUCER)
    a.fields(produced,dict(state="PASS_EXCLUSIVE_FAILED002003_TRANSPORT_NOT_ADMITTED_MANIFEST_RUNTIME_OR_GO",
        exact_original_restore_passes=4,write_rate_bytes_per_second=2097152,cleanup_confirmed=True,
        original_failures_rewritten=False,failures_promoted=False,actual_product_or_Native_executed=False,
        GO_authorized=False),"EXACT_TWO_FAILURE_TRANSPORTS")
    a.require(produced["fresh_inputs"]==produced["final_fresh_hashes"]==24,"ALL_PRODUCER_FINAL_HASHES")
    for pin in produced["source_pins"]:a.exact(q.pin(pin["path"]),pin,"CURRENT_TWO_FAILURE_PRODUCER_SOURCES")
    a.require(type(produced["selected_outputs"]) is list and len(produced["selected_outputs"])==2,"EXACT_TWO_OUTPUTS")
    rows=[]
    for number,root,item in zip((2,3),ROOTS,produced["selected_outputs"]):
        a.exact(item["original_pin"],root,"ONLY_EXACT_FAILED002003")
        failed=a.read_exact(q,root);review=a.read_exact(q,item["independent_review_pin"])
        a.fields(failed,dict(state="STOPPED_NOT_ACCEPTED",selected_test_index=160,task="case160-current-r%03d-tests"%number,
            stop_reason="FLAT_QUEUE_ORIGINAL_SHARED_METADATA_DEADLINE",operation_phase="final_source_freeze",
            cleanup_confirmed=True,owned_tree_empty=True,accepted_count_delta=0),"FAILED_NOT_PRIOR_ACCEPTED_PRODUCT")
        if number==3:a.fields(review,third.review(failed,a),"EXACT_THIRD_WHOLE_REVIEW")
        else:a.fields(review,dict(state="REVIEW_ACTUAL160_RUN002_SHARED_METADATA_DEADLINE_NOT_RUNTIME_OR_ACCEPTANCE_PASS",
            runtime_pin=root,cleanup_confirmed=True,accepted_count_after=153,accepted_count_delta=0,
            whole_Runtime_or_two_byte_boundary_qualified=False),"EXACT_SECOND_INDEPENDENT_REVIEW")
        physical=dict(item["physical_pin"])
        a.require(physical["path"]=="implementation/p09/evidence/p361-lossless-runtime-inputs/case160-runtime-run%03d.failed.envelope.v1.json"%number,
            "EXPLICIT_SAME_CASE_FAILED_PHYSICAL_PATH")
        a.exact(q.fresh_pin(physical["path"]),physical,"ACTUAL_FRESH_FAILURE_DERIVATIVE")
        rows.append(dict(schema_version=SCHEMA,current_case=160,failed_runtime_pin=dict(root),
            independent_review_pin=dict(item["independent_review_pin"]),physical_pin=physical,
            original_failure_promoted=False,current_product_or_GO_qualified=False))
    return rows

def connect(source,binding,admitted):
    require(type(source) is NS and type(binding) is NS and binding.source is source,"ONE_PRIVATE_SOURCE_GRAPH")
    require(type(admitted) is list and len(admitted)==2,"EXACT_TWO_ADMISSIONS")
    expected={};provenance=[]
    for root,row in zip(ROOTS,admitted):
        require(type(row) is dict and set(row)=={"schema_version","current_case","failed_runtime_pin",
            "independent_review_pin","physical_pin","original_failure_promoted","current_product_or_GO_qualified"},"CLOSED_ADMISSION")
        binding.exact({k:row[k] for k in ("schema_version","current_case","failed_runtime_pin",
            "original_failure_promoted","current_product_or_GO_qualified")},
            dict(schema_version=SCHEMA,current_case=160,failed_runtime_pin=root,
                original_failure_promoted=False,current_product_or_GO_qualified=False),"EXACT_TYPED_FAILED_CONTEXT")
        for key in ("failed_runtime_pin","independent_review_pin","physical_pin"):source.copy_pin(row[key])
        number="002" if root==SECOND else "003"
        require(row["physical_pin"]["path"]=="implementation/p09/evidence/p361-lossless-runtime-inputs/case160-runtime-run"+number+".failed.envelope.v1.json",
            "EXACT_PHYSICAL_FAILURE_PATH")
        expected[root["path"]]=dict(row["physical_pin"])
        provenance.append(MappingProxyType({**row,**{key:MappingProxyType(dict(row[key]))
            for key in ("failed_runtime_pin","independent_review_pin","physical_pin")}}))
    env=source.Projection.__init__.__globals__
    require(str(env.get("__name__","")).startswith("p09_exact_") and env.get("descriptor") is source.descriptor,
        "ONLY_FRESH_PRIVATE_DESCRIPTOR_ENVIRONMENT")
    require(not hasattr(source,"failed160_extra_receipts"),"NO_REINSTALL")
    old_descriptor=source.descriptor;old_representation=binding.Binding.representation
    def descriptor(old,new,*,next_case):
        if type(old) is not dict or old.get("path") not in expected:return old_descriptor(old,new,next_case=next_case)
        require(type(next_case) is int and next_case==160,"ONLY_CURRENT160_EXTRA_FAILURES")
        old=source.copy_pin(old);new=source.copy_pin(new)
        original=next(p for p in ROOTS if p["path"]==old["path"])
        binding.exact(old,original,"EXACT_FAILED_ORIGINAL_PIN");binding.exact(new,expected[old["path"]],"EXACT_FAILED_PHYSICAL_PIN")
        return dict(schema_version=source.SCHEMA,semantic_original_pin=old,physical_envelope_pin=new,next_case=160)
    def representation(self,projection):
        require(all(root["path"] in self.originals for root in ROOTS),"BOTH_EXTRA_FAILURES_EXPLICITLY_PRESENT")
        result=old_representation(self,projection)
        result["same_case_failed160_extra_receipt_provenance"]=[{**dict(p),**{key:dict(p[key])
            for key in ("failed_runtime_pin","independent_review_pin","physical_pin")}} for p in provenance]
        return result
    env["descriptor"]=descriptor;source.descriptor=descriptor
    source.failed160_extra_receipts=tuple(provenance);binding.Binding.representation=representation
    return dict(original_all_other_descriptors_and_representation_delegated=True,
        only_private_graph_modified=True,all_original_projection_codec_and_binding_constructor_code_retained=True,
        explicit_failed_not_accepted_provenance_added=True,new_manifest_or_runtime_qualified=False,GO_authorized=False)
