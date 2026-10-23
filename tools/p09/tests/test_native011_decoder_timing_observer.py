import unittest
from pathlib import Path
import shared_metadata_frame_decoder_budget_v1 as shared_module
import native011_decoder_timing_observer as m


class Tests(unittest.TestCase):
    def test_original_operation_result_counters_and_clock_preserved(self):
        calls=[];budget=m.original.DecoderBudget(lambda:calls.append(1));clock=budget.clock;check=budget.check
        observer=m.attach(budget,wall=iter((1.,1.25)).__next__,cpu=iter((2.,2.1)).__next__)
        self.assertEqual(budget.run(lambda checkpoint:(checkpoint(),42)[1]),42)
        row=observer.evidence()
        self.assertIs(budget.clock,clock);self.assertEqual(budget.check,check)
        self.assertEqual(budget.attempts,1);self.assertEqual(budget.completed,1)
        self.assertEqual(row['observed_wall_total'],.25)
        self.assertAlmostEqual(row['observed_CPU_total'],.1)
        self.assertTrue(calls);self.assertFalse(row['failed'])

    def test_original_guard_error_and_failed_no_retry(self):
        error=ValueError('ORIGINAL_GUARD');budget=m.original.DecoderBudget(lambda:(_ for _ in ()).throw(error))
        observer=m.attach(budget)
        with self.assertRaises(ValueError) as found:budget.run(lambda check:None)
        self.assertIs(found.exception,error);self.assertTrue(observer.state.failed)
        with self.assertRaisesRegex(ValueError,'NO_FAILED_RETRY'):budget.run(lambda check:None)
        self.assertEqual(budget.attempts,0)

    def test_original_operation_error_remains_sticky(self):
        budget=m.original.DecoderBudget(lambda:None);observer=m.attach(budget);error=RuntimeError('ORIGINAL_OPERATION')
        with self.assertRaises(RuntimeError) as found:budget.run(lambda check:(_ for _ in ()).throw(error))
        self.assertIs(found.exception,error);self.assertIs(budget.error,error)
        self.assertEqual(observer.evidence()['rows'][0]['original_call_failed'],True)

    def test_observer_clock_failure_does_not_hide_original_error(self):
        budget=m.original.DecoderBudget(lambda:None);error=ValueError('ORIGINAL_OPERATION')
        observer=m.attach(budget,wall=iter((1.,float('nan'))).__next__)
        with self.assertRaises(ValueError) as found:budget.run(lambda check:(_ for _ in ()).throw(error))
        self.assertIs(found.exception,error);self.assertTrue(observer.state.failed)

    def test_used_budget_and_second_installation_rejected(self):
        budget=m.original.DecoderBudget(lambda:None);budget.run(lambda check:None)
        with self.assertRaisesRegex(ValueError,'FRESH_ORIGINAL'):m.attach(budget)
        budget=m.original.DecoderBudget(lambda:None);m.attach(budget)
        with self.assertRaisesRegex(ValueError,'FRESH_ORIGINAL'):m.attach(budget)

    def test_original_five_second_stop_is_not_replaced_by_observation(self):
        ticks=[0.];budget=m.original.DecoderBudget(lambda:None,clock=lambda:ticks[0])
        observer=m.attach(budget,wall=iter((1.,1.01)).__next__,cpu=lambda:0.)
        def operation(check):ticks[0]=5.01;check()
        with self.assertRaisesRegex(ValueError,'STOP_AGGREGATE_ENVELOPE_DECODER5'):budget.run(operation)
        row=observer.evidence();self.assertEqual(row['original_budget']['completed_decodes'],0)
        self.assertTrue(row['original_budget']['terminal_error_seen'])
        self.assertEqual(row['original_budget']['aggregate_limit_seconds'],5.)

    def test_observation_clock_backward_is_failed_not_passed(self):
        budget=m.original.DecoderBudget(lambda:None);observer=m.attach(budget,wall=iter((2.,1.)).__next__)
        with self.assertRaisesRegex(ValueError,'MONOTONIC_OBSERVATIONS'):budget.run(lambda check:42)
        self.assertTrue(observer.state.failed);self.assertEqual(observer.state.completed,0)

    def test_invalid_first_stamp_is_sticky_without_original_execution(self):
        budget=m.original.DecoderBudget(lambda:None);observer=m.attach(budget,wall=lambda:float('nan'))
        with self.assertRaisesRegex(ValueError,'FINITE_NONNEGATIVE'):budget.run(lambda check:None)
        self.assertTrue(observer.state.failed);self.assertEqual(budget.attempts,0)
        with self.assertRaisesRegex(ValueError,'NO_FAILED_RETRY'):budget.run(lambda check:None)

    def test_changed_clock_is_sticky_without_original_execution(self):
        budget=m.original.DecoderBudget(lambda:None);observer=m.attach(budget);budget.clock=lambda:0.
        with self.assertRaisesRegex(ValueError,'ORIGINAL_CLOCK_AND_CHECK'):budget.run(lambda check:None)
        self.assertTrue(observer.state.failed);self.assertEqual(budget.attempts,0)

    def shared_raw(self):
        return (Path(__file__).resolve().parents[3]/m.SHARED['path']).read_bytes()
    def budget_raw(self):
        return (Path(__file__).resolve().parents[3]/m.BUDGET['path']).read_bytes()

    def test_shared_hook_does_not_construct_or_mutate_default_classes(self):
        shared=shared_module.SharedBudget();original_attach=shared_module.SharedBudget.attach
        connector,proof=m.connect_shared(shared,self.shared_raw(),self.budget_raw())
        self.assertIs(shared_module.SharedBudget.attach,original_attach)
        self.assertEqual(connector.state.attempts,0)
        self.assertEqual(proof['budgets_constructed_during_connection'],0)
        self.assertIsNone(shared.metadata);self.assertIsNone(shared.frame)

    def test_actual_original_private_loader_shared_class_is_supported(self):
        import runtime_envelope_namespace_bundle_v1 as loader
        import conservative_maintenance as c
        libs,_=loader.load(c.ROOT,[m.SHARED],{})
        shared=libs.shared_metadata_frame_decoder_budget_v1.SharedBudget()
        connector,_=m.connect_shared(shared,self.shared_raw(),self.budget_raw())
        self.assertEqual(connector.state.attempts,0)

    def test_actual_private_loader_budgets_keep_original_shared_callbacks(self):
        import runtime_envelope_namespace_bundle_v1 as loader
        import conservative_maintenance as c
        libs,_=loader.load(c.ROOT,[m.BUDGET],dict(runtime_envelope_source_projection_v1=m.original.source,
            owned_source_read_pressure=m.original.bytes_policy))
        cls=libs.runtime_envelope_physical_io_v1.DecoderBudget
        shared=shared_module.SharedBudget();connector,_=m.connect_shared(shared,self.shared_raw(),self.budget_raw())
        for role in ('metadata','frame'):
            budget=cls(lambda:None);shared.attach(role,budget);budget.run(lambda check:(check(),42)[1])
        self.assertEqual(connector.evidence()['completed'],2)
        self.assertIs(type(shared.frame),cls);shared.restore()

    def test_actual_shared_two_roles_keep_one_original_five_second_budget(self):
        shared=shared_module.SharedBudget();connector,_=m.connect_shared(shared,self.shared_raw(),self.budget_raw())
        for role in ('metadata','frame'):
            budget=m.original.DecoderBudget(lambda:None)
            self.assertIs(shared.attach(role,budget),budget)
            self.assertEqual(budget.run(lambda check:(check(),42)[1]),42)
        result=connector.evidence()
        self.assertEqual(result['attempts'],2);self.assertEqual(result['completed'],2)
        self.assertEqual(result['original_shared']['metadata_completed'],1)
        self.assertEqual(result['original_shared']['Frame_completed'],1)
        self.assertEqual(result['original_shared']['shared_limit_seconds'],5.)
        shared.restore();self.assertFalse(connector.evidence()['failed'])

    def test_private_whole_original_budget_namespace_is_supported_without_default_mutation(self):
        saved=m.original.DecoderBudget.run
        raw=Path(m.original.__file__).read_bytes();env=dict(__name__='p09_private_test')
        exec(compile(raw,m.original.__file__,'exec'),env)
        cls=env['DecoderBudget'];self.assertIsNot(cls,m.original.DecoderBudget)
        shared=shared_module.SharedBudget();connector,_=m.connect_shared(shared,self.shared_raw(),self.budget_raw())
        budget=cls(lambda:None);shared.attach('metadata',budget);budget.run(lambda check:42)
        self.assertEqual(connector.evidence()['roles']['metadata']['completed'],1)
        self.assertIs(m.original.DecoderBudget.run,saved)
        self.assertIs(type(budget),cls)

    def test_shared_source_drift_and_budget_subclass_rejected(self):
        with self.assertRaisesRegex(ValueError,'EXACT_SHARED_SOURCE'):
            m.connect_shared(shared_module.SharedBudget(),self.shared_raw()+b'\n',self.budget_raw())
        with self.assertRaisesRegex(ValueError,'EXACT_BUDGET_SOURCE'):
            m.connect_shared(shared_module.SharedBudget(),self.shared_raw(),self.budget_raw()+b'\n')
        shared=shared_module.SharedBudget();connector,_=m.connect_shared(shared,self.shared_raw(),self.budget_raw())
        class Extra(m.original.DecoderBudget):pass
        with self.assertRaisesRegex(ValueError,'PRIVATE_BUDGET_CLASS_LAYOUT'):
            shared.attach('metadata',Extra(lambda:None))
        self.assertTrue(connector.state.failed);self.assertIsNone(shared.metadata)

    def test_shared_wrong_order_is_sticky_and_never_becomes_an_attach(self):
        shared=shared_module.SharedBudget();connector,_=m.connect_shared(shared,self.shared_raw(),self.budget_raw())
        with self.assertRaisesRegex(ValueError,'METADATA_THEN_FRAME_NO_RETRY'):
            shared.attach('frame',m.original.DecoderBudget(lambda:None))
        self.assertTrue(connector.state.failed)
        with self.assertRaisesRegex(ValueError,'METADATA_THEN_FRAME_NO_RETRY'):
            shared.attach('metadata',m.original.DecoderBudget(lambda:None))
        self.assertIsNone(shared.metadata)


if __name__=='__main__':unittest.main()
