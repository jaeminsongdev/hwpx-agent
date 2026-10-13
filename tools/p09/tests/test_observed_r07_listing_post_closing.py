import json
import unittest
import close_observed_r07_listing_output as v

class ObservedR07ListingPostClosingTests(unittest.TestCase):
    def row(self):return json.loads((v.c.ROOT/v.ACTUAL['path']).read_text(encoding='utf-8'))
    def test_clean_exact249_list_then_post_CPU_stop_eligible(self):
        self.assertEqual(len(v.metadata_scope(self.row())),1434)
    def test_pre_GO_running_nonzero_or_unclean_run_denied(self):
        for key,value in (('state','DEFERRED_NOT_STARTED'),('operation_phase','running'),
            ('exit_code',1),('writer_authorized',False),('cleanup_confirmed',False)):
            row=self.row();row[key]=value
            with self.assertRaises(ValueError):v.metadata_scope(row)
    def test_partial_or_error_capture_denied(self):
        for key,value in (('error_code','FULL_CAPTURE_OUTPUT_LIMIT'),('per_stream_limit_bytes',32769),
            ('raw_log_content_included',True)):
            row=self.row();row['capture_diagnostics'][key]=value
            with self.assertRaises(ValueError):v.metadata_scope(row)
        row=self.row();row['capture_diagnostics']['received_bytes']['stdout']-=1
        row['capture_diagnostics']['buffered_bytes']['stdout']-=1
        with self.assertRaises(ValueError):v.metadata_scope(row)
    def test_runtime_filtered_or_retroactive_original_PASS_denied(self):
        for key,value in (('runtime_tests_executed',True),('compiled_inventory_exact',True),
            ('current_compiled249_qualified',True),('product_complete',True)):
            row=self.row();row[key]=value
            with self.assertRaises(ValueError):v.metadata_scope(row)
        row=self.row();row['source_test_names'].pop()
        with self.assertRaises(ValueError):v.metadata_scope(row)
    def test_partial_before_or_wrong_profile_EXE_denied(self):
        row=self.row();row['source_freeze'].pop()
        with self.assertRaises(ValueError):v.metadata_scope(row)
        row=self.row();row['test_package_profile_config'].pop()
        with self.assertRaises(ValueError):v.metadata_scope(row)
        row=self.row();row['compiled_test_executable_pin']['path']=row['compiled_test_executable_pin']['path'].replace('r07','r06')
        with self.assertRaises(ValueError):v.metadata_scope(row)
    def test_foreign_or_missing_original_parent_observation_denied(self):
        for key,value in (('foreign_Process_query_executed',True),
            ('readonly_parent_ProcessTimes_observation_connected',False),('original_resource_guards_and_read_rates_preserved',False)):
            row=self.row();row[key]=value
            with self.assertRaises(ValueError):v.metadata_scope(row)
