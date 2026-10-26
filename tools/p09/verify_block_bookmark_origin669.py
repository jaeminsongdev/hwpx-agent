"""Native-position mapping port models; no HWP launch or source capture."""
import json,re,sys,time
from pathlib import Path
import run_prepared_bookmark_native631 as p
from verify_prepared_bookmark631 import command
r=p.r
SELF='tools/p09/verify_block_bookmark_origin669.py'
TEST='implementation/p09/tools/test-block-bookmark-origin668.ps1'
PORT='implementation/p09/tools/block-bookmark-origin668.ps1'
RECOVERY='implementation/p09/evidence/p09-361-block-selection-recovery667-audit001.v1.json'
OUTPUT='implementation/p09/evidence/p09-361-block-bookmark-origin669-code001.v1.json'
FILES={SELF,TEST,PORT,'implementation/p09/tools/test-block-bookmark-selection658.ps1',
    'implementation/p09/tools/block-bookmark-source645-ports.ps1','implementation/p09/tools/block-bookmark-selection658.ps1'}

def require(ok,code):
    if not ok:raise ValueError('ORIGIN669_'+code)

def main():
    require(sys.argv[1:]==['--code-only-no-native']and not(r.c.ROOT/OUTPUT).exists(),'MODE_OR_IMMUTABLE_OUTPUT')
    r.tools.select_own_single_cpu();r.shared.host.configure_host_policy(r.c)
    guard=r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))()
    q=shell=None;start=time.monotonic();row=dict(state='FAILED669_NATIVE_ORIGIN_MODELS',steps=[],Native_started=False,
        source_capture_qualified=False,selection_API_qualified=False,P09_complete=False)
    try:
        guard.acquire();q=r.a.AcceptanceReader(r.c.ROOT,guard.check)
        for path in sorted(FILES):q.pin(path)
        recovery=p.codec.unpack(q.json(RECOVERY))
        require(q.snapshots[RECOVERY]['sha256']=='35e3106f39bfbc1f5c135e0c3948a2c7250c4e2843671ea557ea0d502a62fc3b'
            and recovery['state']=='RECOVERED667_RETAINED_DIAGNOSTICS_NOT_SOURCE_OR_API_PASS'
            and recovery['cleanup']is True and recovery['observations_recorded']==8
            and recovery['Native_replayed']is False and recovery['historical_final_hashes_claimed']is False,'RETAINED_DIAGNOSTICS_ONLY')
        image=Path(p.runtime.base.candidate.original.SHELL);shell=r.a.AcceptanceReader(image.parent,guard.check)
        row['worker_shell_pin']=shell.pin(image.name)
        native=p.runtime.base.session.startup;before=native.hwp_pids(guard.windows,guard.check)
        v=command(guard,[str(image),'-NoLogo','-NoProfile','-NonInteractive','-STA','-File',str(r.c.ROOT/TEST),'-ModelsOnly'],
            r.audit.environment(),row,'actual_mapping_writer_origin_coordinates_text_identity_and_failure_latch')
        require({k:v[k]for k in('run','errors','failures','skipped')}==dict(run=20,errors=0,failures=0,skipped=0)
            and v['actual_native_started']is False and v['position_requirement_weakened']is False,'ALL_ORIGIN_AND_TEXT_MODELS')
        require(native.hwp_pids(guard.windows,guard.check)==before,'NO_HWP_CREATED')
        shell.finish();q.finish();guard.check(force=True)
        row.update(state='QUALIFIED669_OBSERVED_ORIGIN_MAPPING_MODELS_NOT_NATIVE_OR_CAPTURE',new_models=20,
            Native_process_set_unchanged=True,whole_controller_qualified=False,old_suites_replayed=False)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt)as error:
        row.update(**p.runtime.io.safe_failure(error))
        if isinstance(error,ValueError)and re.fullmatch(r'ORIGIN669_[A-Z0-9_]{1,100}',str(error)):row['error_code']=str(error)
    finally:
        guard.close();row.update(cleanup=guard.cleanup and all(v['cleanup']for v in row['steps']),
            source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),
            final_fresh_hashes=0 if q is None else q.final_fresh_hashes,shell_final_fresh_hashes=0 if shell is None else shell.final_fresh_hashes,
            elapsed_seconds=round(time.monotonic()-start,3),system_CPU_max=max((v['system_cpu_percent']for v in guard.samples),default=None),
            available_RAM_min_percent=min((v['available_ram_percent']for v in guard.samples),default=None))
        value,_=p.retention.retain(r.c.ROOT,'implementation/p09/evidence/private/p09-361-block-bookmark-origin669-code001-forensic',row)
        pin=p.publish(OUTPUT,value)
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','cleanup','fresh_inputs','final_fresh_hashes',
            'elapsed_seconds','system_CPU_max','available_RAM_min_percent')},'failed_tests':[n for s in row['steps']for n in s.get('result',{}).get('failed_tests',[])],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('QUALIFIED669_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
