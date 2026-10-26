"""Exact installed set-selection ABI and changed range readback, no Native."""
import json
from pathlib import Path
import re
import sys
import time
import run_prepared_bookmark_native631 as p
from verify_prepared_bookmark631 import command
r=p.r
SELF='tools/p09/verify_block_bookmark_selection659.py'
PORT='implementation/p09/tools/block-bookmark-selection658.ps1'
TEST='implementation/p09/tools/test-block-bookmark-selection658.ps1'
DECL='implementation/p09/evidence/p09-361-block-bookmark-selection657-inspection001.v1.json'
FAIL='implementation/p09/evidence/p09-361-block-bookmark-source655-native001.v1.json'
OUTPUT='implementation/p09/evidence/p09-361-block-bookmark-selection659-code001.v1.json'

def require(ok,code):
    if not ok:raise ValueError('BLOCK659_'+code)

def main():
    require(sys.argv[1:]==['--code-only-no-native']and not(r.c.ROOT/OUTPUT).exists(),'MODE_OR_IMMUTABLE_OUTPUT')
    r.tools.select_own_single_cpu();r.shared.host.configure_host_policy(r.c)
    guard=r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))()
    q=shell=None;start=time.monotonic()
    row=dict(state='FAILED659_SET_SELECTION_CODE_ONLY',steps=[],Native_started=False,
        actual655_root_cause_proven=False,Native_retry_executed=False,P09_complete=False)
    try:
        guard.acquire();q=r.a.AcceptanceReader(r.c.ROOT,guard.check)
        for path in(SELF,PORT,TEST,'implementation/p09/tools/block-bookmark-source653-typed.ps1',
            'implementation/p09/tools/block-bookmark-source645-ports.ps1',
            'implementation/p09/tools/block-bookmark-source646-document.ps1'):q.pin(path)
        declaration=p.codec.unpack(q.json(DECL));failure=p.codec.unpack(q.json(FAIL))
        require(q.snapshots[DECL]['sha256']=='fb92edf22ae012527de4571c311446bb4ce2e5963680319add90f3b2d8717c5c'
            and declaration['cleanup']is True and declaration['Native_started']is False,'CURRENT_COMPLETE_METADATA')
        require(q.snapshots[FAIL]['sha256']=='a077bc3bbf7799337061b0232493d6131d3c9319969111351e2daaee825435f5'
            and failure['cleanup']is True and failure['source_capture_executed']is False,'PRESERVED_CONSUMED655')
        d=declaration['declarations']
        require(d['no_com_server_activation']is True and d['hwp_process_set_unchanged']is True
            and d['typelib_sha256']=='abd7ca72b9873dbd90f2d28df872f2353f875662354d226fcc294557c44ca4f9','EXACT_INSTALLED_TYPELIB')
        methods={v['name']:v for t in d['types']if t['name']=='IHwpObject'for v in t['members']}
        select=methods['GetSelectedPosBySet'];create=methods['CreateSet'];out=methods['GetSelectedPos']
        require(select['member_id']==30106 and select['return_variant_type']==11
            and [(v['name'],v['variant_type'],v['flags'])for v in select['parameters']]==[('sset',9,1),('eset',9,1)]
            and create['member_id']==30102 and create['return_variant_type']==9
            and [(v['variant_type'],v['flags'])for v in create['parameters']]==[(8,1)],'EXACT_SET_SELECTION_SIGNATURE')
        require(out['return_variant_type']==11 and len(out['parameters'])==6
            and all(v['variant_type']==26 and v['pointer_variant_type']==3 and v['flags']==2 for v in out['parameters']),'ORIGINAL_SIX_I4_OUT_NOT_VARIANT')
        image=Path(p.runtime.base.candidate.original.SHELL);shell=r.a.AcceptanceReader(image.parent,guard.check)
        row['worker_shell_pin']=shell.pin(image.name)
        native=p.runtime.base.session.startup;before=native.hwp_pids(guard.windows,guard.check)
        v=command(guard,[str(image),'-NoLogo','-NoProfile','-NonInteractive','-STA','-File',str(r.c.ROOT/TEST),'-ModelsOnly'],
            r.audit.environment(),row,'new_set_selection_readback_and_unchanged_range_writer')
        require({k:v[k]for k in('run','errors','failures','skipped')}==dict(run=29,errors=0,failures=0,skipped=0)
            and v['actual_native_started']is False and v['pointer_out_api_calls']==0
            and v['position_requirement_weakened']is False,'ALL_NEW_SELECTION_MODELS')
        require(native.hwp_pids(guard.windows,guard.check)==before,'UNCHANGED_HWP_SET')
        shell.finish();q.finish();guard.check(force=True)
        row.update(state='QUALIFIED659_SET_SELECTION_BODIES_AND_EXACT_COORDINATE_CONTROLS_NOT_NATIVE',
            new_models=29,old_model_suites_replayed=False,Native_process_set_unchanged=True,
            complete_metadata=q.snapshots[DECL],consumed655=q.snapshots[FAIL],exact_six_coordinate_requirement_preserved=True)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt)as error:
        row.update(**p.runtime.io.safe_failure(error))
        if isinstance(error,ValueError)and re.fullmatch(r'BLOCK659_[A-Z0-9_]{1,100}',str(error)):row['error_code']=str(error)
    finally:
        guard.close();row.update(cleanup=guard.cleanup and all(v['cleanup']for v in row['steps']),
            source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),
            final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
            shell_final_fresh_hashes=0 if shell is None else shell.final_fresh_hashes,
            elapsed_seconds=round(time.monotonic()-start,3),system_CPU_max=max((v['system_cpu_percent']for v in guard.samples),default=None),
            available_RAM_min_percent=min((v['available_ram_percent']for v in guard.samples),default=None))
        row,_=p.retention.retain(r.c.ROOT,'implementation/p09/evidence/private/p09-361-block-bookmark-selection659-code001-forensic',row)
        pin=p.publish(OUTPUT,row)
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','cleanup','fresh_inputs','final_fresh_hashes','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'failed_tests':[n for s in row['steps']for n in s.get('result',{}).get('failed_tests',[])],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('QUALIFIED659_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
