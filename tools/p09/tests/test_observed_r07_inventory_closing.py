import json
import unittest
import audit_observed_r07_inventory as a

class R07InventoryClosingTests(unittest.TestCase):
    def row(self):return json.loads((a.c.ROOT/a.v.ACTUAL).read_text(encoding='utf-8'))
    def test_actual_whole_listing_terminal(self):
        self.assertGreaterEqual(len(a.actual_scope(self.row())),1423)
    def test_missing_GO_cleanup_or_filter_cannot_pass(self):
        for key,value in (('writer_authorized',False),('cleanup_confirmed',False),
            ('full249_current_qualified',True),('runtime_tests_executed',True),('current_compiled249_qualified',False)):
            row=self.row();row[key]=value
            with self.assertRaises(ValueError):a.actual_scope(row)
    def test_stream_and_read_omission_denied(self):
        row=self.row();row['capture_diagnostics']['received_bytes']['stderr']=1
        with self.assertRaises(ValueError):a.actual_scope(row)
        row=self.row();row['source_reader_passes'][1]['read_passes']-=1
        with self.assertRaises(ValueError):a.actual_scope(row)
    def test_forged_parent_or_foreign_sampling_denied(self):
        row=self.row();row['samples'][0]['parent_cpu_machine_percent']+=1
        with self.assertRaises(ValueError):a.actual_scope(row)
        row=self.row();row['foreign_Process_query_executed']=True
        with self.assertRaises(ValueError):a.actual_scope(row)
    def test_readonly_query_or_weakened_rate_claim_denied(self):
        for key,value in (('readonly_parent_ProcessTimes_observation_connected',False),
            ('readonly_extra_sampler_thread_started',True),('original_resource_guards_and_read_rates_preserved',False)):
            row=self.row();row[key]=value
            with self.assertRaises(ValueError):a.actual_scope(row)
    def test_declared_main_roles_preserve_all_guards(self):
        class Reader:
            def __init__(self,changed=False):self.changed=changed
            def pin(self,name):return a.CORE_PIN
            def text(self,name):
                text=(a.c.ROOT/name).read_text(encoding='utf-8')
                if self.changed and name==a.SELF:
                    text=text.replace("and prep['resource_stop_reason'] is None",'and True',1)
                return text
        a.body_inverse(Reader())
        with self.assertRaises(ValueError):a.body_inverse(Reader(changed=True))
