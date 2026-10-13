"""Private exact159 Binding; retain two failed158 roles as prior failures.

Only the old constructor's single next-case literal changes, with inverse code
equality. All original methods/byte/read/cost/decode/cleanup oracles survive.
No old failure is promoted to product; original declarations remain unchanged.
"""
import copy
from types import FunctionType, MappingProxyType, SimpleNamespace as NS

SELF="tools/p09/runtime_successor_binding_v1.py"
TEST="tools/p09/tests/test_runtime_successor_binding_v1.py"
SCHEMA="hwpx-agent.p09-exact159-prior-failure-lineage/v1"
AUTHORITY=dict(path="implementation/p09/evidence/p09-361-case158-current-epoch-accept001.v1.json",
    bytes=396156,sha256="ae5968271c2529880cb562a1ae3a48621af39d2af8d747d1ef77f6c245794f34")
ROOT=dict(path="implementation/p09/evidence/p09-361-case158-current-runtime-run005.v1.json",
    bytes=4404465,sha256="34db0892a40886196a3307ba21decfdcb7ecdede4e6e02feb48422636a54ded4")
ROLE="preserved_prior_case_pre_product_failures_not_accepted_product"


def require(ok,label):
    if not ok:raise ValueError("SUCCESSOR_BINDING_"+label)


def declaration(failures):
    return dict(schema_version=SCHEMA,next_case=159,accepted_count_before=152,
        prior_case=158,source_role=ROLE,authority152_pin=dict(AUTHORITY),actual158_pin=dict(ROOT),
        failures=copy.deepcopy(failures),prior_failures_promoted=False,current159_or_GO_qualified=False)


def admission(q,a,failed003,failed004):
    authority=a.read_exact(q,AUTHORITY)
    a.fields(authority,dict(state="PASS_EXACT_FLAT_CURRENT_EPOCH_ACCEPTED_ONCE_NOT_FULL249_OR_GATE",
        accepted_count_after=152,next_runtime_index=159,runtime_candidate_pin=ROOT,
        resource_cleanup_confirmed=True,full249_current_qualified=False,signed16_current_qualified=False,
        P09_gate="OPEN"),"ACTUAL152_ADMITS_ONLY159")
    prior=a.read_exact(q,ROOT)
    a.fields(prior,dict(state="PASS_EXACT_CURRENT_QUEUE_NATIVE_RUNTIME_CANDIDATE_NOT_QUEUE_OR_GATE",
        selected_test_index=158,Native_source_frame_qualified=True,
        current_generation_runtime_candidate_qualified=True,cleanup_confirmed=True,owned_tree_empty=True),"ACTUAL158_COMMITTED")
    a.fields(prior["source_frame"],dict(frame_state="COMMITTED"),"COMMITTED_PRIOR158")
    a.require(len(prior["source_frame"]["actual_byte_boundaries"])==2,"PRIOR_WHOLE_BYTES_TWO")
    failures=[failed003.admission(q,a),failed004.admission(q,a)]
    a.exact(failures[0],prior["source_input_representation"]["same_case_failed_receipt_provenance"],"EXACT_PRIOR_FAILED003_ROLE")
    a.exact(failures[1],prior["source_input_representation"]["same_case_failed004_receipt_provenance"],"EXACT_PRIOR_FAILED004_ROLE")
    return declaration(failures)


def connect(module,lineage,failed003,failed004):
    source=module.source
    require(type(module) is NS and type(source) is NS and
        str(getattr(module,"__name__","")).startswith("p09_exact_"),"FRESH_PRIVATE_BINDING_NAMESPACE")
    require(not hasattr(module,"successor_failure_lineage"),"ONE_INSTALLATION")
    expected=declaration([dict(schema_version=f.ADMISSION_SCHEMA,source_role=f.ROLE,
        failed_runtime_pin=f.ROOT,independent_review_pin=f.REVIEW,current_case=158,
        original_failure_promoted=False,current_product_or_GO_qualified=False) for f in (failed003,failed004)])
    module.exact(lineage,expected,"EXACT_REVIEWED_PRIOR_FAILURE_LINEAGE")
    original_ctor=module.Binding.__init__;code=original_ctor.__code__
    require(sum(type(x) is int and x==158 for x in code.co_consts)==1,"ONE_EXACT_NEXT158_LITERAL")
    revised=code.replace(co_consts=tuple(159 if type(x) is int and x==158 else x for x in code.co_consts))
    require(revised.replace(co_consts=code.co_consts)==code,"ALL_ORIGINAL_CONSTRUCTOR_CODE_RESTORED")
    env=source.Projection.__init__.__globals__
    require(str(env.get("__name__","")).startswith("p09_exact_") and
        env.get("descriptor") is source.descriptor,"ONE_PRIVATE_DESCRIPTOR_GRAPH")
    original_descriptor=source.descriptor;original_representation=module.Binding.representation
    frozen=copy.deepcopy(lineage)
    pairs=tuple((copy.deepcopy(f.ROOT),f.PHYSICAL) for f in (failed003,failed004))
    def descriptor(old,new,*,next_case):
        for pin,path in pairs:
            if type(old) is dict and old.get("path")==pin["path"]:
                require(type(next_case) is int and next_case==159,"EXACT_NEXT159_PRIOR_FAILURE")
                old,new=source.copy_pin(old),source.copy_pin(new)
                module.exact(old,pin,"UNCHANGED_PRIOR_FAILURE_ROOT")
                require(new["path"]==path and 0<new["bytes"]<=source.codec.MAX_BYTES,
                        "EXACT_PRIOR_FAILED_PHYSICAL_PATH")
                return dict(schema_version=source.SCHEMA,semantic_original_pin=old,
                    physical_envelope_pin=new,next_case=next_case)
        return original_descriptor(old,new,next_case=next_case)
    def representation(self,projection):
        for pin,_ in pairs:
            require(pin["path"] in self.originals,"BOTH_PRIOR_FAILURES_MUST_REMAIN")
            module.exact(dict(self.originals[pin["path"]]),pin,"EXACT_FAILURE_STILL_IN_SCOPE")
        result=original_representation(self,projection)
        result["prior_failure_lineage"]=copy.deepcopy(frozen)
        return result
    module.Binding.__init__=FunctionType(revised,original_ctor.__globals__,
        argdefs=original_ctor.__defaults__,closure=original_ctor.__closure__)
    module.Binding.__init__.__kwdefaults__=original_ctor.__kwdefaults__
    source.descriptor=descriptor;env["descriptor"]=descriptor
    module.Binding.representation=representation
    module.successor_failure_lineage=MappingProxyType(dict(schema_version=SCHEMA,next_case=159,
        exact_constructor_inverse_code_equal=True,prior_failures_promoted=False))
    return dict(original_constructor=original_ctor,original_descriptor=original_descriptor,
        original_representation=original_representation,original_nonconstructor_methods_retained=True,
        default_module_mutated=False,current159_or_product_or_GO_qualified=False)
