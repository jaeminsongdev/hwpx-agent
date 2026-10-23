"""Instance-only old/new source normalization before the original162 Binding."""
import copy
from types import MethodType

SELF='tools/p09/native011_current_epoch_graph.py'
TEST='tools/p09/tests/test_native011_current_epoch_graph.py'


def require(ok,code):
    if not ok:raise ValueError('CURRENT805_GRAPH_'+code)


def attach(binding,versions,scope,checkpoint):
    require(callable(checkpoint),'ORIGINAL_CHECKPOINT');checkpoint()
    require(type(binding.next_case) is int and binding.next_case==165
        and len(binding.descriptors())==162,'ACTUAL_FULL162_BINDING')
    require('semantic_union' not in vars(binding),'NO_PREVIOUS_INSTANCE_ADAPTER')
    original=binding.semantic_union
    require(type(original) is MethodType and original.__self__ is binding,'ORIGINAL_BOUND_SEMANTIC_UNION')
    descriptors=copy.deepcopy(binding.descriptors());manifest=dict(binding.manifest_pin)
    methods=dict(vars(type(binding)));before=dict(vars(binding));calls=[]
    for name,(old,archive,current) in versions.rows.items():
        require(not {name,archive['path']}&(set(binding.originals)|set(binding.physical)),
            'SOURCE_VERSIONS_NOT_WIRE_DESCRIPTORS')
    def semantic_union(self,rows,check):
        require(self is binding and callable(check),'SAME_ORIGINAL_BINDING_OWNER');check()
        verified=scope.pins(list(rows.values()));require(verified==rows,'EXACT_CALL_MAPPING_KEYS')
        normalized=versions.normalize(list(verified.values()))
        result,proof=original(normalized,check)
        require(all(result.get(name)==pin for name,pin in normalized.items()
            if name in versions.rows or name in versions.archives),'ALL_EXPLICIT_SOURCE_VERSIONS_RETAINED')
        require(all(name not in result or result[name]==current for name,(_,_,current) in versions.rows.items()),
            'NO_PRIOR_SOURCE_AT_CURRENT_PATH_AFTER_UNION')
        calls.append(dict(input_count=len(rows),normalized_count=len(normalized),output_count=len(result)))
        return result,dict(proof,current805_source_version_projection_only=True,
            every_original162_guard_called=True,source_freshness_or_runtime_credit=False)
    binding.semantic_union=MethodType(semantic_union,binding)
    require(dict(vars(type(binding)))==methods and binding.descriptors()==descriptors
        and dict(binding.manifest_pin)==manifest,'ORIGINAL_CLASS_METHODS_AND_ENTIRE_MANIFEST_UNCHANGED')
    require(set(vars(binding))==set(before)|{'semantic_union'}
        and all(vars(binding)[name] is value for name,value in before.items()),'ONLY_PRIVATE_INSTANCE_ADAPTER_ADDED')
    return dict(original_semantic_union=original,original_class_methods=methods,original_instance=before,
        manifest_pin=manifest,descriptors=descriptors,calls=calls,
        same_binding_instance_retained=True,original_project_budget_evidence_methods_retained=True,
        actual_source_Frame_or_product_qualified=False)
