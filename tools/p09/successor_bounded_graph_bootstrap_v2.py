"""Bounded actual160 graph bootstrap; history admission remains before GO."""
import successor_bounded_graph_bootstrap_v1 as original
import runtime_successor_binding_v2 as successor
import runtime_successor_manifest_v2 as manifest
import runtime_successor_worker_capsule_v2 as capsule
import successor_runtime_graph_v2 as factory

SELF="tools/p09/successor_bounded_graph_bootstrap_v2.py"
MANIFEST=dict(path=manifest.PATH,bytes=3724,
    sha256="d4f2a5fd4a44deb4fcab40ae67e531c3c8311ebf627e1607b62eaa2678ecbea8")


class Reader(original.Reader):
    def __init__(self,m,checkpoint):
        super().__init__(m,checkpoint)
        self.allowed={p["path"]:dict(p) for p in m.NAMESPACE_SOURCE_PINS+[factory.CAPSULE,MANIFEST]}


def load(m,checkpoint):
    q=Reader(m,checkpoint);row=q.json(MANIFEST["path"])
    m.a.fields(row,dict(schema_version=manifest.SCHEMA,index=160,before=153,
        authority_pin=successor.AUTHORITY,prior_runtime_pin=successor.ROOT),
        "EXACT_BOUNDED160_MANIFEST_CONTEXT")
    graph=factory.build(q,m,successor,capsule,context=row["successor_context"])
    m.a.exact(dict(graph.binding.manifest_pin),MANIFEST,"SAME_EXACT160_MANIFEST_NOT_PLACEHOLDER")
    return graph,dict(bounded_reader_reads=q.reads,bounded_reader_bytes=q.bytes_read,
        original_reader_code_and_64_reads_262144_bytes_limits_retained=True,
        historical_receipts_read_by_this_reader=0,reader_source_pins=list(q.snapshots.values()),
        parent_fresh_whole_admission_and_live_locks_required=True,
        complete_controller_worker_dispatch_or_product_qualified=False,GO_authorized=False)
