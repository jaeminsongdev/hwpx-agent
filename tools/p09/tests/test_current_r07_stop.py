import copy
import json
import unittest
import inspect_current_r07_stop as v

class StopTests(unittest.TestCase):
    def data(self):
        load=lambda pin:json.loads((v.c.ROOT/pin['path']).read_text(encoding='utf-8'))
        return load(v.ACTUAL),load(v.PREP),load(v.run.PARENT)
    def test_real_running_stop_is_not_runtime_or_whole_current_source_pass(self):
        info=v.actual_scope(*self.data())
        self.assertTrue(info['original_test_execution_started'])
        for n in ('original_full249_qualified','original_signed16_qualified','current_whole_runtime_inputs_reaudited',
                'original_final_source_freeze_completed','original_complete_test_summary_available','PC_freeze_cause_established'):
            self.assertIs(info[n],False)
    def test_changed_phase_exit_or_unclean_job_cannot_be_reclassified(self):
        row,prep,parent=self.data()
        for key,value in (('state',v.run.PASS),('operation_phase','final_source_freeze'),('exit_code',0),
                ('cleanup_confirmed',False),('owned_tree_empty',False)):
            candidate=copy.deepcopy(row);candidate[key]=value
            with self.assertRaises(ValueError):v.actual_scope(candidate,prep,parent)
    def test_runtime_signed_product_or_foreign_query_promotion_rejected(self):
        row,prep,parent=self.data()
        for key in ('full249_current_qualified','signed16_current_qualified','product_complete','foreign_Process_query_executed'):
            candidate=copy.deepcopy(row);candidate[key]=True
            with self.assertRaises(ValueError):v.actual_scope(candidate,prep,parent)
    def test_missing_or_drifted_original_whole_before_cannot_be_hidden(self):
        row,prep,parent=self.data();row['source_freeze'].pop()
        with self.assertRaises(ValueError):v.actual_scope(row,prep,parent)
        row,prep,parent=self.data();row['source_freeze'][0]['sha256']='0'*64
        with self.assertRaises(ValueError):v.actual_scope(row,prep,parent)
    def test_original_stop_decision_and_raw_parent_CPU_replayed_not_forged(self):
        row,prep,parent=self.data();row['samples'][-1]['system_cpu_percent']=94
        with self.assertRaises(ValueError):v.actual_scope(row,prep,parent)
        row,prep,parent=self.data();row['samples'][-1]['parent_cpu_machine_percent']=1
        with self.assertRaises(ValueError):v.actual_scope(row,prep,parent)
    def test_stream_partial_and_IO_gate_do_not_become_complete_result_or_cause(self):
        row,prep,parent=self.data();row['capture_diagnostics']['received_bytes']['stdout']=67
        with self.assertRaises(ValueError):v.actual_scope(row,prep,parent)
        row,prep,parent=self.data();row['owned_source_reader_passes'][0]['near_saturation_read_backpressure']['original_read_checks_skipped']=True
        with self.assertRaises(ValueError):v.actual_scope(row,prep,parent)
