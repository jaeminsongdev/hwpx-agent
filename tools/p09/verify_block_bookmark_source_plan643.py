"""Build/validate fixed source plan from exact SDK/installed declaration evidence."""
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

SELF='tools/p09/verify_block_bookmark_source_plan643.py'
TEST='tools/p09/tests/test_block_bookmark_source_plan643.py'
SDK='implementation/p09/evidence/p09-361-block-bookmark-sdk641-review002.v1.json'
TYPELIB='implementation/p09/evidence/p09-361-block-bookmark-typelib642-inspection001.v1.json'
PLAN='implementation/p09/evidence/p09-361-block-bookmark-source-plan643.v1.json'
OUTPUT='implementation/p09/evidence/p09-361-block-bookmark-source-plan643-audit002.v1.json'
PRIOR='implementation/p09/evidence/p09-361-block-bookmark-source-plan643-audit001.v1.json'
ARCHIVE='implementation/p09/source-archive/p361-block-bookmark-source-plan643-audit001/verify_block_bookmark_source_plan643.py'

def require(ok,code):
    if not ok:raise ValueError('P643_'+code)

def main():
    require(sys.argv[1:]==['--fixed-source-plan-no-native'],'PLAN_ONLY_MODE')
    require(not(r.c.ROOT/OUTPUT).exists()and not(r.c.ROOT/PLAN).exists(),'IMMUTABLE_OUTPUTS')
    r.tools.select_own_single_cpu();r.shared.host.configure_host_policy(r.c)
    guard=r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))()
    q=None;start=time.monotonic()
    row=dict(state='FAILED643_SOURCE_PLAN_VALIDATION',steps=[],Native_started=False,native_entry_ready=False,block_content_support_qualified=False,P09_complete=False)
    try:
        guard.acquire();q=r.a.AcceptanceReader(r.c.ROOT,guard.check)
        for path in(SELF,TEST,'tools/p09/block_bookmark_source_plan643.py'):q.pin(path)
        sdk=publisher.codec.unpack(q.json(SDK));decl=publisher.codec.unpack(q.json(TYPELIB))
        require(q.snapshots[SDK]['sha256']=='0fc5fc4738c24c781c8945c93898c256fd9718eab5579dd0f3d5a150aa67578c'
            and sdk['cleanup']is True and sdk['fresh_inputs']==sdk['final_fresh_hashes']==8,'EXACT_SDK_REVIEW')
        require(q.snapshots[TYPELIB]['sha256']=='472322a9955b061098b9a290b11a46713a8692cbd10e6c775b413e5e36ba7ecf'
            and decl['cleanup']is True and decl['fresh_inputs']==decl['final_fresh_hashes']==3,'EXACT_CURRENT_TYPELIB')
        for page in sdk['pages']:require(q.pin(page['source']['path'])==page['source']and q.pin(page['rendered_page']['path'])==page['rendered_page'],'EXACT_PRIMARY_PAGES')
        for pin in decl['source_pins']:require(q.pin(pin['path'])==pin,'INSTALLED_INSPECTOR_UNCHANGED')
        plan=model.build(decl['declarations']);require(model.validate(plan,decl['declarations']),'FIXED_PLAN')
        old=publisher.codec.unpack(q.json(PRIOR))
        require(q.snapshots[PRIOR]['sha256']=='0a987d4b1d8e65ececeea43d6dc4260c4e3d105e6b79d9cfce9e9fce45f10f0b'
            and old['cleanup']is True and old['error_code']=='XREF_LOSSLESS610_ROOT_STATE'
            and len(old['steps'])==1 and old['steps'][0]['cleanup']is True
            and old['steps'][0]['result']==dict(run=10,errors=0,failures=0,skipped=0),'RETAINED_TEN_PASSED_MODELS')
        oldpins={p['path']:p for p in old['source_pins']}
        require(q.pin(ARCHIVE)['sha256']==oldpins[SELF]['sha256'],'PRESERVED_ORIGINAL_DRIVER')
        for path,pin in oldpins.items():
            if path!=SELF:require(q.pin(path)==pin,'UNCHANGED_RETAINED_MODEL_TESTS_AND_METADATA')
        row.update(retained_contracts=10,retained_models_not_replayed=True,retained_receipt=q.snapshots[PRIOR])
        packet=dict(state='PREPARED643_FIXED_SOURCE_CAPTURE_PLAN_NOT_NATIVE_ENTRY',plan=plan)
        row['plan_pin']=publisher.publish(PLAN,packet)
        actual=publisher.codec.unpack(q.json(PLAN))
        require(actual==packet and model.validate(actual['plan'],decl['declarations']),'PUBLISHED_FULL_PLAN_ROUND_TRIP')
        q.finish();guard.check(force=True)
        row.update(state='QUALIFIED643_FIXED_EIGHT_BLOCKS_ONE_SOURCE_PLAN_ONLY_NOT_NATIVE_ENTRY_OR_BLOCK_MAPPING',
            native_source_documents_planned=1,block_ranges_planned=8,fresh_creation_sessions_planned=1,independent_reopen_sessions_planned=1)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt)as error:
        row.update(**publisher.runtime.io.safe_failure(error))
        if isinstance(error,ValueError)and re.fullmatch(r'P643_[A-Z0-9_]{1,100}',str(error)):row['error_code']=str(error)
    finally:
        guard.close();row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),
            source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
            elapsed_seconds=round(time.monotonic()-start,3),system_CPU_max=max((s['system_cpu_percent']for s in guard.samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in guard.samples),default=None))
        row,retained=retention.retain(r.c.ROOT,'implementation/p09/evidence/private/p09-361-block-bookmark-source-plan643-audit002-forensic',row)
        pin=publisher.publish(OUTPUT,row)
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','cleanup','native_source_documents_planned','block_ranges_planned',
            'fresh_inputs','final_fresh_hashes','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('QUALIFIED643_')and row['cleanup']else 2

if __name__=='__main__':raise SystemExit(main())
