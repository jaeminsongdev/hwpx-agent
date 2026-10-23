"""390: actual EMPTY resource-Job configuration/readback/cleanup, not a jobless/native session."""
import json
import time
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import crossref_external_host_inspection as subject
import inspect_external_crossref_host as external

OUTPUT='implementation/p09/evidence/p09-361-external-crossref-empty-limits390.v1.json'
DRIVER='tools/p09/run_external_crossref_empty_limits.py'
ENTRY='implementation/p09/evidence/p09-361-external-crossref-host-inspection-run007.v1.json'
PATHS={external.SELF,external.MODULE,external.TEST,'tools/p09/crossref_native_host_limits.py',
    'tools/p09/crossref_native_startup.py','tools/p09/crossref_owned_host_process.py','tools/p09/conservative_maintenance.py',
    'tools/p09/named_style_verification_runtime.py','tools/p09/prepared_run_closure_v1.py'}


def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'EXTERNAL_EMPTY_LIMITS_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_EXTERNAL_EMPTY_JOB_LIMITS',own_cpu_selection=selection,
        actual_Hangul_COM_or_child_started=False,native_or_worker_process_assigned=False,
        native_preassignment_or_COM_owner_qualified=False,fixed_eight_executed=False,native_startup_qualified=False,
        Native011_executed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);code=external.load_code_proof(q);entry=r.compact.unpack(q.json(ENTRY))
        c.require(q.snapshots[external.CODE]['sha256']=='f8dce9618217b420958ed48047c8782f6ce178f072c4f2e96cd06ce42c033fef'
            and code['fresh_inputs']==code['final_fresh_hashes']==200,'EXACT389_CURRENT24_CONTRACTS')
        c.require(q.snapshots[ENTRY]['sha256']=='ac9a5b961e595bc571942447e712533a40c63a7f3f7a0958a104bee3414e0d91'
            and entry['state']=='DENIED_EXTERNAL_HOST_PREREQUISITES_NO_NATIVE_STARTED'and entry['cleanup']
            and entry['fresh_inputs']==entry['final_fresh_hashes']>0
            and entry['observation']['prerequisites']['failed_prerequisites']==['caller_lifecycle_native_safe']
            and not entry['observation']['process_created'],'ACTUAL_CLI007_ROOT_JOB_DENIAL_COMPLETE_BEFORE_NATIVE')
        pins={p['path']:p for p in code['source_pins']}
        for path in sorted(PATHS):c.require(q.pin(path)==pins[path],'SAME_VERIFIED_INSPECTION_NATIVE_LIMITS_AND_HOST_PROTECTION_SOURCE')
        q.pin(DRIVER)
        def no_native_admission():raise ValueError('EXTERNAL_EMPTY_JOB_NATIVE_ADMISSION_MUST_NOT_BE_CALLED')
        row['actual_empty_resource_layout']=subject.empty_resource_layout(guard.windows,guard.check,no_native_admission)
        c.require(row['actual_empty_resource_layout']['empty_jobs_closed']and not row['actual_empty_resource_layout']['child_started_or_assigned'],
            'ACTUAL_BOTH_EMPTY_JOBS_CLOSED_WITHOUT_PROCESS_ASSIGNMENT')
        q.finish();guard.check(force=True);row.update(state='PASS_ACTUAL_EMPTY_NATIVE7_WORKER1_LIMITS_AND_CLEANUP_NOT_JOBLESS_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            next_work='user_external_inspection001_then_live_factory_preassignment_and_COM_owner_connection_before_fixed_eight')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        row.update(error_type=type(error).__name__,error_code=external.safe_code(error))
        if q is not None:
            try:q.finish();row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
            except(ValueError,OSError,KeyError,TypeError,AttributeError):row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,r.compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','actual_empty_resource_layout','fresh_inputs','final_fresh_hashes','cleanup',
            'elapsed_seconds','system_CPU_max','available_RAM_min_percent')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
