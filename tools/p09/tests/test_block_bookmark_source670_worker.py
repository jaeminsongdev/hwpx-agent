"""Fixed command and profile-specific truthful notice models; no worker launch."""
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import block_bookmark_source670_worker as m

def result(**changes):
    return dict(schema_version=m.RESULT,state='block_source_callbacks_returned_semantics_unqualified',error_code=None,
        completed_callback_cases=1,retained_live_or_uncertain_owners=0,native_execution_authorized=False,**changes)

class Tests(unittest.TestCase):
    def test_only_fixed_script_and_mode(self):
        class Reader:
            root=m.original.prior.original.c.ROOT
            snapshots={}
            def pin(self,path):
                self.snapshots[path]={'sha256':m.original.prior.original.BOOTSTRAP_SHA}
        reader=Reader();args=m.Worker.__new__(m.Worker)._fixed_command(reader)
        inner=json.loads(args[-1])
        self.assertEqual(inner[-1],'-BlockSourceAfterCurrentSession');self.assertEqual(inner[-2],str(reader.root/m.TARGET))
        self.assertNotIn('-Command',inner);self.assertEqual(args[0],sys.executable);self.assertTrue(m.SOURCES<=reader.snapshots.keys())
    def test_original_envelope_not_overridden(self):
        self.assertIs(m.Worker.start_fixed_worker,m.original.FixedWorker.start_fixed_worker)
        self.assertNotIn(m.original.TARGET,m.SOURCES)
        self.assertIn('implementation/p09/tools/block-bookmark-source646-document.ps1',m.SOURCES)
    def test_success_notice_is_not_cleanup_or_authority(self):
        n=m.source_result_notice(result());self.assertFalse(n['worker_failed_or_uncertain'])
        self.assertFalse(n['cleanup_confirmed']);self.assertFalse(n['native_execution_authorized']);self.assertTrue(n['rerun_forbidden'])
    def test_unknown_and_partial_results_not_success(self):
        for key,value in [('state','unknown'),('completed_callback_cases',0),('completed_callback_cases',True),
            ('retained_live_or_uncertain_owners',1),('native_execution_authorized',True),('error_code','P09_XREF_BIND_BLOCK670_FAILED')]:
            v=result();v[key]=value;self.assertTrue(m.source_result_notice(v)['worker_failed_or_uncertain'])
    def test_safe_diagnostics_only(self):
        v=result();v.update(error_code='PRIVATE TEXT',case_failure={'phase':'PRIVATE PATH'})
        raw=json.dumps(m.source_result_notice(v));self.assertNotIn('PRIVATE',raw)

    def test_typed_port_source_and_fresh_worker_namespace(self):
        self.assertIn('implementation/p09/tools/block-bookmark-origin668.ps1',m.SOURCES)
        self.assertIn('implementation/p09/tools/block-bookmark-selection658.ps1',m.SOURCES)
        self.assertIn('670',m.TARGET)
        self.assertNotIn('implementation/p09/tools/run-block-bookmark-source648-worker.ps1',m.SOURCES)
    def test_safe_call_fault_preserves_site_kind_hresult_without_raw_values(self):
        d=dict(schema_version='hwpx-agent.private.block-bookmark668-call-failure/v1',call_site='put_type',
            range_index=1,exception_kind='COMException',hresult='0x80004005',rerun_forbidden=True)
        v=result();v['case_failure']=dict(phase='create_bookmarks',parameter_call_failure=d)
        self.assertEqual(m.source_result_notice(v)['parameter_call_failure'],d)
        for key,value in [('call_site','PRIVATE TEXT'),('range_index',True),('range_index',9),('exception_kind','PRIVATE'),
            ('hresult','PRIVATE'),('rerun_forbidden',False),('message','SECRET')]:
            changed=dict(d);changed[key]=value
            self.assertIsNone(m.safe_call_failure(changed))
    def test_wrong_result_profile_rejected(self):
        v=result();v['schema_version']='old'
        with self.assertRaises(ValueError):m.source_result_notice(v)

if __name__=='__main__':
    result_=unittest.TestResult();unittest.defaultTestLoader.loadTestsFromTestCase(Tests).run(result_)
    print(json.dumps(dict(run=result_.testsRun,errors=len(result_.errors),failures=len(result_.failures),skipped=len(result_.skipped),
        failed_tests=[t.id().rsplit('.',1)[-1]for t,_ in result_.errors+result_.failures],actual_native_started=False)))
    raise SystemExit(0 if result_.wasSuccessful()else 2)



