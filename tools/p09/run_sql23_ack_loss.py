"""New application ack-loss4 campaign. Reuse unchanged real-storage source closure, not its tests."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_sql23_storage as previous
native,shared,c,a,tools,compact,harness,audit=previous.native,previous.shared,previous.c,previous.a,previous.tools,previous.compact,previous.harness,previous.audit
OUTPUT='implementation/p09/evidence/p09-361-sql23-ack-remaining295.v1.json'
FAILED='implementation/p09/evidence/p09-361-sql23-ack-loss292.v1.json'
PRIOR_CASE='implementation/p09/evidence/p09-361-sql23-ack-case1-closure294.v1.json'
DRIVER='tools/p09/run_sql23_ack_loss.py'
WORKER='tools/p09/native_postgres_ack_loss.py'
PROBE='crates/product-cli/examples/sql23_ack_loss.rs'
NEW={DRIVER,WORKER,PROBE,'crates/product-cli/examples/sql23_ack_loss/repository.rs','crates/product-cli/examples/sql23_ack_loss/campaign.rs',
    'crates/product-cli/examples/sql23_ack_loss/setup.rs',FAILED,PRIOR_CASE}
EXE='target/debug/examples/sql23_ack_loss.exe'
SCRATCH='target/p09-sql23-ack-scratch-295'
def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'ACK_IMMUTABLE_RUN_EXISTS');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;observations=None;started=time.monotonic();row=dict(state='FAILED_SQL23_ACK_LOSS',steps=[],own_cpu_selection=selection,
        accepted_count_delta=0,P09_gate='OPEN',P10_started=False,actual_P09_product_or_Native_execution=False,Native011_executed=False,prior_Native_replayed=False,
        actual_network_fault=False,synthetic_route_scanner_validator_and_bytes=True,parent_retained_ephemeral_test_keys=True,
        system_or_security_settings_changed=False,operational_database_accessed=False,previously_passed_tests_reexecuted=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);last=compact.unpack(q.json(previous.OUTPUT))
        prior_case=compact.unpack(q.json(PRIOR_CASE));c.require(q.snapshots[PRIOR_CASE]['sha256']=='ff84f93fb99f57b8b5cd308ec6e9d6724a75451ba6cf45996cf7a3f8d533c8fb'
            and prior_case['cleanup']and prior_case['accepted_ack_cases']==['register_after']and prior_case['fresh_inputs']==prior_case['final_fresh_hashes']==684,'EXACT294_PRIOR_CASE_ACCEPTED_WITHOUT_REPLAY')
        original={p['path']:p for p in prior_case['source_pins']}
        q.pin(PROBE);audit.inverse(q.text(PROBE).replace('hwpx-agent-p09-pg18-ack-295','hwpx-agent-p09-pg18-ack-293'),original[PROBE],'ONLY_NEW_OWNED_CASE_ROOT_CHANGED')
        setup='crates/product-cli/examples/sql23_ack_loss/setup.rs';q.pin(setup)
        audit.inverse(q.text(setup).replace("case()?.replace('_',\"-\")","case()?"),original[setup],'ONLY_NONFIRST_TENANT_FIXTURE_SLUG_UNDERSCORE_CORRECTED')
        failed=compact.unpack(q.json(FAILED));c.require(q.snapshots[FAILED]['sha256']=='74a64755cfebd23c3a1e012765b1fd58ea3ffb0580e446dde053f535d90c2a87'
            and failed['cleanup']and failed['error_code']=='STOP_PREPARATION_SYSTEM_PRESSURE90','EXACT292_SYSTEM_PRESSURE_STOP_RETAINED_NOT_ACCEPTED')
        frozen={p['path']:p for p in failed['source_pins']}
        for name in('crates/product-cli/examples/sql23_ack_loss/repository.rs','crates/product-cli/examples/sql23_ack_loss/campaign.rs'):
            q.pin(name);c.require(q.snapshots[name]==frozen[name],'ORIGINAL_ACK_INJECTION_AND_RECOVERY_EXPECTATIONS_NOT_WEAKENED')
        c.require(q.snapshots[previous.OUTPUT]['sha256']=='d5d44414d97a1cd24158839bcf367d616eabc03ab417abb392d796688cc8a8b8'
            and last['cleanup']and last['fresh_inputs']==last['final_fresh_hashes']==675,'EXACT290_REAL_STORAGE_SOURCE_CLOSURE')
        old={p['path']:p for p in last['source_pins']}
        for name in sorted(previous.inventory(guard.check)|NEW):
            q.pin(name)
            if name not in NEW:c.require(q.snapshots[name]==old[name],'ALL_COMPILED_SERVICES_ENGINE_SQL_CRYPTO_AND_PRIOR_PROBE_BODIES_UNCHANGED')
        import native_postgres_ack_loss as candidate
        scratch=c.ROOT/SCRATCH;parent=c.ROOT/'target'
        c.require(parent.is_dir()and not parent.is_symlink()and not parent.is_junction()and not scratch.exists()and not candidate.OWNED.exists()
            and not(c.ROOT/candidate.OBSERVATION).exists(),'ACK_NEW_OWNED_DATABASES_BLOBS_OBSERVATION_AND_TEMP')
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                p=Path(value).absolute()
                if p.is_relative_to(c.ROOT/'tools/p09')and p.suffix=='.py':q.pin(p.relative_to(c.ROOT).as_posix())
        for name in('tools/p09/fixtures/native_postgres_hba.conf','target/p09-native-postgres-18.6-5-278/runtime-manifest.json'):q.pin(name)
        scratch.mkdir();env=audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch),PYTHONPATH=str(c.ROOT/'tools/p09'),PYTHONDONTWRITEBYTECODE='1')
        from run_search_mutation_dispatch_recovery import snapshot
        print(json.dumps(dict(state='SQL23_ACK_PREFLIGHT',source_inputs=len(q.snapshots),old_tests_replayed=False)),flush=True)
        harness.run_one('compile_sql23_ack_probe',[harness.CARGO,'build','--offline','--locked','-j','1','-p','hwpx-agent-cli','--example','sql23_ack_loss','--message-format=short'],
            set(),guard,env,row,observe_capture=snapshot)
        c.require(row['steps'][-1]['diagnostics']==[],'ACK_BUILD_NO_DIAGNOSTICS');q.pin(EXE);env['P09_ACK_PROBE_SHA256']=q.snapshots[EXE]['sha256']
        try:result=native.runner.run_owned('actual_SQL23_application_ack_loss4',[sys.executable,str(c.ROOT/WORKER),'--owned-ack-loss4'],guard,env,row,300)
        finally:
            if(c.ROOT/candidate.OBSERVATION).is_file():observations=q.json(candidate.OBSERVATION)
        c.require(result['observation_path']==candidate.OBSERVATION and result['observation_sha256']==q.snapshots[candidate.OBSERVATION]['sha256']
            and result['observation_bytes']==q.snapshots[candidate.OBSERVATION]['bytes'],'ACK_EXACT_OBSERVATION')
        c.require(observations['state']=='PASS_REAL_SQL23_APPLICATION_ACK_LOSS4_RESTART_RECOVERY_NOT_NETWORK_PRODUCT_OR_P09_GATE'
            and [r['case']for r in observations['cases']]==list(candidate.ACTIVE_CASES)and all(r['complete']for r in observations['cases'])
            and len(observations['postmasters'])==7 and observations['all_owned_postmasters_normal_stop'],'ACK_ONLY_REMAINING_THREE_CASES_AND_SEVEN_NORMAL_STOPS')
        c.require(observations['actual_initdb_count']==observations['actual_schema23_application_count']==1 and observations['isolated_tenants']==4
            and len(observations['case_checkpoint_pins'])==3 and observations['prior_register_after_executed']is False,'ACK_ONE_CLUSTER_SCHEMA_AND_THREE_DURABLE_CASE_CHECKPOINTS_NO_PRIOR_REPLAY')
        for p in observations['case_checkpoint_pins']:
            evidence=q.json(p['path']);c.require(q.snapshots[p['path']]==p and evidence['compiled_probe_sha256']==q.snapshots[EXE]['sha256']
                and len(evidence['postmasters'])==2 and all(s['normal_stop']for s in evidence['postmasters']),'ACK_EXACT_FRESH_CASE_COMPLETION_EVIDENCE')
        for observed in observations['cases']:
            c.require(len(observed['probes'])==4 and len(observed['blob_snapshots'][0])==6 and observed['blob_snapshots'][0]==observed['blob_snapshots'][1]
                and observed['snapshots'][0]['attempt']==observed['snapshots'][1]['attempt']==1 and observed['probes'][-1]['execution_retried']is False,'ACK_CASE_REAL_RESTART_READBACK_NO_EXTRA_ATTEMPT')
        c.require(not any(scratch.iterdir()),'ACK_TEMP_EMPTY');q.finish();guard.check(force=True)
        row.update(state='PASS_REAL_SQL23_ACK_LOSS4_AND_RESTART_RECOVERY_NOT_NETWORK_PRODUCT_OR_P09_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            current_executed_ack_cases=3,prior_completed_ack_cases_reused=1,ack_case_union=4,actual_network_fault_cases=0,actual_AEAD_objects_current=18,
            actual_committed_reconciliation=1,actual_negative_committed_oracles_current=2,unresolved_no_commit_cases_union=2,
            actual_completion_ack_observed_success_without_second_mutation=1,
            next_work='remaining_actual_negative_boundaries_transport_faults_if_required_and_qualified_P09_product_dispatcher')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        code=str(error);row.update(error_type=type(error).__name__,error_code=code if re.fullmatch('[A-Za-z0-9_]{1,160}',code)else'ACK_FAILURE_NO_RAW_VALUES')
    finally:
        if observations is not None:row.update(actual_database_stage=observations['stage'],last_case=None if not observations['cases']else observations['cases'][-1])
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            columns=list(samples[0]);values=[[s[k]for k in columns]for s in samples];c.require([dict(zip(columns,v))for v in values]==samples,'ACK_LOSSLESS_RESOURCE_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=columns,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        last=None if observations is None or not observations['cases']else observations['cases'][-1]
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent','actual_database_stage')},
            'last_probe':None if last is None or not last['probes']else last['probes'][-1],
            'steps':[{k:s.get(k)for k in('stage','exit_code','diagnostics','result','cleanup')}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
