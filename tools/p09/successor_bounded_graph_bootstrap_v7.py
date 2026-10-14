"""One original bounded reader, stored34 manifest and complete shared graph."""
from types import FunctionType
import successor_bounded_graph_bootstrap_v6 as original
import runtime_successor_manifest_v8 as manifest
import successor_runtime_graph_v7 as factory
SELF="tools/p09/successor_bounded_graph_bootstrap_v7.py"
TEST="tools/p09/tests/test_successor_bounded_graph_bootstrap_v7.py"
MANIFEST=dict(path=manifest.PATH,bytes=520,sha256="0c9662cd6ff8c6d6a55ed055c0b13158285ffac0806d26c795f32e14eaf0e5f4")
CAPSULE=dict(path="implementation/p09/evidence/p09-361-case160-worker-policy-capsule007.compact.v1.json",bytes=12008,
    sha256="ddfa65da0b1ba9324b89d97ea8981494386219538852a2972eedc94557cf2b93")
PRODUCER=dict(path=manifest.PRODUCER,bytes=6180,sha256="763bf8ac9c2db0958142e555780f59d703b092292cce5ca3d38ab32872bf51a1")
EXTRA_PINS=(MANIFEST,CAPSULE,PRODUCER)

def load(m,checkpoint):
    captured=[]
    fn=original.load
    # original.load creates its subclass of original.original.Reader. Supply
    # a new private base whose constructor captures that same one instance.
    class Reader(original.original.Reader):
        def __init__(self,*args):
            super().__init__(*args);self.allowed.update({p["path"]:dict(p) for p in EXTRA_PINS});captured.append(self)
    from types import SimpleNamespace as NS
    old_base=NS(**{**vars(original.original),"Reader":Reader})
    execute=FunctionType(fn.__code__,dict(fn.__globals__,original=old_base),argdefs=fn.__defaults__,closure=fn.__closure__)
    execute.__kwdefaults__=fn.__kwdefaults__
    base,base_proof=execute(m,checkpoint)
    m.a.require(len(captured)==1,"ONE_ORIGINAL_READER_FOR_ALL34")
    q=captured[0];row=q.json(MANIFEST["path"]);manifest.validate(row,m.a,original.MANIFEST)
    m.a.exact(row["extra_prior_producer_pin"],PRODUCER,"EXACT_REAL136130_PRODUCER")
    producer=q.json(PRODUCER["path"]);items=manifest.selected(producer,m.a)
    rows=base.binding.descriptors();m.a.exact(len(rows),32,"ALL_BOUNDED32_RETAINED")
    source=base.binding_module.source
    for root,item in zip(manifest.PRIORS,items):
        selected=source.descriptor(root,item["physical_pin"],next_case=160)
        m.a.exact(selected,item["descriptor"],"EXACT_BOUNDED_REAL_PRIOR_DESCRIPTOR")
        rows.append(selected)
    bound=base.binding_module.Binding(rows,MANIFEST,next_case=160)
    graph,proof=factory.connect(base,bound)
    actual,raw=q._read(CAPSULE["path"],parse=True);q._bind(actual["path"],actual)
    m.a.exact(actual,CAPSULE,"REAL34_CAPSULE_BYTES")
    decoded,decoder=graph.worker.decode(bytes(raw),{k:CAPSULE[k] for k in ("bytes","sha256")},checkpoint)
    m.a.exact(decoded.descriptors(),bound.descriptors(),"ALL34_CAPSULE_AND_MANIFEST_DECLARATIONS")
    m.a.exact(dict(decoded.manifest_pin),MANIFEST,"ACTUAL_MANIFEST030")
    return graph,dict(bounded_reader_reads=q.reads,bounded_reader_bytes=q.bytes_read,
        original64_reads_262144_bytes_limits_retained=True,one_reader_for_all_old_and_new_declarations=True,
        historical_runtime_or_review_body_files_read_by_this_reader=0,reader_source_pins=list(q.snapshots.values()),
        base_graph_proof=base_proof,graph_connection_proof=proof,decoder_proof=decoder,source_pairs=34,
        parent_full_fresh_admission_and_two_actual_Native_boundaries_required=True,
        current_controller_engine_worker_Native_or_GO_qualified=False)
