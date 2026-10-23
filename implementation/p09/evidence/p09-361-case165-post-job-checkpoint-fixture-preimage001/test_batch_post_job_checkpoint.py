"""Execute the frozen original writer with synthetic Job/IO, never a product.

The complete original write/post_guard/sampled bytecode is retained. A small
synthetic Frame commit invokes the real Handoff check at the same call boundary
as Batch.commit. This is NOT actual Native/Frame/product qualification.
"""
import threading
from types import CodeType, FunctionType, SimpleNamespace as NS
import unittest

import batch_native_checkpoint as original
import batch_post_job_checkpoint as module
import metadata_pressure_failfast as pressure

RAW = None  # Inject fresh verified source through the owned test reader.


def function(code, env, values):
    def cell(value):
        return (lambda: value).__closure__[0]
    return FunctionType(code, env, closure=tuple(cell(values[n]) for n in code.co_freevars))


def require(ok, code):
    if not ok:
        raise ValueError(code)


def fixture(*, fixed, fault=None):
    require(type(RAW) is bytes, 'TEST_FRESH_ENGINE_SOURCE_REQUIRED')
    writer_code, guard_code, sample_code = module.codes(RAW)
    run_code = next(v for v in compile(RAW, module.SOURCE['path'], 'exec').co_consts
        if type(v) is CodeType and v.co_name == 'run_owned')
    input_code = next(v for v in run_code.co_consts if type(v) is CodeType and v.co_name == 'input_pins')
    old_code = next(v for v in input_code.co_consts if type(v) is CodeType and v.co_name == 'guarded')
    f = NS(now=1.0, closed_job=False, old_calls=0, sampled=0, decisions=0, commits=0,
        before_check=None, checks_per_commit=1)
    f.owner = NS(lock=threading.Lock(), samples=[dict(system_cpu_percent=20)])
    f.state = NS(attempts=0, frames=[])
    f.batch = NS(phase='READY', shared=NS(metadata=None, frame=None),
        parent_connection=NS(state=f.state), metadata_connection=NS(readers=[], budgets=[]))
    f.result = NS(assembled=NS(batch=f.batch))
    prep = NS(closed=False, broken=False, guard=object(), records=[], check=lambda: None, bind=lambda r: None)
    cls = module.handoff_type(original.Handoff, RAW) if fixed else original.Handoff
    f.relay = cls(prep, lambda r: None, identity=lambda: (1, 2))
    f.relay.bind(f.result)
    prep.closed = True
    prep.guard = None
    prep.records = [dict(stage=s, cleanup_confirmed=True) for s in ('construction', 'opening_and_metadata')]
    f.relay.arm()
    f.context = NS(parent=f.state, active=True, attempts=1, jobs=0, restorations=0)
    f.state.attempts = 1
    def old_job_guard():
        f.old_calls += 1
        if f.closed_job:
            raise ValueError('TEST_CLOSED_JOB_ACCOUNTING')
    def snapshot(windows, raw_sample, last):
        f.sampled += 1
        return dict(system_cpu_percent=20, parent_private_percent=0), (1, 2)
    def decision(row, hot):
        f.decisions += 1
        return hot, fault
    pin = dict(path='synthetic', bytes=1, sha256='0' * 64)
    f.env = dict(require=require, time=NS(monotonic=lambda: f.now),
        parent_snapshot=snapshot, c=NS(decision=decision, POLICY={'job_memory_stop_percent': 95}),
        capture_diagnostics=lambda cap: dict(complete_streams=True), PASS='TEST_NATIVE_PASS',
        FRESH_PIN=pin, FAILED_FIRST_PIN=pin, FAILED_STOP_PIN=pin,
        scope=NS(LIST_PIN=pin, EXE_PIN=pin, CASE112='synthetic'), arguments=lambda: [])
    hard = function(old_code, f.env, dict(checkpoint=old_job_guard, global_deadline=720.0))
    f.owner.checkpoint_io = hard
    f.reader = NS(checkpoint=hard)
    f.pressure = pressure.Checkpoint(f.reader, f.owner)
    f.batch.metadata_connection.readers.append(f.reader)
    f.batch.metadata_connection.budgets.append(object())
    f.relay.admit_metadata(f.reader, f.context)
    f.pressure.restore()
    f.frame = NS(held=NS(started=0.0, acquired=True, closed=False, mark=lambda name: None))
    def commit(row):
        f.commits += 1
        if f.before_check is not None:
            f.before_check()
        for _ in range(f.checks_per_commit):
            f.relay.check()
        return dict(frame_state='COMMITTED')
    f.frame.commit = commit
    f.frame.close = lambda: True
    f.frame.summary = lambda: dict(frame_state='CLOSED')
    f.state.frames.append(f.frame)
    f.context.jobs = 1
    f.window = object()
    f.samples = []
    sampler = function(sample_code, f.env, dict(frame=f.frame, global_deadline=720.0,
        last_parent=None, owner=f.owner, raw_sample=lambda: None, windows_instance=f.window))
    values = dict(accepted=False, budget={}, captures=[NS(terminal={})], context=NS(phase='running'),
        frame=f.frame, global_deadline=720.0, guards=[], inventory=[], metadata={}, owner=f.owner,
        post_samples=f.samples, post_time=0.0, raw_dump=lambda row, file, **kw: dict(row),
        sampled=sampler, windows_instance=f.window, worker_imports=[])
    f.write = function(writer_code, f.env, values)
    f.closed_job = True
    f.row = dict(state='PASS_SCOPED_NOT_GATE', cleanup_confirmed=True, owned_tree_empty=True,
        owned_limits_readback={'verified': True}, writer_authorized=True, samples=[{'system_cpu_percent': 20}])
    return f


class Tests(unittest.TestCase):
    def test_original_writer_reproduces_closed_job_checkpoint_failure_without_product(self):
        f = fixture(fixed=False)
        before = f.old_calls
        result = f.write(f.row, None)
        self.assertEqual(result['state'], 'STOPPED_NOT_ACCEPTED')
        self.assertEqual(result['closing_error_code'], 'TEST_CLOSED_JOB_ACCOUNTING')
        self.assertEqual(f.old_calls, before + 1)
        self.assertEqual(f.sampled, 0)
        self.assertTrue(f.relay.broken)

    def test_original_writer_and_sampler_complete_without_querying_closed_job(self):
        f = fixture(fixed=True)
        before = f.old_calls
        result = f.write(f.row, None)
        self.assertEqual(result['state'], 'TEST_NATIVE_PASS')
        self.assertIsNone(result['closing_error_code'])
        self.assertEqual(f.old_calls, before)
        self.assertEqual((f.sampled, f.decisions, len(f.samples)), (1, 1, 1))
        self.assertEqual((f.relay.post_job_bindings, f.relay.post_job_checks), (1, 1))
        self.assertFalse(f.relay.broken)

    def test_repeated_checks_keep_original_half_second_sampling_cadence(self):
        f = fixture(fixed=True)
        f.checks_per_commit = 4
        result = f.write(f.row, None)
        self.assertEqual(result['state'], 'TEST_NATIVE_PASS')
        self.assertEqual((f.sampled, f.decisions), (1, 1))
        self.assertEqual((f.relay.post_job_bindings, f.relay.post_job_checks), (1, 4))

    def test_original_resource_stop_is_preserved_not_promoted_to_success(self):
        f = fixture(fixed=True, fault='TEST_ORIGINAL_RESOURCE_STOP')
        result = f.write(f.row, None)
        self.assertEqual(result['state'], 'STOPPED_NOT_ACCEPTED')
        self.assertEqual(result['closing_error_code'], 'TEST_ORIGINAL_RESOURCE_STOP')
        self.assertEqual((f.sampled, f.decisions), (1, 1))
        self.assertTrue(f.relay.broken)

    def test_original_lock_deadline_is_preserved(self):
        f = fixture(fixed=True)
        f.now = 650.0
        # Preserve the original global720 and lock600 relationship.
        result = f.write(f.row, None)
        self.assertEqual(result['state'], 'STOPPED_NOT_ACCEPTED')
        self.assertEqual(result['closing_error_code'], 'NATIVE_LOCK_DEADLINE')
        self.assertEqual(f.sampled, 0)

    def test_forged_callback_with_same_function_name_is_not_used(self):
        f = fixture(fixed=True)
        calls = []
        def post_guard():
            calls.append(True)
        f.before_check = lambda: setattr(f.owner, 'checkpoint_io', post_guard)
        result = f.write(f.row, None)
        self.assertEqual(result['state'], 'STOPPED_NOT_ACCEPTED')
        self.assertEqual(calls, [])
        self.assertEqual(f.relay.post_job_checks, 0)

    def test_changed_context_or_frame_is_rejected_before_post_job_sample(self):
        for kind in ('inactive', 'restored', 'jobs', 'frame'):
            with self.subTest(kind=kind):
                f = fixture(fixed=True)
                def change():
                    if kind == 'inactive': f.context.active = False
                    if kind == 'restored': f.context.restorations = 1
                    if kind == 'jobs': f.context.jobs = 2
                    if kind == 'frame': f.state.frames[0] = object()
                f.before_check = change
                result = f.write(f.row, None)
                self.assertEqual(result['state'], 'STOPPED_NOT_ACCEPTED')
                self.assertEqual(f.sampled, 0)
                self.assertTrue(f.relay.broken)

    def test_reader_or_pressure_replacement_is_rejected_before_sample(self):
        for kind in ('reader', 'latched', 'active', 'restoration'):
            with self.subTest(kind=kind):
                f = fixture(fixed=True)
                def change():
                    if kind == 'reader': f.reader.checkpoint = lambda: None
                    if kind == 'latched': f.pressure.latched = True
                    if kind == 'active': f.pressure.active = True
                    if kind == 'restoration': f.pressure.restored = False
                f.before_check = change
                result = f.write(f.row, None)
                self.assertEqual(result['state'], 'STOPPED_NOT_ACCEPTED')
                self.assertEqual(f.sampled, 0)

    def test_callback_cannot_be_reused_outside_original_writer(self):
        f = fixture(fixed=True)
        result = f.write(f.row, None)
        self.assertEqual(result['state'], 'TEST_NATIVE_PASS')
        with self.assertRaisesRegex(ValueError, 'EXACT_ACTIVE_ORIGINAL_WRITER'):
            f.relay.check()
        self.assertTrue(f.relay.broken)

    def test_engine_source_tamper_rejected_before_class_construction(self):
        with self.assertRaisesRegex(ValueError, 'EXACT_WHOLE_ORIGINAL_ENGINE'):
            module.handoff_type(original.Handoff, RAW + b'\n')

    def test_published_original_handoff_class_is_not_mutated(self):
        before = dict(vars(original.Handoff))
        f = fixture(fixed=True)
        f.write(f.row, None)
        self.assertEqual(vars(original.Handoff), before)
        self.assertFalse(f.relay.evidence()['actual_post_Job_runtime_qualified'])
