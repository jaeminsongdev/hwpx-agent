"""Observation-only Native entry code; no source-capture acceptance or Native GO."""
import json
from pathlib import Path
import re
import subprocess
import sys
import time
import run_block_selection_probe664 as entry
from verify_prepared_bookmark631 import command,ReadyDenial
r=entry.r;m=entry.runtime
SELF='tools/p09/verify_block_selection_probe665.py'
TEST='tools/p09/tests/test_block_selection_probe664.py'
PORT_PROOF='implementation/p09/evidence/p09-361-block-selection-probe663-code001.v1.json'
OLD_PROOF='implementation/p09/evidence/p09-361-block-bookmark-source661-code001.v1.json'
FAIL='implementation/p09/evidence/p09-361-block-bookmark-source660-native001.v1.json'
FAILED='implementation/p09/evidence/p09-361-block-selection-probe665-code001.v1.json'
ARCHIVE='implementation/p09/source-archive/p361-block-selection-probe665-code001/'

def require(ok,code):
    if not ok:raise ValueError('PROBE665_'+code)

def project_worker(value):
    for old,new in(('BLOCK660_','BLOCK664_'),('block-bookmark-source660-trace','block-selection-probe664-trace'),
        ('block-bookmark-source660-result','block-selection-probe664-result'),('block-bookmark660-source-document001','block-selection-probe664-document001'),
        ("'block-bookmark-selection658','block-bookmark-source646-document'","'block-bookmark-selection658','block-selection-probe662','block-bookmark-source646-document'"),
        ('Assert-P09Block658Selection $script:P09Block648State $Hwp $Case','Invoke-P09SelectionProbe662 $script:P09Block648State $Hwp $Case'),
        ("    $phase='prewarm';","    Initialize-P09SelectionProbe662\n    $phase='prewarm';"),
        ('selection_observations=[Collections.Generic.List[object]]::new();','selection_observations=[Collections.Generic.List[object]]::new();selection_probe=[Collections.Generic.List[object]]::new();probe_complete=$false;'),
        ('selection_observations=$trace.selection_observations;cleanup_error_code','selection_observations=$trace.selection_observations;selection_probe=$trace.selection_probe;probe_complete=$false;cleanup_error_code'),
        ('case_failure=$caseFailure;planned_cases=1;planned_block_ranges=8;',
        'case_failure=$caseFailure;planned_cases=1;planned_block_ranges=0;diagnostic_only=$true;\n    probe_complete=($null -ne $state -and $state.probe_complete);source_capture_executed=$false;')):
        require(old in value,'WORKER_PROJECTION_ANCHOR');value=value.replace(old,new)
    return value

def main():
    require(sys.argv[1:]==['--code-only-no-native']and not(r.c.ROOT/entry.CODE).exists(),'MODE_OR_IMMUTABLE_OUTPUT')
    r.tools.select_own_single_cpu();r.shared.host.configure_host_policy(r.c)
    guard=r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))()
    q=shell=None;start=time.monotonic();row=dict(state='FAILED665_PROBE_ENTRY_CODE',steps=[],Native_started=False,
        all_new_tests_passed=False,whole_source_execution_qualified=False,selection_API_qualified=False,P09_complete=False)
    try:
        guard.acquire();q=r.a.AcceptanceReader(r.c.ROOT,guard.check)
        ports=entry.publisher.codec.unpack(q.json(PORT_PROOF));old=entry.publisher.codec.unpack(q.json(OLD_PROOF))
        failed=entry.publisher.codec.unpack(q.json(FAIL))
        require(q.snapshots[PORT_PROOF]['sha256']=='a11e5f6d7c3a2493ac6f887bd3b4441f3d84c84e7d96e801eeb756ad1a1847b0'
            and ports['state']=='QUALIFIED663_OBSERVATION_ONLY_PROBE_BODIES_NOT_NATIVE_OR_CAPTURE'
            and ports['cleanup']is True and ports['new_models']==14 and ports['fresh_inputs']==ports['final_fresh_hashes']==11,'RETAINED_PROBE_MODELS')
        require(q.snapshots[OLD_PROOF]['sha256']=='7c322b5010be3e6c325318e91f50439d58230d8bc682a0701f47df21450fa9f2'
            and old['cleanup']is True and old['all_new_tests_passed']is True,'PRESERVED_CONSUMED660_CODE')
        require(q.snapshots[FAIL]['sha256']=='97da434dd6ca1dac41da5ba1b4d38c667f80b9682b91b18de8943d045831f1b1'
            and failed['cleanup']is True and failed['source_capture_executed']is False,'ORIGINAL660_REMAINS_FAILURE')
        for proof in(ports,old):
            for pin in proof['source_pins']:require(q.pin(pin['path'])==pin,'FROZEN_PRIOR_OR_PROBE_SOURCE_CHANGED')
        def text(path):return(r.c.ROOT/path).read_text(encoding='utf-8').rstrip('\n')
        prior_failure=entry.publisher.codec.unpack(q.json(FAILED))
        require(q.snapshots[FAILED]['sha256']=='8437710240364b5715b91fd63eaeb8446d929e4e189a877c9c0d028fc4bc2bee'
            and prior_failure['cleanup']is True and len(prior_failure['steps'])==1
            and {k:prior_failure['steps'][0]['result'][k]for k in('run','errors','failures','skipped')}==dict(run=14,errors=2,failures=0,skipped=0),
            'PRESERVED_TWO_MODEL_FIXTURE_ERRORS_NOT_NATIVE')
        for pin in prior_failure['source_pins']:
            if pin['path']in(SELF,TEST,entry.SELF):require(q.pin(ARCHIVE+Path(pin['path']).name)['sha256']==pin['sha256'],'ARCHIVED_ORIGINAL_FIXTURE_SOURCE')
            else:require(q.pin(pin['path'])==pin,'UNCHANGED_OTHER_PROBE_CODE')
        old_test=text(ARCHIVE+Path(TEST).name)
        old_runner='    result=unittest.TestResult();unittest.defaultTestLoader.loadTestsFromTestCase(Tests).run(result)'
        new_runner="    result=unittest.TestResult()\n    names=('test_normal_capture_exit_or_unexpected_failure_not_promoted_to_diagnostic','test_only_exact_diagnostic_exit2_with_closed_inputs_is_observed')\n    suite=unittest.TestSuite([Tests(name)for name in names])if sys.argv[1:]==['--changed-controller-fixture-only']else unittest.defaultTestLoader.loadTestsFromTestCase(Tests)\n    suite.run(result)"
        require(text(TEST)==old_test.replace("self.source=Reader();self.native_pin=Mock();self.shell_pin=Mock();self.fingerprint='0'*64;self.closed=False",
            "self.label=args[3];self.source=Reader();self.native_pin=Mock();self.shell_pin=Mock();self.fingerprint='0'*64;self.closed=False").replace(old_runner,new_runner),
            'ONLY_BOUNDARY_LABEL_FIXTURE_AND_CHANGED_RUNNER')
        require(text(entry.SELF)==text(ARCHIVE+Path(entry.SELF).name).replace('probe665-code001','probe665-code002'),'ONLY_NEW_PROOF_POINTER')
        require(text(m.worker_code.TARGET)==project_worker(text('implementation/p09/tools/run-block-bookmark-source660-worker.ps1')),'ONLY_FIXED_PROBE_WIRING_AND_NONCAPTURE_RESULT_WORKER_CHANGES')
        require('source_capture_executed=True'not in text(entry.SELF)
            and "diagnostic_observations_recorded=True"in text(entry.SELF),'NO_DIAGNOSTIC_PROMOTION_TO_SOURCE')
        paths=m.SOURCES|m.prior.prepared.loaded_dependencies(r.c.ROOT)|{SELF,TEST,entry.SELF,PORT_PROOF,
            'tools/p09/tests/test_block_bookmark_source660.py'}
        row['execution_dependency_paths']=sorted(paths)
        for path in sorted(paths):q.pin(path)
        m.absent()
        for path in(entry.OUTPUT,entry.CLAIM,entry.SCRATCH):m.prior.prepared.require_absent(r.c.ROOT,path)
        image=Path(m.base.candidate.original.SHELL);shell=r.a.AcceptanceReader(image.parent,guard.check)
        row['worker_shell_pin']=shell.pin(image.name)
        require(row['worker_shell_pin']==ports['worker_shell_pin']==old['worker_shell_pin'],'EXACT_TARGET_SHELL')
        native=m.base.session.startup;before=native.hwp_pids(guard.windows,guard.check)
        v=command(guard,[sys.executable,'-B',str(r.c.ROOT/TEST),'--changed-controller-fixture-only'],r.audit.environment(),row,'changed_controller_fixture_paths_only2')
        require({k:v[k]for k in('run','errors','failures','skipped')}==dict(run=2,errors=0,failures=0,skipped=0)
            and v['actual_native_started']is False,'ALL_NEW_OBSERVATION_ENTRY_MODELS')
        worker=m.worker_code.Worker(guard);denial=ReadyDenial(worker,lambda:shell.fresh_pin(image.name))
        attempt={};row['ready_denial']=attempt
        v=m.prior.io.run(guard,worker,q,worker.start_fixed_worker,denial,m.worker_code.RESULT,r.audit.environment(),lambda v:None,attempt)
        require(attempt['cleanup']is True and attempt['exit_code']==2 and attempt['requests']==1 and denial.calls==1
            and v['state']=='block_source_callbacks_failed_or_partial'and v['completed_callback_cases']==0
            and v['retained_live_or_uncertain_owners']==0 and v['planned_cases']==1 and v['planned_block_ranges']==0
            and v['probe_complete']is False and v['diagnostic_only']is True and v['source_capture_executed']is False
            and v['error_code']=='P09_XREF_BIND_BLOCK664_CURRENT_RELEASE_REQUIRED','ACTUAL_READY_DENIED_BEFORE_DIAGNOSTIC')
        require(native.hwp_pids(guard.windows,guard.check)==before and not(r.c.ROOT/m.DIRECTORY).exists(),'NO_HWP_OR_PRIVATE_SLOT_CREATED')
        shell.finish();q.finish();guard.check(force=True)
        row.update(state=entry.STATE,all_new_tests_passed=True,new_entry_models=14,retained_entry_models_not_replayed=12,changed_fixture_models=2,retained_probe_models_not_replayed=14,
            actual_READY_frames=1,actual_case_frames=0,Native_process_set_unchanged=True,source_directory_created=False,
            actual660_root_cause_proven=False,consumed660=q.snapshots[FAIL])
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError,KeyboardInterrupt)as error:
        row.update(**m.prior.io.safe_failure(error))
        if isinstance(error,ValueError)and re.fullmatch(r'PROBE665_[A-Z0-9_]{1,100}',str(error)):row['error_code']=str(error)
    finally:
        guard.close();row.update(cleanup=guard.cleanup and all(v['cleanup']for v in row['steps'])and('ready_denial'not in row or row['ready_denial'].get('cleanup')is True),
            source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),
            final_fresh_hashes=0 if q is None else q.final_fresh_hashes,shell_final_fresh_hashes=0 if shell is None else shell.final_fresh_hashes,
            elapsed_seconds=round(time.monotonic()-start,3),system_CPU_max=max((v['system_cpu_percent']for v in guard.samples),default=None),
            available_RAM_min_percent=min((v['available_ram_percent']for v in guard.samples),default=None))
        row,_=entry.publisher.retention.retain(r.c.ROOT,'implementation/p09/evidence/private/p09-361-block-selection-probe665-code002-forensic',row)
        pin=entry.publisher.publish(entry.CODE,row)
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','cleanup','fresh_inputs','final_fresh_hashes','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'failed_tests':[n for s in row['steps']for n in s.get('result',{}).get('failed_tests',[])],'receipt':pin}),flush=True)
    return 0 if row['state']==entry.STATE and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
