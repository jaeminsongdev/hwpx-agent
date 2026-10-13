"""P340 stop-review wrapper with a separate, bounded process-CPU sidecar.

The P340 v24 verifier remains unchanged and keeps its own-process-only contract.
This controller samples closed process-name groups while the exact P340 child runs.
It never stores raw process names, command lines, paths, or tool output.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import time

import conservative_maintenance as resources
from bounded_process_progress import BoundedProcessCapture
import process_cpu_attribution as cpu

ROOT = resources.ROOT
SELF = 'tools/p09/run_p340_stop_review_attribution.py'
TEST = 'tools/p09/tests/test_p340_stop_review_attribution.py'
SCANNER = 'tools/p09/resume_preserved106_queue_runtime.py'
SCANNER_TEST = 'tools/p09/tests/test_preserved106_queue_runtime.py'
FILES = (SELF, TEST, 'tools/p09/process_cpu_attribution.py',
    'tools/p09/tests/test_process_cpu_attribution.py',
    'tools/p09/conservative_maintenance.py', 'tools/p09/bounded_process_progress.py',
    'tools/p09/audit_evidence_io.py', 'tools/p09/observe_shared_metadata_recheck.py',
    'tools/p09/sync_shared_resumable_r07_progress.py', SCANNER, SCANNER_TEST)
STOP_REVIEW_PASS = 'PASS_PRESERVED106_PRE_PRODUCT_STOP_REVIEW_NOT_GO'
MAX_SAMPLES = 1800
MAX_SECONDS = 1500
SAMPLE_SECONDS = 0.5
BACKSTOP_CPU_PERCENT = 98
BACKSTOP_CPU_WINDOWS = 6
BACKSTOP_RAM_PERCENT = 8
BACKSTOP_COMMIT_PERCENT = 95
STOP_ROOT = re.compile(r'p340-(?:case-[0-9]{3}|admission|light|light-review)-run[0-9]{3}\.v1\.json\Z')
ERROR_CODE = re.compile(r'[A-Z][A-Z0-9_]{0,119}\Z')


def require(ok, code):
    if not ok:
        raise ValueError('P340_ATTRIBUTION_' + code)


def task_for(observer_run, scan_run):
    require(type(observer_run) is int and 1 <= observer_run <= 999
        and type(scan_run) is int and 1 <= scan_run <= 999, 'RUN_BOUNDS')
    return f'p340-stop-review-attribution-r{observer_run:03}-scan{scan_run:03}'


def validate_stop_pins(rows):
    require(type(rows) is list and 1 <= len(rows) <= 8, 'STOP_PIN_COUNT')
    require(all(type(row) is dict and set(row) == {'path', 'bytes', 'sha256'}
        and isinstance(row['path'], str) and row['path'].startswith('implementation/p09/evidence/locked-r07/')
        and STOP_ROOT.fullmatch(row['path'].rsplit('/', 1)[-1])
        and type(row['bytes']) is int and 0 < row['bytes'] <= 16 * 1024 * 1024
        and isinstance(row['sha256'], str) and re.fullmatch(r'[0-9a-f]{64}', row['sha256'])
        for row in rows), 'STOP_PIN_SCOPE')
    require(len({row['path'] for row in rows}) == len(rows), 'STOP_PIN_UNIQUE')
    return [dict(row) for row in rows]


def fresh_pins(checkpoint=None):
    reader = resources.AuditEvidenceReader(ROOT, (lambda: None) if checkpoint is None else checkpoint)
    return [reader.pin(path) for path in FILES]


def validate_process_sample(row):
    original = ('system_cpu_percent', 'total_system_delta_100ns', 'top_cpu_groups', 'process_counts',
        'inaccessible_processes', 'newly_seen_or_reused_PIDs', 'counter_reset_processes',
        'no_longer_readable_PIDs', 'scan_seconds', 'snapshot_interval_seconds',
        'CPU_samples_not_atomic', 'all_system_CPU_attributed',
        'exited_short_lived_protected_processes_and_kernel_work_may_be_missing',
        'CPU_cause_or_PC_freeze_resolution_established')
    require(type(row) is dict and set(original).issubset(row), 'PROCESS_SAMPLE_SHAPE')
    require(set(row) == set(original) | {'time_utc', 'host_system_cpu_percent', 'available_ram_percent',
        'commit_used_percent', 'scanner_child_alive'}, 'PROCESS_SAMPLE_CLOSED_FIELDS')
    require(all(type(row[name]) in (int, float) and not isinstance(row[name], bool)
        and math.isfinite(row[name]) and row[name] >= 0 for name in (
            'system_cpu_percent', 'host_system_cpu_percent', 'available_ram_percent',
            'commit_used_percent', 'scan_seconds', 'snapshot_interval_seconds')),
        'PROCESS_SAMPLE_NUMBERS')
    require(type(row['total_system_delta_100ns']) is int and row['total_system_delta_100ns'] > 0
        and 0 < row['snapshot_interval_seconds'] and type(row['scanner_child_alive']) is bool,
        'PROCESS_SAMPLE_INTERVAL')
    require(row['CPU_samples_not_atomic'] is True and row['all_system_CPU_attributed'] is False
        and row['exited_short_lived_protected_processes_and_kernel_work_may_be_missing'] is True
        and row['CPU_cause_or_PC_freeze_resolution_established'] is False,
        'PROCESS_SAMPLE_NO_CAUSE_OVERCLAIM')
    require(isinstance(row['time_utc'], str) and len(row['time_utc']) <= 40, 'PROCESS_SAMPLE_TIMESTAMP')
    require(type(row['process_counts']) is dict and len(row['process_counts']) <= len(cpu.LABEL_VALUES)
        and all(name in cpu.LABEL_VALUES and type(count) is int and 0 <= count <= cpu.MAX_PROCESSES
            for name, count in row['process_counts'].items()), 'PROCESS_SAMPLE_CLOSED_LABELS')
    groups = row['top_cpu_groups']
    require(type(groups) is list and len(groups) <= cpu.TOP, 'PROCESS_SAMPLE_TOP_BOUND')
    for group in groups:
        require(type(group) is dict and set(group) == {'label', 'cpu_delta_100ns', 'matched_processes', 'machine_cpu_percent'}
            and group['label'] in cpu.LABEL_VALUES and type(group['cpu_delta_100ns']) is int
            and group['cpu_delta_100ns'] >= 0 and type(group['matched_processes']) is int
            and 0 <= group['matched_processes'] <= cpu.MAX_PROCESSES
            and type(group['machine_cpu_percent']) in (int, float)
            and math.isfinite(group['machine_cpu_percent']) and group['machine_cpu_percent'] >= 0,
            'PROCESS_SAMPLE_GROUP_SCOPE')
    return row


class AttributionController:
    """Use one low-priority controller loop; no sampler thread or WMI query."""
    def __init__(self, windows=None, process_cpu=None, clock=time.monotonic, sleep=time.sleep):
        self.windows = resources.Windows() if windows is None else windows
        self.process_cpu = cpu.ProcessCPU(self.windows.k, self.windows.times) if process_cpu is None else process_cpu
        self.clock = clock
        self.sleep = sleep
        self.samples = []
        self.observer_error = None
        self.previous = None
        self.next_process_sample = 0.0
        self.hot_cpu_windows = 0
        self.low_memory_windows = 0
        self.stop_reason = None

    def baseline(self):
        self.previous = self.process_cpu.snapshot()
        self.next_process_sample = self.clock() + 1.0

    def sample(self, child_alive, sample_stream=None):
        host = self.windows.sample()
        now = self.clock()
        self.hot_cpu_windows = self.hot_cpu_windows + 1 if host['system_cpu_percent'] >= BACKSTOP_CPU_PERCENT else 0
        self.low_memory_windows = self.low_memory_windows + 1 if (
            host['available_ram_percent'] < BACKSTOP_RAM_PERCENT
            or host['commit_used_percent'] >= BACKSTOP_COMMIT_PERCENT) else 0
        if self.hot_cpu_windows >= BACKSTOP_CPU_WINDOWS:
            self.stop_reason = 'STOP_CONTROLLER_SUSTAINED_SYSTEM_CPU'
        elif self.low_memory_windows >= 2:
            self.stop_reason = 'STOP_CONTROLLER_RAM_OR_COMMIT'
        if self.observer_error is None and self.previous is not None and now >= self.next_process_sample:
            try:
                current = self.process_cpu.snapshot()
                row = cpu.compare(self.previous, current)
                row.update(time_utc=datetime.now(timezone.utc).isoformat(),
                    host_system_cpu_percent=host['system_cpu_percent'],
                    available_ram_percent=host['available_ram_percent'],
                    commit_used_percent=host['commit_used_percent'],
                    scanner_child_alive=bool(child_alive))
                validate_process_sample(row)
                require(len(self.samples) < MAX_SAMPLES, 'SAMPLE_LIMIT')
                self.samples.append(row)
                if sample_stream is not None:
                    sample_stream.write(json.dumps(row, separators=(',', ':'), allow_nan=False) + '\n')
                    sample_stream.flush()
                self.previous = current
                self.next_process_sample = self.clock() + 1.0
            except (ValueError, OSError, AttributeError, TypeError) as error:
                safe_code = str(error) if isinstance(error, ValueError) else ''
                self.observer_error = safe_code if re.fullmatch(r'CPU_ATTRIBUTION_[A-Z0-9_]{1,64}', safe_code) \
                    else 'CPU_ATTRIBUTION_OBSERVER_FAILURE'
        return host

    def summary(self):
        sample_rows = list(self.samples)
        return dict(state='PASS_BOUNDED_PROCESS_CPU_OBSERVATION' if sample_rows and self.observer_error is None
                else 'INCOMPLETE_PROCESS_CPU_OBSERVATION',
            samples=sample_rows, completed_intervals=len(sample_rows),
            observer_error=self.observer_error, controller_stop_reason=self.stop_reason,
            sample_interval_min_seconds=1.0, maximum_processes_per_snapshot=cpu.MAX_PROCESSES,
            maximum_snapshot_seconds=cpu.MAX_SCAN_SECONDS, process_labels=list(sorted(cpu.LABEL_VALUES)),
            raw_process_names_saved=False, command_lines_paths_environments_or_modules_queried=False,
            process_state_changed=False, new_sampler_thread_started=False, all_system_CPU_attributed=False,
            causal_attribution=False, CPU_cause_or_PC_freeze_resolution_established=False)


def scanner_receipt_pin(scan_run):
    path = ROOT / 'implementation/p09/evidence/locked-r07' / f'p340-stop-review-run{scan_run:03}.v1.json'
    if not path.is_file():
        return None
    digest = hashlib.sha256(); size = 0
    with path.open('rb') as stream:
        while chunk := stream.read(65536):
            size += len(chunk)
            require(size <= 16 * 1024 * 1024, 'SCANNER_RECEIPT_BOUND')
            digest.update(chunk)
    return dict(path=path.relative_to(ROOT).as_posix(), bytes=size, sha256=digest.hexdigest())


def scanner_result(pin):
    if pin is None:
        return dict(state='NOT_WRITTEN', error_code=None, resource_stop_reason=None)
    path = ROOT / pin['path']
    try:
        payload = path.read_bytes()
        require(len(payload) <= 16 * 1024 * 1024, 'SCANNER_RECEIPT_BOUND')
        require(len(payload) == pin['bytes'] and hashlib.sha256(payload).hexdigest() == pin['sha256'],
            'SCANNER_RECEIPT_PIN_MISMATCH')
        doc = json.loads(payload.decode('utf-8'))
        require(type(doc) is dict and doc.get('schema_version') == 'hwpx-agent.p09-preserved106-fixed-runtime-queue/v24',
            'SCANNER_RECEIPT_SCHEMA')
        state = doc.get('state') if doc.get('state') in ('FAILED_NOT_ACCEPTED', STOP_REVIEW_PASS) else 'UNRECOGNIZED_STATE'
        error = doc.get('error_code')
        stop = doc.get('resource_stop_reason')
        return dict(state=state, error_code=error if isinstance(error, str) and ERROR_CODE.fullmatch(error) else None,
            resource_stop_reason=stop if isinstance(stop, str) and ERROR_CODE.fullmatch(stop) else None)
    except (OSError, ValueError, KeyError, TypeError):
        return dict(state='UNREADABLE_OR_INVALID', error_code=None, resource_stop_reason=None)


def launch_scanner(args):
    """Provide the EOF pipe expected by BoundedProcessCapture."""
    return subprocess.Popen(args, cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW | subprocess.BELOW_NORMAL_PRIORITY_CLASS)


def run(scan_run, observer_run, stop_pins):
    task_for(observer_run, scan_run); stop_pins = validate_stop_pins(stop_pins)
    receipt_path = ROOT / 'implementation/p09/evidence' / f'p09-p340-stop-review-attribution-run{observer_run:03}.v1.json'
    samples_path = ROOT / 'implementation/p09/evidence' / f'p09-p340-stop-review-attribution-run{observer_run:03}.samples.jsonl'
    scanner_path = ROOT / 'implementation/p09/evidence/locked-r07' / f'p340-stop-review-run{scan_run:03}.v1.json'
    require(not receipt_path.exists() and not samples_path.exists() and not scanner_path.exists(), 'FRESH_OUTPUTS_REQUIRED')
    before = fresh_pins()
    controller = None; process = capture = sample_stream = None
    started = time.monotonic(); exit_code = None; child_output_state = None; cleanup = True
    controller_killed_child = False
    out = dict(schema_version='hwpx-agent.p09-p340-process-cpu-sidecar/v1',
        state='FAILED_NOT_ACCEPTED', product_complete=False, P09_gate='OPEN',
        scanner_child_started=False, scanner_child_replayed=False, actual_product_child_executed=False,
        process_creation_or_command_line_saved=False, raw_logs_saved=False, PC_freeze_resolved=False,
        stop_root_pins=stop_pins, process_cpu_attribution=None, scanner_receipt_pin=None,
        scanner_result=None, source_pins=before)
    try:
        controller = AttributionController()
        controller.baseline()
        sample_stream = samples_path.open('x', encoding='utf-8', newline='\n')
        args = [sys.executable, str(ROOT / SCANNER), '--mode', 'stop-review', '--run', str(scan_run)]
        for pin in stop_pins:
            args.extend(('--stop-root-pin', json.dumps(pin, separators=(',', ':'))))
        process = launch_scanner(args)
        out['scanner_child_started'] = True
        out['scanner_child_pid'] = process.pid
        capture = BoundedProcessCapture(process, output_limit=16384, parse_markers=False)
        out['scanner_child_replayed'] = False
        deadline = started + MAX_SECONDS
        while True:
            if time.monotonic() >= deadline:
                controller.stop_reason = 'STOP_CONTROLLER_DURATION_LIMIT'
                process.kill()
            try:
                output, errors = capture.communicate(timeout=SAMPLE_SECONDS)
                require(errors == '' and len(output.encode('utf-8')) <= 16384, 'SCANNER_OUTPUT_SCOPE')
                try:
                    result_line = output.strip().splitlines()[-1]
                    summary = json.loads(result_line)
                    child_output_state = summary.get('state') if type(summary) is dict else None
                except (ValueError, IndexError, AttributeError):
                    child_output_state = 'UNRECOGNIZED_OUTPUT'
                exit_code = process.returncode
                break
            except subprocess.TimeoutExpired:
                capture.progress()
                host = controller.sample(process.poll() is None, sample_stream)
                if controller.stop_reason is not None and process.poll() is None and not controller_killed_child:
                    # Give P340's own matching resource guard time to write its terminal receipt.
                    if controller.stop_reason == 'STOP_CONTROLLER_DURATION_LIMIT' or controller.hot_cpu_windows >= BACKSTOP_CPU_WINDOWS + 2 \
                            or controller.low_memory_windows >= 4:
                        process.kill();controller_killed_child=True
        require(process.poll() is not None, 'SCANNER_CHILD_STILL_RUNNING')
        exit_code = process.returncode
    except (ValueError, OSError, subprocess.SubprocessError, KeyboardInterrupt) as error:
        code = str(error) if isinstance(error, ValueError) else ''
        out['error_code'] = code if ERROR_CODE.fullmatch(code) else 'CONTROLLER_FAILURE'
    finally:
        if process is not None and process.poll() is None:
            try: process.kill()
            except OSError: cleanup = False
        if process is not None:
            try: process.wait(timeout=5)
            except (OSError, subprocess.SubprocessError): cleanup = False
        if capture is not None:
            try: capture.close()
            except (ValueError, OSError): cleanup = False
        if sample_stream is not None:
            try: sample_stream.close()
            except OSError: cleanup = False
        if controller is not None: out['process_cpu_attribution'] = controller.summary()
        out.update(scanner_child_cleanup_confirmed=cleanup, scanner_exit_code=exit_code,
            scanner_stdout_state=child_output_state, scanner_receipt_pin=scanner_receipt_pin(scan_run),
            elapsed_seconds=round(time.monotonic()-started, 3),
            sample_stream_path=samples_path.relative_to(ROOT).as_posix() if samples_path.exists() else None,
            sample_stream_pin=None, source_closing_exact=False)
        if samples_path.is_file():
            size=samples_path.stat().st_size
            if size <= 16 * 1024 * 1024:
                digest=hashlib.sha256(samples_path.read_bytes()).hexdigest()
                out['sample_stream_pin']=dict(path=samples_path.relative_to(ROOT).as_posix(),bytes=size,sha256=digest)
            else:
                out['error_code']='SAMPLE_STREAM_BOUND'
                out['sample_stream_bound_exceeded']=True
        out['scanner_result']=scanner_result(out['scanner_receipt_pin'])
        try:
            after=fresh_pins();out['source_closing_exact']=before==after;out['source_pins_after']=after
        except (ValueError, OSError):
            out['source_pins_after']=[]
        out['source_closing_exact']=out.get('source_closing_exact') is True
        out['state']='PASS_BOUNDED_ATTRIBUTION_SIDE_CAR_NOT_GATE' if (
            out['process_cpu_attribution'] is not None
            and out['process_cpu_attribution']['state']=='PASS_BOUNDED_PROCESS_CPU_OBSERVATION'
            and cleanup and out['source_closing_exact'] and not out.get('sample_stream_bound_exceeded', False)) else 'FAILED_NOT_ACCEPTED'
        if out['scanner_result']['state'] != STOP_REVIEW_PASS:
            out['state']='STOPPED_NOT_ACCEPTED'
        out['resource_stop_reason']=controller.stop_reason if controller else None
        out['startup_policy']=dict(observer_priority='BelowNormal',observer_single_logical_CPU=True,
            process_snapshot_seconds_max=cpu.MAX_SCAN_SECONDS,interval_seconds_min=1.0,
            original_scanner_resource_guards_unchanged=True,controller_cpu_backstop_windows=BACKSTOP_CPU_WINDOWS)
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        with receipt_path.open('x', encoding='utf-8') as stream: json.dump(out,stream,ensure_ascii=False,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','error_code','resource_stop_reason','scanner_exit_code',
            'scanner_result','elapsed_seconds','scanner_child_cleanup_confirmed')},ensure_ascii=False))
    return 0 if out['state']=='PASS_BOUNDED_ATTRIBUTION_SIDE_CAR_NOT_GATE' else 2


def main(argv=None):
    parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=('actual',),required=True)
    parser.add_argument('--scan-run',type=int,required=True);parser.add_argument('--observer-run',type=int,required=True)
    parser.add_argument('--stop-root-pin',action='append',required=True)
    args=parser.parse_args(argv)
    require(Path.cwd().resolve()==ROOT,'REPOSITORY_CWD')
    return run(args.scan_run,args.observer_run,[json.loads(value) for value in args.stop_root_pin])


if __name__=='__main__':
    try: raise SystemExit(main())
    except (ValueError, OSError, KeyError, TypeError, AttributeError, subprocess.SubprocessError) as error:
        code=str(error) if isinstance(error,ValueError) else ''
        print(code if ERROR_CODE.fullmatch(code) else 'P340_ATTRIBUTION_NOT_STARTED')
        raise SystemExit(2) from None
