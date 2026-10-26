"""Bind six closed684 captures and preserve failed seventh; no Native replay."""
import json,re,subprocess,sys,time
from pathlib import Path
import run_prepared_bookmark_native684 as old
r=old.r
SELF='tools/p09/audit_prepared_bookmark688.py'
OUTPUT='implementation/p09/evidence/p09-361-prepared-bookmark688-retained-six001.v1.json'
FAILED_SHA='970f50e7fad3b67c8f150cfd593873898f75d65535a8daf0400f1a399655ab27'

def require(ok,code):
    if not ok:raise ValueError('XREF_RETAIN688_'+code)

def hold(reader,pin):
    observed=reader.snapshots.get(pin['path'])
    if observed is None:observed=reader.pin(pin['path'])
    require(observed==pin,'CURRENT_UNCHANGED_PIN')

def retain(reader):
    value=old.codec.unpack(reader.json(old.OUTPUT),reader.checkpoint)
    require(reader.snapshots[old.OUTPUT]['sha256']==FAILED_SHA and value['state']=='FAILED684_BLOCK_PRODUCT_CAPTURE'
        and value['error_code']=='XREF_PREPARED631_DRAIN_SINGLE_RETIREMENT_PER_SESSION'
        and value['cleanup']is True and value['fixed_eight_executed']is False
        and value['fresh_inputs']==value['final_fresh_hashes']==974,'EXACT_FAILED684_NOT_RECLASSIFIED')
    for pin in value['source_pins']:hold(reader,pin)
    handler=value['capture_worker']['handler_summary'];scope=handler['protocol']['scope'];protocol=handler['protocol']['protocol']
    require(value['capture_worker']['cleanup']is True and value['capture_worker']['cleanup_pending']is False
        and value['capture_worker']['io_threads_joined']is True and handler['worker_lease_closed']is True
        and len(value['case_source_boundaries'])==6 and len(scope['retired_sessions'])==13
        and scope['finished_cases']==[dict(case_index=i,case_status='returned')for i in range(1,7)]
        and protocol['completed_callback_cases']==scope['finished_cases'],'SIX_CLOSED_CASES_ONLY')
    roots=dict(source=r.c.ROOT,native=Path(old.runtime.base.installed.native.EXECUTABLE).parent,
        shell=Path(old.runtime.base.candidate.original.SHELL).parent,runtime=old.runtime.prepared.inspection.fixed.PYTHON.parent)
    readers={key:r.a.AcceptanceReader(root,reader.checkpoint)for key,root in roots.items()if key!='source'};readers['source']=reader
    union={key:{}for key in roots}
    for i,boundary in enumerate(value['case_source_boundaries'],1):
        require(boundary['label']=='case'+str(i)and old.runtime.sections.closed_boundary(boundary),'WHOLE_CLOSED_CASE_INPUT_BOUNDARY')
        for label,detail in boundary['readers'].items():
            for pin in detail['pins']:
                prior=union[label].get(pin['path']);require(prior is None or prior==pin,'SAME_INPUT_ACROSS_RETAINED_CASES');union[label][pin['path']]=pin
    for label,pins in union.items():
        for pin in pins.values():hold(readers[label],pin)
    rows=[]
    for i in range(1,7):
        profiles=scope['retired_sessions'][2*(i-1):2*i]
        require(all(p['case_index']==i for p in profiles),'EXACT_CASE_OWNER_ORDINALS')
        rows.append(old.runtime.evidence.captured(reader,old.runtime.directory(i),i,profiles))
    seventh=reader.json(old.runtime.directory(7)+'/case-trace.json')
    require(seventh['state']=='capture_started_semantics_unqualified'and seventh['phase']=='create_reopen_session'
        and seventh['error_code']=='P09_XREF_BIND_HOST_REPLY_EOF'and seventh['source_identity_preserved']is False,'SEVENTH_PARTIAL_NOT_ACCEPTED')
    partial={name:reader.pin(old.runtime.directory(7)+'/'+name)for name in('case-trace.json','initial.hwpx','saved.hwpx','initial-page-001.bmp')}
    require(not(r.c.ROOT/old.runtime.directory(8)).exists(),'EIGHTH_NOT_RUN')
    for key,q in readers.items():
        if key!='source':q.finish()
    return dict(cases=rows,partial_seventh_preserved=partial,source_failed_receipt=reader.snapshots[old.OUTPUT],
        original_failed684_reclassified=False,retained_case_count=6,new_or_repeated_Native_started=False,
        reference_display_or_navigation_semantics_qualified=False,P09_complete=False)

def main():
    require(sys.argv[1:]==['--audit-no-native']and not(r.c.ROOT/OUTPUT).exists(),'MODE_IMMUTABLE')
    r.tools.select_own_single_cpu();r.shared.host.configure_host_policy(r.c)
    guard=r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))();q=None;begin=time.monotonic()
    row=dict(state='FAILED688_RETAIN_SIX',Native_started=False,P09_complete=False)
    try:
        guard.acquire();q=r.a.AcceptanceReader(r.c.ROOT,guard.check);q.pin(SELF)
        row['retained']=retain(q);q.finish();guard.check(force=True)
        row['state']='QUALIFIED688_SIX_CLOSED684_CAPTURES_RETAINED_SEVENTH_PARTIAL_NOT_PROMOTED'
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError,KeyboardInterrupt)as error:row.update(**old.runtime.io.safe_failure(error))
    finally:
        guard.close();row.update(cleanup=guard.cleanup,source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),
            final_fresh_hashes=0 if q is None else q.final_fresh_hashes,elapsed_seconds=round(time.monotonic()-begin,3),
            system_CPU_max=max((v['system_cpu_percent']for v in guard.samples),default=None),available_RAM_min_percent=min((v['available_ram_percent']for v in guard.samples),default=None))
        value,_=old.publisher.retention.retain(r.c.ROOT,'implementation/p09/evidence/private/p09-361-prepared-bookmark688-retained-six001-forensic',row)
        pin=old.publisher.publish(OUTPUT,value)
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','cleanup','fresh_inputs','final_fresh_hashes','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('QUALIFIED688_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
