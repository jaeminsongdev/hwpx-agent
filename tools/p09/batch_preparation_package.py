"""Publish immutable run010 preparation data, never a launcher or acceptor."""
import copy
import hashlib
import json
from types import SimpleNamespace as NS

SELF = 'tools/p09/batch_preparation_package.py'
PREFIX = 'implementation/p09/evidence/p09-361-case165-'
MANIFEST = PREFIX+'successor-run010-manifest001.v1.json'
WIRE = PREFIX+'successor-worker-capsule010.compact.v1.json'
BOOTSTRAP = PREFIX+'successor-worker-bootstrap010.v1.json'
REPORT = PREFIX+'successor-run010-graph001.v1.json'
PATHS = (MANIFEST, WIRE, BOOTSTRAP, REPORT)


def require(ok, code):
    if not ok:raise ValueError('BATCH_PACKAGE_'+code)


def encoded(row):
    return (json.dumps(row, sort_keys=True, ensure_ascii=True, allow_nan=False,
        separators=(',', ':'))+'\n').encode('ascii')


def pin(name, data):
    return dict(path=name, bytes=len(data), sha256=hashlib.sha256(data).hexdigest())


def report_path(generation):
    require(type(generation) is int and 1 <= generation <= 8, 'EXPLICIT_BOUNDED_REPORT_GENERATION')
    return PREFIX+f'successor-run010-graph{generation:03}.v1.json'


def prepare(root, reader, guard, prepared, original_manifest, original_hint, evidence,
            prior, provenance_keys, known, bytes_policy, a, publisher, worker):
    """Build only the explicitly named new package; preserve all old files."""
    reader.checkpoint()
    history = {name:copy.deepcopy(prior['source_input_representation'][name])
        for name in provenance_keys if name in prior['source_input_representation']}
    a.exact(original_hint['historical_provenance'], history, 'SAME_ORIGINAL_PREDECESSOR_PROVENANCE')
    manifest = copy.deepcopy(original_manifest)
    manifest.update(schema_version='hwpx-agent.p09-run010-prepared-manifest/v1', physical_run=10,
        historical_predecessor_provenance=history, current_whole_Native_source_scope_qualified=False)
    manifest_data = encoded(manifest)
    manifest_pin = pin(MANIFEST, manifest_data)
    old = prepared.graph
    bound = old.binding_module.Binding(manifest['descriptors'], manifest_pin, next_case=165)
    a.exact(bound.descriptors(), old.binding.descriptors(), 'ALL162_OLD_ROWS_AND_ROLES_UNCHANGED')
    reference = NS(**{**vars(old), 'binding':bound})
    # Reference bootstrap/wire remain constructor data, with their original
    # identity and manifest. Only the NEW execution wire points to new data.
    transport = worker.prepare_worker_transport(root, prepared.loader, known, prepared.api,
        prepared.bounded_wire, bytes_policy, reference, original_hint, evidence,
        prepared.reference_wire, reader.checkpoint, a.exact)
    a.exact(transport.graph.binding.descriptors(), original_manifest['descriptors'], 'NEW_PACKAGE_ALL162')
    core = json.loads(transport.bootstrap.decode('ascii'))['execution']
    a.exact(core['manifest_pin'], manifest_pin, 'NEW_EXECUTION_NOT_OLD_MANIFEST_RELABEL')
    a.exact(core['historical_provenance'], history, 'UNCHANGED_NEW_EXECUTION_LINEAGE')
    data = ((MANIFEST, manifest_data, 262144), (WIRE, transport.wire, 16384),
        (BOOTSTRAP, transport.bootstrap, 16384))
    published = []
    created = []
    for name, raw, limit in data:
        reader.checkpoint()
        existed = (root/name).exists()
        actual = publisher.publish_bytes(root, name, raw, reader, guard, bytes_policy, a, limit)
        a.exact(actual, pin(name, raw), 'EXCLUSIVE_NEW_PACKAGE_BYTES')
        published.append(actual)
        if not existed:created.append(name)
    # REAL disk input path: no prototype dictionary and no codec qualification
    # cases are called by reconstruct(). No process or product is reachable.
    def reference_factory(hint, packet, checkpoint):
        return prepared.api.reconstruct(hint, packet, checkpoint)
    def transport_factory(reference, step, checkpoint):
        return worker.transport_graph(root, prepared.loader, known, prepared.api,
            prepared.bounded_wire, bytes_policy, reference, step, checkpoint)
    admitted = worker.reconstruct(transport.proof['task'], published[2], worker.file_reader(root, reader.checkpoint),
        reference_factory, transport_factory, reader.checkpoint)
    a.exact(dict(admitted.graph.binding.manifest_pin), manifest_pin, 'REAL_DISK_NEW_MANIFEST_IDENTITY')
    a.exact(admitted.graph.binding.descriptors(), original_manifest['descriptors'], 'REAL_DISK_ALL162')
    # This source is required by the complete original parent callback.
    step_program = 'tools/p09/prepare_current_queue_step.py'
    a.exact(reader.fresh_pin(step_program), known[step_program], 'ORIGINAL_PARENT_DERIVATION_PROGRAM')
    return NS(manifest=manifest, manifest_pin=manifest_pin, wire_pin=published[1], bootstrap_pin=published[2],
        step=copy.deepcopy(original_hint['step']), data_pins=published, publisher=publisher, created_paths=created,
        proof=dict(data_artifacts=len(published), real_disk_metadata_inputs=4,
            whole_original_reference_and_inner_decoder_completed=True, all162_and_lineage_unchanged=True,
            Native_or_worker_process_or_product_executed=False, GO_authorized=False, accepted_count_delta=0))


def finish(root, prepared, source_reader, guard, a, bytes_policy, generation=1):
    """Publish only after the actual preparation reader/guard have closed."""
    require(guard.cleanup is True and source_reader.final_fresh_hashes == len(source_reader.snapshots),
        'REAL_SOURCE_CLOSING_AND_CLEANUP_BEFORE_REPORT')
    name = report_path(generation)
    row = dict(state='PREPARED_CURRENT_SUCCESSOR_GRAPH_AND_WIRE_NOT_CODE_PREFLIGHT_NATIVE_OR_GO',
        preparation_report_generation=generation,
        index=165, physical_run=10, step=prepared.step, manifest_pin=prepared.manifest_pin,
        capsule_pin=prepared.wire_pin, bootstrap_pin=prepared.bootstrap_pin, descriptors=162,
        source_pins=[dict(p) for p in source_reader.snapshots.values()],
        fresh_inputs=len(source_reader.snapshots), final_fresh_hashes=source_reader.final_fresh_hashes,
        cleanup_confirmed=True, accepted_count_delta=0, product_or_Native_executed=False, GO_authorized=False,
        actual_current_Native_source_hashes_or_Frame_qualified=False,
        parent_metadata_admission_or_cost_or_new_process_qualified=False,
        actual_file_entry_proof=prepared.proof)
    raw = encoded(row)
    verifier = a.AcceptanceReader(root, guard.check)
    existed = (root/name).exists()
    report_pin = prepared.publisher.publish_bytes(root, name, raw, verifier, guard, bytes_policy, a, 262144)
    verifier.finish()
    a.require(verifier.final_fresh_hashes == len(verifier.snapshots) == 1, 'ONLY_NEW_REPORT_CLOSING_READ')
    return dict(report_pin=report_pin, source_inputs=len(source_reader.snapshots),
        source_final_hashes=source_reader.final_fresh_hashes, report_final_hashes=1,
        immutable_artifact_pins=prepared.data_pins+[report_pin],
        files_created=len(prepared.created_paths)+(0 if existed else 1),
        unchanged_files_reused=4-len(prepared.created_paths)-(0 if existed else 1),
        state='PUBLISHED_RUN010_PREPARATION_PACKAGE_AND_REAL_FILE_ENTRY_NOT_NATIVE',
        GO_authorized=False, accepted_count_delta=0)
