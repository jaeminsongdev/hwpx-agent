"""Entry state machine contracts; all execution objects below are synthetic."""
import unittest
from types import SimpleNamespace as NS
import native009_full75_runtime_v1 as module


def fixture(events):
    def outer(run): events.append(('original_outer', run)); return 17
    connected = NS(parent_state=NS(attempts=0, frames=[]), callback_calls=[], outer=outer)
    built = NS(context=NS(attempts=0, jobs=0), connected=connected, engine=NS(state=NS(calls=0)),
        shared=NS(metadata=None, frame=None, restored=False))
    q = NS(finish=lambda: events.append('final_hashes'))
    guard = NS(cleanup=False)
    def close(): events.append('close_preparation'); guard.cleanup=True
    guard.close=close
    return built, q, guard


class Tests(unittest.TestCase):
    def test_original_outer_after_final_hashes_and_closed_preparation(self):
        events=[]; built,q,guard=fixture(events); once=module.Once()
        self.assertEqual(once.execute(built,q,guard),17)
        self.assertEqual(events,['final_hashes','close_preparation',('original_outer',1)])
        self.assertEqual(once.attempts,1)

    def test_no_second_entry_attempt(self):
        events=[]; built,q,guard=fixture(events); once=module.Once(); once.execute(built,q,guard)
        with self.assertRaises(ValueError): once.execute(built,q,guard)
        self.assertEqual(events.count(('original_outer',1)),1)

    def test_final_hash_failure_closes_preparation_and_never_calls_outer(self):
        events=[]; built,q,guard=fixture(events); failure=OSError('SYNTHETIC_FRESH_SOURCE_FAILURE')
        def fail(): raise failure
        q.finish=fail; once=module.Once()
        with self.assertRaises(OSError) as caught: once.execute(built,q,guard)
        self.assertIs(caught.exception,failure); self.assertTrue(guard.cleanup)
        self.assertEqual(events,['close_preparation'])
        with self.assertRaises(ValueError): once.execute(built,q,guard)

    def test_cleanup_failure_never_calls_outer(self):
        events=[]; built,q,guard=fixture(events); guard.close=lambda:events.append('cleanup_failed')
        with self.assertRaises(ValueError): module.Once().execute(built,q,guard)
        self.assertNotIn(('original_outer',1),events)

    def test_original_outer_failure_preserved_and_not_retried(self):
        events=[]; built,q,guard=fixture(events); failure=ValueError('SYNTHETIC_NATIVE_STOP')
        def fail(run): raise failure
        built.connected.outer=fail; once=module.Once()
        with self.assertRaises(ValueError) as caught: once.execute(built,q,guard)
        self.assertIs(caught.exception,failure); self.assertTrue(guard.cleanup)
        with self.assertRaises(ValueError): once.execute(built,q,guard)

    def test_existing_parent_job_worker_frame_and_metadata_are_rejected(self):
        for kind in ('parent','job','worker','frame','metadata'):
            events=[]; built,q,guard=fixture(events)
            if kind=='parent': built.connected.parent_state.attempts=1
            if kind=='job': built.context.jobs=1
            if kind=='worker': built.engine.state.calls=1
            if kind=='frame': built.connected.parent_state.frames=[object()]
            if kind=='metadata': built.connected.callback_calls=[1]
            with self.assertRaises(ValueError): module.Once().execute(built,q,guard)
            self.assertEqual(events,[])

    def test_used_or_restored_shared_budget_is_rejected(self):
        for kind in ('metadata','frame','restored'):
            events=[]; built,q,guard=fixture(events)
            setattr(built.shared,kind,True if kind=='restored' else object())
            with self.assertRaises(ValueError): module.Once().execute(built,q,guard)
            self.assertEqual(events,[])

    def test_only_explicit_finite_native9_identity(self):
        self.assertEqual(module.NATIVE,'implementation/p09/evidence/p09-361-case165-current-runtime-run009.v1.json')
        self.assertNotEqual(module.NATIVE,module.CLAIM)
        self.assertTrue(module.CLAIM.endswith('runtime-once-intent.v1.json'))

    def test_qualification_requires_closed_original_limits_not_fake_runtime_pass(self):
        row=dict(state='PASS_FULL75_SAME_RUNTIME_ENTRY9_NOT_NATIVE_PRODUCT_OR_ACCEPTANCE',
            contracts=dict(run=9,errors=0,failures=0,skipped=0),cleanup_confirmed=True,
            actual_product_or_Native_executed=False,GO_authorized=False,accepted_count_delta=0,
            actual_parent_attempts=0,actual_worker_calls=0,actual_Frame_instances=0,original_metadata_callback_calls=0,
            shared_owner_connected_but_unused=True,previous_scope_and_budget_exactly_reconstructed=True,
            persisted_scope_uses_original_noninjecting_union=True,additional_readiness_seconds_without_old_credit=15,
            fresh_inputs=4,final_fresh_hashes=4,predicted_complete_seconds_with_readiness=598.0,
            helper_inventory=dict(Native_count=64))
        def fields(actual,expected,label):
            for key,value in expected.items():
                if type(actual.get(key)) is not type(value) or actual[key]!=value: raise ValueError(label)
        api=NS(fields=fields); module.validate_qualification(row,api)
        for delta in (dict(state='PRODUCT_PASS'),dict(final_fresh_hashes=3),dict(fresh_inputs=True),
                dict(predicted_complete_seconds_with_readiness=600.0),dict(helper_inventory=dict(Native_count=65)),
                dict(additional_readiness_seconds_without_old_credit=3),dict(actual_parent_attempts=1),dict(GO_authorized=True)):
            with self.assertRaises(ValueError): module.validate_qualification(dict(row,**delta),api)


if __name__=='__main__': unittest.main()
