"""Actual32 bootstrap with the unchanged original64/262144 reader limits.

Only capsule, declaration and small producer metadata are read here. Fresh
whole admission and Native byte boundaries remain parent requirements.
"""
from types import FunctionType
import successor_bounded_graph_bootstrap_v5 as original
import runtime_successor_manifest_v7 as manifest
import successor_runtime_graph_v6 as factory
import runtime_failed160_extras_v1 as extras

SELF="tools/p09/successor_bounded_graph_bootstrap_v6.py"
TEST="tools/p09/tests/test_successor_bounded_graph_bootstrap_v6.py"
MANIFEST=dict(path=manifest.PATH,bytes=742,sha256="6e2998cfc5cd7ebb690f1c46f61c6a34bcaa9c211a41d1638521ab23d608fde6")
CAPSULE=dict(path="implementation/p09/evidence/p09-361-case160-worker-policy-capsule006.compact.v1.json",bytes=11346,
    sha256="2f17b916d461df129f5a4f7f45913dd472c7c7a56119ebd4000c5d867262bb92")
FAILURES=dict(path=extras.PRODUCER,bytes=6572,sha256="f81aa985d888625da0db2911a13fabfbec048a86151367738bb93b3fbc41b395")
PRIOR132=dict(path=manifest.PRIOR_PRODUCER,bytes=4538,sha256="8f125ad4309747c8b30dd9f21a69dea69c81c335e19efde536402eb3428106aa")
EXTRA_PINS=(MANIFEST,CAPSULE,FAILURES,PRIOR132)

def declared_failures(produced,a):
    a.fields(produced,dict(state="PASS_EXCLUSIVE_FAILED002003_TRANSPORT_NOT_ADMITTED_MANIFEST_RUNTIME_OR_GO",
        exact_original_restore_passes=4,cleanup_confirmed=True,failures_promoted=False,
        original_failures_rewritten=False,actual_product_or_Native_executed=False,GO_authorized=False),"BOUNDED_EXACT_FAILURE_DECLARATION")
    rows=produced["selected_outputs"];a.require(type(rows) is list and len(rows)==2,"BOUNDED_TWO_FAILURES")
    declared=[]
    for root,item in zip(extras.ROOTS,rows):
        a.exact(item["original_pin"],root,"BOUNDED_ONLY_EXACT_FAILED002003")
        declared.append(dict(schema_version=extras.SCHEMA,current_case=160,failed_runtime_pin=dict(root),
            physical_pin=dict(item["physical_pin"]),independent_review_pin=dict(item["independent_review_pin"]),
            original_failure_promoted=False,current_product_or_GO_qualified=False))
    return declared

def load(m,checkpoint):
    captured=[]
    class Reader(original.Reader):
        def __init__(self,*args):
            super().__init__(*args)
            self.allowed.update({p["path"]:dict(p) for p in EXTRA_PINS});captured.append(self)
    # The entire old loader and actual Reader method code are retained. The
    # one Reader instance accumulates both old and new reads under one bound.
    fn=original.load
    execute=FunctionType(fn.__code__,dict(fn.__globals__,Reader=Reader),argdefs=fn.__defaults__,closure=fn.__closure__)
    execute.__kwdefaults__=fn.__kwdefaults__
    base,base_proof=execute(m,checkpoint)
    m.a.require(len(captured)==1,"ONE_ORIGINAL_BOUNDED_READER")
    q=captured[0];row=q.json(MANIFEST["path"]);manifest.validate(row,m.a,original.MANIFEST)
    m.a.exact(row["extra_failure_producer_pin"],FAILURES,"EXACT_FAILURE_PRODUCER_BYTES")
    m.a.exact(row["prior132_producer_pin"],PRIOR132,"EXACT_PRIOR132_PRODUCER_BYTES")
    failed=q.json(FAILURES["path"]);admitted=declared_failures(failed,m.a)
    prior=q.json(PRIOR132["path"])
    m.a.fields(prior,dict(state="PASS_PRIOR132_EXCLUSIVE_LOSSLESS_IN_ACTUAL_SCOPE_NOT_ADOPTED_MANIFEST_OR_GO",
        original_pin=manifest.PRIOR,cleanup_confirmed=True,exact_original_restore_passes=2,
        original_receipt_rewritten=False,product_or_Native_reexecuted=False,GO_authorized=False),"EXACT_BOUNDED_PRIOR132")
    rows=base.binding.descriptors();m.a.exact(len(rows),29,"ALL_BOUNDED_BASE29")
    connected=extras.connect(base.binding_module.source,base.binding_module,admitted)
    source=base.binding_module.source
    rows.extend(source.descriptor(r["failed_runtime_pin"],r["physical_pin"],next_case=160) for r in admitted)
    selected=source.descriptor(manifest.PRIOR,prior["physical_pin"],next_case=160)
    m.a.exact(selected,prior["descriptor"],"EXACT_PRIOR132_DESCRIPTOR")
    rows.append(selected)
    bound=base.binding_module.Binding(rows,MANIFEST,next_case=160)
    graph,graph_proof=factory.connect(base,bound)
    actual,raw=q._read(CAPSULE["path"],parse=True);q._bind(actual["path"],actual)
    m.a.exact(actual,CAPSULE,"REAL_EXACT_COMPACT32_CAPSULE")
    decoded,decoder=graph.worker.decode(bytes(raw),{k:CAPSULE[k] for k in ("bytes","sha256")},checkpoint)
    m.a.exact(decoded.descriptors(),bound.descriptors(),"CAPSULE32_AND_DECLARATION_ALL_EQUAL")
    m.a.exact(dict(decoded.manifest_pin),MANIFEST,"CAPSULE32_ACTUAL_MANIFEST029")
    return graph,dict(bounded_reader_reads=q.reads,bounded_reader_bytes=q.bytes_read,
        original64_reads_262144_bytes_limits_retained=True,single_original_reader_for_base_and_extensions=True,
        historical_runtime_or_review_body_files_read_by_this_reader=0,
        reader_source_pins=list(q.snapshots.values()),base_graph_proof=base_proof,
        failure_declarations=admitted,failure_role_connection=connected,graph_connection=graph_proof,
        capsule_decoder_proof=decoder,source_pairs=32,worker_task=graph.worker.TASK,
        parent_fresh_whole_admission_and_live_locks_required=True,
        actual_controller_Native_worker_or_GO_qualified=False)
