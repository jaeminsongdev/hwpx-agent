import copy
import io
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import probe_host_cpu_observer as s


def payload():
    snap=dict(processor_count=16,cpu_instance_count=3,pid_instance_count=3,stable_candidate_count=1,
        unavailable_instances=0,unstable_instances=0,causal_attribution=False,
        top=[dict(pid=50,role='other',owned=False,processor_time_raw_percent=800.0,machine_cpu_percent=50.0)])
    return dict(schema_version='hwpx-agent.p09-host-cpu-observer-probe/v1',state='PASS_TWO_NATIVE_SAMPLES_ONLY',
        worker_pid=60,query_cleanup_confirmed=True,query_count=1,
        samples=[dict(sequence=i+1,observed_at=f'2026-10-07T01:00:0{i}+00:00',collect_seconds=.05,observation=copy.deepcopy(snap)) for i in range(2)],
        causal_attribution=False,raw_process_names_saved=False,commands_paths_saved=False)


class ProbeHostCPUObserverTests(unittest.TestCase):
    def test_closed_run(self):
        self.assertEqual(s.task_for(1),'p153-host-cpu-observer-r01')
        for run in (True,0,100,'1'):
            with self.assertRaises(ValueError):s.task_for(run)
    def test_exact_redacted_output(self):self.assertIs(s.validate_payload(row:=payload()),row)
    def test_extra_private_text_rejected(self):
        row=payload();row['cmdline']='private'
        with self.assertRaises(ValueError):s.validate_payload(row)
        row=payload();row['samples'][0]['observation']['top'][0]['path']='private'
        with self.assertRaises(ValueError):s.validate_payload(row)
    def test_no_partial_summary_or_failed_cleanup(self):
        for mutation in (lambda r:r['samples'].pop(),lambda r:r.update(query_cleanup_confirmed=False),lambda r:r.update(causal_attribution=True)):
            row=payload();mutation(row)
            with self.assertRaises(ValueError):s.validate_payload(row)
    def test_normalization_no_clamp_or_nan(self):
        for value in (100.,float('nan')):
            row=payload();row['samples'][0]['observation']['top'][0]['machine_cpu_percent']=value
            with self.assertRaises(ValueError):s.validate_payload(row)
    def test_GO_required_before_native(self):
        with patch.object(s.sys,'stdin',io.StringIO('wrong\n')),patch.object(s.observer,'Observer') as api:
            with self.assertRaises(ValueError):s.worker(s.task_for(1))
            api.assert_not_called()
    def test_job_required_before_native(self):
        class Kernel:
            def GetCurrentProcess(self):return 1
            def IsProcessInJob(self,p,j,out):out._obj.value=False;return True
        with patch.object(s.sys,'stdin',io.StringIO('P149_GO\n')), \
                patch.object(s.c,'Windows',return_value=SimpleNamespace(k=Kernel())),patch.object(s.observer,'Observer') as api:
            with self.assertRaises(ValueError):s.worker(s.task_for(1))
            api.assert_not_called()
    def test_unique_timestamp_and_instance_counts(self):
        row=payload();row['samples'][1]['observed_at']=row['samples'][0]['observed_at']
        with self.assertRaises(ValueError):s.validate_payload(row)
        row=payload();row['samples'][0]['observation']['stable_candidate_count']=9
        with self.assertRaises(ValueError):s.validate_payload(row)


if __name__=='__main__':unittest.main()
