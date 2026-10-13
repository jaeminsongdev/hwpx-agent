"""Bounded20 input bootstrap for actual26 pairs; no history receipt reads."""
import successor_bounded_graph_bootstrap_v3 as original
import runtime_successor_manifest_v5 as manifest
import runtime_successor_worker_capsule_v4 as capsule
import successor_runtime_graph_v4 as factory
SELF="tools/p09/successor_bounded_graph_bootstrap_v4.py"
MANIFEST={"bytes":594,"path":"implementation/p09/evidence/p09-361-case160-source-manifest027.v5.json","sha256":"b89647d46eccd88c76503b51111d6556488a102392fd874092e5e31f0f0c6cd9"}
PREVIOUS_MANIFEST={"bytes":1673,"path":"implementation/p09/evidence/p09-361-case160-source-manifest026.v4.json","sha256":"ed71159aab491202603e8f59ab275dd0e4808512b14a83c8401021ff4a195da9"}
BASE_MANIFEST=original.BASE_MANIFEST
class Reader(original.original.Reader):
    def __init__(self,m,checkpoint):
        super().__init__(m,checkpoint)
        self.allowed={p["path"]:dict(p) for p in m.NAMESPACE_SOURCE_PINS+
            [factory.CAPSULE,MANIFEST,PREVIOUS_MANIFEST,BASE_MANIFEST]}
def load(m,checkpoint):
    q=Reader(m,checkpoint);row=q.json(MANIFEST["path"])
    m.a.fields(row,dict(schema_version=manifest.SCHEMA,index=160,before=153,physical_product_run=2),
        "EXACT_BOUNDED_RUN002_26")
    m.a.exact(row["base_manifest_pin"],PREVIOUS_MANIFEST,"EXACT_ACTUAL25_BASE")
    previous=q.json(PREVIOUS_MANIFEST["path"])
    m.a.exact(previous["base_manifest_pin"],BASE_MANIFEST,"EXACT_ACTUAL24_CONTEXT_BASE")
    base=q.json(BASE_MANIFEST["path"])
    m.a.fields(base,dict(index=160,before=153,authority_pin=original.successor.AUTHORITY,
        prior_runtime_pin=original.successor.ROOT),"EXACT_ORIGINAL_CURRENT_CONTEXT")
    graph=factory.build(q,m,original.successor,capsule,original.partial,
        context=base["successor_context"],partial_admission=previous["partial_failure_admission"])
    m.a.exact(dict(graph.binding.manifest_pin),MANIFEST,"EXACT_REAL_MANIFEST027")
    return graph,dict(bounded_reader_reads=q.reads,bounded_reader_bytes=q.bytes_read,
        original_reader_code_and_64_reads_262144_bytes_limits_retained=True,
        historical_receipts_read_by_this_reader=0,reader_source_pins=list(q.snapshots.values()),
        parent_fresh_whole_admission_and_live_locks_required=True,
        current_controller_or_product_or_GO_qualified=False)
