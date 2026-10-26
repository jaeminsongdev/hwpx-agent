"""Guarded read-only recovery of retained 664 diagnostics. Never starts Native."""
import json,re,sys,time
from pathlib import Path
import block_selection_recovery666 as model
import run_prepared_bookmark_native631 as p
from verify_prepared_bookmark631 import command
r=p.r
SELF='tools/p09/recover_block_selection667.py'
OUTPUT='implementation/p09/evidence/p09-361-block-selection-recovery667-audit001.v1.json'
TEST='tools/p09/tests/test_block_selection_recovery666.py'

def main():
    model.require(sys.argv[1:]==['--recover-retained-only']and not(r.c.ROOT/OUTPUT).exists(),'MODE_OR_IMMUTABLE_OUTPUT')
    r.tools.select_own_single_cpu();r.shared.host.configure_host_policy(r.c)
    guard=r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))()
    readers={};start=time.monotonic();row=dict(state='FAILED667_RETAINED_DIAGNOSTICS_RECOVERY',steps=[],Native_started=False,
        Native_replayed=False,source_capture_executed=False,selection_API_qualified=False,P09_complete=False)
    try:
        guard.acquire();q=r.a.AcceptanceReader(r.c.ROOT,guard.check);readers['source']=q
        for path in(SELF,TEST,'tools/p09/block_selection_recovery666.py'):q.pin(path)
        receipt=p.codec.unpack(q.json(model.RECEIPT));trace=q.json(model.TRACE)
        model.require(q.snapshots[model.RECEIPT]['sha256']==model.RECEIPT_SHA
            and q.snapshots[model.TRACE]['sha256']==model.TRACE_SHA,'ORIGINAL_RECEIPT_AND_PRIVATE_TRACE_UNCHANGED')
        row.update(model.validate(receipt,trace));pins=model.original_pins(receipt)
        installed=p.runtime.base.installed
        roots=dict(native=Path(installed.native.EXECUTABLE).parent,shell=Path(p.runtime.base.candidate.original.SHELL).parent,
            runtime=installed.fixed.PYTHON.parent)
        for label,root in roots.items():readers[label]=r.a.AcceptanceReader(root,guard.check)
        for label,expected in pins.items():
            for path,pin in sorted(expected.items()):model.require(readers[label].pin(path)==pin,'CURRENT_INPUT_DIFFERS_FROM_ORIGINAL')
        before=p.runtime.base.session.startup.hwp_pids(guard.windows,guard.check)
        v=command(guard,[sys.executable,'-B',str(r.c.ROOT/TEST)],r.audit.environment(),row,'retained_diagnostic_binding_negative_models')
        model.require(v['run']==10 and v['errors']==v['failures']==v['skipped']==0,'ALL_RECOVERY_MODELS')
        model.require(p.runtime.base.session.startup.hwp_pids(guard.windows,guard.check)==before,'NO_HWP_PROCESS_CHANGE')
        for reader in readers.values():reader.finish()
        guard.check(force=True)
        row.update(state='RECOVERED667_RETAINED_DIAGNOSTICS_NOT_SOURCE_OR_API_PASS',
            original_receipt=q.snapshots[model.RECEIPT],private_trace=q.snapshots[model.TRACE],
            current_rebinding_only=True,Native_process_set_unchanged=True,
            current_boundaries={k:dict(fresh_inputs=len(v.snapshots),final_fresh_hashes=v.final_fresh_hashes,closed=True)for k,v in readers.items()})
    except(ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt)as error:
        row.update(**p.runtime.io.safe_failure(error))
        if isinstance(error,ValueError)and re.fullmatch(r'PROBE666_[A-Z0-9_]{1,100}',str(error)):row['error_code']=str(error)
    finally:
        guard.close();row.update(cleanup=guard.cleanup and all(v['cleanup']for v in row['steps']),
            source_pins=[]if'source'not in readers else list(readers['source'].snapshots.values()),
            fresh_inputs=0 if'source'not in readers else len(readers['source'].snapshots),
            final_fresh_hashes=0 if'source'not in readers else readers['source'].final_fresh_hashes,
            elapsed_seconds=round(time.monotonic()-start,3),system_CPU_max=max((v['system_cpu_percent']for v in guard.samples),default=None),
            available_RAM_min_percent=min((v['available_ram_percent']for v in guard.samples),default=None))
        value,_=p.retention.retain(r.c.ROOT,'implementation/p09/evidence/private/p09-361-block-selection-recovery667-audit001-forensic',row)
        pin=p.publish(OUTPUT,value)
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','cleanup','observations_recorded','fresh_inputs','final_fresh_hashes',
            'elapsed_seconds','system_CPU_max','available_RAM_min_percent')},'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('RECOVERED667_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
