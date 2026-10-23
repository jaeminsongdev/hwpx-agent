"""Original Batch/Frame bodies with synthetic IO/Job/guard dependencies.

These are connection contracts, never physical Native or product evidence.
"""
import copy
from types import FunctionType, SimpleNamespace as NS
import unittest

import accept_case112_current_epoch as a
import batch_post_native as module
import batch_verification as policy
from tools.p09.tests.test_batch_verification import Reader, Held, H, N


class Guard:
    def __init__(self):
        self.acquires = self.closes = self.checks = 0
        self.cleanup = None
        self.error = None
        self.close_ok = True

    def acquire(self):
        self.acquires += 1

    def check(self, *args, **kwargs):
        self.checks += 1
        if self.error is not None:
            raise self.error

    def close(self):
        self.closes += 1
        self.cleanup = self.close_ok


class OracleReader(Reader):
    def __init__(self, rows, checkpoint):
        super().__init__(rows)
        self.checkpoint = checkpoint
        self.finishes = 0
        self.error = None

    def finish(self):
        self.checkpoint()
        self.finishes += 1
        if self.error is not None:
            raise self.error


def fixture():
    f = NS(calls=[], source_calls=[], ident=[(1, 2)], guards=[], oracle_error=None)
    relay = NS(phase='PREPARATION', broken=False, result=None,
        pressure=NS(restored=True, latched=False))
    def bind(result):
        relay.result = result
    relay.bind = bind
    def original(*args, **kwargs):
        f.source_calls.append((args, kwargs))
        if relay.phase == 'NATIVE_TERMINAL':
            raise ValueError('ORIGINAL_TERMINAL_READER_DENIED')
    def factory(role):
        assert role == 'whole_metadata_preflight'
        guard = Guard()
        f.guards.append(guard)
        return guard
    route = module.Closing(relay, original, factory, a.exact, identity=lambda: f.ident[0])
    b = policy.Batch({H['path']: H, N['path']: N}, {N['path']: N}, {H['path']: H},
        first_index=165, checkpoint=route.checkpoint)
    base = policy.phased.frames
    def never_run():
        raise AssertionError('no original fixture product body')
    body = FunctionType(never_run.__code__, dict(never_run.__globals__, native=NS(frames=base)))
    engine = NS(run_owned=body, worker=never_run)
    def connect(engine, binding):
        state = NS(original=engine.run_owned, original_worker=engine.worker, frames=[], attempts=0)
        class Projected(base.Frame):
            pass
        class Parent(Projected):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                state.frames.append(self)
        native = NS(frames=NS(Frame=Parent))
        def execute():
            state.attempts += 1
            return native.frames.Frame(base.Registry(), policy.plain(b.current),
                route.checkpoint, held=Held()).acquire()
        return NS(run_owned=execute, worker=engine.worker), state
    parent, state = b.connect_parent(engine, NS(parent=NS(connect_engine=connect), binding=NS(next_case=165)))
    f.answer = object()
    def validate(reader, row, listing, oldbody, fresh, ctx, flat):
        f.calls.append((reader, row, listing, oldbody, fresh, ctx, flat))
        b._closed_oracle_case(165)
        if f.oracle_error is not None:
            raise f.oracle_error
        return f.answer
    checker = NS(validate_candidate=validate)
    result = NS(assembled=NS(batch=b, checker=checker))
    context = NS(parent=state, active=False, attempts=0, jobs=0, restorations=0,
        bindings=[], frame_checks=0)
    route.construction_api().bind(result)
    route.bind_context(context)
    f.__dict__.update(route=route, relay=relay, batch=b, parent=parent, state=state,
        checker=checker, result=result, context=context)
    return f


def reader(f, rows=None):
    return OracleReader(policy.plain(f.batch.whole) if rows is None else rows, f.route.checkpoint)


def committed(f):
    f.batch.begin(reader(f))
    f.relay.phase = 'NATIVE'
    f.context.active = True
    f.context.attempts = f.context.jobs = 1
    f.context.bindings.append(object())
    f.context.frame_checks = 1
    frame = f.parent.run_owned()
    for _ in range(2):
        frame.read_boundary(lambda checkpoint: reader(f, policy.plain(f.batch.current)), lambda: None)
    frame.commit(dict(cleanup_confirmed=True, owned_tree_empty=True,
        job_final=dict(active_processes=0, owned_processes=[])))
    frame.raw_policy = NS(restored=True, installed=False)
    f.context.active = False
    f.context.restorations = 1
    f.relay.phase = 'NATIVE_TERMINAL'
    f.frame = frame
    f.row = dict(selected_test_index=165, cleanup_confirmed=True, owned_tree_empty=True,
        product_body_observed=True, actual_product_child_executed=True,
        Native_source_frame_qualified=True, current_generation_runtime_candidate_qualified=True,
        accepted_count_delta=0, source_frame=frame.summary())
    return f


def closed(f):
    f.route.start_closing()
    f.closing = reader(f)
    f.route.finish_whole(f.closing)
    return f


def verify(f, q=None):
    return f.route.verify(q or reader(f), f.row, {'listing': True}, {'oldbody': True},
        {'fresh': True}, NS(INDEX=165))


class Tests(unittest.TestCase):
    def test_original_checkpoint_arguments_preserved_without_added_guard(self):
        f = fixture()
        f.route.checkpoint(1, force=True)
        self.assertEqual(f.source_calls[-1], ((1,), {'force': True}))
        self.assertEqual(f.guards, [])

    def test_native_terminal_reader_cannot_fall_back_to_old_guard(self):
        f = committed(fixture())
        with self.assertRaisesRegex(ValueError, 'ORIGINAL_TERMINAL_READER_DENIED'):
            f.route.checkpoint()
        with self.assertRaises(ValueError):
            f.route.start_closing()
        self.assertEqual(f.guards, [])

    def test_original_two_boundaries_whole_close_and_same_checker_result(self):
        f = committed(fixture())
        original = f.checker.validate_candidate
        before = copy.deepcopy(f.row)
        closed(f)
        self.assertEqual(f.closing.read_passes, len(f.batch.whole))
        self.assertEqual(f.closing.finishes, 0)  # No third full whole boundary.
        q = reader(f)
        self.assertIs(verify(f, q), f.answer)
        self.assertIs(f.checker.validate_candidate, original)
        self.assertIs(f.calls[0][1], f.row)
        self.assertEqual(f.row, before)
        self.assertEqual(q.finishes, 1)
        self.assertEqual(len(f.frame.boundaries), 2)
        self.assertEqual((f.guards[0].acquires, f.guards[0].closes), (1, 1))
        self.assertEqual(f.route.phase, 'CHECKED_NOT_ACCEPTED')
        self.assertFalse(f.route.evidence()['queue_advance_authorized'])

    def test_no_guard_for_unstarted_or_no_go_aborted_native(self):
        f = fixture()
        with self.assertRaises(ValueError):
            f.route.start_closing()
        self.assertEqual(f.guards, [])
        f = committed(fixture())
        f.frame.state = 'CLOSED'
        f.batch.phase = 'BROKEN'
        f.batch.cases.clear()
        with self.assertRaises(ValueError):
            f.route.start_closing()
        self.assertEqual(f.guards, [])

    def test_weak_or_live_owner_context_rejected(self):
        for name, value in (('active', True), ('jobs', 0), ('attempts', 2),
                            ('restorations', 0), ('bindings', []), ('frame_checks', 0)):
            f = committed(fixture())
            setattr(f.context, name, value)
            with self.assertRaises(ValueError):
                f.route.start_closing()
            self.assertEqual(f.guards, [])

    def test_failed_or_unrestored_native_relay_rejected(self):
        for name, value in (('restored', False), ('latched', True)):
            f = committed(fixture())
            setattr(f.relay.pressure, name, value)
            with self.assertRaises(ValueError):
                f.route.start_closing()
            self.assertEqual(f.guards, [])

    def test_second_boundary_and_raw_restoration_cannot_be_skipped(self):
        for mutate in (lambda f: f.frame.boundaries.pop(),
                       lambda f: setattr(f.frame.raw_policy, 'restored', False),
                       lambda f: setattr(f.frame.held, 'closed', False)):
            f = committed(fixture())
            mutate(f)
            with self.assertRaises(ValueError):
                f.route.start_closing()
            self.assertEqual(f.guards, [])

    def test_original_connected_frame_method_identity_still_enforced(self):
        f = committed(fixture())
        f.frame.check = lambda: None
        with self.assertRaisesRegex(ValueError, 'NO_INSTANCE_FRAME_METHOD_REPLACEMENT'):
            f.route.start_closing()
        self.assertEqual(f.guards, [])

    def test_original_whole_changed_or_missing_denies_oracle_and_closes(self):
        for rows in ({N['path']: N}, {H['path']: H, N['path']: dict(N, bytes=3)}):
            f = committed(fixture())
            f.route.start_closing()
            with self.assertRaises((ValueError, FileNotFoundError)):
                f.route.finish_whole(reader(f, rows))
            self.assertEqual(f.calls, [])
            self.assertEqual(f.guards[0].closes, 1)
            self.assertTrue(f.route.broken)

    def test_oracle_before_whole_closing_never_runs(self):
        f = committed(fixture())
        f.route.start_closing()
        with self.assertRaises(ValueError):
            verify(f)
        self.assertEqual(f.calls, [])
        self.assertEqual(f.guards[0].closes, 1)

    def test_no_second_guard_or_oracle_retry_after_success(self):
        f = closed(committed(fixture()))
        verify(f)
        with self.assertRaises(ValueError):
            verify(f)
        with self.assertRaises(ValueError):
            f.route.start_closing()
        self.assertEqual(len(f.guards), 1)
        self.assertEqual(len(f.calls), 1)

    def test_altered_candidate_flags_or_summary_never_reach_checker(self):
        for key, value in (('selected_test_index', 166), ('accepted_count_delta', True),
                           ('Native_source_frame_qualified', False), ('product_body_observed', False),
                           ('source_frame', {})):
            f = closed(committed(fixture()))
            f.row[key] = value
            with self.assertRaises(ValueError):
                verify(f)
            self.assertEqual(f.calls, [])
            self.assertTrue(f.guards[0].cleanup)

    def test_reused_or_foreign_checkpoint_oracle_reader_denied(self):
        for kind in ('closing', 'initial', 'used', 'foreign'):
            f = closed(committed(fixture()))
            q = f.closing if kind == 'closing' else f.batch.initial_reader if kind == 'initial' else reader(f)
            if kind == 'used':
                q.fresh_pin(N['path'])
            if kind == 'foreign':
                q.checkpoint = lambda: None
            with self.assertRaises(ValueError):
                verify(f, q)
            self.assertEqual(f.calls, [])

    def test_original_checker_failure_preserved_and_cleanup_unconditional(self):
        f = closed(committed(fixture()))
        error = ValueError('ORIGINAL_FULL_ORACLE_REJECTION')
        f.oracle_error = error
        with self.assertRaises(ValueError) as caught:
            verify(f)
        self.assertIs(caught.exception, error)
        self.assertEqual(f.route.oracle_attempts, 1)
        self.assertTrue(f.guards[0].cleanup)

    def test_oracle_final_fresh_hash_error_not_promoted(self):
        f = closed(committed(fixture()))
        q = reader(f)
        q.error = ValueError('ORIGINAL_FINAL_FRESH_HASH_MISMATCH')
        with self.assertRaises(ValueError) as caught:
            verify(f, q)
        self.assertIs(caught.exception, q.error)
        self.assertTrue(f.route.broken)
        self.assertEqual(f.guards[0].closes, 1)

    def test_replaced_or_in_place_modified_checker_never_accepted(self):
        for replace in (False, True):
            f = closed(committed(fixture()))
            if replace:
                f.checker.validate_candidate = lambda *args: True
            else:
                method = f.checker.validate_candidate
                method.__code__ = method.__code__.replace(co_name='changed_checker')
            with self.assertRaisesRegex(ValueError, 'UNCHANGED_ORIGINAL_FULL_CHECKER'):
                verify(f)
            self.assertEqual(f.calls, [])
            self.assertTrue(f.guards[0].cleanup)

    def test_resource_error_identity_and_cleanup_not_pressure_gated(self):
        f = closed(committed(fixture()))
        error = ValueError('STOP_ORIGINAL_RAM95')
        f.guards[0].error = error
        with self.assertRaises(ValueError) as caught:
            verify(f)
        self.assertIs(caught.exception, error)
        self.assertEqual(f.calls, [])
        self.assertEqual(f.guards[0].closes, 1)

    def test_original_guard_cleanup_required_after_checker_success(self):
        f = closed(committed(fixture()))
        f.guards[0].close_ok = False
        with self.assertRaisesRegex(ValueError, 'ORIGINAL_READ_ONLY_OWNER_CLEANUP'):
            verify(f)
        self.assertTrue(f.route.broken)
        self.assertFalse(f.route.cleanup)

    def test_foreign_owner_sticky_failure_without_guard_or_native_replay(self):
        f = committed(fixture())
        f.ident[0] = (1, 3)
        with self.assertRaises(ValueError):
            f.route.start_closing()
        f.ident[0] = (1, 2)
        with self.assertRaises(ValueError):
            f.route.start_closing()
        self.assertEqual(f.guards, [])


if __name__ == '__main__':
    unittest.main()
