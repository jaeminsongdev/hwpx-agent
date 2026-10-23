"""Dedicated6-case target, exact shared fixture extraction, same resource/time guards."""
import hashlib,json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_stored_review_literal_components as base
harness,shared,c,a=base.harness,base.shared,base.c,base.a
OUTPUT='implementation/p09/evidence/p09-361-stored-review-literal-focused085.v1.json'
FAILED=base.OUTPUT
LEGACY='crates/product-cli/tests/form_stored_provider.rs'
FIXTURE='crates/product-cli/tests/support/stored_source_fixture.rs'
TARGET='crates/product-cli/tests/review_literal_stored.rs'
WRAPPER='crates/product-cli/tests/review_literal_stored/actual_import.rs'
HARNESS='tools/p09/run_source_note_api_components.py'
EXTRA={FIXTURE,TARGET,WRAPPER}
INCLUDE='include!("support/stored_source_fixture.rs");\nimpl StoredFixture {\n'
ADDED='#[path = "actual_import/review_literal_output.rs"]\nmod review_literal_output;\n'


def inventory(check):return base.inventory(check)|EXTRA


def snapshot(capture,expected):
    with capture.lock:stdout,stderr=bytes(capture.buffers['stdout']),bytes(capture.buffers['stderr'])
    parsed=re.findall(rb'(?m)^test ([A-Za-z0-9_:]+) \.\.\. (ok|FAILED|ignored)\r?$',stdout)
    tests=[(n.decode('ascii'),s.decode('ascii'))for n,s in parsed if n.decode('ascii')in expected]
    started=bool(re.search(rb'(?m)^running [0-9]+ tests?\r?$',stdout))
    phase='TEST_HARNESS_OBSERVED'if started else 'BUILD_FINISHED_OBSERVED'if b'Finished'in stderr else 'BUILD_ACTIVITY_OBSERVED'if any(v in stderr for v in (b'Compiling ',b'Checking '))else'NO_PHASE_MARKER_OBSERVED'
    return dict(phase=phase,observed_completed_expected_cases=tests,observed_harness_started=started,
        cargo_file_lock_marker_observed=b'Blocking waiting for file lock'in stderr,stdout_bytes=len(stdout),stderr_bytes=len(stderr),
        stdout_sha256=hashlib.sha256(stdout).hexdigest(),stderr_sha256=hashlib.sha256(stderr).hexdigest(),phase_observation_only=True)


def extraction(q,initial):
    fixture=q.text(FIXTURE);c.require(fixture.endswith('    }\n}\n')and fixture.count('impl StoredFixture {')==1
        and '#[test]'not in fixture and 'fn prepare('not in fixture,'EXACT_NEW_PROVIDER_FIXTURE_ONLY_NOT_LEGACY_TESTS')
    text=q.text(LEGACY);c.require(text.count(INCLUDE)==1,'ONE_SHARED_FIXTURE_INCLUDE_AT_ORIGINAL_LEXICAL_SCOPE')
    base.prior.audit.inverse(text.replace(INCLUDE,fixture[:-2]),initial[LEGACY],'ENTIRE_LEGACY_ROOT_ALL_HELPERS_AND_TEST_BODIES_EXACT_INVERSE')
    text=q.text(base.MODULE);anchor='mod literal_text_atom_product;\n';c.require(text.count(anchor)==1 and ADDED not in text,'REVIEW_SIX_MOVED_NOT_DUPLICATED_IN_LEGACY_TARGET')
    base.prior.audit.inverse(text.replace(anchor,anchor+ADDED),initial[base.MODULE],'ALL_LEGACY_MODULES_EXACT_EXCEPT_SIX_CASE_DEDICATED_TARGET_MOVE')
    c.require(q.text(TARGET)==('//! Dedicated6-case target; source fixture is shared byte-for-byte with the legacy suite.\n'
        'use domain_ir::DocumentId;\nuse std::error::Error;\ntype TestResult=Result<(),Box<dyn Error>>;\n'
        'include!("support/stored_source_fixture.rs");\n#[path="review_literal_stored/actual_import.rs"]\nmod actual_import;\n')
        and q.text(WRAPPER)=='use super::*;\n#[path="../form_stored_provider/actual_import/review_literal_output.rs"]\nmod review_literal_output;\n',
        'DEDICATED_TARGET_CONTAINS_ONLY_EXACT_SHARED_FIXTURE_AND_ORIGINAL_SIX_CASE_MODULE')
    text=q.text(HARNESS)
    for current,old in (('def run_one(label, args, expected, guard, env, row, *, observe_capture=None):','def run_one(label, args, expected, guard, env, row):'),
        ("                    if observe_capture is not None:\n                        step['bounded_output_observation'] = observe_capture(capture, expected)\n                        print(json.dumps(dict(stage=label, bounded_output_observation=step['bounded_output_observation'])), flush=True)\n",''),
        ("        try:\n            if observe_capture is not None and capture is not None:\n                step['bounded_output_observation'] = observe_capture(capture, expected)\n        finally:\n            if owned is not None:\n                owned.kill(); owned.wait(timeout=2)\n                if capture is not None: capture.close()\n                owned.close(); step.update(cleanup=owned.profile['cleanup_confirmed'], owned_job=owned.profile)\n",
         "        if owned is not None:\n            owned.kill(); owned.wait(timeout=2)\n            if capture is not None: capture.close()\n            owned.close(); step.update(cleanup=owned.profile['cleanup_confirmed'], owned_job=owned.profile)\n")):
        c.require(text.count(current)==1,'ONLY_OPTIONAL_SAFE_CAPTURE_OBSERVER_AND_ALWAYS_FINALLY_CLEANUP');text=text.replace(current,old)
    base.prior.audit.inverse(text,initial[HARNESS],'ORIGINAL_COMMAND_DEADLINE_OUTPUT_TEST_SET_AND_JOB_RESOURCE_CLEANUP_UNCHANGED')


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'FOCUSED_REVIEW_LITERAL_IMMUTABLE_RUN_EXISTS');shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_FOCUSED_STORED_REVIEW_LITERAL',steps=[],actual_Hangul_or_COM=False,Native011_executed=False,
        prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        row['preflight_stage']='original_failure_record'
        failed=q.json(FAILED);c.require(q.snapshots[FAILED]['sha256']=='a3a5315831e670bc28b40e7d341b4413dca8e2a10711ee6085d0558d9aadc697'
            and failed['state']=='FAILED_STORED_REVIEW_LITERAL_COMPONENTS'and failed['error_code']=='STOP_SOURCE_NOTE_API_COMMAND_DEADLINE'
            and failed['cleanup']and len(failed['steps'])==1 and 'tests'not in failed['steps'][0],'ORIGINAL_DEADLINE_FAILURE_UNRECORDED_CASE_COMPLETION_NOT_RELABELLED')
        initial={p['path']:p for p in failed['source_pins']}
        for name in names-EXTRA-{LEGACY,base.MODULE}:c.require(q.snapshots[name]==initial[name],'NO_PRODUCTION_CORE_SIX_TEST_OR_OTHER_SOURCE_CHANGE_DURING_TARGET_SPLIT')
        row['preflight_stage']='exact_target_extraction'
        extraction(q,initial)
        expected={'actual_import::review_literal_output::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(base.TEST))}
        c.require(len(expected)==6,'EXACT_SAME_SIX_ORIGINAL_STORED_REVIEW_CASES')
        env=base.prior.audit.environment();common=[harness.CARGO,'--offline','--locked','-j','1','-p','hwpx-agent-cli']
        print(json.dumps(dict(state='FOCUSED_REVIEW_LITERAL_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),test_bodies_unchanged=True,shared_fixture_exact=True,deadline_and_limits_unchanged=True)),flush=True)
        harness.run_one('six_dedicated_stored_review_literal_cases',[common[0],'test',*common[1:],'--test','review_literal_stored','--','--test-threads=1'],expected,guard,env,row,observe_capture=snapshot)
        harness.run_one('legacy_form_stored_provider_typecheck_no_tests_executed',[common[0],'check',*common[1:],'--test','form_stored_provider'],set(),guard,env,row,observe_capture=snapshot)
        c.require(inventory(guard.check)==names,'FINAL_FOCUSED_REVIEW_LITERAL_SOURCE_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_FOCUSED_STORED_REVIEW_LITERAL_SIX_CASES_LEGACY_TYPECHECK_CORE32_RETAINED_NOT_JSON_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,current_stored_cases=6,retained_core_cases=32,
            shared_fixture_and_legacy_root_exact_inverse_verified=True,six_case_bodies_and_production_unchanged=True,legacy_target_typechecked_not_executed=True,
            original_deadline_failure_preserved=True,failed_attempt_case_completion_unrecorded=True,resource_and_300_second_command_limits_unchanged=True,
            raw_logs_persisted=False,strict_v3_json_or_owned_source_handoff_added=False,next_work='Strict_v3_review_literal_product_JSON_with_explicit_body_policy_and_owned_source')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'FOCUSED_REVIEW_LITERAL_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_FOCUSED_REVIEW_LITERAL_RESOURCE_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','diagnostics','locations','summaries','tests','panic_locations','safe_error_variants','bounded_output_observation')}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
