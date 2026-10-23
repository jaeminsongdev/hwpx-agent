"""Exact201 raw source declaration and complete budget, never live evidence."""
import copy
from types import SimpleNamespace as NS
import unittest
import current_stored_runtime_scope as scope
import native011_ready_scope_connection as control


class ReadyScopeContracts(unittest.TestCase):
    def fixture(self):
        required={f'tools/p09/model{i}.py':dict(path=f'tools/p09/model{i}.py',bytes=1,sha256='0'*64) for i in range(201)}
        history={f'implementation/p09/evidence/model{i}.json':dict(path=f'implementation/p09/evidence/model{i}.json',
            bytes=1,sha256='0'*64) for i in range(419)}
        whole={**required,**history}
        data=NS(planned=NS(current=required,whole=whole,history=history,logical=whole),
            declared=NS(to_physical=scope.pins))
        class Base:pass
        class Physical(Base):pass
        class Shared(Physical):pass
        class Native(Shared):pass
        return data,required,Native,Base
    def test_exact_raw_worker_sources_and_history_retained_without_mutation(self):
        data,required,frame,base=self.fixture();before=copy.deepcopy(data.planned.__dict__)
        result=control.inspect_current(data,required,scope,frame,base)
        self.assertEqual(data.planned.__dict__,before);self.assertEqual(result['direct_current_worker_sources'],201)
        self.assertFalse(result['actual_live_Frame_coverage_qualified'])
    def test_missing_or_conflicting_source_does_not_become_alias_coverage(self):
        for conflict in (False,True):
            data,required,frame,base=self.fixture();data.planned.current=copy.deepcopy(required)
            name=next(iter(required))
            if conflict:data.planned.current[name]['sha256']='1'*64
            else:del data.planned.current[name]
            data.planned.whole={**data.planned.current,**data.planned.history}
            with self.assertRaisesRegex(ValueError,'EVERY_WORKER_RAW_PIN'):control.inspect_current(data,required,scope,frame,base)
    def test_same_source_in_history_not_promoted_to_current(self):
        data,required,frame,base=self.fixture();data.planned.history=copy.deepcopy(data.planned.history)
        data.planned.history[next(iter(required))]=required[next(iter(required))]
        with self.assertRaises(ValueError):control.inspect_current(data,required,scope,frame,base)
    def test_logical_and_physical_scope_must_recompose_the_whole(self):
        data,required,frame,base=self.fixture();data.declared.to_physical=lambda rows:{}
        with self.assertRaisesRegex(ValueError,'ENTIRE_LOGICAL_PHYSICAL'):control.inspect_current(data,required,scope,frame,base)
    def test_other_base_or_incomplete_class_chain_rejected(self):
        data,required,frame,base=self.fixture()
        for wrong in (frame,object):
            with self.assertRaises(ValueError):control.inspect_current(data,required,scope,frame,wrong)
        with self.assertRaises(ValueError):control.inspect_current(data,required,scope,base,base)
    def budget(self):return dict(unchanged_lock_deadline_seconds=600,unallocated_margin_seconds=60,
        aggregate_envelope_decoder_allowance_seconds=5,strict_GO_to_complete_capture_window_seconds=10,
        product_allowance_seconds=10,actual_completion_guaranteed=False,predicted_runtime_combined_seconds=576)
    def test_complete_budget_adds_full_ready15_without_reducing_margin(self):
        original=self.budget();before=dict(original);result=control.complete_budget(original)
        self.assertEqual(original,before);self.assertEqual(result['with_readiness15_seconds'],591)
        self.assertEqual(result['remaining_nominal_seconds'],9);self.assertFalse(result['actual_Native_qualified'])
    def test_budget_at_deadline_or_with_weakened_original_guards_rejected(self):
        for key,value in (('predicted_runtime_combined_seconds',585),('unallocated_margin_seconds',59),
            ('aggregate_envelope_decoder_allowance_seconds',6),('product_allowance_seconds',9)):
            row=self.budget();row[key]=value
            with self.assertRaises(ValueError):control.complete_budget(row)
    def test_control_names_are_closed_and_include_runtime_bridge_code_and_provenance(self):
        self.assertEqual(len(control.CONTROLS),27);self.assertEqual(len(set(control.CONTROLS)),27)
        self.assertIn(control.READY['path'],control.CONTROLS)
        self.assertIn('tools/p09/native011_inherited_source_probe_child.py',control.CONTROLS)
    def test_optional_exact_sources_are_explicit_and_not_added_to_default_scope(self):
        from unittest.mock import patch
        q=NS();a=NS(read_exact=lambda *args:None)
        with patch.object(control,'declarations',return_value={}):
            default=control.admit(q,a,scope);exact=control.admit(q,a,scope,exact_read=True)
        self.assertEqual(default.control_names,control.CONTROLS)
        self.assertEqual(exact.control_names,control.CONTROLS+control.EXACT_CONTROLS)
        self.assertEqual(len(exact.control_names),29);self.assertFalse(default.exact_read)
        self.assertTrue(exact.exact_read);self.assertFalse(exact.live_Frame_or_product_qualified)
        with self.assertRaises(ValueError):control.admit(q,a,scope,exact_read=1)

    def test_timing_sources_are_closed_optional_and_require_exact_mode(self):
        from unittest.mock import patch
        q=NS();a=NS(read_exact=lambda *args:None)
        with patch.object(control,'declarations',return_value={}):
            timed=control.admit(q,a,scope,exact_read=True,decoder_timing=True)
        self.assertEqual(timed.control_names,control.CONTROLS+control.EXACT_CONTROLS+control.TIMING_CONTROLS)
        self.assertEqual(len(timed.control_names),31);self.assertTrue(timed.decoder_timing)
        for args in (dict(decoder_timing=True),dict(exact_read=True,decoder_timing=1)):
            with self.assertRaises(ValueError):control.admit(q,a,scope,**args)

    def test_shared_codec_sources_require_explicit_exact_and_timing_modes(self):
        from unittest.mock import patch
        with patch.object(control,'declarations',return_value={}):
            coded=control.admit(NS(),NS(read_exact=lambda *args:None),scope,
                exact_read=True,decoder_timing=True,chunk_join=True)
        self.assertEqual(coded.control_names,control.CONTROLS+control.EXACT_CONTROLS+control.TIMING_CONTROLS+control.CHUNK_CONTROLS)
        self.assertEqual(len(coded.control_names),35);self.assertTrue(coded.chunk_join)
        for options in (dict(chunk_join=True),dict(exact_read=True,chunk_join=True),
                dict(exact_read=True,decoder_timing=True,chunk_join=1)):
            with self.assertRaises(ValueError):control.admit(None,None,None,**options)

    def test_metadata_tail_sources_require_all_explicit_modes_without_default_scope_change(self):
        from unittest.mock import patch
        with patch.object(control,'declarations',return_value={}):
            value=control.admit(NS(),NS(read_exact=lambda *args:None),scope,
                exact_read=True,decoder_timing=True,chunk_join=True,metadata_tail=True)
        self.assertEqual(value.control_names,control.CONTROLS+control.EXACT_CONTROLS+control.TIMING_CONTROLS
            +control.CHUNK_CONTROLS+control.METADATA_TAIL_CONTROLS)
        self.assertEqual(len(value.control_names),39);self.assertTrue(value.metadata_tail)
        for options in (dict(metadata_tail=True),dict(exact_read=True,decoder_timing=True,metadata_tail=True),
                dict(exact_read=True,decoder_timing=True,chunk_join=True,metadata_tail=1)):
            with self.assertRaises(ValueError):control.admit(None,None,None,**options)
