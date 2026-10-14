"""Stored run004 declaration: retain29, add two exact failures and real prior132.

This loader proves a full declaration, not a runtime admission or GO.
"""
import runtime_failed160_extras_v1 as extras
SELF="tools/p09/runtime_successor_manifest_v7.py"
TEST="tools/p09/tests/test_runtime_successor_manifest_v7.py"
SCHEMA="hwpx-agent.p09-successor160-run004-source-manifest/v7"
PATH="implementation/p09/evidence/p09-361-case160-source-manifest029.v7.json"
PRIOR_PRODUCER="implementation/p09/evidence/p09-361-case160-prior132-transport-producer-r848.v1.json"
PRIOR=dict(path="implementation/p09/evidence/p09-361-case132-current-runtime-run001.v1.json",bytes=2472248,
    sha256="6ebab43e075e1da55674120b9e5883408b6be63d45ab58170d06c27058d42f4d")

def validate(row,a,base_pin):
    a.require(type(row) is dict and set(row)=={"schema_version","index","before","physical_product_run",
        "base_manifest_pin","extra_failure_producer_pin","prior132_producer_pin"},"CLOSED_ACTUAL32_RUN004_MANIFEST")
    a.fields(row,dict(schema_version=SCHEMA,index=160,before=153,physical_product_run=4,
        base_manifest_pin=base_pin),"EXACT_RUN004_CONTEXT_BASE29_NOT_RELABELED")
    a.exact(row["extra_failure_producer_pin"]["path"],extras.PRODUCER,"EXACT_FAILED002003_PRODUCER_PATH")
    a.exact(row["prior132_producer_pin"]["path"],PRIOR_PRODUCER,"EXACT_REAL_PRIOR132_PRODUCER_PATH")
    return row

def load(q,pin,a,*,base_graph,base_pin,prepared_scope):
    row=validate(a.read_exact(q,pin),a,base_pin)
    a.exact(pin["path"],PATH,"ACTUAL_MANIFEST029_PATH")
    a.exact(dict(base_graph.binding.manifest_pin),base_pin,"BASE_REAL29_GRAPH_MANIFEST")
    descriptors=base_graph.binding.descriptors();a.exact(len(descriptors),29,"ALL_ORIGINAL29_RETAINED")
    producer=a.read_exact(q,row["prior132_producer_pin"])
    a.fields(producer,dict(state="PASS_PRIOR132_EXCLUSIVE_LOSSLESS_IN_ACTUAL_SCOPE_NOT_ADOPTED_MANIFEST_OR_GO",
        original_pin=PRIOR,exact_original_restore_passes=2,write_rate_bytes_per_second=2097152,
        cleanup_confirmed=True,original_receipt_rewritten=False,product_or_Native_reexecuted=False,GO_authorized=False),
        "ACTUAL_UNMODIFIED_PRIOR132_TRANSPORT")
    a.require(producer["fresh_inputs"]==producer["final_fresh_hashes"]==18,"ALL_PRIOR132_FINAL_HASHES")
    for p in producer["source_pins"]:a.exact(q.pin(p["path"]),p,"CURRENT_PRIOR132_SOURCE_BYTES")
    a.exact(prepared_scope.get(PRIOR["path"]),PRIOR,"REAL_PRIOR132_IN_WHOLE_PREPARED_SCOPE")
    a.exact(q.fresh_pin(PRIOR["path"]),PRIOR,"FRESH_REAL_PRIOR132")
    a.exact(q.fresh_pin(producer["physical_pin"]["path"]),producer["physical_pin"],"FRESH_REAL_PRIOR132_PHYSICAL")
    admitted=extras.admission(q,a)
    a.exact(q.snapshots[extras.PRODUCER],row["extra_failure_producer_pin"],"SAME_ACTUAL_FAILURE_PRODUCER_PIN")
    connected=extras.connect(base_graph.binding_module.source,base_graph.binding_module,admitted)
    source=base_graph.binding_module.source
    for entry in admitted:
        descriptors.append(source.descriptor(entry["failed_runtime_pin"],entry["physical_pin"],next_case=160))
    descriptor=source.descriptor(PRIOR,producer["physical_pin"],next_case=160)
    a.exact(descriptor,producer["descriptor"],"SAME_PRIOR132_DECLARATION")
    descriptors.append(descriptor)
    scope=source.scope.extend(prepared_scope,q.snapshots)
    for entry in admitted:scope=source.scope.extend(scope,{entry["failed_runtime_pin"]["path"]:entry["failed_runtime_pin"]})
    scope=source.scope.extend(scope,{pin["path"]:pin})
    bound=base_graph.binding_module.Binding(descriptors,pin,next_case=160)
    a.exact(len(bound.descriptors()),32,"ACTUAL_STORED32_MANIFEST")
    q.pin(SELF)
    return bound,source.scope.extend(scope,q.snapshots),dict(actual_manifest029_pin=pin,source_pairs=32,
        original29_retained=True,extra_failure_admissions=admitted,failed_role_connection=connected,
        actual_stored_declaration_not_diagnostic_constructor=True,
        new_run004_controller_Native_independent_oracle_or_GO_qualified=False)
