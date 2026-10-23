"""Changed worker/channel models plus actual one-READY denial, never Native GO."""
import json
from pathlib import Path
import re
import subprocess
import sys
import time
import named_style_verification_runtime as r
import run_prepared_bookmark_native631 as publisher
import metadata_forensic_retention615 as retention
from verify_prepared_bookmark631 import command,ReadyDenial
import block_bookmark_source648_worker as worker_code
import block_bookmark_source647_host as host_code

SELF='tools/p09/verify_block_bookmark_source649.py'
PY_TEST='tools/p09/tests/test_block_bookmark_source648_worker.py'
PS_TEST='implementation/p09/tools/test-block-bookmark-source648.ps1'
PRIOR='implementation/p09/evidence/p09-361-block-bookmark-source647-code001.v1.json'
OUTPUT='implementation/p09/evidence/p09-361-block-bookmark-source649-code001.v1.json'
PWSH=Path(sys.executable).parent.parent/'native/powershell/pwsh.exe'
DIRECTORY='implementation/p09/evidence/private/p09-361-block-bookmark643-source-document001'

def require(ok,code):
    if not ok:raise ValueError('P649_'+code)

def main():
    require(sys.argv[1:]==['--code-only-no-native'],'CODE_ONLY_MODE')
    require(not(r.c.ROOT/OUTPUT).exists(),'IMMUTABLE_OUTPUT')
    r.tools.select_own_single_cpu();r.shared.host.configure_host_policy(r.c)
    guard=r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))()
    q=model_shell=worker_shell=None;start=time.monotonic()
    row=dict(state='FAILED649_FIXED_SOURCE_WORKER_CODE',steps=[],Native_started=False,
        native_entry_ready=False,block_source_or_content_qualified=False,P09_complete=False,
        previous_model_suites_replayed=False,old249_replayed=False)
    try:
        guard.acquire();q=r.a.AcceptanceReader(r.c.ROOT,guard.check)
        old=publisher.codec.unpack(q.json(PRIOR))
        require(q.snapshots[PRIOR]['sha256']=='b954c2a38c1fe316981bf785b1e667ad6ff22ff0ad6d167726cb07fee1502c7d'
            and old['state']=='QUALIFIED647_DOCUMENT_REFERENCE_GUARD_AND_FIXED_HOST_CODE_NOT_NATIVE_OR_ENTRY'
            and old['cleanup'] is True and old['fresh_inputs']==old['final_fresh_hashes']==26
            and old['new_document_models']==13 and old['new_host_models']==12,'RETAINED647_CURRENT_CODE')
        for pin in old['source_pins']:require(q.pin(pin['path'])==pin,'UNCHANGED_RETAINED_MODEL_INPUTS')
        for path in sorted(worker_code.SOURCES|{SELF,PY_TEST,PS_TEST,'tools/p09/block_bookmark_source648_worker.py',
            'tools/p09/crossref_fixed_worker.py','tools/p09/crossref_session_worker.py','tools/p09/crossref_native_worker_io603.py',
            'tools/p09/verify_prepared_bookmark631.py'}):q.pin(path)
        row['retained647']=q.snapshots[PRIOR]
        model_shell=r.a.AcceptanceReader(PWSH.parent,guard.check);row['model_shell_pin']=model_shell.pin(PWSH.name)
        native=publisher.runtime.base.session.startup;before=native.hwp_pids(guard.windows,guard.check)
        require(not(r.c.ROOT/DIRECTORY).exists()and not(r.c.ROOT/DIRECTORY).is_symlink(),'NO_SOURCE_CAPTURE_DIRECTORY')
        env=r.audit.environment()
        ps=command(guard,[str(PWSH),'-NoLogo','-NoProfile','-NonInteractive','-File',str(r.c.ROOT/PS_TEST),'-ModelsOnly'],env,row,'new_channel_and_flow17')
        require({k:ps[k]for k in('run','errors','failures','skipped')}==dict(run=17,errors=0,failures=0,skipped=0)
            and ps['actual_native_started'] is False and ps['steps']==list(host_code.STEPS),'NEW17_AND_EXACT_HOST_STEP_BINDING')
        py=command(guard,[sys.executable,'-B',str(r.c.ROOT/PY_TEST)],env,row,'new_fixed_command_and_notice6')
        require({k:py[k]for k in('run','errors','failures','skipped')}==dict(run=6,errors=0,failures=0,skipped=0)
            and py['actual_native_started'] is False,'NEW6_WORKER_AND_NOTICE')
        shell_path=Path(worker_code.original.prior.original.SHELL)
        worker_shell=r.a.AcceptanceReader(shell_path.parent,guard.check);row['worker_shell_pin']=worker_shell.pin(shell_path.name)
        worker=worker_code.Worker(guard)
        denial=ReadyDenial(worker,lambda:worker_shell.fresh_pin(shell_path.name))
        attempt={};row['ready_denial']=attempt
        value=publisher.runtime.io.run(guard,worker,q,worker.start_fixed_worker,denial,worker_code.RESULT,env,lambda v:None,attempt)
        require(attempt['cleanup'] is True and attempt['exit_code']==2 and attempt['requests']==1 and denial.calls==1
            and value['state']=='block_source_callbacks_failed_or_partial'and value['completed_callback_cases']==0
            and value['retained_live_or_uncertain_owners']==0 and value['planned_cases']==1
            and value['error_code']=='P09_XREF_BIND_BLOCK648_CURRENT_RELEASE_REQUIRED','ACTUAL_SINGLE_READY_DENIED_NO_CASE_IO')
        require(native.hwp_pids(guard.windows,guard.check)==before and not(r.c.ROOT/DIRECTORY).exists(),'NO_HWP_OR_CAPTURE_SIDE_EFFECT')
        model_shell.finish();worker_shell.finish();q.finish();guard.check(force=True)
        row.update(state='QUALIFIED649_FIXED_WORKER_MODELS_AND_READY_DENIAL_NOT_NATIVE_ENTRY',
            new_channel_flow_models=17,new_command_notice_models=6,retained647_models_not_replayed=25,
            actual_READY_frames=1,actual_case_frames=0,source_directory_created=False,
            full_controller_entry_and_real_capture_qualified=False,Native_process_set_unchanged=True)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError,KeyboardInterrupt)as error:
        row.update(**publisher.runtime.io.safe_failure(error))
        if isinstance(error,ValueError)and re.fullmatch(r'P649_[A-Z0-9_]{1,100}',str(error)):row['error_code']=str(error)
    finally:
        guard.close();row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps'])
            and('ready_denial'not in row or row['ready_denial'].get('cleanup')is True),
            source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),
            final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
            model_shell_final=0 if model_shell is None else model_shell.final_fresh_hashes,
            worker_shell_final=0 if worker_shell is None else worker_shell.final_fresh_hashes,
            elapsed_seconds=round(time.monotonic()-start,3),system_CPU_max=max((s['system_cpu_percent']for s in guard.samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in guard.samples),default=None))
        row,_=retention.retain(r.c.ROOT,'implementation/p09/evidence/private/p09-361-block-bookmark-source649-code001-forensic',row)
        pin=publisher.publish(OUTPUT,row)
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','cleanup','fresh_inputs','final_fresh_hashes','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'failed_tests':[n for s in row['steps']for n in s.get('result',{}).get('failed_tests',[])],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('QUALIFIED649_')and row['cleanup']else 2

if __name__=='__main__':raise SystemExit(main())
