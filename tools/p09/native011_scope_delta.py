"""Explicit case165 readonly-worker scope additions, not a Native runner.

The eight roles are fixed. Existing partition/history is retained; the runtime
adapter only accepts a not-yet-opened original Batch and returns a new plan.
The diagnostic CLI derives a minimal current-scope proposal, not a whole
Native011 closure or authority to reuse worker byte boundaries.
"""
import hashlib
import json
from types import SimpleNamespace as NS
import current_stored_runtime_scope as scope
import native011_scope_map as mapping

SELF='tools/p09/native011_scope_delta.py'
PREFIX='implementation/p09/evidence/p09-361-case165-'
CODE=('tools/p09/native011_ready_worker.py','tools/p09/native011_preparation.py',
    'tools/p09/native011_worker_transport.py','tools/p09/native011_zlib_binding.py',
    'tools/p09/native011_worker_preparation.py')
DATA=(PREFIX+'successor-run011-zlib-manifest001.v1.json',
    PREFIX+'successor-worker-bootstrap011.zlib.v1.json',
    PREFIX+'successor-worker-capsule011.compact.zlib.v1.json')
ROLES=CODE+DATA


def require(ok,code):
    if not ok:raise ValueError('NATIVE011_SCOPE_DELTA_'+code)


def plain(rows):return {name:dict(pin) for name,pin in rows.items()}


def digest(rows):
    raw=json.dumps(rows,sort_keys=True,ensure_ascii=True,allow_nan=False,separators=(',',':')).encode('ascii')
    return hashlib.sha256(raw).hexdigest()


def derive(worker_pins,prior_current,prior_logical):
    wanted=scope.pins(worker_pins)
    current=scope.pins(list(prior_current.values()));logical=scope.pins(list(prior_logical.values()))
    require(current==prior_current and logical==prior_logical,'EXACT_OLD_MAPPING_KEYS')
    missing=set(wanted)-set(current)
    require(missing==set(ROLES),'ONLY_EIGHT_NAMED_MISSING_ROLES_NOT_ARBITRARY_SCOPE_UNION')
    require(not missing & set(logical),'NEW_CONTROL_NOT_PRIOR_LOGICAL_RECLASSIFICATION')
    require(all(current[name]==pin for name,pin in wanted.items() if name not in missing),
        'EXISTING_WORKER_PINS_DIRECT_CURRENT_NOT_ALIAS_OR_CONFLICT')
    additions={name:dict(wanted[name]) for name in ROLES}
    return dict(schema_version='hwpx-agent.p09-native011-worker-scope-delta/v1',index=165,
        source_epoch='Readonly inherited-event-worker001, not product entry qualification',
        control_code_pins=[additions[n] for n in CODE],control_data_pins=[additions[n] for n in DATA],
        additions=additions,prior_current_count=len(current),prior_current_sha256=digest(current),
        required_worker_count=len(wanted),required_worker_sha256=digest(wanted),
        whole_native011_scope_qualified=False,worker_IO_exemptions_applied=False)


def extend_plan(plan,delta,worker_pins,batch,checkpoint):
    """Construct an original Batch with only the explicit new control inputs."""
    require(callable(checkpoint),'ORIGINAL_CHECKPOINT_REQUIRED');checkpoint()
    old=plan.batch;old.check()
    require(type(old) is batch.Batch and old.first_index==165 and old.phase=='NEW' and old.parent_connection is None
        and old.initial is old.final is old.active is None and not old.cases
        and not old.metadata_reader_active,'UNOPENED_ORIGINAL_BATCH_ONLY')
    require(plain(old.whole)==plain(plan.whole) and plain(old.current)==plain(plan.current)
        and plain(old.history)==plain(plan.history),'PLAN_IS_EXACT_ORIGINAL_BATCH_PARTITION')
    current,whole,history,logical=(plain(getattr(plan,n)) for n in ('current','whole','history','logical'))
    actual=derive(worker_pins,current,logical)
    require(actual==delta,'EXACT_REDERIVED_EIGHT_ROLE_DELTA')
    additions=scope.pins(list(delta['additions'].values()))
    require(not set(additions)&(set(history)|set(whole)),'NO_EXISTING_HISTORY_OR_SOURCE_RECLASSIFICATION')
    new_current=scope.extend(current,additions);new_whole=scope.extend(whole,additions)
    new_logical=scope.extend(logical,additions)
    wanted=scope.pins(worker_pins)
    require(all(new_current.get(n)==p for n,p in wanted.items()),'EVERY_WORKER_PIN_EXACT_IN_NEW_CURRENT')
    next_batch=batch.Batch(new_whole,new_current,history,first_index=old.first_index,
        checkpoint=checkpoint,identity=old.identity)
    require(plain(next_batch.history)==history,'EXACT_PRESERVATION_PARTITION_UNCHANGED')
    checkpoint()
    return NS(**{**vars(plan),'batch':next_batch,'whole':new_whole,'current':new_current,
        'history':history,'logical':new_logical}),dict(added_control_inputs=len(additions),
        preserved_current_inputs=len(current),preserved_history_inputs=len(history),
        full_worker_pin_coverage=len(wanted),original_batch_not_mutated=True,
        actual_Native_parent_or_Frame_constructed=False,worker_IO_exemptions_applied=False)


def main():
    import argparse,re,sys,time,traceback
    from pathlib import Path
    sys.dont_write_bytecode=True
    parser=argparse.ArgumentParser();parser.add_argument('--attempt',type=int,required=True)
    args=parser.parse_args();require(1<=args.attempt<=8,'BOUNDED_PROPOSAL_ATTEMPT')
    denied=[]
    def deny(event,arguments):
        if event in ('subprocess.Popen','os.system','os.startfile','os.exec','os.posix_spawn','os.fork'):
            denied.append(event);raise ValueError('NATIVE011_SCOPE_DELTA_PROCESS_DENIED')
    sys.addaudithook(deny)
    import accept_case112_current_epoch as a,conservative_maintenance as c
    import prepared_run_closure_v1 as host,owned_cpu_baseline_v1 as baseline
    import preparation_attributed_cpu_v1 as policy,distinct_final_sample_guard_v1 as final
    import successor_preparation_workspace_v1 as publisher
    host.configure_host_policy(c)
    guard=baseline.guard_type(policy.guard_type(final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    output=f'implementation/p09/evidence/p09-361-native011-minimal-scope-proposal-attempt{args.attempt:03}.v1.json'
    row=dict(state='FAILED_NATIVE011_MINIMAL_SCOPE_PROPOSAL_NOT_NATIVE',GO_authorized=False,
        accepted_count_delta=0,actual_scope_modified=False,actual_projected_Frame_constructed=False)
    q=None;started=time.monotonic()
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        require(not (c.ROOT/output).exists(),'NEW_PROPOSAL_RESULT')
        for name in (SELF,mapping.SELF,scope.SELF):q.pin(name)
        prior=a.read_exact(q,mapping.PRIOR);worker=a.read_exact(q,mapping.WORKER)
        a.fields(prior,dict(state='DEFERRED_NOT_STARTED',task='case165-current-r010-tests',
            worker_created=False,product_body_observed=False),'FAILED_PRIOR_ONLY_NOT_NATIVE011')
        representation=prior['source_frame']['explicit_source_input_representation']
        compared=mapping.compare(worker['source_pins'],representation,prior_frame_count=prior['source_frame']['input_count'])
        require(compared['counts']['DIRECT_PIN_DECLARED']==190
            and compared['counts']['MISSING_FROM_PRIOR_DECLARATION']==8
            and sum(compared['counts'].values())==198,'SAME_REAL198_REQUIRED_INPUT_COMPARISON')
        physical=scope.pins(representation['physical_source_freeze']);logical=scope.pins(representation['semantic_source_freeze'])
        delta=derive(worker['source_pins'],physical,logical)
        for name,pin in delta['additions'].items():a.exact(q.fresh_pin(name),pin,'ACTUAL_CURRENT_EIGHT_NEW_CONTROL_PINS')
        proposed=scope.extend(physical,delta['additions']);wanted=scope.pins(worker['source_pins'])
        require(all(proposed.get(n)==p for n,p in wanted.items()),'PLANNED_ALL198_EXACT_NOT_LIVE_HANDLES')
        q.finish();guard.check(force=True)
        require(not denied,'NO_PRODUCT_OR_PROCESS')
        row.update(state='PROPOSED_EIGHT_EXPLICIT_CONTROLS_FOR_REAL198_NOT_FULL_NATIVE011_SCOPE',delta=delta,
            baseline_current_count=len(physical),minimal_proposed_current_count=len(proposed),
            baseline_declared_bytes=sum(p['bytes'] for p in physical.values()),
            added_declared_bytes=sum(p['bytes'] for p in delta['additions'].values()),
            proposed_current_sha256=digest(proposed),planned_exact_worker_pin_coverage=198,
            old2929_current_files_freshly_hashed=False,new_eight_files_freshly_hashed=True,
            preservation_partition_not_available_from_case_receipt=True,
            full_parent_plan_or_600_second_cost_or_helper_union_qualified=False,
            original_failed_native010_promoted=False,worker_IO_exemptions_applied=False)
    except (ValueError,OSError,KeyError,IndexError,TypeError,AttributeError,MemoryError,NameError,ImportError) as error:
        row['error_type']=type(error).__name__
        row['error_code']=error.args[0] if error.args and type(error.args[0]) is str and re.fullmatch(
            '[A-Za-z0-9_]{1,160}',error.args[0]) else 'CLOSED_SCOPE_PROPOSAL_FAILURE'
        row['error_frames']=[dict(file=Path(f.filename).name,function=f.name,line=f.lineno)
            for f in traceback.extract_tb(error.__traceback__)[-5:]]
    finally:
        guard.close();row.update(cleanup_confirmed=guard.cleanup,elapsed_seconds=time.monotonic()-started,
            source_pins=[] if q is None else list(q.snapshots.values()),resource_samples=guard.samples,
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
            process_creation_attempts=len(denied))
        pin=publisher.publish(c.ROOT,output,row,NS(require=c.require,exact=a.exact))
        print(json.dumps(dict(state=row['state'],error_code=row.get('error_code'),error_frames=row.get('error_frames'),
            baseline_current_count=row.get('baseline_current_count'),minimal_proposed_count=row.get('minimal_proposed_current_count'),
            baseline_declared_bytes=row.get('baseline_declared_bytes'),added_bytes=row.get('added_declared_bytes'),
            cleanup=row['cleanup_confirmed'],fresh=row['fresh_inputs'],final=row['final_fresh_hashes'],
            elapsed=row['elapsed_seconds'],receipt=pin)),flush=True)
    return 0 if row['state'].startswith('PROPOSED_') and row['cleanup_confirmed'] else 2


if __name__=='__main__':raise SystemExit(main())
