"""Bind existing Native page inventories to exact initial/reopened bytes. No new Native."""
import json,sys,time
from pathlib import Path
import named_style_verification_runtime as r
import resource_bundle714 as journal
import run_prepared_bookmark_native631 as p
SELF='tools/p09/inspect_single_page732.py'
PRIOR='implementation/p09/evidence/p09-361-bookmark-results730-product001.v1.json'
CAPTURE='implementation/p09/evidence/p09-361-block-bookmark693-capture-readback001.v1.json'
MANIFEST='implementation/p09/evidence/p09-361-block-bookmark693-product-inputs.v1.json'
INPUT='implementation/p09/evidence/p09-361-single-page732-inputs.v1.json'
OUTPUT='implementation/p09/evidence/p09-361-single-page732-inspection001.v1.json'
def require(ok,code):
    if not ok:raise ValueError('XREF_PAGE732_'+code)
def main():
    require(sys.argv[1:]==['--existing-capture-inventories-only']and not(r.c.ROOT/OUTPUT).exists()and not(r.c.ROOT/INPUT).exists(),'IMMUTABLE_MODE')
    r.tools.select_own_single_cpu();r.shared.host.configure_host_policy(r.c)
    guard=r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))();observer=q=None;begin=time.monotonic()
    row=dict(state='FAILED732_CAPTURE_PAGE_INVENTORIES',Native_started=False,P09_complete=False)
    try:
        observer=journal.Attached(guard);guard.acquire();observer.phase('input_binding');q=r.a.AcceptanceReader(r.c.ROOT,guard.check)
        prior=p.codec.unpack(q.json(PRIOR),guard.check);capture=p.codec.unpack(q.json(CAPTURE),guard.check)
        require(q.snapshots[PRIOR]['sha256']=='e7553c1ae5f0783a745a5741aabc13a6aee93fd5f280b83851a7ce166bb1384b'and prior['cleanup']is True
            and q.snapshots[CAPTURE]['sha256']=='63412d6663f04184b91a58045eca3ecf1f84f2a4264e93afc7c2207669ba60f3'and capture['cleanup']is True,'EXACT_PRODUCER_AND_RESULT_BASELINES')
        pins={v['path']:v for v in prior['source_pins']};manifest=q.json(MANIFEST);rows=[]
        for index in(1,2,7,8):
            case=manifest['cases'][index-1];folder=Path(case['stages']['initial']['pin']['path']).parent.as_posix();name=folder+'/case-trace.json'
            require(q.pin(name)==pins[name],'EXACT_PREVIOUSLY_PRODUCER_BOUND_TRACE');trace=q.json(name)
            require(trace['state']=='capture_returned_semantics_unqualified'and trace['source_identity_preserved']is True
                and trace['error_code']is None and trace['cleanup_error']is None and trace['SDK_insertion_invoked']is False
                and all(s['quit_invoked']is True and s['remaining_owned_process_count']==0 and s['cleanup_error']is None for s in trace['sessions']),'CLOSED_CAPTURE_NOT_NEW_EXECUTION')
            for label,session in(('initial',0),('reopened',1)):
                pin=case['stages'][label]['pin'];require(q.pin(pin['path'])==pin,'EXACT_HWPX_SNAPSHOT')
                artifact=trace['artifacts'][label+'.hwpx'];require(artifact['pin']=={k:pin[k]for k in('bytes','sha256')}
                    and artifact['owner']==trace['sessions'][session]['process'],'SAME_EXACT_NATIVE_SNAPSHOT_OWNER')
                images={k:v for k,v in trace['artifacts'].items()if k.startswith(label+'-page-')}
                require(set(images)=={label+'-page-001.bmp'},'ONE_WHOLE_RENDERED_PAGE')
                image=images[label+'-page-001.bmp'];ipath=folder+'/'+label+'-page-001.bmp';require(q.pin(ipath)==pins[ipath]
                    and image['pin']=={k:pins[ipath][k]for k in('bytes','sha256')}
                    and image['owner']==artifact['owner']and image['page_count']==1 and image['page_number']==0,'BOUND_PAGECOUNT_ONE_NOT_FIELD_CACHE_INFERENCE')
                rows.append(dict(case_index=index,stage=label,snapshot=pin,trace=pins[name],page_image=pins[ipath],page_count=1,page_indices=[0],
                    previously_closed_native_producer_bound=True,scope='specific_snapshot_not_saved_candidate_or_general_flow'))
        for module in tuple(sys.modules.values()):
            name=getattr(module,'__file__',None)
            if name:
                path=Path(name)
                if path.is_relative_to(r.c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(r.c.ROOT).as_posix())
        q.pin(SELF);observer.phase('final_source');q.finish();observer.phase('final_resource');guard.check(force=True)
        payload=dict(schema='hwpx-agent.p09.existing-single-page-snapshot-inputs/v1',source_capture_receipt=q.snapshots[CAPTURE],
            source_result_receipt=q.snapshots[PRIOR],snapshots=rows,saved_or_candidate_extent_inferred=False,Native_started=False,P09_complete=False)
        bound=r.shared.publisher.publish(r.c.ROOT,INPUT,payload,p.NS(require=r.c.require,exact=r.a.exact))
        row.update(state='OBSERVED732_EXISTING_INITIAL_REOPENED_SINGLE_PAGE8_PRODUCER_BOUND_NOT_GENERAL_FLOW',input_manifest=bound,snapshots=rows)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt)as error:row.update(**p.runtime.io.safe_failure(error))
    finally:
        guard.close();closed=True if observer is None else observer.close()
        if observer is not None:row['phase_resources']=observer.packet()
        row.update(cleanup=guard.cleanup and closed,source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),
            final_fresh_hashes=0 if q is None else q.final_fresh_hashes,elapsed_seconds=round(time.monotonic()-begin,3),
            system_CPU_max=max((v['system_cpu_percent']for v in guard.samples),default=None),available_RAM_min_percent=min((v['available_ram_percent']for v in guard.samples),default=None))
        value,_=p.retention.retain(r.c.ROOT,'implementation/p09/evidence/private/p09-361-single-page732-inspection001-forensic',row);pin=p.publish(OUTPUT,value)
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','cleanup','fresh_inputs','final_fresh_hashes','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},'resource_samples':len(guard.samples),'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('OBSERVED732_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
