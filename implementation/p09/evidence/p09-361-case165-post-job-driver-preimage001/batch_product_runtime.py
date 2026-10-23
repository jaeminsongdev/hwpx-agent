"""One explicit case165 Native010 product chain; no automatic retry/acceptance.

--connect-only never creates a process or intent. --run-product is an explicit
operator action requiring current code/construction qualification; that record
is NOT execution permission. This agent must obtain the separately required
human execution authority before using that mode. Native008/009 never replay.
Original Native ownership/Frame/limits and the full checker are retained.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from types import SimpleNamespace as NS

SELF = 'tools/p09/batch_product_runtime.py'
TEST = 'tools/p09/tests/test_batch_product_runtime.py'
TASK = 'case165-current-r010-tests'
CANONICAL = 'implementation/p09/evidence/p09-361-case165-current-runtime-run010.v1.json'
INTENT = 'implementation/p09/evidence/p09-361-case165-native010-product-dispatch001.intent.v1.json'
RESULT = 'implementation/p09/evidence/p09-361-case165-native010-product-dispatch001.v1.json'
QUALIFICATION = 'implementation/p09/evidence/p09-361-case165-native010-dispatch-qualification001.v1.json'
PRIOR = dict(path='tools/p09/batch_pre_go_runtime.py', bytes=25016,
    sha256='cc4d2b0030c7ce4324c6cb994f5deb4f042a8d4f1bb2cc0b8366c2b9e8e83761')
POST = dict(path='tools/p09/batch_post_native.py', bytes=11267,
    sha256='cd386dba0aef5f55a31cf221bf5cf524da67c97b5973bced5f3aacf6a386b961')
WORKER = dict(path='tools/p09/batch_product_worker.py', bytes=4818,
    sha256='45ff19b23f16e930e796e0b17d48da9661afc85e4673e4b3fa9adffaea53c1e3')
LAUNCH = dict(path='tools/p09/batch_product_launch.py', bytes=3590,
    sha256='33c4d7dc489bae347357844a44241dce41c18bbb49d56424595a391f7e428492')
CHECKPOINT = dict(path='tools/p09/preparation_checkpoint_owner.py', bytes=5731,
    sha256='2ef536c53e0e2a82df44f0917783cf7f9fcd67e8d5dcd3d28d17d458c5285078')


def require(ok, code):
    if not ok:
        raise ValueError('PRODUCT_NATIVE010_' + code)


def mode(argv):
    require(type(argv) is list and argv in (['--connect-only'], ['--run-product']),
        'EXPLICIT_CONNECT_OR_ONE_PRODUCT_MODE')
    return argv == ['--run-product']


def bootstrap(root):
    path = root / PRIOR['path']
    require(path.is_file() and not path.is_symlink() and not path.is_junction(), 'DIRECT_QUALIFIED_SOURCE')
    for ancestor in (path.parent, *path.parent.parents):
        require(ancestor.is_dir() and not ancestor.is_symlink() and not ancestor.is_junction(),
            'DIRECT_QUALIFIED_SOURCE_ANCESTORS')
        if ancestor == root:
            break
    with path.open('rb') as stream:
        raw = stream.read(PRIOR['bytes'] + 1)
    require(len(raw) == PRIOR['bytes'] and hashlib.sha256(raw).hexdigest() == PRIOR['sha256'],
        'EXACT_ORIGINAL_CONNECTION_DEPENDENCIES')
    env = dict(__name__='p09_exact_native010_dependencies', __file__=str(path))
    exec(compile(raw, PRIOR['path'], 'exec'), env)
    return NS(**env)


class ProcessPolicy:
    def __init__(self, root, *, product):
        require(type(product) is bool, 'EXPLICIT_PRODUCT_MODE')
        self.root, self.product = root, product
        self.context = None
        self.attempts = 0
        self.denied = []

    def arm(self, context):
        require(self.product and self.context is None and not self.denied
            and not context.active and context.attempts == context.jobs == 0,
            'ONE_UNUSED_PRODUCT_PARENT_AFTER_WHOLE_OPENING')
        self.context = context

    def __call__(self, event, args):
        if event not in ('subprocess.Popen', 'os.system', 'os.startfile', 'os.exec', 'os.posix_spawn', 'os.fork'):
            return
        try:
            require(event == 'subprocess.Popen' and self.product and self.context is not None
                and self.attempts == 0 and not self.denied and len(args) == 4,
                'ONE_CURRENT_PRODUCT_ENTRY_PROCESS_ONLY')
            prefix = subprocess.list2cmdline([sys.executable, '-B', str(self.root / WORKER['path']), '--ready-handle'])
            suffix = subprocess.list2cmdline(['--task', TASK])
            match = re.fullmatch(re.escape(prefix) + ' ([1-9][0-9]{0,19}) ' + re.escape(suffix), args[1]) \
                if type(args[1]) is str else None
            require(match is not None and int(match[1]) < 2**64
                and args[0] in (None, sys.executable) and os.fspath(args[2]) == os.fspath(self.root)
                and args[3] is None, 'EXACT_ENTRY_TASK_HANDLE_ROOT_AND_INHERITED_ENV')
            self.context.checkpoint()  # Same actual first-boundary Frame and owned Job.
            self.attempts += 1
        except BaseException:
            self.denied.append(event)
            raise


def admit_qualification(reader, a):
    row = reader.json(QUALIFICATION)
    a.fields(row, dict(state='QUALIFIED_NATIVE010_DISPATCH_CODE_AND_CONSTRUCTION_NOT_EXECUTION',
        GO_authorized=False, accepted_count_delta=0, official_accepted_count=158, next_case=165),
        'CURRENT_QUALIFICATION_NOT_GO_PERMISSION')
    tests, closing, constructed = row['dispatcher_contracts'], row['closing_contracts'], row['actual_connection']
    checkpoint = row['preparation_checkpoint_contracts']
    require(type(tests['tests']) is int and tests['tests'] > 0, 'ALL_CURRENT_DISPATCHER_CONTRACTS')
    a.fields(tests, dict(errors=0, failures=0, skips=0, process_creation_attempts=0,
        cleanup_confirmed=True), 'ALL_CURRENT_DISPATCHER_CONTRACT_RESULTS')
    a.fields(closing, dict(tests=22, errors=0, failures=0, skips=0, cleanup_confirmed=True,
        process_creation_attempts=0), 'CURRENT_READER_OWNED_ORACLE_CONTRACTS')
    a.fields(checkpoint, dict(tests=9, errors=0, failures=0, skips=0, cleanup_confirmed=True,
        process_creation_attempts=0), 'ORIGINAL_PROFILE_PREPARATION_CHECKPOINT_CONTRACTS')
    a.fields(constructed, dict(state='PASS_NATIVE010_PRODUCT_DRIVER_CONNECTION_NOT_EXECUTION', mode='connect-only',
        original_parent_execution_attempted=False, process_creation_attempts=0, cleanup_confirmed=True),
        'ACTUAL_NONEXECUTING_CURRENT_CONSTRUCTION')
    require(constructed['helper_inventory']['Native_count'] <= 64
        and constructed['construction_fresh_inputs'] == constructed['construction_final_hashes'] > 0,
        'COMPLETE_CONSTRUCTION_AND_ORIGINAL_HELPER_BOUND')
    current = {p['path']: p for p in constructed['construction_source_pins']}
    require(type(constructed['construction_fresh_inputs']) is int
        and type(constructed['construction_final_hashes']) is int
        and len(current) == len(constructed['construction_source_pins']) == constructed['construction_fresh_inputs'],
        'EXACT_COMPLETE_CONSTRUCTION_SOURCE_TABLE')
    for group in (tests['source_pins'], closing['source_pins'], checkpoint['source_pins']):
        for pin in group:
            a.exact(reader.pin(pin['path']), pin, 'EXACT_CURRENT_QUALIFIED_PROGRAM')
            if pin['path'] in current:
                a.exact(current[pin['path']], pin, 'SAME_CODE_IN_ACTUAL_CONSTRUCTION')
    for path in (SELF, TEST, PRIOR['path'], POST['path'], WORKER['path'], LAUNCH['path'], CHECKPOINT['path']):
        require(path in current, 'EXPLICIT_TESTED_DRIVER_AND_ALL_CONNECTION_DEPENDENCIES')
        a.exact(reader.pin(path), current[path], 'CURRENT_DRIVER_CONSTRUCTION_SOURCE')
    return dict(reader.snapshots[QUALIFICATION])


def oracle_inputs(reader, context, a):
    """Same original inputs as flat_current_queue_acceptance.prepare, no replay."""
    row = reader.json(CANONICAL)
    listing = a.read_exact(reader, a.scope.LIST_PIN)
    body = a.read_exact(reader, a.BODY_PIN)
    fresh = a.packed.unpack(a.read_exact(reader, a.FRESH_PIN), reader.checkpoint)
    assembled = context.result.assembled
    ctx = assembled.checker.environment['context'](assembled.built.window.M.base.CONFIG)
    require(ctx.INDEX == 165 and ctx.BEFORE == 158 and ctx.CASE == context.connected.core['step']['case'],
        'ORIGINAL_CURRENT_ORACLE_CONTEXT')
    return row, listing, body, fresh, ctx


def execute_chain(context, route, relay, epochs, Reader, process_policy, a, progress):
    """One original Native call, real whole boundaries, then unchanged oracle."""
    batch = context.result.assembled.batch
    epochs.advance('opening_and_metadata')
    progress('RUNNING_FRESH_WHOLE_OPENING')
    opening = Reader(a.c.ROOT, route.checkpoint)
    batch.begin(opening)
    epochs.check(force=True)
    epochs.close()
    relay.arm()
    process_policy.arm(route.context)
    progress('RUNNING_ORIGINAL_NATIVE010_PRODUCT_ONCE')
    try:
        code = context.result.assembled.parent.run_owned(1)
    finally:
        relay.finish_native(route.context)
    require(type(code) is int and code == 0, 'ORIGINAL_NATIVE_FAILED_NO_AUTOMATIC_RETRY')
    require(process_policy.attempts == 1 and not process_policy.denied, 'ONE_ACTUAL_PRODUCT_ENTRY')
    route.start_closing()
    progress('RUNNING_FRESH_WHOLE_CLOSING')
    closing = Reader(a.c.ROOT, route.checkpoint)
    summary = route.finish_whole(closing)
    progress('RUNNING_ORIGINAL_FULL_ORACLE')
    oracle_reader = Reader(a.c.ROOT, route.checkpoint)
    loaded = []
    def inputs(actual):
        require(not loaded, 'ONE_ORIGINAL_ORACLE_INPUT_LOAD')
        values = oracle_inputs(actual, context, a)
        loaded.append(values)
        return values
    result = route.verify(oracle_reader, load_inputs=inputs)
    require(type(result) is tuple and len(result) == 2 and all(type(x) is dict for x in result),
        'ORIGINAL_FULL_ORACLE_RESULT_PAIR')
    return dict(whole_opening_inputs=len(opening.snapshots), whole_opening_bytes=opening.bytes_read,
        whole_closing_inputs=len(closing.snapshots), whole_closing_bytes=closing.bytes_read,
        original_batch_summary=summary, canonical_receipt_pin=dict(oracle_reader.snapshots[CANONICAL]),
        oracle_fresh_inputs=len(oracle_reader.snapshots), oracle_final_hashes=oracle_reader.final_fresh_hashes,
        original_Native_resource_samples=loaded[0][0]['samples'], original_oracle_result=result)


def observe_failure(root, factory, Reader):
    """Fresh original failure/cleanup evidence, never resume the Native owner."""
    guard = factory('whole_metadata_preflight')
    reader = None
    observed = dict(original_receipt_observed=False, original_cleanup_confirmed=False)
    try:
        guard.acquire()
        reader = Reader(root, guard.check)
        original = reader.json(CANONICAL)
        frame = original.get('source_frame')
        handles = {} if frame is None else frame['handles']
        released = (original.get('worker_created') is False and original.get('job_assigned') is False) \
            if frame is None else (frame['frame_state'] in ('CLOSED', 'COMMITTED')
                and handles['input_lock_handles_remaining'] == 0
                and handles['input_lock_handles_opened'] == handles['input_lock_handles_closed']
                and handles['active_reader_bindings'] == handles['active_byte_streams'] == 0
                and handles['handle_close_failed_attempts'] == 0)
        reader.finish()
        guard.check(force=True)
        observed.update(original_receipt_observed=True, receipt_pin=dict(reader.snapshots[CANONICAL]),
            original_cleanup_confirmed=original['cleanup_confirmed'] is True
                and original['owned_tree_empty'] is True and released,
            original_Frame_boundaries=0 if frame is None else len(frame['actual_byte_boundaries']),
            original_product_body_observed=original.get('product_body_observed') is True)
        for name in ('state', 'stop_reason'):
            value = original.get(name)
            if type(value) is str and re.fullmatch('[A-Z0-9_]{1,256}', value):
                observed['original_' + name] = value
    finally:
        guard.close()
        observed['observer_cleanup'] = guard.cleanup
    return observed


def close_all(actions):
    failed = False
    for action in actions:
        if action is not None:
            try:
                action()
            except (ValueError, OSError):
                failed = True
    return not failed


def main():
    product = mode(sys.argv[1:])
    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root / 'tools/p09'))
    sys.dont_write_bytecode = True
    process_policy = ProcessPolicy(root, product=product)
    sys.addaudithook(process_policy)
    prior = bootstrap(root)
    probe = prior.bootstrap(root)
    metadata = probe.bootstrap(root)
    prep, parent, loader, entry, profile = metadata.bootstrap(root)
    import accept_case112_current_epoch as a, conservative_maintenance as c, owned_source_read_pressure as byte_policy
    policy, witness, Reader, chunk = metadata.approved_admission(root, prep, loader, entry, a, c)
    guards, _ = loader.load(root, list(entry.BOOTSTRAP[1:]), {})
    guards.prepared_run_closure_v1.configure_host_policy(c)
    post_guards = []
    publication_guards = []
    def factory(role):
        return guards.owned_cpu_baseline_v1.guard_type(policy.guard_type(
            guards.distinct_final_sample_guard_v1.guard_type(a.Guard), role=role))()
    def closing_factory(role):
        guard = factory(role)
        post_guards.append(guard)
        return guard
    epochs = metadata.ReadOnlyEpochs(factory)
    q = context = route = relay = restore = publisher = checkpoint_owner = None
    started = time.monotonic()
    consumed = False
    row = dict(state='FAILED_NATIVE010_PRODUCT_DRIVER', mode='run-product' if product else 'connect-only',
        GO_authorized=product, accepted_count_delta=0, official_accepted_count=158, next_case=165,
        Native008_or_Native009_reexecuted=False, queue_acceptance_authorized=False)
    def progress(stage):
        print(json.dumps(dict(stage=stage, elapsed_seconds=time.monotonic()-started, product_mode=product)), flush=True)
    try:
        require(all(prior.direct_absence(root, p) for p in (CANONICAL, INTENT, RESULT)),
            'NO_EXISTING_NATIVE010_RESULT_OR_CONSUMED_ATTEMPT')
        epochs.advance('construction')
        libraries, _ = loader.load(root, [*prior.SOURCES, POST, LAUNCH, CHECKPOINT], {})
        relay = libraries.batch_native_checkpoint.Handoff(epochs, metadata.idle)
        original_checkpoint = prior.source_checkpoint(relay)
        # Bootstrap only this frozen profile definition before the profiler or
        # any lazy reader exists. The original source is still a fresh input.
        seed = Reader(root, original_checkpoint)
        source = libraries.preparation_checkpoint_owner.SOURCE
        actual_source, profile_raw = seed._read(source['path'], parse=True)
        seed._bind(actual_source['path'], actual_source)
        a.exact(actual_source, source, 'WHOLE_ORIGINAL_CONSTRUCTION_PROFILE_SOURCE')
        seed.finish()
        checkpoint_owner = libraries.preparation_checkpoint_owner.Checkpoint(relay, original_checkpoint, bytes(profile_raw))
        route = libraries.batch_post_native.Closing(relay, checkpoint_owner.checkpoint, closing_factory, a.exact)
        q = Reader(root, route.checkpoint)
        checkpoint_owner.bind_reader(q)
        entry, parent = libraries.batch_product_launch.parent_apis(entry, parent, probe=False)
        for pin in (PRIOR, POST, WORKER, LAUNCH, CHECKPOINT, source, prior.PARENT, probe.METADATA, *prior.SOURCES):
            a.exact(q.pin(pin['path']), pin, 'EXACT_CURRENT_DISPATCHER_DEPENDENCY')
        q.pin(SELF)
        q.pin(TEST)
        names = (SELF, PRIOR['path'], POST['path'], WORKER['path'], LAUNCH['path'], CHECKPOINT['path'],
            prior.PARENT['path'], *(p['path'] for p in prior.SOURCES))
        extras = {name: dict(q.pin(name)) for name in names}
        if product:
            extras[QUALIFICATION] = admit_qualification(q, a)
        source, raw = q._read(prior.ORIGINAL_ENGINE['path'], parse=True)
        q._bind(source['path'], source)
        a.exact(source, prior.ORIGINAL_ENGINE, 'EXACT_ORIGINAL_ENGINE_SOURCE')
        selected = prior.require_current_dependencies(probe.extended_parent(parent, extras),
            prior.engine_dependency_pins(bytes(raw)))
        context = metadata.construct(root, q, route.construction_api(), a, selected, entry, profile,
            loader, prep, policy, witness, byte_policy)
        actual = metadata.readiness_context(context.result)
        route.bind_context(actual)
        row['parent_entry_binding'] = prior.bind_parent_entry(context)
        restore = prior.connect_callback(context, relay, actual)
        route._checker()
        a.exact(context.result.proof['worker_entry_pin'], WORKER, 'ACTUAL_SEPARATE_PRODUCT_ENTRY_PIN')
        require(context.result.assembled.built.names.root_path(NS(index=165)) == CANONICAL,
            'ORIGINAL_NATIVE010_CANONICAL_RESULT_NOT_DIAGNOSTIC_NAMESPACE')
        known = context.connected.known
        inspections, _ = context.connected.loader.load(root,
            [known['tools/p09/native009_full72_construction_v1.py'],
             known['tools/p09/successor_preparation_workspace_v1.py']], {})
        publisher = inspections.successor_preparation_workspace_v1
        helpers = inspections.native009_full72_construction_v1.helper_inventory(root, context.result.assembled.parent)
        require(helpers['Native_count'] <= 64, 'ORIGINAL_NATIVE_HELPER64')
        for name in helpers['original_Native_helper_union']:
            require(name in known and name in context.result.assembled.batch.current, 'ALL_HELPERS_DECLARED_CURRENT')
            a.exact(q.pin(name), known[name], 'ACTUAL_CURRENT_HELPER_PIN')
        q.finish()
        epochs.check(force=True)
        metadata.idle(context.result)
        require(q.final_fresh_hashes == len(q.snapshots), 'COMPLETE_CURRENT_CONSTRUCTION_CLOSING')
        row.update(construction_source_pins=list(q.snapshots.values()), construction_fresh_inputs=len(q.snapshots),
            construction_final_hashes=q.final_fresh_hashes, scope_projection=context.projection,
            helper_inventory=helpers, original_checker_connection=context.result.proof['additional_independent_accounting_oracle'],
            with_preparation15_seconds=context.result.proof['with_preparation15_seconds'])
        if not product:
            row['state'] = 'PASS_NATIVE010_PRODUCT_DRIVER_CONNECTION_NOT_EXECUTION'
        else:
            row['intent_pin'] = publisher.publish(root, INTENT, dict(
                schema_version='hwpx-agent.p09-native010-explicit-product-intent/v1', task=TASK,
                qualification_pin=extras[QUALIFICATION], programs=[extras[n] for n in names],
                original_result=CANONICAL, one_product_attempt_no_retry=True, queue_acceptance_authorized=False), a)
            consumed = True
            proof = execute_chain(context, route, relay, epochs, Reader, process_policy, a, progress)
            samples = proof.pop('original_Native_resource_samples')
            oracle_result = proof.pop('original_oracle_result')
            publication = factory('whole_metadata_preflight')
            publication_guards.append(publication)
            try:
                publication.acquire()
                row['original_oracle_result_lossless'] = a.packed.pack(oracle_result, publication.check)
                publication.check(force=True)
            finally:
                publication.close()
            require(publication.cleanup is True, 'ORACLE_RESULT_PUBLICATION_OWNER_CLEANUP')
            row.update(actual_product_chain=proof,
                original_Native_resource_tail=metadata.epoch_evidence(dict(stage='original_native_terminal',
                    samples=samples, cleanup_confirmed=True)),
                state='PASS_NATIVE010_PRODUCT_WHOLE_CLOSING_AND_ORACLE_NOT_QUEUE_OR_GATE')
    except (ValueError, OSError, KeyError, TypeError, AttributeError, NameError, ImportError, MemoryError) as error:
        import traceback
        row['error_type'] = type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch('[A-Z0-9_]{1,160}', error.args[0]):
            row['error_code'] = error.args[0]
        row['error_frames'] = [dict(file=Path(f.filename).name, function=f.name, line=f.lineno)
            for f in traceback.extract_tb(error.__traceback__)[-6:]]
    finally:
        if not close_all((restore, None if route is None else route.close,
                None if context is None else context.result.assembled.batch.shared.restore, epochs.close)):
            row['state'] = 'CLEANUP_FAILED_NATIVE010_PRODUCT_DRIVER'
        cleanup = bool(epochs.records) and all(r['cleanup_confirmed'] is True for r in epochs.records)
        cleanup = cleanup and all(g.cleanup is True for g in post_guards)
        cleanup = cleanup and all(g.cleanup is True for g in publication_guards)
        native_called = False
        if context is not None:
            actual = metadata.readiness_context(context.result)
            cleanup = cleanup and not actual.active
            row['actual_parent_context'] = actual.evidence()
            native_called = actual.attempts > 0
            if native_called and not row['state'].startswith('PASS_') and not actual.active:
                try:
                    row['original_failure_observation'] = observe_failure(root, factory, Reader)
                    observed = row['original_failure_observation']
                    cleanup = cleanup and observed['original_cleanup_confirmed'] and observed['observer_cleanup'] is True
                except (ValueError, OSError, KeyError, TypeError, AttributeError):
                    row['original_failure_cleanup_unverified'] = True
                    cleanup = False
        if not cleanup:
            row['state'] = 'CLEANUP_FAILED_NATIVE010_PRODUCT_DRIVER'
        row.update(cleanup_confirmed=cleanup, elapsed_seconds=time.monotonic()-started,
            preparation_epochs=[metadata.epoch_evidence(r) for r in epochs.records],
            post_Native_owner_sample_counts=[len(g.samples) for g in post_guards],
            original_parent_execution_attempted=native_called, intent_consumed=consumed,
            process_creation_attempts=process_policy.attempts, denied_process_creation_events=process_policy.denied,
            post_Native_connection=None if route is None else route.evidence(),
            preparation_checkpoint_owner=None if checkpoint_owner is None else checkpoint_owner.evidence(),
            actual_Native_policy_changed=False, official_queue_advanced=False)
        if consumed and publisher is not None:
            try:
                pin = publisher.publish(root, RESULT, row, a)
                row['driver_result_pin'] = pin
            except (ValueError, OSError):
                row['driver_result_publication_failed'] = True
                row['state'] = 'FAILED_NATIVE010_DRIVER_RESULT_PUBLICATION'
        print(json.dumps(row, ensure_ascii=True), flush=True)
    return 0 if row['state'].startswith('PASS_') and cleanup else 2


if __name__ == '__main__':
    raise SystemExit(main())
