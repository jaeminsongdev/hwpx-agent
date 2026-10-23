"""Dependency-only binding and original refusal/identity contracts, not runtime."""
from types import SimpleNamespace as NS
import unittest
import native011_shared_parent as shared
import native011_current_epoch_report_admission as admission
import current_stored_runtime_scope as scope


class ReportAdmissionContracts(unittest.TestCase):
    def test_named_admission_controls_are_required_inputs_not_extra_projector_controls(self):
        pin=lambda name:dict(path=name,bytes=1,sha256='a'*64)
        controls={name:pin(name) for name in (admission.SELF,admission.TEST)}
        baseline={'tools/p09/model_prior.py':pin('tools/p09/model_prior.py')}
        original=NS(required=baseline)
        updated=admission.declare_controls(original,controls,scope)
        self.assertEqual(updated.required,{**baseline,**controls});self.assertEqual(original.required,baseline)
        with self.assertRaisesRegex(ValueError,'ONLY_TWO_NAMED_ADMISSION_CONTROLS'):
            admission.declare_controls(original,{**controls,'tools/p09/arbitrary.py':pin('tools/p09/arbitrary.py')},scope)

    def test_full_original_code_defaults_closure_and_other_globals_retained(self):
        original=shared.admit_report;old=original.__globals__['reports'];current=NS()
        bound,proof=admission.connect(original,current)
        self.assertIs(bound.__code__,original.__code__)
        self.assertIs(bound.__defaults__,original.__defaults__)
        self.assertIs(bound.__kwdefaults__,original.__kwdefaults__)
        self.assertIs(bound.__closure__,original.__closure__)
        self.assertIs(bound.__globals__['reports'],current)
        self.assertIs(original.__globals__['reports'],old)
        self.assertTrue(proof['original_history_reclassification_guard_retained'])

    def test_original_owner_phase_gate_runs_before_new_report_or_io(self):
        events=[]
        class Batch:
            phase='READY';parent_connection=None
            def check(self):events.append('original-check')
        bound,_=admission.connect(shared.admit_report,NS())
        with self.assertRaisesRegex(ValueError,'REPORT_BEFORE_ANY_PARENT_CONNECTION'):
            bound(None,NS(),NS(),NS(Batch=Batch),NS(planned=NS(batch=Batch())),3)
        self.assertEqual(events,['original-check'])

    def test_unrelated_function_not_admitted(self):
        with self.assertRaisesRegex(ValueError,'ENTIRE_ORIGINAL_REPORT_ADMISSION_FUNCTION'):
            admission.connect(lambda:None,NS())
