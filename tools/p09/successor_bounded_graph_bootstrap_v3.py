"""Bounded19-input run002 graph; historical admission remains before GO."""
import successor_bounded_graph_bootstrap_v1 as original
import runtime_successor_binding_v2 as successor
import runtime_successor_manifest_v4 as manifest
import runtime_successor_worker_capsule_v3 as capsule
import runtime_failed160_partial_projection_v2 as partial
import successor_runtime_graph_v3 as factory

SELF="tools/p09/successor_bounded_graph_bootstrap_v3.py"
MANIFEST={"bytes":1673,"sha256":"ed71159aab491202603e8f59ab275dd0e4808512b14a83c8401021ff4a195da9","path":"implementation/p09/evidence/p09-361-case160-source-manifest026.v4.json"}
BASE_MANIFEST=dict(path="implementation/p09/evidence/p09-361-case160-source-manifest024.v2.json",
    bytes=3724,sha256="d4f2a5fd4a44deb4fcab40ae67e531c3c8311ebf627e1607b62eaa2678ecbea8")


class Reader(original.Reader):
    def __init__(self,m,checkpoint):
        super().__init__(m,checkpoint)
        self.allowed={p["path"]:dict(p) for p in m.NAMESPACE_SOURCE_PINS+
            [factory.CAPSULE,MANIFEST,BASE_MANIFEST]}


def load(m,checkpoint):
    q=Reader(m,checkpoint);row=q.json(MANIFEST["path"])
    m.a.fields(row,dict(schema_version=manifest.SCHEMA,index=160,before=153,physical_product_run=2),
        "EXACT_BOUNDED160_RUN002_MANIFEST")
    m.a.exact(row["base_manifest_pin"],BASE_MANIFEST,"EXACT_UNCHANGED_BASE24_MANIFEST")
    base=q.json(BASE_MANIFEST["path"])
    m.a.fields(base,dict(schema_version=manifest.original.SCHEMA,index=160,before=153,
        authority_pin=successor.AUTHORITY,prior_runtime_pin=successor.ROOT),"EXACT_BASE24_CONTEXT")
    graph=factory.build(q,m,successor,capsule,partial,context=base["successor_context"],
        partial_admission=row["partial_failure_admission"])
    m.a.exact(dict(graph.binding.manifest_pin),MANIFEST,"EXACT_ACTUAL26_MANIFEST_NOT_PLACEHOLDER")
    return graph,dict(bounded_reader_reads=q.reads,bounded_reader_bytes=q.bytes_read,
        original_reader_code_and_64_reads_262144_bytes_limits_retained=True,
        historical_receipts_read_by_this_reader=0,reader_source_pins=list(q.snapshots.values()),
        parent_fresh_whole_admission_and_live_locks_required=True,
        complete_controller_worker_dispatch_or_product_qualified=False,GO_authorized=False)
