"""Fixed observation-only probe models; never Native or source acceptance."""
import json
from pathlib import Path
import re
import sys
import time
import run_prepared_bookmark_native631 as p
from verify_prepared_bookmark631 import command
r=p.r
SELF='tools/p09/verify_block_selection_probe663.py'
TEST='implementation/p09/tools/test-block-selection-probe662.ps1'
FILES={SELF,TEST,'implementation/p09/tools/block-selection-probe662.ps1',
    'implementation/p09/tools/block-selection-probe662-reflection.cs',
    'implementation/p09/tools/block-bookmark-source645-ports.ps1',
    'implementation/p09/tools/block-bookmark-source646-document.ps1',
    'implementation/p09/tools/block-bookmark-source653-typed.ps1',
    'implementation/p09/tools/block-bookmark-selection658.ps1'}
FAIL='implementation/p09/evidence/p09-361-block-bookmark-source660-native001.v1.json'
DECL='implementation/p09/evidence/p09-361-block-bookmark-selection657-inspection001.v1.json'
TEXT_DECL='implementation/p09/evidence/p09-361-block-bookmark-selection644-inspection001.v1.json'
OUTPUT='implementation/p09/evidence/p09-361-block-selection-probe663-code001.v1.json'

def require(ok,code):
    if not ok:raise ValueError('PROBE663_'+code)

def main():
    require(sys.argv[1:]==['--code-only-no-native']and not(r.c.ROOT/OUTPUT).exists(),'MODE_OR_IMMUTABLE_OUTPUT')
    r.tools.select_own_single_cpu();r.shared.host.configure_host_policy(r.c)
    guard=r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))()
    q=shell=None;start=time.monotonic();row=dict(state='FAILED663_PROBE_CODE',steps=[],Native_started=False,
        source_capture_qualified=False,selection_API_qualified=False,P09_complete=False)
    try:
        guard.acquire();q=r.a.AcceptanceReader(r.c.ROOT,guard.check)
        for path in sorted(FILES):q.pin(path)
        failure=p.codec.unpack(q.json(FAIL));declaration=p.codec.unpack(q.json(DECL));text=p.codec.unpack(q.json(TEXT_DECL))
        require(q.snapshots[FAIL]['sha256']=='97da434dd6ca1dac41da5ba1b4d38c667f80b9682b91b18de8943d045831f1b1'
            and failure['cleanup']is True and failure['source_capture_executed']is False,'CONSUMED660_PRESERVED')
        require(q.snapshots[DECL]['sha256']=='fb92edf22ae012527de4571c311446bb4ce2e5963680319add90f3b2d8717c5c'
            and q.snapshots[TEXT_DECL]['sha256']=='2c7e40e5d54b79f0473774cd71bf06cb42b294b8084a9c7e09376e419657d943'
            and declaration['cleanup']is True and text['cleanup']is True,'ORIGINAL_INSTALLED_METADATA')
        methods={v['name']:v for v in text['declarations']['selected_members']}
        require(methods['GetTextFile']['return_variant_type']==12
            and [(v['variant_type'],v['flags'])for v in methods['GetTextFile']['parameters']]==[(8,1),(8,1)]
            and methods['GetPosBySet']['return_variant_type']==9 and methods['GetPosBySet']['parameters']==[],'TEXT_AND_CARET_DECLARATIONS')
        image=Path(p.runtime.base.candidate.original.SHELL);shell=r.a.AcceptanceReader(image.parent,guard.check)
        row['worker_shell_pin']=shell.pin(image.name)
        native=p.runtime.base.session.startup;before=native.hwp_pids(guard.windows,guard.check)
        v=command(guard,[str(image),'-NoLogo','-NoProfile','-NonInteractive','-STA','-File',str(r.c.ROOT/TEST),'-ModelsOnly'],
            r.audit.environment(),row,'observation_only_text_caret_two_OUT_paths_set_and_no_Execute')
        require({k:v[k]for k in('run','errors','failures','skipped')}==dict(run=14,errors=0,failures=0,skipped=0)
            and v['actual_native_started']is False and v['probe_not_source_capture']is True,'ALL_NEW_PROBE_MODELS')
        require(native.hwp_pids(guard.windows,guard.check)==before,'NO_HWP_CREATED')
        shell.finish();q.finish();guard.check(force=True)
        row.update(state='QUALIFIED663_OBSERVATION_ONLY_PROBE_BODIES_NOT_NATIVE_OR_CAPTURE',new_models=14,
            Native_process_set_unchanged=True,whole_controller_qualified=False,old_suites_replayed=False)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt)as error:
        row.update(**p.runtime.io.safe_failure(error))
        if isinstance(error,ValueError)and re.fullmatch(r'PROBE663_[A-Z0-9_]{1,100}',str(error)):row['error_code']=str(error)
    finally:
        guard.close();row.update(cleanup=guard.cleanup and all(v['cleanup']for v in row['steps']),
            source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),
            final_fresh_hashes=0 if q is None else q.final_fresh_hashes,shell_final_fresh_hashes=0 if shell is None else shell.final_fresh_hashes,
            elapsed_seconds=round(time.monotonic()-start,3),system_CPU_max=max((v['system_cpu_percent']for v in guard.samples),default=None),
            available_RAM_min_percent=min((v['available_ram_percent']for v in guard.samples),default=None))
        row,_=p.retention.retain(r.c.ROOT,'implementation/p09/evidence/private/p09-361-block-selection-probe663-code001-forensic',row)
        pin=p.publish(OUTPUT,row)
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','cleanup','fresh_inputs','final_fresh_hashes','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'failed_tests':[n for s in row['steps']for n in s.get('result',{}).get('failed_tests',[])],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('QUALIFIED663_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
