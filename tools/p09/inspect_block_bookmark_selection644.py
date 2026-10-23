"""Single guarded read-only installed selection declaration query."""
import json
from pathlib import Path
import re
import sys
import time
import named_style_verification_runtime as r
import run_prepared_bookmark_native631 as publisher
import metadata_forensic_retention615 as retention
from verify_prepared_bookmark631 import command

SELF='tools/p09/inspect_block_bookmark_selection644.py'
SCRIPT='tools/p09/inspect_block_bookmark_selection644.ps1'
OUTPUT='implementation/p09/evidence/p09-361-block-bookmark-selection644-inspection001.v1.json'
PWSH=Path(sys.executable).parent.parent/'native/powershell/pwsh.exe'

def require(ok,code):
    if not ok:raise ValueError('P644_'+code)

def main():
    require(sys.argv[1:]==['--declarations-only-no-native'],'READONLY_MODE')
    require(not(r.c.ROOT/OUTPUT).exists(),'IMMUTABLE_OUTPUT')
    r.tools.select_own_single_cpu();r.shared.host.configure_host_policy(r.c)
    guard=r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))()
    q=shell=None;start=time.monotonic()
    row=dict(state='FAILED644_SELECTION_DECLARATION_INSPECTION',steps=[],Native_started=False,P09_complete=False)
    try:
        guard.acquire();q=r.a.AcceptanceReader(r.c.ROOT,guard.check)
        for name in(SELF,SCRIPT,'tools/p09/inspect_click_here_lifecycle_typelib.ps1'):q.pin(name)
        shell=r.a.AcceptanceReader(PWSH.parent,guard.check);row['shell_pin']=shell.pin(PWSH.name)
        value=command(guard,[str(PWSH),'-NoLogo','-NoProfile','-NonInteractive','-File',str(r.c.ROOT/SCRIPT)],r.audit.environment(),row,'installed_selection_metadata_only')
        require(value['state']=='OBSERVED644_INSTALLED_SELECTION_DECLARATIONS_NOT_NATIVE'
            and value['exact_build']=='11.0.0.9136' and value['typelib_sha256']=='abd7ca72b9873dbd90f2d28df872f2353f875662354d226fcc294557c44ca4f9'
            and value['no_com_server_activation'] is True and value['registry_read_only'] is True
            and value['hwp_process_set_unchanged'] is True and value['native_selection_methods_invoked'] is False,'CURRENT_READONLY_DECLARATIONS')
        row['declarations']=value
        shell.finish();q.finish();guard.check(force=True)
        row['state']='OBSERVED644_CURRENT_SELECTION_DECLARATIONS_NOT_NATIVE_SOURCE'
    except(ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt)as error:
        row.update(**publisher.runtime.io.safe_failure(error))
        if isinstance(error,ValueError)and re.fullmatch(r'P644_[A-Z0-9_]{1,100}',str(error)):row['error_code']=str(error)
    finally:
        guard.close();row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),
            source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),
            final_fresh_hashes=0 if q is None else q.final_fresh_hashes,shell_final_fresh_hashes=0 if shell is None else shell.final_fresh_hashes,
            elapsed_seconds=round(time.monotonic()-start,3),system_CPU_max=max((s['system_cpu_percent']for s in guard.samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in guard.samples),default=None))
        row,_=retention.retain(r.c.ROOT,'implementation/p09/evidence/private/p09-361-block-bookmark-selection644-inspection001-forensic',row)
        pin=publisher.publish(OUTPUT,row)
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','cleanup','fresh_inputs','final_fresh_hashes','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('OBSERVED644_')and row['cleanup']else 2

if __name__=='__main__':raise SystemExit(main())
