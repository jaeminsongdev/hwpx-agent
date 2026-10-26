"""Bound failure650 receipt and query installed metadata without Native retry."""
import json
from pathlib import Path
import sys
import time
import run_prepared_bookmark_native631 as p
from verify_prepared_bookmark631 import command
r=p.r
SELF='tools/p09/inspect_block_bookmark_surface652.py'
SCRIPT='tools/p09/inspect_block_bookmark_surface652.ps1'
FAIL='implementation/p09/evidence/p09-361-block-bookmark-source650-native001.v1.json'
OUTPUT='implementation/p09/evidence/p09-361-block-bookmark-surface652-inspection001.v1.json'

def main():
    if sys.argv[1:]!=['--metadata-only-no-native']or(r.c.ROOT/OUTPUT).exists():raise ValueError('BLOCK652_MODE_OR_IMMUTABLE_OUTPUT')
    r.tools.select_own_single_cpu();r.shared.host.configure_host_policy(r.c)
    guard=r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))()
    q=shell=None;start=time.monotonic();row=dict(state='FAILED652_METADATA_ONLY',steps=[],Native_started=False)
    try:
        guard.acquire();q=r.a.AcceptanceReader(r.c.ROOT,guard.check)
        for name in(SELF,SCRIPT,'tools/p09/inspect_click_here_lifecycle_typelib.ps1'):q.pin(name)
        fail=p.codec.unpack(q.json(FAIL))
        if q.snapshots[FAIL]['sha256']!='1d468b67f6ed889cc67607ddd8ffc84004af1d534bee8d29c799693ebd5d927c'or fail['cleanup']is not True:
            raise ValueError('BLOCK652_ORIGINAL_FAILURE')
        trace=q.json('implementation/p09/evidence/private/p09-361-block-bookmark643-source-document001/case-trace.json')
        row['original650_failure']=q.snapshots[FAIL]
        image=Path(sys.executable).parent.parent/'native/powershell/pwsh.exe'
        shell=r.a.AcceptanceReader(image.parent,guard.check);row['shell_pin']=shell.pin(image.name)
        v=command(guard,[str(image),'-NoLogo','-NoProfile','-NonInteractive','-File',str(r.c.ROOT/SCRIPT)],r.audit.environment(),row,'current_complete_BookMark_metadata')
        row['declarations']=v
        if v['state']!='OBSERVED652_COMPLETE_BOOKMARK_DECLARATIONS_NOT_NATIVE'or v['Native_started']is not False:raise ValueError('BLOCK652_METADATA_ONLY_REQUIRED')
        shell.finish();q.finish();guard.check(force=True);row['state']='OBSERVED652_COMPLETE_BOOKMARK_METADATA_NO_NATIVE_RETRY'
    except(ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt)as error:row.update(**p.runtime.io.safe_failure(error))
    finally:
        guard.close();row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),source_pins=[]if q is None else list(q.snapshots.values()),
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
            elapsed_seconds=round(time.monotonic()-start,3),system_CPU_max=max((v['system_cpu_percent']for v in guard.samples),default=None),
            available_RAM_min_percent=min((v['available_ram_percent']for v in guard.samples),default=None))
        row,_=p.retention.retain(r.c.ROOT,'implementation/p09/evidence/private/p09-361-block-bookmark-surface652-inspection001-forensic',row)
        pin=p.publish(OUTPUT,row);print(json.dumps({k:row.get(k)for k in('state','error_code','cleanup','fresh_inputs','final_fresh_hashes','system_CPU_max')},ensure_ascii=True))
        if 'declarations'in row:print(json.dumps(row['declarations'],ensure_ascii=True))
    return 0 if row['state'].startswith('OBSERVED652_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
