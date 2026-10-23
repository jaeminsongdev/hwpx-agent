"""Only the new readonly pre-COM prefix role; no prior host/channel suite replay."""
import io
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools/p09'))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import crossref_owned_host_process as host
import accept_case112_current_epoch as a
from bounded_process_progress import BoundedProcessCapture
from test_crossref_owned_host_process import drain_readonly


class PreComPrefixContracts(unittest.TestCase):
    actual=[]

    def test_01_unknown_native_or_arbitrary_role_rejected_before_reader(self):
        for role in ('native','execute','../outside',True,None,'pre_com_prefix;execute'):
            with self.assertRaisesRegex(ValueError,'FIXED_READONLY_ROLE'):
                host.readonly_command(None,role=role)

    def test_02_prefix_source_has_no_native_owner_or_document_invocation(self):
        text=(ROOT/host.PREFIX).read_text(encoding='utf-8')
        self.assertIn('param([switch]$InspectOnly)',text)
        self.assertIn('Initialize-P09XrefFrozenWindowBridge',text)
        for code in ('New-P58Owner ', 'Open-P58Document ', 'Invoke-P09XrefNativeCaseWorkflow ',
                '-ComObject ', '.SaveAs(', '.Quit(', 'New-Item ', 'SetValue('):
            self.assertNotIn(code,text)
        self.assertIn("$classes.OpenSubKey('HWPFrame.HwpObject.2\\CLSID',$false)",text)

    def test_03_actual_pre_com_prefix_in_one_percent_host_worker(self):
        windows=host.c.Windows();process=host.OwnedHostProcess(windows,lambda:None)
        reader=a.AcceptanceReader(ROOT,lambda:None);capture=None
        try:
            process.start_waiting(reader,role='pre_com_prefix')
            process.signal_readonly_target()
            capture=BoundedProcessCapture(process,output_limit=8192,parse_markers=False)
            output,error,peak=drain_readonly(process,capture,60)
            result=json.loads(output)
            self.actual.append(dict(exit_code=process.returncode,stderr_bytes=len(error.encode()),result=result,
                maximum_active_owned_processes=peak,profile=process.profile))
            self.assertEqual(error,'')
            self.assertEqual(process.returncode,0)
            self.assertEqual(result['state'],'pre_com_prefix_loaded_not_native_ready')
            self.assertTrue(result['x86_sta'] and result['window_type_loaded'] and
                result['registry_readonly_bindings_match'] and result['hwp_inventory_preserved'])
            self.assertEqual(result['hwp_before_count'],result['hwp_after_count'])
            self.assertFalse(result['actual_Hangul_or_COM'] or result['native_execution_authorized'] or
                result['native_directories_created'] or result['window_native_method_invoked'])
            self.assertEqual(len(result['installed_pins']),4)
            reader.finish()
            self.assertEqual(reader.final_fresh_hashes,len(reader.snapshots))
            process.profile['qualification_source_reads']=dict(fresh=len(reader.snapshots),final=reader.final_fresh_hashes)
        finally:
            if capture is not None:capture.close()
            process.close()


if __name__=='__main__':
    result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(PreComPrefixContracts))
    failures=[dict(test=t.id(),last_line=trace.splitlines()[-1][:160]) for t,trace in result.errors+result.failures]
    print(json.dumps(dict(state='three_pre_com_prefix_contracts_pass_not_native' if result.wasSuccessful()
        else 'pre_com_prefix_contract_failed',passed=result.testsRun-len(failures),failed=len(failures),declared=result.testsRun,
        failures=failures,actual_prefix_children=PreComPrefixContracts.actual,prior_host_and_channel_tests_reexecuted=False,
        actual_Hangul_or_COM=False,native_execution_authorized=False,complete_native_guard_integration_qualified=False,
        p09_complete=False)))
    raise SystemExit(0 if result.wasSuccessful() else 2)
