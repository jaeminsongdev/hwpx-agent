"""Finish source closure for the already completed293 case; do NOT run its product again."""
import json,re,time
from types import SimpleNamespace as NS
import run_sql23_ack_loss as prior
shared,c,a,tools,compact=prior.shared,prior.c,prior.a,prior.tools,prior.compact
OUTPUT='implementation/p09/evidence/p09-361-sql23-ack-case1-closure294.v1.json'
FAILED='implementation/p09/evidence/p09-361-sql23-ack-optimized293.v1.json'
CASE='target/p09-sql23-ack-case-293-register_after.json'
DRIVER='tools/p09/run_sql23_ack_case_closure.py'
def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'ACK_CASE_CLOSURE_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_ACK_CASE_CLOSURE',own_cpu_selection=selection,current_run_Rust_DB_or_execution_replayed=False,
        accepted_count_delta=0,P09_gate='OPEN',P10_started=False,actual_network_fault=False,actual_P09_product_or_Native_execution=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);failed=compact.unpack(q.json(FAILED))
        c.require(q.snapshots[FAILED]['sha256']=='d36048a2df0823fe1b8be4ed8c5afcd5d1259a72baf8e16eb9fc27cda9734471'
            and failed['cleanup']and failed['last_case']['probes'][-1]['sqlstate']=='23514','EXACT293_NONFIRST_TENANT_FIXTURE_FAILURE_RETAINED')
        for pin in failed['source_pins']:q.pin(pin['path']);c.require(q.snapshots[pin['path']]==pin,'ALL_ORIGINAL293_COMPILED_AND_RUNTIME_INPUTS_STILL_EXACT')
        observation=q.json('target/p09-sql23-ack-observations-293.json');case=q.json(CASE)
        c.require(q.snapshots[CASE]['sha256']=='da6dcd0eba3ebc63806da99e0f532d9bc1d0e6975b8e0d9ec2d69e677663d2a1'
            and case['case']==observation['cases'][0]and case['case']['complete']and case['case']['case']=='register_after'
            and len(case['postmasters'])==2 and all(s['normal_stop']for s in case['postmasters']),'ORIGINAL_FIRST_CASE_FULL_RUNTIME_AND_TWO_NORMAL_STOPS')
        c.require(case['compiled_probe_sha256']==q.snapshots[prior.EXE]['sha256']and len(case['case']['probes'])==4
            and all(p['state'].startswith('PASS_')for p in case['case']['probes'])and case['case']['blob_snapshots'][0]==case['case']['blob_snapshots'][1]
            and case['case']['snapshots'][0]==case['case']['snapshots'][1]and case['case']['snapshots'][1]['record_state']=='outcome_unknown'
            and case['case']['probes'][-1]['left_unknown_without_no_effect_or_retry']and case['case']['probes'][-1]['oracle_negative_SQLSTATE55000'],
            'FIRST_CASE_REGISTER_ACK_LOSS_RESTART_PRESERVES_UNKNOWN_NOT_FALSE_SUCCESS_OR_RETRY')
        import native_postgres_ack_loss as worker
        manifest=q.json(worker.cluster.MANIFEST)
        for pin in manifest['runtime_pins']:
            guard.check();p=worker.ASSET/pin['path'];c.require(p.is_file()and not p.is_symlink()and not p.is_junction()
                and p.stat().st_size==pin['bytes']and worker.cluster.runtime.sha_file(p)==pin['sha256'],'ALL1583_RUNTIME_BYTES_UNCHANGED_AFTER_ORIGINAL_FIRST_CASE')
        for step in failed['steps']:
            j=step['owned_job'];c.require(j['owned_tree_empty']and j['job_handle_closed']and j['cleanup_confirmed']and j['last_job_accounting']['active_processes']==0,'ALL293_JOBS_TERMINAL')
        q.pin(DRIVER);q.finish();guard.check(force=True)
        row.update(state='PASS_PRIOR_REAL_SQL23_REGISTER_ACK_CASE1_LATE_SOURCE_CLOSURE_NO_EXECUTION_REPLAY',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            accepted_ack_cases=['register_after'],remaining_ack_cases=['cas_before','cas_after','complete_after'],runtime_files_verified=len(manifest['runtime_pins']),
            original293_batch_stays_failed=True,next_work='correct_nonfirst_fixture_slug_and_run_only_remaining_three_in_fresh_owned_cluster')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        code=str(error);row.update(error_type=type(error).__name__,error_code=code if re.fullmatch('[A-Za-z0-9_]{1,160}',code)else'ACK_CASE_CLOSURE_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
