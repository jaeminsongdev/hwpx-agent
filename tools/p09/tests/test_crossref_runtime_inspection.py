"""Actual closed host/batch/protocol/parent-observation composition, no native."""
import ast
import io
import json
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools/p09'))
import accept_case112_current_epoch as a
import crossref_runtime_inspection as runtime
import crossref_owned_host_process as host


class RuntimeConnectionContracts(unittest.TestCase):
    actual=[]

    def test_01_unknown_reply_probe_cannot_supply_native_provider(self):
        for value in ('native','execute',True,None,'positive_transport_guard;execute'):
            with self.assertRaisesRegex(ValueError,'FIXED_READONLY_PROBE'):
                runtime.inspect_connection(None,None,value)

    def test_02_closed_scope_rejects_admission_and_keeps_finish_unguarded(self):
        calls=[];scope=runtime.ClosedInspectionScope(lambda:calls.append('sample'),'negative')
        with self.assertRaisesRegex(ValueError,'STOP_XREF_NATIVE_STARTUP_UNQUALIFIED'):
            scope.checkpoint(1,'prepare_slot')
        with self.assertRaisesRegex(ValueError,'STOP_XREF_NATIVE_PROVIDER_ABSENT'):
            scope.admit_owner(1,{},1)
        scope.check=lambda:(_ for _ in ()).throw(ValueError('STOP_TEST'))
        scope.finish(1,'failed')
        self.assertEqual(calls,['sample']);self.assertEqual(scope.finish_calls,1)
        self.assertEqual(scope.profiles,[]);self.assertIsNone(scope.current)

    def test_03_worker_and_supervisor_have_no_native_launcher_or_force_kill(self):
        source=(ROOT/host.CONNECTION).read_text(encoding='utf-8')
        self.assertIn('param([switch]$InspectConnectionOnly)',source)
        self.assertIn('class P09InspectionDenyReader',source)
        self.assertIn('INSPECTION_REQUIRES_DENIAL',source)
        self.assertIn('Invoke-P09XrefFixedHostBatch $channel $lease $batch',source)
        for bad in ('-ComObject ', 'New-P58Owner ', '.SaveAs(', '.Quit(', 'New-Item '):self.assertNotIn(bad,source)
        tree=ast.parse((ROOT/'tools/p09/crossref_runtime_inspection.py').read_text(encoding='utf-8'))
        calls=[n.func.attr if isinstance(n.func,ast.Attribute) else n.func.id for n in ast.walk(tree)
            if isinstance(n,ast.Call) and isinstance(n.func,(ast.Name,ast.Attribute))]
        self.assertFalse(set(calls) & {'TerminateJobObject','TerminateProcess','kill','system'})

    def _actual(self,probe):
        # The enclosing original owned-Job supervisor is the sole resource sampler.
        # This test child supplies no additional sampler; actual Windows limits are read back.
        guard=NS(windows=host.c.Windows(),check=lambda:None)
        reader=a.AcceptanceReader(ROOT,lambda:None)
        result=runtime.inspect_connection(guard,reader,probe)
        self.actual.append(result)
        self.assertEqual(result['request_count'],2)
        self.assertTrue(result['host_profile']['host_worker_one_percent_installed'] and
            result['host_profile']['cleanup_confirmed'] and result['io_threads_joined'])
        self.assertEqual(len(result['parent_records']),1)
        self.assertEqual(result['parent_records'][0]['finish_status'],'failed')
        self.assertEqual(result['parent_records'][0]['owner_admissions'],[])
        self.assertEqual(result['parent_records'][0]['artifacts'],[])
        self.assertEqual(result['worker_result']['batch']['completed_callback_cases'],0)
        self.assertFalse(result['actual_Hangul_or_COM'] or result['native_provenance_qualified'])
        self.assertTrue(all(row['state']=='NOT_RUN' for row in result['actual_fixed_inventory']['cases']))
        reader.finish()
        self.assertEqual(reader.final_fresh_hashes,len(reader.snapshots))
        result['closing_source_reads']=dict(fresh=len(reader.snapshots),final=reader.final_fresh_hashes)
        return result

    def test_04_actual_negative_policy_flows_through_real_fixed_batch_and_parent_records(self):
        result=self._actual('negative')
        self.assertFalse(result['worker_result']['positive_or_invalid_reply_blocked'])
        self.assertEqual(result['protocol']['primary_error'],'STOP_XREF_NATIVE_STARTUP_UNQUALIFIED')

    def test_05_actual_positive_parent_ack_is_blocked_inside_worker_before_slot(self):
        result=self._actual('positive_transport_guard')
        self.assertTrue(result['worker_result']['positive_or_invalid_reply_blocked'])
        self.assertEqual(result['protocol']['primary_error'],'XREF_HOST_WORKER_REPORTED_FAILURE')


if __name__=='__main__':
    result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(RuntimeConnectionContracts))
    failures=[dict(test=t.id(),last_line=trace.splitlines()[-1][:160]) for t,trace in result.errors+result.failures]
    print(json.dumps(dict(state='five_actual_closed_runtime_connection_contracts_pass_not_native' if result.wasSuccessful()
        else 'closed_runtime_connection_contract_failed',passed=result.testsRun-len(failures),failed=len(failures),declared=result.testsRun,
        failures=failures,actual_connections=RuntimeConnectionContracts.actual,prior_host_and_batch_suites_reexecuted=False,
        actual_Hangul_or_COM=False,native_execution_authorized=False,native_provenance_qualified=False,
        complete_native_guard_integration_qualified=False,p09_complete=False)))
    raise SystemExit(0 if result.wasSuccessful() else 2)
