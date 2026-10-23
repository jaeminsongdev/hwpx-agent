"""New document guard and concrete host schedule controls; never starts Native."""
import json
from pathlib import Path
import re
import sys
import time
import named_style_verification_runtime as r
import run_prepared_bookmark_native631 as publisher
import metadata_forensic_retention615 as retention
from verify_prepared_bookmark631 import command

SELF='tools/p09/verify_block_bookmark_source647.py'
PY_TEST='tools/p09/tests/test_block_bookmark_source647_host.py'
PS_TEST='implementation/p09/tools/test-block-bookmark-source646-document.ps1'
PRIOR='implementation/p09/evidence/p09-361-block-bookmark-source645-code002.v1.json'
OUTPUT='implementation/p09/evidence/p09-361-block-bookmark-source647-code001.v1.json'
PWSH=Path(sys.executable).parent.parent/'native/powershell/pwsh.exe'

def require(ok,code):
    if not ok:raise ValueError('P647_'+code)

def main():
    require(sys.argv[1:]==['--code-only-no-native'],'CODE_ONLY_MODE')
    require(not(r.c.ROOT/OUTPUT).exists(),'IMMUTABLE_OUTPUT')
    r.tools.select_own_single_cpu();r.shared.host.configure_host_policy(r.c)
    guard=r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))()
    q=shell=None;start=time.monotonic()
    row=dict(state='FAILED647_DOCUMENT_GUARD_AND_HOST_CODE',steps=[],Native_started=False,
        native_entry_ready=False,block_source_or_content_qualified=False,P09_complete=False,
        original645_models_replayed=False,old249_replayed=False)
    try:
        guard.acquire();q=r.a.AcceptanceReader(r.c.ROOT,guard.check)
        old=publisher.codec.unpack(q.json(PRIOR))
        require(q.snapshots[PRIOR]['sha256']=='2c525189425dc4df57500b098565843db3fccf16f6c5d33c7fed342b3bf9c7c0'
            and old['state']=='QUALIFIED645_FIXED_BLOCK_SOURCE_PORT_BODIES_MODELS_NOT_NATIVE_ENTRY_OR_CAPTURE'
            and old['cleanup'] is True and old['fresh_inputs']==old['final_fresh_hashes']==13
            and old['retained_models_not_replayed'] is True and old['new_port_models']==22,'UNCHANGED_645_22_MODELS_AND_WIRE')
        for pin in old['source_pins']:require(q.pin(pin['path'])==pin,'UNCHANGED_645_DEPENDENCIES')
        for path in(SELF,PY_TEST,PS_TEST,'implementation/p09/tools/block-bookmark-source646-document.ps1',
            'tools/p09/block_bookmark_source647_host.py','tools/p09/crossref_qualified_batch.py',
            'tools/p09/crossref_preassigned_host_protocol.py','tools/p09/crossref_preassigned_session_scope.py',
            'tools/p09/crossref_native_host_channel.py','tools/p09/crossref_native_startup.py',
            'tools/p09/crossref_native_host_limits.py','tools/p09/prepared_bookmark631_drain.py'):q.pin(path)
        row['retained_645']=q.snapshots[PRIOR]
        shell=r.a.AcceptanceReader(PWSH.parent,guard.check);row['shell_pin']=shell.pin(PWSH.name)
        native=publisher.runtime.base.session.startup;before=native.hwp_pids(guard.windows,guard.check)
        env=r.audit.environment()
        doc=command(guard,[str(PWSH),'-NoLogo','-NoProfile','-NonInteractive','-File',str(r.c.ROOT/PS_TEST),'-ModelsOnly'],env,row,'new_document_guard13')
        require({k:doc[k]for k in('run','errors','failures','skipped')}==dict(run=13,errors=0,failures=0,skipped=0)
            and doc['actual_native_started'] is False,'DOCUMENT_GUARD_13')
        host=command(guard,[sys.executable,'-B',str(r.c.ROOT/PY_TEST)],env,row,'new_host_schedule12')
        require({k:host[k]for k in('run','errors','failures','skipped')}==dict(run=12,errors=0,failures=0,skipped=0)
            and host['actual_native_started'] is False,'HOST_SCHEDULE_12')
        require(native.hwp_pids(guard.windows,guard.check)==before,'HWP_SET_UNCHANGED')
        shell.finish();q.finish();guard.check(force=True)
        row.update(state='QUALIFIED647_DOCUMENT_REFERENCE_GUARD_AND_FIXED_HOST_CODE_NOT_NATIVE_OR_ENTRY',
            new_document_models=13,new_host_models=12,retained645_models_not_replayed=22,
            planned_documents=1,planned_ranges=8,planned_sessions=2,planned_wire_requests=54,
            Native_process_set_unchanged=True,worker_channel_save_reopen_wiring_qualified=False)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt)as error:
        row.update(**publisher.runtime.io.safe_failure(error))
        if isinstance(error,ValueError)and re.fullmatch(r'P647_[A-Z0-9_]{1,100}',str(error)):row['error_code']=str(error)
    finally:
        guard.close();row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),
            source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),
            final_fresh_hashes=0 if q is None else q.final_fresh_hashes,shell_final_fresh_hashes=0 if shell is None else shell.final_fresh_hashes,
            elapsed_seconds=round(time.monotonic()-start,3),system_CPU_max=max((s['system_cpu_percent']for s in guard.samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in guard.samples),default=None))
        row,_=retention.retain(r.c.ROOT,'implementation/p09/evidence/private/p09-361-block-bookmark-source647-code001-forensic',row)
        pin=publisher.publish(OUTPUT,row)
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','cleanup','fresh_inputs','final_fresh_hashes','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'failed_tests':[n for s in row['steps']for n in s.get('result',{}).get('failed_tests',[])],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('QUALIFIED647_')and row['cleanup']else 2

if __name__=='__main__':raise SystemExit(main())
