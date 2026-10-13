"""Connect unchanged160 binding to one private159 declaration admission.

The original full bind/previous callback/prior159 prepare code stays intact.
Only private dependencies share a graph and completed declaration per reader.
No Native/product or queue writer is invoked by this connection.
"""
import copy
from types import SimpleNamespace as NS
import same_reader_manifest_declaration_once_v1 as declaration

SELF="tools/p09/successor_manifest_shared_admission_v1.py"


def bind(q,controller,original):
    m=controller.M;a=m.a
    q.pin(SELF);q.pin(declaration.SELF);q.pin(declaration.TEST)
    family=m.only159.__globals__;before=(m.base.CONFIG,family["_graph"],family["_checkpoint"])
    holder={};count={}
    original_manifest=m.current_binding.manifest
    cached,counts=declaration.connect(original_manifest.load)
    def isolate(ctrl,step):
        a.require(ctrl is controller and q.final_fresh_hashes==0,"EXACT_SHARED159_CONTROLLER_BEFORE_FINISH")
        if holder:
            a.exact(vars(step),holder["step"],"SAME_REAL159_STEP_ALL_FIELDS")
            count["reuses"]+=1
            return holder["facade"],copy.deepcopy(holder["proof"])
        facade,proof=original.predecessor.isolate(ctrl,step)
        current_binding=NS(**{**vars(facade.current_binding),
            "manifest":NS(**{**vars(original_manifest),"load":cached})})
        facade.current_binding=current_binding
        facade.only159.__globals__["current_binding"]=current_binding
        holder.update(facade=facade,proof=copy.deepcopy(proof),step=copy.deepcopy(vars(step)))
        count.update(reuses=0)
        return facade,proof
    clone=m.prior.LINK.clone
    prior=NS(**{**vars(original.predecessor),"isolate":isolate,
        "prepare":clone(original.predecessor.prepare,isolate=isolate)})
    callback=clone(original.previous_callback,predecessor=prior)
    execute=clone(original.bind,predecessor=prior,previous_callback=callback)
    a.require(execute.__code__ is original.bind.__code__ and
        callback.__code__ is original.previous_callback.__code__ and
        prior.prepare.__code__ is original.predecessor.prepare.__code__,"WHOLE_ORIGINAL_FUNCTION_CODES_UNCHANGED")
    result=execute(q,controller)
    a.require(m.base.CONFIG is before[0] and family["_graph"] is before[1] and family["_checkpoint"] is before[2],
        "DEFAULT160_CONFIG_AND_ORIGINAL159_GRAPH_CHECKPOINT_UNCHANGED")
    a.exact(counts,dict(original_complete_admissions=1,duplicate_declarations_avoided=1),
        "ACTUAL_ONE_WHOLE159_MANIFEST_AND_ONE_REUSED_DECLARATION")
    a.exact(count,dict(reuses=1),"ONE_SHARED159_FACADE_REUSE")
    return result,dict(manifest_declaration_counts=dict(counts),private159_facade_counts=dict(count),
        original_bind_previous_callback_and_prepare_code_objects_retained=True,
        default_CONFIG_graph_checkpoint_or_manifest_loader_mutated=False,
        file_payload_parsed_JSON_or_hash_calculation_cache=False,
        Native_or_product_reexecuted=False,queue_acceptance_called=False)
