"""Run003 bounded21 inputs with original64 reads and262144 bytes limits."""
import successor_bounded_graph_bootstrap_v4 as original
import runtime_successor_manifest_v6 as manifest
import runtime_successor_worker_capsule_v5 as capsule
import successor_runtime_graph_v5 as factory
SELF="tools/p09/successor_bounded_graph_bootstrap_v5.py"
MANIFEST={"path":"implementation/p09/evidence/p09-361-case160-source-manifest028.v6.json","bytes":589,"sha256":"57bd8fe8425a54dbf46860e045f62d88ba86c1f4cb41696661ca4a0d66677496"}
PREVIOUS_MANIFEST=original.MANIFEST
PARTIAL_MANIFEST=original.PREVIOUS_MANIFEST
BASE_MANIFEST=original.BASE_MANIFEST
class Reader(original.Reader):
    def __init__(self,m,checkpoint):
        super().__init__(m,checkpoint)
        self.allowed={p["path"]:dict(p) for p in m.NAMESPACE_SOURCE_PINS+
            [factory.CAPSULE,MANIFEST,PREVIOUS_MANIFEST,PARTIAL_MANIFEST,BASE_MANIFEST]}

def load(m,checkpoint):
    q=Reader(m,checkpoint);row=q.json(MANIFEST["path"])
    m.a.fields(row,dict(schema_version=manifest.SCHEMA,index=160,before=153,physical_product_run=3),
        "EXACT_BOUNDED_RUN003_29")
    m.a.exact(row["base_manifest_pin"],PREVIOUS_MANIFEST,"UNCHANGED_ACTUAL26_PREVIOUS_MANIFEST")
    previous=q.json(PREVIOUS_MANIFEST["path"])
    m.a.exact(previous["base_manifest_pin"],PARTIAL_MANIFEST,"UNCHANGED_ACTUAL25_PARTIAL_MANIFEST")
    partial=q.json(PARTIAL_MANIFEST["path"])
    m.a.exact(partial["base_manifest_pin"],BASE_MANIFEST,"UNCHANGED_ACTUAL24_CONTEXT_BASE")
    base=q.json(BASE_MANIFEST["path"])
    successor=original.original.successor;role=original.original.partial
    m.a.fields(base,dict(index=160,before=153,authority_pin=successor.AUTHORITY,
        prior_runtime_pin=successor.ROOT),"EXACT_ORIGINAL_CURRENT_CONTEXT")
    graph=factory.build(q,m,successor,capsule,role,context=base["successor_context"],
        partial_admission=partial["partial_failure_admission"])
    m.a.exact(dict(graph.binding.manifest_pin),MANIFEST,"EXACT_ACTUAL_MANIFEST028")
    return graph,dict(bounded_reader_reads=q.reads,bounded_reader_bytes=q.bytes_read,
        original_reader_code_and_64_reads_262144_bytes_limits_retained=True,
        historical_receipts_read_by_this_reader=0,reader_source_pins=list(q.snapshots.values()),
        parent_fresh_whole_admission_and_live_locks_required=True,
        current_controller_or_product_or_GO_qualified=False)
