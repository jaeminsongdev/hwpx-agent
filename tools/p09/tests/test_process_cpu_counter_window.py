"""P310 pure bounded counter contracts; no real Native/product/WMI work."""
import copy
import unittest
import process_cpu_counter_window as m

def fixture():
    def snap(t):
        rows=[]
        for pid,name,cpu in ((0,'Idle',120000000+t*12),(0,'_Total',160000000+t*16),
            (20,'MsMpEng',20000000+t*2),(21,'git',0),(22,'python',10000000+t)):
            rows.append(dict(pid=pid,name=name,creating_pid=1 if pid else 0,raw_elapsed_token='100',
                cpu_100ns=str(cpu),sys_100ns=str(200000000+t),frequency_sys100ns='10000000',
                private_bytes='4000',working_set_bytes='5000'))
        return dict(schema_version=m.SCHEMA,counter_class='Win32_PerfRawData_PerfProc_Process',
            query_started_utc='2026-10-09T10:00:00.0000000Z',query_finished_utc='2026-10-09T10:00:00.1000000Z',
            operation_timeout_seconds=5,rows=rows)
    return snap(0),snap(10000000)

class Tests(unittest.TestCase):
    def setUp(self):self.a,self.b=fixture()
    def result(self):return m.window(self.a,self.b,16)
    def reject(self):
        with self.assertRaises(ValueError):self.result()
    def row(self):return self.b['rows'][2]
    def test_exact_delta_not_cumulative(self):
        r=self.result();self.assertEqual(r['top8'][0]['machine_CPU_percent'],12.5);self.assertEqual(r['host_busy_from_idle_percent'],25)
    def test_uint64_precision_preserved(self):
        for x in self.a['rows']:x['sys_100ns']='134360120319896469'
        for x in self.b['rows']:x['sys_100ns']='134360120329896469'
        self.assertEqual(self.result()['top8'][0]['machine_CPU_percent'],12.5)
    def test_raw_float_rejected(self):self.row()['cpu_100ns']=1.1;self.reject()
    def test_raw_int_rejected(self):self.row()['cpu_100ns']=100;self.reject()
    def test_leading_zero_rejected(self):self.row()['cpu_100ns']='01';self.reject()
    def test_uint64_overflow(self):self.row()['cpu_100ns']=str(2**64);self.reject()
    def test_negative_counter(self):self.row()['cpu_100ns']='-1';self.reject()
    def test_counter_reset(self):self.row()['cpu_100ns']='0';self.reject()
    def test_same_timestamp(self):self.row()['sys_100ns']=self.a['rows'][2]['sys_100ns'];self.reject()
    def test_wrong_frequency(self):self.row()['frequency_sys100ns']='1';self.reject()
    def test_pid_reuse_skipped(self):
        self.row()['raw_elapsed_token']='200';r=self.result();self.assertEqual(r['identity_drift_skipped'],1);self.assertFalse(any(x['pid']==20 for x in r['watched']))
    def test_instance_drift_skipped(self):self.row()['name']='MsMpEng#1';self.assertEqual(self.result()['identity_drift_skipped'],1)
    def test_parent_drift_skipped(self):self.row()['creating_pid']=2;self.assertEqual(self.result()['identity_drift_skipped'],1)
    def test_disappeared_process(self):self.b['rows'].pop();self.assertEqual(self.result()['disappeared_count'],1)
    def test_new_process(self):
        x=copy.deepcopy(self.row());x.update(pid=44,name='other');self.b['rows'].append(x);self.assertEqual(self.result()['new_count'],1)
    def test_unknown_command_field(self):self.row()['CommandLine']='PRIVATE';self.reject()
    def test_path_as_instance(self):self.row()['name']='C:/private.exe';self.reject()
    def test_duplicate_pid(self):self.b['rows'].append(copy.deepcopy(self.row()));self.reject()
    def test_missing_idle(self):self.b['rows'].pop(0);self.reject()
    def test_no_processor_guess(self):
        with self.assertRaises(ValueError):m.window(self.a,self.b,None)
    def test_multiple_processor_groups_rejected(self):
        with self.assertRaises(ValueError):m.window(self.a,self.b,128)
    def test_wrong_schema(self):self.b['schema_version']='OTHER';self.reject()
    def test_no_CPU_clamp(self):self.row()['cpu_100ns']='1000000000';self.reject()
    def test_no_cause_or_runtime_claim(self):
        r=self.result();self.assertFalse(r['CPU_cause_or_PC_freeze_resolution_established']);self.assertFalse(r['source_scope_or_guard_changed'])
if __name__=='__main__':unittest.main()
