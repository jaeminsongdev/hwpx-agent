"""Fixed opt-in metadata failfast connection; no qualified file is edited.

Immutable per-step connection DATA authorizes exact120/run002 after reviewed
prebody failure; later exact steps use run001, not automatic retries. Original
entry/engine code, Native locks/two whole byte passes/GO/Job/sole sampler/guards
and cleanup remain. No skipped source, deadline extension or queue write.
"""
import argparse
import io
import json
from pathlib import Path
import re
import sys
import threading
import time
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

import flat_current_queue_runtime as base
import metadata_pressure_failfast as pressure

c = base.c
a = base.accepted115.a
SELF = 'tools/p09/flat_current_queue_metadata_runtime.py'
TEST = 'tools/p09/tests/test_flat_current_queue_metadata_connection.py'
ACCEPTOR = 'tools/p09/flat_current_queue_metadata_acceptance.py'
FILES = (SELF, TEST, ACCEPTOR, 'tools/p09/metadata_pressure_failfast.py')
FAILED120 = dict(path='implementation/p09/evidence/p09-361-case120-current-runtime-run001.v1.json',
                 bytes=46951, sha256='ce95eeb3db66595d59467e72c3ac43aba162e7b6931cf03886961918df9629b4')
QUALIFIED = dict(path='implementation/p09/evidence/p09-361-case120-stop-and-metadata-failfast-qualification-r266.v1.json',
                 bytes=8231, sha256='f8cea5f0c0441c8152349e62efe5e8657be53c4cc53d568651fcdb43683b248a')


def require(ok, code):
    if not ok:
        raise ValueError('METADATA_CONNECTION_' + code)


def data_path(index):
    require(type(index) is int and 120 <= index <= 249, 'INDEX')
    return f'implementation/p09/evidence/p09-361-case{index}-metadata-connection-data001.v1.json'


def validate_data(row, step):
    require(type(row) is dict and set(row) == {
        'schema_version', 'index', 'before', 'run', 'base_step_pin',
        'failed_runtime_pin', 'optimization_qualification_pin', 'connection_code_pins'}, 'DATA_SHAPE')
    run = 2 if step.index == 120 else 1
    a.fields(row, dict(schema_version='hwpx-agent.p09-flat-metadata-connection/v1',
                       index=step.index, before=step.before, run=run), 'DATA_CURSOR')
    a.exact(row['base_step_pin'], step.pin, 'EXACT_BASE_STEP')
    a.exact(row['optimization_qualification_pin'], QUALIFIED, 'EXACT_QUALIFICATION')
    a.exact(row['failed_runtime_pin'], FAILED120 if run == 2 else None, 'ONLY_REVIEWED_PREBODY_RETRY')
    pins = base.scope.pins(row['connection_code_pins'], len(FILES))
    require(set(pins) == set(FILES), 'EXACT_CONNECTION_FILES')
    return row


def connection_data(q):
    step = base.CONFIG
    require(step is not None, 'BASE_CONFIG_REQUIRED')
    text = q.text(data_path(step.index))
    require(0 < len(text.encode('utf-8')) <= 16384, 'BOUNDED_DATA')
    return validate_data(json.loads(text, object_pairs_hook=base.unique), step)


def review_failure(row):
    a.fields(row, dict(state='DEFERRED_NOT_STARTED', selected_test_index=120,
                       stop_reason='STOP_SYSTEM_COMMIT_PRESSURE', worker_created=False,
                       product_body_observed=False, source_frame=None,
                       Native_source_frame_qualified=False, cleanup_confirmed=True,
                       owned_tree_empty=True, accepted_count_delta=0,
                       full249_current_qualified=False, signed16_current_qualified=False,
                       P09_gate='OPEN', A12_gate='OPEN', A13_gate='OPEN'), 'PREBODY_FAILURE_ONLY')
    a.exact(row['passed_test_names'], [], 'NO_REPLAYED_BODY')
    return True


def reviewed_inputs(q, run):
    row = connection_data(q)
    a.exact(run, row['run'], 'ONE_REVIEWED_ATTEMPT')
    qualification = a.read_exact(q, QUALIFIED)
    a.fields(qualification, dict(
        state='PASS_FAILED120_REVIEW_AND_SYNTHETIC12_NOT_RUNTIME_CONNECTION_OR_GATE',
        synthetic_contracts_passed=12, cleanup_confirmed=True,
        accepted_count_after=113, accepted_count_delta=0,
        runtime_connection_qualified=False, retry_run002_executed=False), 'OPTIN_QUALIFICATION_NOT_PRODUCT')
    for pin in qualification['new_code_pins'] + qualification['frozen_core_pins']:
        a.exact(q.pin(pin['path']), pin, 'PRESERVED_QUALIFIED_CODE')
    for pin in row['connection_code_pins']:
        a.exact(q.pin(pin['path']), pin, 'CONNECTION_CODE_BEFORE_NATIVE')
    if row['failed_runtime_pin'] is not None:
        review_failure(a.read_exact(q, row['failed_runtime_pin']))
    return row


def binding_attempt(q, run):
    reviewed_inputs(q, run)
    # All prior full oracle/source/fresh/bootstrap pins still join this frame.
    required, rust = base.binding(q)
    return base.scope.extend(required, q.snapshots), rust


class MetadataCheckpoint(pressure.Checkpoint):
    # Preserve the original summary's policy fields, separately report actual
    # failfast mode. These cooling parameters are retained, not executed here.
    COOL_SAMPLES = 2
    MAX_WINDOWS = 8
    pause_windows = 0

    @property
    def warning_entries(self):
        return self.warning_stops


def template():
    engine, proof = base.template()
    environment = engine.run_owned.__globals__
    require(environment['SELF'] == base.SELF and environment['TEST'] == base.TEST,
            'EXACT_FROZEN_ENGINE_ENVIRONMENT')
    original_build = environment['build']
    modified_pressure = NS(**{**vars(original_build.pressure),
                             'PreSaturationReadCheckpoint': MetadataCheckpoint})
    original_summary = original_build.pressure_summary

    def summary(guard):
        require(type(guard) is MetadataCheckpoint, 'EXACT_METADATA_BINDING')
        return dict(original_summary(guard), metadata_failfast_connection=guard.summary())

    environment.update(SELF=SELF, TEST=TEST,
                       build=NS(**{**vars(original_build), 'pressure': modified_pressure,
                                   'pressure_summary': summary}))
    # Only the parent constructs metadata readers. Worker still uses unchanged
    # stored EXE/arguments, original GO/Job and one-thread environment.
    engine.worker.__globals__.update(SELF=SELF, TEST=TEST)
    proof.update(original_engine_bytecode_unchanged=True,
                 original_build_module_not_mutated=True,
                 connection_is_metadata_reader_factory_only=True,
                 new_sampler_or_guard_relaxation=False)
    return engine, proof


def context(step):
    return NS(**{**vars(base.context(step)), 'SELF': SELF, 'TEST': TEST})


def worker(task):
    import flat_current_queue_metadata_acceptance
    require(base.run_for(task) == (2 if base.CONFIG.index == 120 else 1), 'EXACT_WORKER_ATTEMPT')
    engine, _ = template()
    return engine.worker(task)


def run_owned(run):
    import flat_current_queue_metadata_acceptance
    require(type(run) is int and run == (2 if base.CONFIG.index == 120 else 1), 'EXACT_ATTEMPT')
    api, _ = base.entry()
    api.run_owned.__globals__.update(template=template, binding_attempt=binding_attempt)
    # Reuse qualified sole-observer wrapper unchanged; no extra diagnostic query.
    return api.run_owned(run)


def preflight():
    import flat_current_queue_metadata_acceptance
    destination = c.ROOT / f'implementation/p09/evidence/p09-361-case{base.CONFIG.index}-metadata-preflight001.v1.json'
    require(not destination.exists(), 'FRESH_PREFLIGHT')
    guard = None
    q = None
    binding = None
    proposed = None
    out = dict(state='FAILED_NOT_ACCEPTED', index=base.CONFIG.index,
               product_worker_or_Native_frame_executed=False, accepted_count_delta=0,
               runtime_connection_qualified=False, PC_freeze_resolved=False)
    started = time.monotonic()
    try:
        guard = a.Guard()
        guard.acquire()
        q = a.AcceptanceReader(c.ROOT, guard.check)
        owner = NS(lock=threading.Lock(), samples=guard.samples, checkpoint_io=guard.check)
        binding = MetadataCheckpoint(q, owner)
        sys.path.insert(0, str(c.ROOT / 'tools/p09/tests'))
        import test_flat_current_queue_metadata_connection as tests
        with patch('subprocess.Popen', side_effect=AssertionError('NO_CHILD')), \
             patch('subprocess.run', side_effect=AssertionError('NO_CHILD')):
            result = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(
                unittest.defaultTestLoader.loadTestsFromModule(tests))
        require(result.wasSuccessful() and result.testsRun == 10 and not result.skipped, 'CONTRACT10')
        out['synthetic_connection_contracts_passed'] = result.testsRun
        engine, proof = template()
        out['template_proof'] = proof
        row = connection_data(q)
        required, rust = binding_attempt(q, row['run'])
        environment = engine.run_owned.__globals__
        for pin in environment['FAILED_PREIMAGES']:
            directory, name, size, digest = pin
            path = 'implementation/p09/evidence/' + directory + '/' + name
            a.exact(q.pin(path), dict(path=path, bytes=size, sha256=digest), 'ORIGINAL_FAILURE_ARCHIVE')
        names = {SELF, TEST, base.SELF, base.TEST, base.native.SELF, base.native.TEST,
                 base.scope.SELF, base.scope.TEST}
        for module in tuple(sys.modules.values()):
            name = getattr(module, '__file__', None)
            if name:
                path = Path(name).absolute()
                if path.is_relative_to(c.ROOT / 'tools/p09') and path.suffix == '.py':
                    names.add(path.relative_to(c.ROOT).as_posix())
        require(len(names) <= 64, 'ORIGINAL_HELPER_BOUND')
        for name in sorted(names):
            q.pin(name)
        for pin in base.native.SOURCES:
            a.exact(q.pin(pin['path']), pin, 'NATIVE_DEFINITION_PIN')
        required = base.scope.extend(required, q.snapshots)
        build = environment['build']
        pacer = build.QueryPacer(q.checkpoint)
        a.exact(build.base.inputs.rust_inputs(c.ROOT, pacer.reserve), rust, 'WHOLE_RUST787')
        model = base.stable.runtime_budget(required, pacer.requests)
        require(model['predicted_runtime_combined_seconds'] < 600, 'ORIGINAL600')
        q.finish()
        time.sleep(.5)
        guard.check(force=True)
        out.update(inputs=len(required), directories=len({p.as_posix() for name in required
                   for p in Path(name).parents}), bytes=sum(p['bytes'] for p in required.values()),
                   current_Rust=len(rust), imports=len(names), complete_runtime_budget=model,
                   connection_data_pin=q.snapshots[data_path(base.CONFIG.index)])
        proposed = 'PASS_REVIEWED_METADATA_CONNECTION_PREFLIGHT_NOT_NATIVE_OR_PRODUCT_OR_ACCEPTANCE'
    except (ValueError, OSError, KeyError, TypeError, AttributeError) as exc:
        code = str(exc) if isinstance(exc, ValueError) else 'REDACTED_PREFLIGHT_FAILURE'
        out['error_code'] = code if re.fullmatch('[A-Z0-9_]{1,256}', code) else 'REDACTED_PREFLIGHT_FAILURE'
    finally:
        if binding is not None:
            binding.restore()
            out['metadata_connection'] = binding.summary()
        if guard is not None:
            guard.close()
        out['cleanup_confirmed'] = bool(guard is not None and guard.cleanup)
        if proposed and out['cleanup_confirmed']:
            out['state'] = proposed
        samples = guard.samples if guard is not None else []
        out.update(elapsed_seconds=time.monotonic()-started, resource_samples=samples,
                   host_CPU_max_percent=max((x['system_cpu_percent'] for x in samples), default=None),
                   available_RAM_min_percent=min((x['available_ram_percent'] for x in samples), default=None),
                   fresh_inputs=len(q.snapshots) if q else 0, fresh_read_passes=q.read_passes if q else 0,
                   fresh_bytes_read=q.bytes_read if q else 0, final_fresh_hashes=q.final_fresh_hashes if q else 0)
        with destination.open('x', encoding='utf-8') as stream:
            json.dump(out, stream, indent=2)
        print(json.dumps({k: out.get(k) for k in ('state', 'error_code', 'inputs', 'bytes',
            'imports', 'host_CPU_max_percent', 'available_RAM_min_percent', 'cleanup_confirmed')}))
    return 0 if proposed and out['cleanup_confirmed'] else 2


if __name__ == '__main__':
    try:
        if len(sys.argv) == 4 and sys.argv[1:3] == ['--owned-worker', '--task']:
            base.configure(base.task_index(sys.argv[3]))
            raise SystemExit(worker(sys.argv[3]))
        parser = argparse.ArgumentParser()
        parser.add_argument('--case', type=int, required=True)
        parser.add_argument('--run', type=int)
        parser.add_argument('--preflight', action='store_true')
        args = parser.parse_args()
        base.configure(args.case)
        require(args.preflight != (args.run is not None), 'ONE_EXECUTION_MODE')
        raise SystemExit(preflight() if args.preflight else run_owned(args.run))
    except (ValueError, OSError, KeyError, TypeError, AttributeError) as exc:
        code = str(exc) if isinstance(exc, ValueError) else 'REDACTED_METADATA_CONNECTION_FAILURE'
        print(json.dumps(dict(state='FAILED_NOT_ACCEPTED', error_code=code
              if re.fullmatch('[A-Z0-9_]{1,256}', code) else 'REDACTED_METADATA_CONNECTION_FAILURE')))
        raise SystemExit(2) from None
