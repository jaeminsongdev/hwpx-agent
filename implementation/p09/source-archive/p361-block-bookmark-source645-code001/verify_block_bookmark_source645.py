"""Guarded changed port bodies on models, never a Native release or entry."""
import json
from pathlib import Path
import re
import sys
import time
import named_style_verification_runtime as r
import run_prepared_bookmark_native631 as publisher
import metadata_forensic_retention615 as retention
from verify_prepared_bookmark631 import command
import block_bookmark_source_plan643 as model

SELF='tools/p09/verify_block_bookmark_source645.py'
PORTS='implementation/p09/tools/block-bookmark-source645-ports.ps1'
TEST='implementation/p09/tools/test-block-bookmark-source645-ports.ps1'
DECL='implementation/p09/evidence/p09-361-block-bookmark-typelib642-inspection001.v1.json'
SELECT='implementation/p09/evidence/p09-361-block-bookmark-selection644-inspection001.v1.json'
PLAN='implementation/p09/evidence/p09-361-block-bookmark-source-plan643.v1.json'
OUTPUT='implementation/p09/evidence/p09-361-block-bookmark-source645-code001.v1.json'
PWSH=Path(sys.executable).parent.parent/'native/powershell/pwsh.exe'

def require(ok,code):
    if not ok:raise ValueError('P645_'+code)

def main():
    require(sys.argv[1:]==['--code-only-no-native'],'CODE_ONLY_MODE')
    require(not(r.c.ROOT/OUTPUT).exists(),'IMMUTABLE_OUTPUT')
    r.tools.select_own_single_cpu();r.shared.host.configure_host_policy(r.c)
    guard=r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))()
    q=shell=None;start=time.monotonic()
    row=dict(state='FAILED645_BLOCK_SOURCE_PORTS_CODE',steps=[],Native_started=False,
        native_entry_ready=False,block_source_or_content_qualified=False,P09_complete=False,
        prior_plan_ten_tests_replayed=False,old249_replayed=False)
    try:
        guard.acquire();q=r.a.AcceptanceReader(r.c.ROOT,guard.check)
        for name in(SELF,PORTS,TEST,'tools/p09/block_bookmark_source_plan643.py',
            'implementation/p09/tools/sdk-baseline-owned-session.ps1',
            'implementation/p09/tools/crossref-preassigned-owner.ps1',
            'implementation/p09/tools/crossref-owned-active-source.ps1'):q.pin(name)
        decl=publisher.codec.unpack(q.json(DECL));selection=publisher.codec.unpack(q.json(SELECT))
        require(q.snapshots[DECL]['sha256']=='472322a9955b061098b9a290b11a46713a8692cbd10e6c775b413e5e36ba7ecf'
            and q.snapshots[SELECT]['sha256']=='2c7e40e5d54b79f0473774cd71bf06cb42b294b8084a9c7e09376e419657d943'
            and decl['cleanup'] is True and selection['cleanup'] is True,'CURRENT_DECLARATION_RECEIPTS')
        observed=selection['declarations']
        require(observed['native_selection_methods_invoked'] is False and observed['no_com_server_activation'] is True
            and observed['hwp_process_set_unchanged'] is True and observed['typelib_sha256']==decl['declarations']['typelib_sha256'],
            'SELECTION_METADATA_NOT_NATIVE')
        members=[x for x in observed['selected_members']if x['name']=='GetSelectedPos']
        require(len(members)==1 and members[0]['member_id']==30105 and members[0]['return_variant_type']==11
            and [p['name']for p in members[0]['parameters']]==['slist','spara','spos','elist','epara','epos']
            and all(p['variant_type']==26 and p['flags']==2 for p in members[0]['parameters']),
            'EXACT_SIX_OUT_SELECTION_SIGNATURE')
        packet=publisher.codec.unpack(q.json(PLAN))
        require(q.snapshots[PLAN]['sha256']=='856cb37d5ca7d32c398017ed2072bb07597b2aeb1c10c80b8f926adf960cebff'
            and packet['state']=='PREPARED643_FIXED_SOURCE_CAPTURE_PLAN_NOT_NATIVE_ENTRY'
            and model.validate(packet['plan'],decl['declarations']),'FIXED643_PLAN')
        shell=r.a.AcceptanceReader(PWSH.parent,guard.check);row['shell_pin']=shell.pin(PWSH.name)
        native=publisher.runtime.base.session.startup
        before=native.hwp_pids(guard.windows,guard.check)
        result=command(guard,[str(PWSH),'-NoLogo','-NoProfile','-NonInteractive','-File',str(r.c.ROOT/TEST),'-ModelsOnly'],
            r.audit.environment(),row,'new_ports_models22')
        require({k:result[k]for k in('run','errors','failures','skipped')}==dict(run=22,errors=0,failures=0,skipped=0)
            and result['actual_native_started'] is False,'ALL_NEW_PORT_MODELS')
        projected=[{k:v for k,v in c.items()if k not in('seed_text_sha256','selected_text_sha256')}for c in packet['plan']['cases']]
        require(json.dumps(result['fixed_cases'],sort_keys=True,ensure_ascii=False)==json.dumps(projected,sort_keys=True,ensure_ascii=False),
            'POWERSHELL_CASES_EXACT_CANONICAL643_TYPES_AND_TEXT')
        require(native.hwp_pids(guard.windows,guard.check)==before,'UNCHANGED_HWP_PROCESS_SET')
        shell.finish();q.finish();guard.check(force=True)
        row.update(state='QUALIFIED645_FIXED_BLOCK_SOURCE_PORT_BODIES_MODELS_NOT_NATIVE_ENTRY_OR_CAPTURE',
            new_port_models=22,fixed_case_count=8,fixed_seed_executions_planned=1,
            owner_guard_and_reference_release_models_not_live_COM_qualification=True,
            fixed_plan_body_matches=True,Native_process_set_unchanged=True)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt)as error:
        row.update(**publisher.runtime.io.safe_failure(error))
        if isinstance(error,ValueError)and re.fullmatch(r'P645_[A-Z0-9_]{1,100}',str(error)):row['error_code']=str(error)
    finally:
        guard.close();row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),
            source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),
            final_fresh_hashes=0 if q is None else q.final_fresh_hashes,shell_final_fresh_hashes=0 if shell is None else shell.final_fresh_hashes,
            elapsed_seconds=round(time.monotonic()-start,3),system_CPU_max=max((s['system_cpu_percent']for s in guard.samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in guard.samples),default=None))
        row,_=retention.retain(r.c.ROOT,'implementation/p09/evidence/private/p09-361-block-bookmark-source645-code001-forensic',row)
        pin=publisher.publish(OUTPUT,row)
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','cleanup','fresh_inputs','final_fresh_hashes','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'failed_tests':[n for s in row['steps']for n in s.get('result',{}).get('failed_tests',[])],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('QUALIFIED645_')and row['cleanup']else 2

if __name__=='__main__':raise SystemExit(main())
