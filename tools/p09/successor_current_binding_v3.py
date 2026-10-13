"""Unchanged full160 bind with shared159 declaration and actual25 inputs."""
from types import SimpleNamespace as NS
import successor_current_binding_v2 as original
import successor_manifest_shared_admission_v1 as shared
import runtime_successor_manifest_v4 as manifest
import runtime_successor_worker_capsule_v3 as capsule
import runtime_failed160_partial_projection_v2 as partial
import successor_runtime_graph_v3 as factory

SELF="tools/p09/successor_current_binding_v3.py"


def bind(q,controller):
    m=controller.M
    for path in (SELF,shared.SELF,shared.declaration.SELF,shared.declaration.TEST,
        manifest.SELF,capsule.SELF,capsule.TEST,partial.SELF,partial.TEST,factory.SELF):q.pin(path)
    def build(reader,old,successor,unused_capsule,*,context=None):
        m.a.require(unused_capsule is capsule,"EXACT_CURRENT_RUN002_CAPSULE_DEPENDENCY")
        return factory.build(reader,old,successor,capsule,partial,context=context)
    next_factory=NS(**{**vars(factory),"build":build})
    clone=m.prior.LINK.clone
    whole=clone(original.bind,factory=next_factory,manifest=manifest,capsule=capsule)
    package=NS(**{**vars(original),"bind":whole,"factory":next_factory,"manifest":manifest,"capsule":capsule})
    result,proof=shared.bind(q,controller,package)
    complete,rust,graph,live,old_proof=result
    m.a.require(len(live.descriptors())==25 and graph.worker.TASK=="case160-current-r002-tests",
        "EXACT25_RUN002_FULL_BINDING_NOT_OLD24")
    m.a.exact(dict(live.manifest_pin),dict(graph.binding.manifest_pin),"REAL_MANIFEST026_SHARED_BINDING")
    return complete,rust,graph,live,dict(old_proof,shared_declaration_connection=proof,
        whole_original160_bind_code_object_retained=whole.__code__ is original.bind.__code__,
        current160_run002_controller_DATA_whole_preflight_or_GO_qualified=False)
