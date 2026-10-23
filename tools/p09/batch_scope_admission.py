"""Staged NO-GO admission of the immutable run010 package.

Read the small declaration records first, estimate cost before whole-corpus IO,
and never replay qualified preparation suites or accepted product bodies.
This is not a launcher and cannot authorize Native, a worker process, or GO.
"""
import json
import re
from types import SimpleNamespace as NS

SELF = 'tools/p09/batch_scope_admission.py'
TEST = 'tools/p09/tests/test_batch_scope_admission.py'
PREFIX = 'implementation/p09/evidence/p09-361-case165-'
PACKAGE = (
    dict(path=PREFIX+'successor-run010-manifest001.v1.json', bytes=92656,
        sha256='d1cd6925c634f070777f7226d2e00d9c6bddc4a1b8ff9ea099f680d2885620b7'),
    dict(path=PREFIX+'successor-worker-capsule010.compact.v1.json', bytes=15862,
        sha256='b0ba04432a678a8a0d2b179e31be6e48a103b792df4973c991672e1a3fe4a14a'),
    dict(path=PREFIX+'successor-worker-bootstrap010.v1.json', bytes=4899,
        sha256='6e33cce35d016532879a68afba16bd0a744d083e4bba5339ca9e2220e99b9e6b'),
    dict(path=PREFIX+'successor-run010-graph002.v1.json', bytes=11673,
        sha256='104a632a894608e33f51e3ea98c9e0080dd226465b3efc92dc410e3e6a899363'),
)
NATIVE009 = dict(path=PREFIX+'current-runtime-run009.v1.json', bytes=5046802,
    sha256='3588e9d53ff9b442c711d165e8ad09fb93627bc0dc756a467a059f11a71ce753')
PREPARATION_PROOF = dict(path=PREFIX+'fixed162-worker-transport-g001-code002.v1.json', bytes=55056,
    sha256='9c96a89833b30dc53c464e19b298846f50085ead9595e768ab0ad3531a962713')
PROGRAMS = ('tools/p09/verification_reuse.py', 'tools/p09/tests/test_verification_reuse.py',
    'tools/p09/batch_verification.py', 'tools/p09/tests/test_batch_verification.py',
    'tools/p09/batch_worker_entry.py', 'tools/p09/batch_preparation_package.py', SELF, TEST)


def require(ok, code):
    if not ok:
        raise ValueError('BATCH_ADMISSION_'+code)


def validate_report(report, scope):
    expected = dict(state='PREPARED_CURRENT_SUCCESSOR_GRAPH_AND_WIRE_NOT_CODE_PREFLIGHT_NATIVE_OR_GO',
        index=165, preparation_report_generation=2, cleanup_confirmed=True,
        product_or_Native_executed=False, GO_authorized=False, accepted_count_delta=0,
        fresh_inputs=64, final_fresh_hashes=64)
    require(all(type(report.get(k)) is type(v) and report[k] == v for k,v in expected.items()),
        'EXACT_PUBLISHED_REPORT_NOT_ACCEPTANCE')
    for name, expected_pin in zip(('manifest_pin','capsule_pin','bootstrap_pin'), PACKAGE[:3]):
        require(report.get(name) == expected_pin, 'EXACT_PACKAGE_PINS')
    sources = scope.pins(report['source_pins'])
    require(len(sources) == 64 and not set(sources) & {p['path'] for p in PACKAGE[3:]},
        'CLOSED64_PREPARATION_SOURCES_NOT_SELF_REFERENCE')
    return sources


def extend_plan(declared, mandatory, program_pins, package_pins, batch, checkpoint):
    """Only named current additions, never a reader.snapshots union."""
    scope = batch.scope
    require(type(program_pins) is dict and set(program_pins) == set(PROGRAMS),
        'EXPLICIT_PROGRAMS_NOT_OBSERVED_UNION')
    programs = scope.pins(list(program_pins.values()))
    require(set(programs) == set(PROGRAMS), 'EXPLICIT_PROGRAMS_NOT_OBSERVED_UNION')
    require(package_pins == scope.pins(list(PACKAGE)), 'IMMUTABLE_FOUR_FILE_PACKAGE')
    partition = batch.partition.candidate(declared.physical, 165, tuple(sorted(mandatory)), checkpoint)
    hot = scope.pins(partition['per_case_candidate'])
    cold = scope.pins(partition['batch_preservation_candidate'])
    additions = scope.extend(programs, package_pins)
    additions = scope.extend(additions, {batch.LEGACY_CONFIG['path']:batch.LEGACY_CONFIG})
    # The preparation's own receipt is not in its self-free source_pins table,
    # but graph002 explicitly depends on it. Declare that one named input.
    additions = scope.extend(additions, {PREPARATION_PROOF['path']:PREPARATION_PROOF})
    require(not set(additions) & set(cold), 'NO_HISTORICAL_RECEIPT_RECLASSIFIED')
    whole = scope.extend(declared.physical, additions)
    current = scope.extend(hot, additions)
    policy = batch.Batch(whole, current, cold, first_index=165, checkpoint=checkpoint)
    logical = scope.extend(declared.logical, additions)
    return NS(batch=policy, logical=logical, current=current, history=cold, whole=whole)


def early_budget(current, scope, views):
    """Conservative screen: original20s model, not the tighter10s credit.

    Keep both actual byte passes, Native acquisition14, margin60, PDH2.05,
    shared decoder5, final distinct sample0.5, and preparation15s allowance.
    A negative screen is NOT proof the actual tightened engine cannot fit.
    """
    raw = scope.cost(current, 14)
    # model() enforces its original600 deadline. Test the same arithmetic first
    # so an oversized declaration can be reported without a misleading crash.
    predicted = raw['predicted_combined_seconds'] - 2*len(current)/20 + 20+3+167/20+11+5+2.05
    if predicted >= 600:
        return dict(state='CONSERVATIVE_SCREEN_EXCEEDS600_NOT_ACTUAL_TIGHTENED_ENGINE_RESULT',
            original20_model_seconds=predicted, with_shared_decoder_final_sample_and_preparation_seconds=predicted+20.5,
            conservative_fits=False, actual_tightened_engine_budget_qualified=False)
    model = views.model(current, 167)
    require(abs(model['predicted_runtime_combined_seconds']-predicted) < 1e-9,
        'ORIGINAL_MODEL_ALL_TERMS_NOT_DISCOUNTED')
    total = model['predicted_runtime_combined_seconds'] + 5 + .5 + 15
    return dict(state='CONSERVATIVE_DECLARATION_COST_ONLY_NOT_NATIVE',
        original20_model_seconds=predicted, with_shared_decoder_final_sample_and_preparation_seconds=total,
        shared_decoder_allowance_seconds=5, final_sample_allowance_seconds=.5, preparation_allowance_seconds=15,
        conservative_fits=total < 600, actual_tightened_engine_budget_qualified=False,
        original_model=model, product_credit_taken=False, corpus_bytes_freshly_verified=False)


def read_plan(reader, a, batch, reuse):
    require(reuse.PROOF == PREPARATION_PROOF, 'EXACT_RETAINED_PREPARATION_RECEIPT')
    evidence = a.read_exact(reader, reuse.PROOF)
    reuse.dependencies(evidence)
    packet = a.read_exact(reader, evidence['prior_probe_pin'])
    history_name = PREFIX+'legacy-history-binding-code001.v1.json'
    history_pin = next(p for p in evidence['source_pins'] if p['path'] == history_name)
    history = a.read_exact(reader, history_pin)
    native = a.read_exact(reader, NATIVE009)
    manifest = a.read_exact(reader, evidence['manifest_pin'])
    hint = a.read_exact(reader, evidence['bootstrap_pin'])
    declared = batch.reconstruct_declared_scope(native, history, packet, evidence, manifest, reader.checkpoint)
    mandatory = set(declared.to_physical(evidence['source_pins']))
    mandatory.update(declared.to_physical([hint['step']['prior_queue_pin'],hint['step']['prior_candidate_pin']]))
    mandatory.update(native['imported_worker_source_paths'])
    require(mandatory <= set(declared.physical), 'ALL_ORIGINAL_REFERENCE_INPUTS_RETAINED')
    programs = {n:dict(reader.pin(n)) for n in PROGRAMS}
    a.exact(reader.pin(batch.LEGACY_CONFIG['path']), batch.LEGACY_CONFIG, 'EXACT_LEGACY_CONFIGURATION')
    report = a.read_exact(reader, PACKAGE[3])
    sources = validate_report(report, batch.scope)
    a.exact(report['step'], hint['step'], 'SAME_PUBLISHED_AND_ORIGINAL_PREDECESSOR_STEP')
    planned = extend_plan(declared, mandatory, programs, batch.scope.pins(list(PACKAGE)), batch, reader.checkpoint)
    # Declaration membership is not a source byte verification.
    physical_sources = declared.to_physical(list(sources.values()))
    mismatches = [n for n,p in physical_sources.items() if planned.current.get(n) != p]
    if mismatches:
        error = ValueError('BATCH_ADMISSION_ALL64_PACKAGE_DEPENDENCIES_IN_CURRENT')
        error.input_paths = mismatches[:16]
        raise error
    return NS(planned=planned, declared=declared, evidence=evidence, manifest=manifest,
        hint=hint, report=report, package_sources=sources)


class ReadOnlyEpochs:
    """Three bounded serial preparation phases, never a Native timer reset.

    Batch's whole witnesses have the same process/thread owner throughout.
    A CPU/deadline/IO failure cannot rotate to a new guard or retry a phase.
    Rotation is unavailable as soon as any actual case/Frame has started.
    """
    STAGES = ('construction', 'opening_and_metadata', 'closing')

    def __init__(self, factory, clock=None, identity=None):
        import os, threading, time
        self.factory = factory
        self.clock = clock or time.monotonic
        self.identity = identity or (lambda:(os.getpid(),threading.get_ident()))
        self.owner = self.identity()
        self.guard = None
        self.records = []
        self.broken = False
        self.started = None
        self.stage = None

    def check(self, *args, **kwargs):
        require(not self.broken and self.identity() == self.owner and self.guard is not None,
            'LIVE_SERIAL_READ_ONLY_EPOCH')
        try:self.guard.check(*args, **kwargs)
        except BaseException:
            self.broken = True
            raise

    def advance(self, stage, batch=None):
        require(not self.broken and self.identity() == self.owner, 'NO_FAILED_EPOCH_RETRY')
        index = len(self.records)+(1 if self.guard is not None else 0)
        require(index < len(self.STAGES) and stage == self.STAGES[index],
            'THREE_EXACT_SERIAL_PREPARATION_STAGES')
        if self.guard is not None:
            self.check(force=True)
            require(batch is not None and batch.phase in ('NEW','READY') and batch.active is None
                and not batch.cases and not batch.metadata_reader_active and batch.parent_connection is None,
                'NO_NATIVE_FRAME_CASE_OR_LIVE_METADATA_DURING_ROTATION')
            self.close()
        try:
            self.stage = stage
            self.started = self.clock()
            self.guard = self.factory()
            self.guard.acquire()
        except BaseException:
            self.broken = True
            raise

    def close(self):
        if self.guard is None:return
        guard = self.guard
        self.guard = None
        try:guard.close()
        except BaseException:
            self.broken = True
            raise
        finally:
            elapsed = None if self.started is None else self.clock()-self.started
            self.records.append(dict(stage=self.stage,elapsed_seconds=elapsed,
                cleanup_confirmed=guard.cleanup, samples=list(guard.samples)))
        if guard.cleanup is not True:self.broken = True
        require(guard.cleanup is True, 'EXACT_EPOCH_CLEANUP_BEFORE_SUCCESSOR')


def connect_package(root, reader, data, a, batch, bytes_policy):
    """Construct only the graph required by this real published entry.

    Unlike preparation publication, do not encode a successor packet, run
    negative qualification cases, construct an engine, or publish anything.
    """
    import importlib
    import batch_worker_entry as worker
    known = batch.scope.extend(data.planned.logical, batch.scope.pins(data.evidence['source_pins']))
    name = 'tools/p09/runtime_envelope_namespace_bundle_v1.py'
    a.exact(reader.pin(name), known[name], 'ORIGINAL_NAMESPACE_LOADER_SOURCE')
    original = importlib.import_module('runtime_envelope_namespace_bundle_v1')
    initial = batch.PacedNamespaceLoader(original, reader, known)
    libraries, _ = initial.api.load(root, [known['tools/p09/'+n+'.py'] for n in
        ('ast_clone_namespace_v1','ast_copy_namespace_connection_v1')], {})
    optimized, _ = libraries.ast_copy_namespace_connection_v1.connect(original,libraries.ast_clone_namespace_v1)
    paced = batch.PacedNamespaceLoader(optimized,reader,known)
    libraries, _ = paced.api.load(root,[known['tools/p09/native009_full72_construction_v1.py']],{})
    loader, _ = libraries.native009_full72_construction_v1.private_runtime_imports(paced.api)
    libraries, _ = loader.load(root,[known['tools/p09/'+n+'.py'] for n in
        ('fixed162_worker_transport_v1','receipt_xz_envelope_v1','bounded_successor_capsule_wire_v2')],{})
    api = libraries.fixed162_worker_transport_v1.connect(root,loader,batch.scope,bytes_policy,
        libraries.receipt_xz_envelope_v1,libraries.bounded_successor_capsule_wire_v2,reader.checkpoint,a.exact)
    def read(pin, limit):
        require(limit == 16384 and pin['bytes'] <= limit, 'ENTRY_ORIGINAL_READ_BOUND')
        before = reader.maximum_parse_bytes
        try:
            reader.maximum_parse_bytes = min(before,limit+1)
            actual, raw = reader._read(pin['path'],parse=True)
            reader._bind(actual['path'],actual)
        finally:reader.maximum_parse_bytes = before
        a.exact(actual,pin,'ENTRY_REAL_OWNED_PACED_BYTES')
        return bytes(raw)
    def transport(reference,step,check):
        return worker.transport_graph(root,loader,known,api,libraries.bounded_successor_capsule_wire_v2,
            bytes_policy,reference,step,check)
    entry = worker.reconstruct('case165-current-r010-tests',PACKAGE[2],read,api.reconstruct,transport,reader.checkpoint)
    require(entry.graph.binding.descriptors() == data.manifest['descriptors']
        and dict(entry.graph.binding.manifest_pin) == PACKAGE[0], 'REAL_PACKAGE_ALL162_AND_NEW_MANIFEST')
    actual, raw = reader._read(batch.RUNTIME,parse=True);reader._bind(actual['path'],actual)
    a.exact(actual,known[batch.RUNTIME],'ORIGINAL_PARENT_SCOPE_SOURCE')
    runtime, inverse = batch.install_scope(entry.runtime,bytes(raw),data.planned.batch)
    # Load every late metadata dependency BEFORE reader.finish(). The terminal
    # closing count must not be invalidated by a later loader source open.
    metadata_libraries, _ = loader.load(root,[known['tools/p09/'+n+'.py'] for n in
        ('fresh_lossless_metadata_reader_v1','shared_metadata_frame_decoder_budget_v1')],{})
    return NS(graph=entry.graph,runtime=runtime,core=entry.core,loader=loader,known=known,
        metadata_libraries=metadata_libraries,
        proof=dict(entry.proof,original_scope_AST_inverse=inverse['exact_original_AST_inverse'],
            actual_engine_constructed=False,encoder_or_negative_qualification_cases_run=False))


def optimized_reader(root, reader, known, loader, base, a):
    """Reuse the already-qualified fresh-stat and64KiB-workspace adapters.

    Do not change any published reader or default module. Exact source pins,
    wrapper MRO, original checkpoints/rates and full closing reads remain.
    """
    import audit_evidence_io as original
    names = ('single_snapshot_source_guard_v1','reusable_audit_chunk_v1')
    libs, _ = loader.load(root,[known['tools/p09/'+n+'.py'] for n in names],
        {'audit_evidence_io':original})
    snapshot,chunk = libs.single_snapshot_source_guard_v1,libs.reusable_audit_chunk_v1
    actual,raw = reader._read(snapshot.ORIGINAL_PIN['path'],parse=True)
    reader._bind(actual['path'],actual)
    a.exact(actual,snapshot.ORIGINAL_PIN,'EXACT_ORIGINAL_READER_SOURCE_FOR_OPTIMIZATION')
    a.exact(actual,chunk.ORIGINAL_PIN,'SAME_ORIGINAL_READER_FOR_BOTH_ADAPTERS')
    Source,source_proof = snapshot.reader_type(base,bytes(raw))
    Reader,chunk_proof = chunk.reader_type(Source,bytes(raw))
    return NS(Reader=Reader,chunk=chunk,source_proof=source_proof,chunk_proof=chunk_proof)


class MetadataRouter:
    """Fresh original decoder work under the owner's original shared budget."""
    def __init__(self, projection, budget):
        self.projection = projection
        self.budget = budget
        self.semantic_pins = projection.semantic_pins
        self.physical_pins = projection.physical_pins
        self.next_case = projection.next_case
        self.counts = {}

    def decode_fresh(self, name, pin, raw, live_checkpoint):
        previous = self.budget.checkpoint
        def guarded():previous();live_checkpoint()
        self.budget.checkpoint = guarded
        try:
            value = self.budget.run(lambda check:self.projection.decode_fresh(name,pin,raw,check))
            self.counts[name] = self.counts.get(name,0)+1
            return value
        finally:self.budget.checkpoint = previous


def parent_sources(data,batch):
    """Complete small callback declaration, checked before whole-corpus IO."""
    explicit = batch.scope.extend(data.package_sources,
        {n:dict(data.planned.current[n]) for n in PROGRAMS})
    explicit = batch.scope.extend(explicit,batch.scope.pins(list(PACKAGE)))
    explicit = batch.scope.extend(explicit,{batch.LEGACY_CONFIG['path']:batch.LEGACY_CONFIG})
    step_path = PREFIX+'step-config001.v1.json'
    require(step_path in data.planned.current,'ORIGINAL_STEP_CONFIG_DECLARED_BEFORE_WHOLE_IO')
    explicit = batch.scope.extend(explicit,{step_path:dict(data.planned.current[step_path])})
    physical = data.declared.to_physical(list(explicit.values()))
    require(all(data.planned.current.get(n) == p for n,p in physical.items()),
        'EVERY_PARENT_SOURCE_IS_EXACT_CURRENT_INPUT')
    return explicit


def metadata_admission(root, epochs, data, connected, reader_factory, a, batch):
    """Real full callback after actual begin(), no synthetic phase/witness."""
    policy = data.planned.batch
    require(policy.phase == 'READY' and policy.initial == batch.plain(policy.whole),
        'REAL_WHOLE_BEGIN_BEFORE_PARENT_METADATA')
    graph = connected.graph
    libs = connected.metadata_libraries
    projection, _ = graph.binding.project(data.planned.logical,epochs.check)
    budget = graph.frames.connection.original.DecoderBudget(epochs.check)
    shared = libs.shared_metadata_frame_decoder_budget_v1.SharedBudget()
    shared.attach('metadata',budget)
    router = MetadataRouter(projection,budget)
    Reader = libs.fresh_lossless_metadata_reader_v1.reader_type(reader_factory,router,graph.binding.descriptors())
    reader = Reader(root,epochs.check)
    explicit = connected.parent_sources
    try:
        required,rust = connected.runtime.current_input_scope(reader,graph,connected.core['step'],PACKAGE[3],PACKAGE[0],explicit)
        projection, _ = graph.binding.project(required,epochs.check)
        a.exact(batch.plain(projection.physical_pins),data.planned.current,'EXACT_CURRENT_NOT_WHOLE_OR_SUBSET')
        with policy.metadata_reader(reader,graph.binding):reader.finish()
        epochs.check(force=True)
        require(reader.final_fresh_hashes == len(reader.snapshots),'ALL_METADATA_CLOSING_HASHES')
        return dict(state='PASS_REAL_PARENT_INPUT_CALLBACK_NOT_NATIVE_OR_ENGINE_EXECUTION',
            fresh_inputs=len(reader.snapshots),final_fresh_hashes=reader.final_fresh_hashes,
            physical_read_passes=reader.read_passes,physical_bytes_read=reader.bytes_read,
            selected_current_inputs=len(projection.physical_pins),rust_declared_inputs=len(rust),
            metadata=libs.fresh_lossless_metadata_reader_v1.summary(reader),
            shared_decoder=shared.evidence(),all421_preserved_not_per_case_reinjected=True,
            parent_engine_worker_Frame_or_Native_executed=False,GO_authorized=False)
    finally:shared.restore()


def main():
    import argparse
    import sys
    import time
    sys.dont_write_bytecode = True
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--metadata',action='store_true',
        help='Read actual whole start/end boundaries and original parent input callback; no engine/process/GO')
    args = parser.parse_args()
    denied = []
    def audit(event, values):
        if event in ('subprocess.Popen','os.system','os.startfile'):
            denied.append(event)
            raise ValueError('BATCH_ADMISSION_PROCESS_DENIED')
    sys.addaudithook(audit)
    import accept_case112_current_epoch as a
    import conservative_maintenance as c
    import distinct_final_sample_guard_v1 as final
    import owned_cpu_baseline_v1 as baseline
    import prepared_run_closure_v1 as policy
    import terminal_metadata_pressure_v1 as pressure
    import batch_verification as batch
    import verification_reuse as reuse
    import held_native_read_views_v1 as views
    policy.configure_host_policy(c)
    factory = baseline.guard_type(pressure.guard_type(final.guard_type(a.Guard)))
    epochs = ReadOnlyEpochs(factory)
    guard = epochs
    reader = None
    started = time.monotonic()
    out = dict(state='FAILED_DECLARATION_SCREEN_NOT_NATIVE', GO_authorized=False,
        accepted_count_delta=0, product_or_worker_or_process_executed=False, evidence_files_created=0)
    try:
        epochs.advance('construction')
        reader = a.AcceptanceReader(c.ROOT, guard.check)
        data = read_plan(reader, a, batch, reuse)
        for module in (batch.scope, views):
            expected = data.planned.current[module.SELF]
            a.exact(reader.pin(module.SELF), expected, 'ORIGINAL_COST_SOURCE')
        model = early_budget(data.planned.current, batch.scope, views)
        out.update(scope_declaration=data.planned.batch.summary(), early_budget=model,
            original16_or87_tests_reexecuted=False, whole_corpus_read=False,
            package64_fresh_dependency_check_executed=False, parent_metadata_executed=False)
        if args.metadata:
            require(model['conservative_fits'],'COST_BEFORE_EXPENSIVE_IO')
            explicit = parent_sources(data,batch)
            import owned_source_read_pressure as bytes_policy
            connected = connect_package(c.ROOT,reader,data,a,batch,bytes_policy)
            connected.parent_sources = explicit
            out['package_connection'] = connected.proof
            optimized = optimized_reader(c.ROOT,reader,connected.known,connected.loader,a.AcceptanceReader,a)
            out['reader_optimization'] = dict(fresh_source_stat_and_reusable64KiB=True,
                published_default_sources_unchanged=True,byte_hash_JSON_or_stat_cache=False,
                original_checkpoints_open20_byte_rates_and_closing_reads_retained=True)
        reader.finish();guard.check(force=True)
        require(reader.final_fresh_hashes == len(reader.snapshots) and not denied, 'CLOSING_AND_NO_PROCESS')
        out['construction_source_pins'] = [dict(reader.snapshots[n]) for n in PROGRAMS]
        if args.metadata:
            epochs.advance('opening_and_metadata',data.planned.batch)
            print(json.dumps(dict(state='RUNNING_READ_ONLY_WHOLE_OPENING',inputs=len(data.planned.whole),
                declared_bytes=sum(p['bytes'] for p in data.planned.whole.values()),GO_authorized=False)),flush=True)
            opening = optimized.Reader(c.ROOT,guard.check)
            data.planned.batch.begin(opening)
            out['whole_opening'] = dict(fresh_inputs=len(opening.snapshots),bytes_read=opening.bytes_read,
                actual_read_passes=opening.read_passes,closing_hashes_not_required_for_single_boundary=True)
            out['whole_corpus_read'] = True
            print(json.dumps(dict(state='RUNNING_READ_ONLY_PARENT_METADATA',whole_opening_inputs=len(opening.snapshots),
                GO_authorized=False)),flush=True)
            out['parent_metadata_executed'] = True
            out['parent_metadata'] = metadata_admission(c.ROOT,epochs,data,connected,optimized.Reader,a,batch)
            epochs.advance('closing',data.planned.batch)
            print(json.dumps(dict(state='RUNNING_READ_ONLY_WHOLE_CLOSING',inputs=len(data.planned.whole),
                GO_authorized=False)),flush=True)
            closing = optimized.Reader(c.ROOT,guard.check)
            out['whole_batch'] = data.planned.batch.finish(closing)
            out['whole_closing'] = dict(fresh_inputs=len(closing.snapshots),bytes_read=closing.bytes_read,
                actual_read_passes=closing.read_passes)
            guard.check(force=True)
            out.update(whole_corpus_read=True,parent_metadata_executed=True,
                package64_fresh_dependency_check_executed=True,
                state='PASS_BATCH_REAL_METADATA_AND_WHOLE_BOUNDARIES_NOT_NATIVE')
        else:out['state'] = 'PASS_STAGED_DECLARATION_AND_CONSERVATIVE_COST_SCREEN_NOT_NATIVE'
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        out['error_type'] = type(error).__name__
        if hasattr(error,'input_paths'):out['scope_disagreements'] = error.input_paths
        if error.args and type(error.args[0]) is str and re.fullmatch('[A-Z0-9_]{1,160}', error.args[0]):
            out['error_code'] = error.args[0]
        import traceback
        out['error_frames'] = [dict(file=c.Path(f.filename).name,function=f.name,line=f.lineno)
            for f in traceback.extract_tb(error.__traceback__)[-4:]]
    finally:
        try:epochs.close()
        except (ValueError,OSError):out['state'] = 'CLEANUP_FAILED_NOT_NATIVE'
        cleanup = bool(epochs.records) and all(r['cleanup_confirmed'] is True for r in epochs.records)
        samples = [s for r in epochs.records for s in r['samples']]
        if not cleanup:out['state'] = 'CLEANUP_FAILED_NOT_NATIVE'
        if args.metadata and 'data' in locals():out['current_batch_phase'] = data.planned.batch.phase
        for label in ('opening','closing'):
            observed = locals().get(label)
            if observed is not None:
                out['whole_'+label+'_progress'] = dict(fresh_inputs=len(observed.snapshots),
                    actual_read_passes=observed.read_passes,bytes_read=observed.bytes_read,
                    source_stat=observed.source_snapshot_diagnostics(),workspace=optimized.chunk.summary(observed))
        out.update(cleanup_confirmed=cleanup, elapsed_seconds=time.monotonic()-started,
            read_only_resource_epochs=[{k:v for k,v in r.items() if k != 'samples'} for r in epochs.records],
            fresh_inputs=0 if reader is None else len(reader.snapshots),
            final_fresh_hashes=0 if reader is None else reader.final_fresh_hashes,
            bytes_read=0 if reader is None else reader.bytes_read,
            CPU_max=max((s['system_cpu_percent'] for s in samples),default=None),
            owned_CPU_machine_max=max((s.get('parent_cpu_machine_percent') or 0 for s in samples),default=None),
            private_MiB_max=max((s['parent_private_mib'] for s in samples),default=None),
            RAM_available_min=min((s['available_ram_percent'] for s in samples),default=None),
            subprocess_creation_attempts=len(denied))
        print(json.dumps(out,ensure_ascii=True))
    return 0 if out['state'].startswith('PASS_') else 2


if __name__ == '__main__':
    raise SystemExit(main())
