import io
import json
import math
import unittest
from unittest.mock import patch
import run_p340_stop_review_attribution as m


def pin(name='p340-light-review-run076.v1.json'):
    return dict(path='implementation/p09/evidence/locked-r07/'+name,
        bytes=123,sha256='a'*64)


def process_snapshot(system=(100,200,100),cpu_time=20,stamp=1.0):
    return dict(system=system,rows={17:(10,cpu_time,'git.exe')},
        counts={'git.exe':1,'OTHER':2},inaccessible=1,scan_seconds=.01,time=stamp)


def sample_row():
    return dict(system_cpu_percent=25.0,total_system_delta_100ns=40,
        top_cpu_groups=[dict(label='git.exe',cpu_delta_100ns=10,matched_processes=1,machine_cpu_percent=25.0)],
        process_counts={'git.exe':1,'OTHER':2},inaccessible_processes=1,
        newly_seen_or_reused_PIDs=0,counter_reset_processes=0,no_longer_readable_PIDs=0,
        scan_seconds=.01,snapshot_interval_seconds=1.0,CPU_samples_not_atomic=True,
        all_system_CPU_attributed=False,
        exited_short_lived_protected_processes_and_kernel_work_may_be_missing=True,
        CPU_cause_or_PC_freeze_resolution_established=False,
        time_utc='2026-10-11T03:00:00+00:00',host_system_cpu_percent=25.0,
        available_ram_percent=50.0,commit_used_percent=30.0,scanner_child_alive=True)


class FakeWindows:
    def __init__(self,row):self.row=row
    def sample(self):return dict(self.row)


class FakeProcessCPU:
    def __init__(self,rows):self.rows=list(rows)
    def snapshot(self):
        row=self.rows.pop(0)
        if isinstance(row,Exception):raise row
        return row


class P340StopReviewAttributionTests(unittest.TestCase):
    def test_scanner_capture_uses_closable_eof_stdin_pipe(self):
        with patch.object(m.subprocess,'Popen') as popen:
            m.launch_scanner(['scanner.py'])
        self.assertIs(popen.call_args.kwargs['stdin'],m.subprocess.PIPE)
        self.assertIs(popen.call_args.kwargs['stdout'],m.subprocess.PIPE)
        self.assertIs(popen.call_args.kwargs['stderr'],m.subprocess.PIPE)

    def test_task_ids_are_closed(self):
        self.assertEqual(m.task_for(1,104),'p340-stop-review-attribution-r001-scan104')
        for args in ((True,1),(0,1),(1000,1),(1,1000)):
            with self.assertRaises(ValueError):m.task_for(*args)

    def test_stop_pins_accept_only_unique_scoped_literals(self):
        rows=m.validate_stop_pins([pin(),pin('p340-light-run083.v1.json')])
        self.assertEqual(len(rows),2)
        for rows in ([pin(),pin()], [dict(pin(),sha256='BAD')],
                [dict(pin(),path='C:/private.json')], []):
            with self.assertRaises(ValueError):m.validate_stop_pins(rows)

    def test_process_sample_closed_labels_and_no_cause_claim(self):
        self.assertIs(m.validate_process_sample(sample_row())['CPU_cause_or_PC_freeze_resolution_established'],False)
        row=sample_row();row['process_counts']['secret-client.exe']=1
        with self.assertRaises(ValueError):m.validate_process_sample(row)
        row=sample_row();row['command_line']='private-token'
        with self.assertRaises(ValueError):m.validate_process_sample(row)

    def test_controller_emits_interval_only_after_one_second(self):
        ticks=[0.0]
        controller=m.AttributionController(FakeWindows(dict(system_cpu_percent=25.0,
            available_ram_percent=50.0,commit_used_percent=30.0)),
            FakeProcessCPU([process_snapshot(stamp=0),process_snapshot(system=(110,230,110),cpu_time=30,stamp=1.1)]),
            clock=lambda:ticks[0],sleep=lambda _:None)
        controller.baseline();ticks[0]=.5;controller.sample(True)
        self.assertEqual(controller.samples,[])
        ticks[0]=1.0;controller.sample(True)
        self.assertEqual(len(controller.samples),1)
        self.assertEqual(controller.samples[0]['scanner_child_alive'],True)
        self.assertEqual(controller.summary()['completed_intervals'],1)

    def test_controller_logs_bounded_jsonl_and_resources(self):
        ticks=[0.0];stream=io.StringIO()
        controller=m.AttributionController(FakeWindows(dict(system_cpu_percent=44.0,
            available_ram_percent=49.0,commit_used_percent=31.0)),
            FakeProcessCPU([process_snapshot(stamp=0),process_snapshot(system=(110,230,110),cpu_time=30,stamp=1.1)]),
            clock=lambda:ticks[0],sleep=lambda _:None)
        controller.baseline();ticks[0]=1.0;controller.sample(False,stream)
        row=json.loads(stream.getvalue())
        self.assertEqual(row['host_system_cpu_percent'],44.0)
        self.assertEqual(row['available_ram_percent'],49.0)
        self.assertFalse(row['scanner_child_alive'])

    def test_observer_failure_is_redacted_not_zero_cpu(self):
        ticks=[0.0]
        controller=m.AttributionController(FakeWindows(dict(system_cpu_percent=30.0,
            available_ram_percent=50.0,commit_used_percent=30.0)),
            FakeProcessCPU([process_snapshot(stamp=0),ValueError('private command line')]),
            clock=lambda:ticks[0],sleep=lambda _:None)
        controller.baseline();ticks[0]=1.0;controller.sample(True)
        self.assertEqual(controller.samples,[])
        self.assertEqual(controller.observer_error,'CPU_ATTRIBUTION_OBSERVER_FAILURE')
        self.assertNotIn('private',str(controller.summary()))

    def test_observer_failure_keeps_only_closed_internal_code(self):
        ticks=[0.0]
        controller=m.AttributionController(FakeWindows(dict(system_cpu_percent=30.0,
            available_ram_percent=50.0,commit_used_percent=30.0)),
            FakeProcessCPU([process_snapshot(stamp=0),ValueError('CPU_ATTRIBUTION_PROCESS_LIMIT')]),
            clock=lambda:ticks[0],sleep=lambda _:None)
        controller.baseline();ticks[0]=1.0;controller.sample(True)
        self.assertEqual(controller.observer_error,'CPU_ATTRIBUTION_PROCESS_LIMIT')
        self.assertEqual(controller.samples,[])

    def test_host_stop_backstop_is_separate_from_scanner_state(self):
        ticks=[0.0];cpu_rows=[process_snapshot(stamp=0)];
        for i in range(1,7):cpu_rows.append(process_snapshot(system=(100+i,200+i,100+i),cpu_time=20+i,stamp=float(i)))
        controller=m.AttributionController(FakeWindows(dict(system_cpu_percent=99.0,
            available_ram_percent=50.0,commit_used_percent=30.0)),
            FakeProcessCPU(cpu_rows),clock=lambda:ticks[0],sleep=lambda _:None)
        controller.baseline()
        for i in range(1,7):ticks[0]=float(i);controller.sample(True)
        self.assertEqual(controller.stop_reason,'STOP_CONTROLLER_SUSTAINED_SYSTEM_CPU')
        self.assertFalse(controller.summary()['CPU_cause_or_PC_freeze_resolution_established'])

    def test_p340_receipt_pin_reader_preserves_only_closed_fields(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as root:
            target=Path(root)/'p340.json'
            target.write_text(json.dumps(dict(schema_version='hwpx-agent.p09-preserved106-fixed-runtime-queue/v24',
                state='FAILED_NOT_ACCEPTED',error_code='STOP_SUSTAINED_SYSTEM_CPU',
                resource_stop_reason='STOP_SUSTAINED_SYSTEM_CPU')),encoding='utf-8')
            expected=dict(path='p340.json',bytes=target.stat().st_size,
                sha256=__import__('hashlib').sha256(target.read_bytes()).hexdigest())
            with patch.object(m,'ROOT',Path(root)):
                self.assertEqual(m.scanner_result(expected),dict(state='FAILED_NOT_ACCEPTED',
                    error_code='STOP_SUSTAINED_SYSTEM_CPU',resource_stop_reason='STOP_SUSTAINED_SYSTEM_CPU'))
                changed=dict(expected,sha256='0'*64)
                self.assertEqual(m.scanner_result(changed),dict(state='UNREADABLE_OR_INVALID',
                    error_code=None,resource_stop_reason=None))


if __name__=='__main__':unittest.main()
