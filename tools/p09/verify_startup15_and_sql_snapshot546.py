"""Approved initial-wait candidate and SQL denial snapshot fix. Pure models; no process wait/SQL/Native replay."""
import ast,hashlib,importlib.util,json,re,sys,time,unittest
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import search_sql_receipt as layout
import native_postgres_storage as storage
SELF='tools/p09/verify_startup15_and_sql_snapshot546.py'
OUTPUT='implementation/p09/evidence/p09-361-startup15-and-sql-snapshot547.v1.json'
PRIOR='implementation/p09/evidence/p09-361-startup15-and-sql-snapshot546.v1.json'
FIX='implementation/p09/source-archive/p361-startup15-547/'
FAILED='implementation/p09/evidence/p09-361-https-late-revoke-sql545.v1.json'
OBS='target/p09-https-late-revoke-sql26-observation-545.json'
ARCHIVE='implementation/p09/source-archive/p361-https-late-revoke546/'
LEAF='tools/p09/crossref_startup_input_idle.py'
CANDIDATE='tools/p09/crossref_startup_input_idle_candidate546.py'
OLD_TEST='tools/p09/tests/test_crossref_startup_input_idle.py'
NEW_TEST='tools/p09/tests/test_crossref_startup_idle15.py'
SQL_TEST='tools/p09/test_https_denied_snapshot.py'
CAMPAIGN='tools/p09/native_postgres_storage.py'
def load(path,name):
    spec=importlib.util.spec_from_file_location(name,r.c.ROOT/path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
def main():
    c,a,shared=r.c,r.a,r.shared;c.require(sys.argv[1:]==['--pure-models-only'],'P546_PURE_MODELS_ONLY')
    c.require(not(c.ROOT/OUTPUT).exists(),'P546_IMMUTABLE_RECEIPT')
    candidate=load(CANDIDATE,'p546_candidate');new=load(NEW_TEST,'p546_new');prior=load(OLD_TEST,'p546_affected');sql=load(SQL_TEST,'p546_sql')
    prior.subject=candidate
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    started=time.monotonic();q=None
    row=dict(state='FAILED_STARTUP15_CANDIDATE_AND_SQL_SNAPSHOT',own_cpu_selection=selection,actual_Hancom_COM_or_native_wait_or_SQL_or_Cargo_started=False,
        previous_SQL545_or_external003_or_Native_replayed=False,actual_startup15_applied=False,original545_final_fresh_or_restart_reconstructed=False,
        accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        names={SELF,FAILED,OBS,LEAF,CANDIDATE,OLD_TEST,NEW_TEST,SQL_TEST,CAMPAIGN,PRIOR,FIX+'candidate546.py',FIX+'verifier546.py',
            *[ARCHIVE+n for n in('campaign545.py','verifier545.py','input-idle-before.py','input-idle-tests-before.py')],
            'tools/p09/crossref_native_startup.py','tools/p09/crossref_native_host_limits.py','tools/p09/crossref_session_qualification.py',
            'tools/p09/crossref_preassigned_session_scope.py','implementation/p09/tools/crossref-existing-owner.cs',
            'crates/product-cli/examples/sql23_storage/https_late_revoke.rs',
            'crates/product-cli/src/stored_revision_commit.rs','crates/product-cli/src/stored_revision_commit/job.rs',
            'crates/product-cli/src/form_stored_provider/actual_import/https_target_output/atomic_job.rs',
            'crates/revision-service/src/postgres/source_formula_policy/issuer_registry/stored_revision_jobs/atomic_https.rs',
            'migrations/postgres/0023_p09_stored_revision_jobs.up.sql','migrations/postgres/0026_p09_https_policy_atomic_commit.up.sql'}
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':names.add(path.relative_to(c.ROOT).as_posix())
        for path in sorted(names):q.pin(path)
        prior_failure=layout.unpack(q.json(PRIOR))
        c.require(q.snapshots[PRIOR]['sha256']=='ed5df522dbf23b7d196aff362e3a7d755b8cf17ac61d1027f3624f5c7b1a414c'
            and prior_failure['error_code']=='P546_ONLY_APPROVED_STARTUP_BOUND_AND_CLIPPED_SLEEP_NO_GUARD_OWNER_OR_RETRY_CHANGE'
            and prior_failure['fresh_inputs']==210 and prior_failure['final_fresh_hashes']==0 and prior_failure['cleanup']is True
            and 'contracts'not in prior_failure,'P547_PRESERVE546_PREMODEL_FAILURE')
        fixed={SELF:FIX+'verifier546.py',CANDIDATE:FIX+'candidate546.py'}
        for pin in prior_failure['source_pins']:
            actual=q.snapshots[fixed.get(pin['path'],pin['path'])]
            c.require((actual['bytes'],actual['sha256'])==(pin['bytes'],pin['sha256']),'P547_ALL_OTHER546_INPUTS_UNCHANGED')
        c.require(q.text(FIX+'candidate546.py').replace('POLL_SECONDS=.05\n\ndef require','POLL_SECONDS=.05\ndef require')
            .replace("raise ValueError('XREF_NATIVE_STARTUP_INPUT_IDLE_'+code)\n\ndef _wait", "raise ValueError('XREF_NATIVE_STARTUP_INPUT_IDLE_'+code)\ndef _wait")==q.text(CANDIDATE),'P547_ONLY_TWO_BLANK_LINES_CHANGED_NO_ALGORITHM_OR_ASSERTION_CHANGE')
        failed=layout.unpack(q.json(FAILED));observation=q.json(OBS)
        c.require(q.snapshots[FAILED]['sha256']=='03187a840ef6b58027b4a97b7b392c7d7b0229fa2e6cf99f604709c9149e2a3b'
            and failed['state']=='FAILED_HTTPS_LATE_REVOKE_SQL26'and failed['cleanup']is True and failed['fresh_inputs']==871 and failed['final_fresh_hashes']==0,
            'P546_KEEP545_FAILED_ORIGINAL_NO_FINAL_CLOSURE')
        previous={p['path']:p for p in failed['source_pins']}
        c.require((q.snapshots[OBS]['bytes'],q.snapshots[OBS]['sha256'])==(previous[OBS]['bytes'],previous[OBS]['sha256']),'P546_EXACT_PARENT_OBSERVATION_PIN')
        for path in names:
            if path in previous and(path.startswith('crates/')or path.startswith('migrations/')or path=='tools/p09/crossref_native_host_limits.py'):
                c.require(q.snapshots[path]==previous[path],'P546_UNCHANGED_ORIGINAL_PRODUCT_SQL_AND_NATIVE_GUARDS')
        c.require(observation['state']=='FAILED_HTTPS_LATE_REVOKE_SQL26'and observation['stage']=='completed_before_restart'
            and observation['error_code']=='PG_STORAGE_EXACT_COMPLETED_SINGLE_ATTEMPTS_AND_SEALED_HEAD'and observation['snapshots']==[]
            and len(observation['probes'])==3,'P546_KEEP_SNAPSHOT_FAILURE_RESTART_NOT_RUN')
        body=observation['probes'][2]
        c.require(body['state']=='PASS_HTTPS_REAL_SQL26_LATE_REVOCATION_DENIES_ORIGINAL_CAS_RETAINS_EVIDENCE'
            and body['last_app_guard_reads_completed']is True and body['original_SQL_CAS_denied']is True and body['result_intent_precommit_AEAD_retained']is True
            and body['head_generation']==1 and body['attempt']==1 and body['claim_lease_CAS_or_execution_retried']is False,'P546_OBSERVED545_BODY_NOT_WHOLE_RUN_PASS')
        projection=dict(artifacts=7,available=7,jobs=2,succeeded_jobs=1,successful_records=1,attempts=2,authorizations=1,intents=1,revisions=1,seals=1,head=1)
        raw=(json.dumps(projection,separators=(', ',' : '))+'\r\n').encode()
        command=next(v for v in observation['commands']if v['stage']=='completed_before_restart')
        c.require(command['exit_code']==0 and len(raw)==command['stdout_bytes']==191
            and hashlib.sha256(raw).hexdigest()==command['stdout_sha256'],'P546_EXACT_RECORDED_AGGREGATE_STDOUT_SHA_NOT_GUESSED_VALUES')
        stops=[v for v in observation['commands']if v['stage']=='stop_owned_postmaster'];c.require(len(stops)==1 and stops[0]['exit_code']==0,'P546_ONE_OWNED545_POSTMASTER_NORMAL_STOP_NO_RESTART')
        text=q.text(CAMPAIGN);a0=text.index('def denied_snapshot(');b=text.index('def campaign(',a0);text=text[:a0]+text[b:]
        text=text.replace("            if denied:denied_snapshot(receipt,result,expected_artifacts)\n            else:\n                cluster.require(result==expected,'PG_STORAGE_EXACT_COMPLETED_SINGLE_ATTEMPTS_AND_SEALED_HEAD');receipt['snapshots'].append(result)",
            "            if denied:expected.update(succeeded_jobs=1,successful_records=1,revisions=1,seals=1,head=1)\n            cluster.require(result==expected,'PG_STORAGE_EXACT_COMPLETED_SINGLE_ATTEMPTS_AND_SEALED_HEAD');receipt['snapshots'].append(result)")
        r.audit.inverse(text,q.snapshots[ARCHIVE+'campaign545.py'],'P546_ONLY_DENIAL_EXPECTATION_AND_RETAIN_BEFORE_COMPARE_CHANGED_DEFAULT_SUCCESS_UNCHANGED')
        r.audit.inverse(q.text(LEAF),q.snapshots[ARCHIVE+'input-idle-before.py'],'P546_CANDIDATE_NOT_APPLIED_BEFORE_QUALIFICATION')
        text=q.text(CANDIDATE).replace('BOUND_SECONDS=15.0','BOUND_SECONDS=3.0').replace("            remaining=BOUND_SECONDS-(clock()-started)\n            require(remaining>0,'BOUNDED_STARTUP_WAIT_EXPIRED_NO_RETRY')\n            sleep(min(POLL_SECONDS,remaining))",'            sleep(POLL_SECONDS)')
        r.audit.inverse(text,q.snapshots[ARCHIVE+'input-idle-before.py'],'P546_ONLY_APPROVED_STARTUP_BOUND_AND_CLIPPED_SLEEP_NO_GUARD_OWNER_OR_RETRY_CHANGE')
        text=q.text(OLD_TEST).replace('subject.BOUND_SECONDS+.1','3.1').replace('subject.BOUND_SECONDS+1.0','4.0')
        r.audit.inverse(text,q.snapshots[ARCHIVE+'input-idle-tests-before.py'],'P546_ONLY_TWO_AFFECTED_BOUND_ASSERTIONS_CHANGED')
        c.require(candidate.BOUND_SECONDS==15.0 and candidate.POLL_SECONDS==.05,'P546_EXACT_APPROVED_FINITE_BOUND_AND_ORIGINAL_CADENCE')
        cases=unittest.defaultTestLoader.loadTestsFromTestCase(new.Tests)
        cases.addTest(prior.Tests('test_never_idle_stops_at_original_fixed_bound_without_retry'))
        cases.addTest(prior.Tests('test_expired_final_image_check_does_not_report_observed'))
        cases.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(sql.Snapshot));c.require(cases.countTestCases()==15,'P546_NEW8_AFFECTED2_SNAPSHOT5_ONLY')
        result=unittest.TestResult();cases.run(result)
        row.update(contracts=dict(run=result.testsRun,errors=len(result.errors),failures=len(result.failures),skipped=len(result.skipped)),
            failed_contract_names=[test.id()for test,_ in result.errors+result.failures])
        c.require(row['contracts']==dict(run=15,errors=0,failures=0,skipped=0),'P546_ALL_SELECTED_PURE_MODELS_PASS')
        observed=dict(snapshots=[]);storage.denied_snapshot(observed,projection,7);c.require(observed['snapshots']==[projection],'P546_RECORDED_ACTUAL_PROJECTION_ACCEPTED_BY_FIXED_CHECK')
        for path in(SELF,CANDIDATE,NEW_TEST,SQL_TEST,CAMPAIGN):ast.parse(q.text(path))
        q.finish();guard.check(force=True)
        row.update(state='PASS_STARTUP15_CANDIDATE_NEW8_AFFECTED2_AND_SQL_DENIED_SNAPSHOT5_NOT_NATIVE_OR_545_CLOSURE',
            qualified_startup_candidate=q.snapshots[CANDIDATE],observed545_SQL_aggregate_projection=projection,
            projection_proof=dict(source=OBS,stage=command['stage'],bytes=len(raw),sha256=command['stdout_sha256']),
            original545_state_preserved=True,original545_restart_not_run=True,original545_final_fresh_hashes=0)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,StopIteration)as error:
        code=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'P546_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup,source_pins=[]if q is None else list(q.snapshots.values()),
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,resource_samples=samples,
            elapsed_seconds=round(time.monotonic()-started,3),system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:v for k,v in row.items()if k not in('source_pins','resource_samples')},'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
