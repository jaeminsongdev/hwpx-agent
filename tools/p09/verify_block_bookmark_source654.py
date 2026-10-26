"""Current lowercase typed declaration and changed range bodies, no Native."""
import json
from pathlib import Path
import re
import sys
import time
import run_prepared_bookmark_native631 as p
from verify_prepared_bookmark631 import command
r=p.r
SELF='tools/p09/verify_block_bookmark_source654.py'
PORT='implementation/p09/tools/block-bookmark-source653-typed.ps1'
TEST='implementation/p09/tools/test-block-bookmark-source653-typed.ps1'
DECL='implementation/p09/evidence/p09-361-block-bookmark-surface652-inspection001.v1.json'
FAIL='implementation/p09/evidence/p09-361-block-bookmark-source650-native001.v1.json'
OUTPUT='implementation/p09/evidence/p09-361-block-bookmark-source654-code003.v1.json'

def require(ok,code):
    if not ok:raise ValueError('BLOCK654_'+code)

def main():
    require(sys.argv[1:]==['--code-only-no-native']and not(r.c.ROOT/OUTPUT).exists(),'MODE_OR_IMMUTABLE_OUTPUT')
    r.tools.select_own_single_cpu();r.shared.host.configure_host_policy(r.c)
    guard=r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))()
    q=shell=None;start=time.monotonic()
    row=dict(state='FAILED654_TYPED_RANGE_CODE_ONLY',steps=[],Native_started=False,
        actual650_root_cause_proven=False,Native_retry_executed=False,P09_complete=False)
    try:
        guard.acquire();q=r.a.AcceptanceReader(r.c.ROOT,guard.check)
        for path in(SELF,PORT,TEST,'tools/p09/inspect_block_bookmark_surface652.py',
            'tools/p09/inspect_block_bookmark_surface652.ps1',
            'implementation/p09/tools/block-bookmark-source645-ports.ps1',
            'implementation/p09/tools/block-bookmark-source646-document.ps1'):q.pin(path)
        declaration=p.codec.unpack(q.json(DECL));failure=p.codec.unpack(q.json(FAIL))
        require(q.snapshots[DECL]['sha256']=='bb7d1fae41349410f24a46ff857d94a08996502ef6ba4340bf3f200aa849ecf3'
            and declaration['cleanup']is True and declaration['Native_started']is False,'CURRENT_COMPLETE_METADATA')
        require(q.snapshots[FAIL]['sha256']=='1d468b67f6ed889cc67607ddd8ffc84004af1d534bee8d29c799693ebd5d927c'
            and failure['cleanup']is True and failure['source_capture_executed']is False,'PRESERVED_CONSUMED650')
        d=declaration['declarations']
        require(d['no_com_server_activation']is True and d['hwp_process_set_unchanged']is True
            and d['typelib_sha256']=='abd7ca72b9873dbd90f2d28df872f2353f875662354d226fcc294557c44ca4f9','EXACT_INSTALLED_TYPELIB')
        book=[v for v in d['types']if v['name']=='HBookMark'];require(len(book)==1,'EXACT_BOOKMARK_TYPE')
        for name,dispid,vt in(('name',28703,8),('type',28704,19),('Command',28705,19)):
            members=[v for v in book[0]['members']if v['name']==name]
            require(len(members)==2,'COMPLETE_TYPED_PAIR')
            get=[v for v in members if v['invoke_kind']=='INVOKE_PROPERTYGET']
            put=[v for v in members if v['invoke_kind']=='INVOKE_PROPERTYPUT']
            require(len(get)==len(put)==1 and get[0]['member_id']==put[0]['member_id']==dispid
                and get[0]['return_variant_type']==vt and get[0]['parameters']==[]
                and put[0]['return_variant_type']==24 and len(put[0]['parameters'])==1
                and put[0]['parameters'][0]['variant_type']==vt and put[0]['parameters'][0]['flags']==1,'EXACT_TYPED_SIGNATURE')
        image=Path(p.runtime.base.candidate.original.SHELL)
        shell=r.a.AcceptanceReader(image.parent,guard.check);row['worker_shell_pin']=shell.pin(image.name)
        native=p.runtime.base.session.startup;before=native.hwp_pids(guard.windows,guard.check)
        result=command(guard,[str(image),'-NoLogo','-NoProfile','-NonInteractive','-STA','-File',str(r.c.ROOT/TEST),'-ModelsOnly'],
            r.audit.environment(),row,'changed_typed_range_bodies_exact_target_shell')
        require({k:result[k]for k in('run','errors','failures','skipped')}==dict(run=24,errors=0,failures=0,skipped=0)
            and result['actual_native_started']is False and result['generic_item_calls']==0,'ALL_NEW_TYPED_RANGE_MODELS')
        require(native.hwp_pids(guard.windows,guard.check)==before,'UNCHANGED_HWP_SET')
        shell.finish();q.finish();guard.check(force=True)
        row.update(state='QUALIFIED654_TYPED_RANGE_BODIES_AND_SAFE_CALL_DIAGNOSTICS_NOT_NATIVE',
            new_models=24,old_model_suites_replayed=False,Native_process_set_unchanged=True,
            declaration_filter_gap_proven=True,complete_metadata=q.snapshots[DECL],consumed650=q.snapshots[FAIL])
    except(ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt)as error:
        row.update(**p.runtime.io.safe_failure(error))
        if isinstance(error,ValueError)and re.fullmatch(r'BLOCK654_[A-Z0-9_]{1,100}',str(error)):row['error_code']=str(error)
    finally:
        guard.close();row.update(cleanup=guard.cleanup and all(v['cleanup']for v in row['steps']),
            source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),
            final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
            shell_final_fresh_hashes=0 if shell is None else shell.final_fresh_hashes,
            elapsed_seconds=round(time.monotonic()-start,3),system_CPU_max=max((v['system_cpu_percent']for v in guard.samples),default=None),
            available_RAM_min_percent=min((v['available_ram_percent']for v in guard.samples),default=None))
        row,_=p.retention.retain(r.c.ROOT,'implementation/p09/evidence/private/p09-361-block-bookmark-source654-code003-forensic',row)
        pin=p.publish(OUTPUT,row)
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','cleanup','fresh_inputs','final_fresh_hashes','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'failed_tests':[n for s in row['steps']for n in s.get('result',{}).get('failed_tests',[])],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('QUALIFIED654_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
