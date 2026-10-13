"""Pure trace fixtures and fixed queue source checks; NEVER native receipts/dispatch."""
import copy
import json
import unittest
from tools.p09 import reference_native_queue as q

f=q.field


def synthetic_complete(row,pins):
    trace={k:None for k in f.TRACE_KEYS}
    trace.update(schema_version='hwpx-agent.p09-55-click-format-owned-target-trace/v1',case_id=row['case_id'],
        worker_plan_case_id=row['worker_plan_case_id'],state=f.COMPLETE,started_at_utc='2026-10-03T00:00:00.0000000Z',
        completed_at_utc='2026-10-03T00:00:05.0000000Z',target=copy.deepcopy(f.TARGET),
        source_sha256=row['source_package_sha256'],plan_sha256=row['plan_sha256'],harness_sha256=pins[f.p.HARNESS],
        lifecycle_library_sha256=pins[f.p.LIBRARY],
        p54_worker_sha256='6ccda3e4c42979e99be67f1033c4ff10866a97a822effee5c2ea1746e70cca89',
        p50_copy_library_sha256='c0534e9bfdcb0d4e93cd8535585d462df59813c7d9788f7b55afcf4d23c48183',
        security_module_sha256='9ac5b97c47ac8aed1e8bca27a3eef39411361d8f68c262509f0c40a8f9d21bb6',
        checks={n:copy.deepcopy(f.APPLICATION if i==0 else f.VERIFICATION) for i,n in enumerate(f.CHECKS)},
        remaining_hwp_process_count=0)
    for name in f.FALSE_FIELDS:trace[name]=False
    trace['sessions']=[{'label':label,'version':'11.0.0.9136','register_module_return':False,
        'process':{'process_id':100+i,'session_id':1,'created_at_utc':f'2026-10-03T00:00:0{i}.0000000Z',
            'executable_sha256':f.TARGET['executable_sha256'],'window_handle_binds_exact_process':True},
        'close_without_dirty_prompt_returned':True,'quit_invoked':True,'remaining_owned_process_count':0,'cleanup_error':None}
        for i,label in enumerate(('save','reopen'))]
    package=f.p.m.prior.candidate.bounded(q.ROOT/row['sdk_expected_file'])
    # In-memory hypothetical outputs, not native files; NEVER write trace/artifacts/dispatch.
    outputs={'saved.hwpx':package,'saved.pdf':b'%PDF-pure-fixture','reopened.hwpx':package,'reopened.pdf':b'%PDF-pure-fixture'}
    trace['artifacts']={name:{'sha256':q.sha(raw),'bytes':len(raw)} for name,raw in outputs.items()}
    return trace,outputs


class ReferenceNativeQueue(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ctx=q.context();cls.rows=f.p.original_inputs()[0];cls.pins=cls.ctx['p55_source_sha256']

    def bind(self,trace,code=0):
        return f.bind_trace(trace,self.rows[0],code,source_pins=self.pins)

    def test_all_seventeen_exact_inputs_and_existing_frozen_source_graph(self):
        self.assertEqual(tuple(r['case_id'] for r in self.ctx['complete_ordered_queue']),q.EXPECTED_IDS)
        self.assertEqual(len({r['run_directory'] for r in self.ctx['complete_ordered_queue']}),17)
        self.assertEqual(len(self.ctx['p55_source_sha256']),7)
        self.assertEqual(len(self.ctx['p52_source_sha256']),6)

    def test_queue_rejects_subset_reorder_alias_and_boolean_coercion(self):
        for mode in ('subset','reverse','alias','coerced'):
            changed=copy.deepcopy(self.ctx)
            if mode=='subset':changed['complete_ordered_queue'].pop()
            if mode=='reverse':changed['complete_ordered_queue'].reverse()
            if mode=='alias':changed['complete_ordered_queue'][0]['run_directory']='alias'
            if mode=='coerced':changed['private_field_plan_bundle']['native_runtime_qualified']=0
            self.assertRaises(ValueError,q.check_context,changed,self.ctx)

    def test_both_synthetic_complete_traces_bind_only_non_green_diagnostics(self):
        for row in self.rows:
            trace,_=synthetic_complete(row,self.pins)
            result=f.bind_trace(trace,row,0,source_pins=self.pins)
            self.assertEqual(result['lifecycle'],'pass')
            self.assertFalse(result['native_package_render_differential_or_product_qualified'])

    def test_trace_rejects_foreign_hash_unknown_values_target_or_false_green(self):
        original,_=synthetic_complete(self.rows[0],self.pins)
        for key,value in [('source_sha256','0'*64),('plan_sha256','0'*64),('harness_sha256','0'*64),
            ('extra_values','private'),('p09_complete',True),('remaining_hwp_process_count',False)]:
            trace=copy.deepcopy(original);trace[key]=value;self.assertRaises(ValueError,self.bind,trace)
        trace=copy.deepcopy(original);trace['target']['unknown']=False;self.assertRaises(ValueError,self.bind,trace)

    def test_trace_rejects_duplicate_or_coerced_owner_and_wrong_timestamp_order(self):
        original,_=synthetic_complete(self.rows[0],self.pins)
        for mode in ('duplicate','bool_pid','old_birth','reverse_time'):
            trace=copy.deepcopy(original)
            if mode=='duplicate':trace['sessions'][1]['process']['process_id']=100
            if mode=='bool_pid':trace['sessions'][0]['process']['process_id']=True
            if mode=='old_birth':trace['sessions'][0]['process']['created_at_utc']='2026-10-02T00:00:00.0000000Z'
            if mode=='reverse_time':trace['completed_at_utc']='2026-10-02T00:00:00.0000000Z'
            self.assertRaises(ValueError,self.bind,trace)

    def test_trace_exit_cleanup_and_stage_gap_cannot_be_promoted(self):
        original,_=synthetic_complete(self.rows[0],self.pins)
        self.assertRaises(ValueError,self.bind,original,2)
        trace=copy.deepcopy(original);del trace['checks']['after_first_save'];self.assertRaises(ValueError,self.bind,trace)
        trace=copy.deepcopy(original);trace['checks']['fresh_reopen']['document_style_or_text_write_invoked']=True
        self.assertRaises(ValueError,self.bind,trace)
        trace=copy.deepcopy(original);trace['sessions'][1]['quit_invoked']=False
        trace['sessions'][1]['cleanup_error']=f.CLEANUP_ERRORS[1]
        self.assertRaises(ValueError,self.bind,trace,0)
        self.assertEqual(self.bind(trace,2)['lifecycle'],'fail')

    def test_failure_prefix_and_rollback_claims_preserve_unverified_status(self):
        trace,_=synthetic_complete(self.rows[0],self.pins)
        trace.update(state='effect_unknown',failed_phase='native_text_and_complete_style_application',
            error_code='P09_CLICK_FORMAT_NATIVE_FAILED',checks={},artifacts={})
        trace['sessions']=trace['sessions'][:1]
        trace['binding_failure']={'failed_phase':'native_text_replacement','error_code':'P09_CLICK_FORMAT_NATIVE_NEW_TEXT_MISMATCH',
            'rollback_state':f.ROLLBACK[2],'raw_document_values_present':False}
        record=self.bind(trace,2)
        self.assertEqual(record['lifecycle'],'fail')
        self.assertFalse(record['native_package_render_differential_or_product_qualified'])
        bad=copy.deepcopy(trace);bad['binding_failure']['rollback_state']='pass';self.assertRaises(ValueError,self.bind,bad,2)
        bad=copy.deepcopy(trace);bad['checks']['first_application']=copy.deepcopy(f.APPLICATION)
        bad['failed_phase']='first_source_open';self.assertRaises(ValueError,self.bind,bad,2)

    def test_complete_artifacts_bind_hashes_and_actual_sdk_full_package_comparison(self):
        trace,raw=synthetic_complete(self.rows[0],self.pins)
        result=f.bind_artifacts(trace,self.rows[0],raw)
        for name in ('saved.hwpx','reopened.hwpx'):
            self.assertTrue(result[name]['whole_sdk_package_comparison']['whole_expanded_bytes_exact'])
            self.assertFalse(result[name]['native_render_or_product_qualified'])
        bad=dict(raw);bad['saved.pdf']=b'not-a-pdf';self.assertRaises(ValueError,f.bind_artifacts,trace,self.rows[0],bad)
        bad=dict(raw);bad.pop('saved.hwpx');self.assertRaises(ValueError,f.bind_artifacts,trace,self.rows[0],bad)

    def test_zero_byte_partial_is_preserved_not_saved_package_acceptance(self):
        trace,_=synthetic_complete(self.rows[0],self.pins)
        trace.update(state='effect_unknown',failed_phase='first_save',error_code='P55_NATIVE_SAVE_FAILED',artifacts={})
        trace['checks']={n:trace['checks'][n] for n in f.CHECKS[:2]};trace['sessions']=trace['sessions'][:1]
        self.bind(trace,2)
        partial=f.bind_artifacts(trace,self.rows[0],{'saved.hwpx':b''})
        self.assertEqual(partial['saved.hwpx']['bytes'],0)
        self.assertTrue(partial['saved.hwpx']['partial_unqualified_preserved'])
        self.assertNotIn('whole_sdk_package_comparison',partial['saved.hwpx'])

    def test_absent_complete_dispatch_returns_not_run_without_native_files(self):
        self.assertFalse((q.ROOT/q.DISPATCH).exists())
        result=q.observe_current({})
        self.assertEqual(result['state'],'NOT_RUN');self.assertEqual(result['case_count'],0)
        self.assertFalse(result['native_session_started'])
        self.assertFalse((q.ROOT/q.CURRENT).exists())

    def test_dispatcher_reuses_whole_original_fifteen_and_never_auto_retries(self):
        import inspect
        source=inspect.getsource(q.execute_full_queue)
        self.assertIn('form_dispatch.run()',source)
        self.assertIn('saved.bind_actual_current()',source)
        self.assertIn("command[-1]='-ExecuteNative'",source)
        self.assertIn('record[\'cleanup_safe_to_continue\']',source)
        for forbidden in ('Stop-Process','kill(','terminate(','timeout=','shell=True'):
            self.assertNotIn(forbidden,source)


if __name__=='__main__':
    unittest.main()
