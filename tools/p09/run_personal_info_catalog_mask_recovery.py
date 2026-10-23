"""428: fix only include-file comment; retain source30, execute previously uncompiled stored20."""
import json,re,subprocess,time
from types import SimpleNamespace as NS
import run_personal_info_catalog_mask as prior
r,layout=prior.r,prior.layout
OUTPUT='implementation/p09/evidence/p09-361-personal-info-catalog-mask-recovery428.v1.json'
DRIVER='tools/p09/run_personal_info_catalog_mask_recovery.py'


def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'CATALOG_MASK428_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;final_attempted=False;started=time.monotonic();row=dict(state='FAILED_PERSONAL_INFO_CATALOG_MASK_RECOVERY428',steps=[],own_cpu_selection=selection,
        actual_DB_Hangul_or_COM_started=False,Native011_executed=False,prior_Native_replayed=False,official249_replayed=False,
        previously_passed_source30_replayed=False,original427_failure_preserved=True,strict_product_catalog_mask_not_implemented=True,
        common_compiler_catalog_mask_not_implemented=True,source_document_mutation=False,ingest_commit_or_publication=False,
        whole_package_personal_data_removed=False,native_catalog_mask_semantics_or_service_execution_qualified=False,
        accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);base=layout.unpack(q.json(prior.OUTPUT))
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='9b766f491502fb82b2c96726795339600d3286235ebe487cd0d5561dc2f5cf80'
            and base['state']=='FAILED_PERSONAL_INFO_CATALOG_MASK427'and base['cleanup']is True
            and base['fresh_inputs']==base['final_fresh_hashes']==842 and len(base['steps'])==2,'EXACT427_SOURCE30_AND_STORED_PRE_EXECUTION_FAILURE_RETAINED')
        config=prior.CONFIGS[1];old={p['path']:p for p in base['source_pins']}
        for path in sorted(set(old)|{DRIVER}):
            pin=q.pin(path)
            if path in old and path!=config['source']:c.require(pin==old[path],'ALL_PRODUCT_ALGORITHMS_PASSED_SOURCE30_TESTS_AND_GUARDS_UNCHANGED')
        text=q.text(config['source']);c.require(text.startswith('// Current access/config'),'ONE_INCLUDE_FILE_COMMENT_FIX')
        r.audit.inverse('//!'+text[2:],old[config['source']],'ONLY_INNER_DOC_COMMENT_TO_REGULAR_COMMENT_NO_TEST_ASSERTION_CHANGE')
        source=prior.CONFIGS[0];source_cases={source['prefix']+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(source['source']))}
        r.tools.good_step(base['steps'][0],source_cases);c.require(len(source_cases)==30 and not base['steps'][0]['diagnostics'],'EXACT30_PREVIOUS_SOURCE_CASES_RETAINED_NO_REPLAY')
        failed=base['steps'][1]['bounded_output_observation']
        c.require(base['steps'][1]['exit_code']==101 and not base['steps'][1]['tests']and failed['rust_error_codes']==['E0753']
            and failed['short_error_locations']==[[config['source'],'1','1']],'EXACT_SINGLE_TEST_COMMENT_COMPILE_FAILURE_NOT_PRODUCT_FAILURE')
        found={config['prefix']+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',text)}
        c.require(len(found)==20 and '#[ignore]'not in text and '#[cfg('not in text,'EXACT20_PREVIOUSLY_UNCOMPILED_STORED_CASES')
        expected=set(base['compiled_test_inputs'][1]['expected_dependency_paths'])
        c.require(expected<=set(old),'ALL_STORED_EXPECTED_COMPILE_INPUTS_ALREADY_FRESH_PINNED')
        scratch=c.ROOT/'target/p09-catalog-mask-scratch-428';c.require(not scratch.exists()and scratch.parent.is_dir()
            and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'CATALOG_MASK428_UNIQUE_COMPILER_TEMP')
        scratch.mkdir();env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch))
        print(json.dumps(dict(state='CATALOG_MASK428_PREFLIGHT',inputs=len(q.snapshots),source30_retained=True,stored20_to_execute=True)),flush=True)
        args=[r.harness.CARGO,'test','--offline','--locked','-j','1','-p',config['package'],'--test',config['test'],'--message-format=short','--',*sorted(found),'--test-threads=1']
        r.harness.run_one(config['label'],args,found,guard,env,row,observe_capture=r.snapshot)
        r.tools.good_step(row['steps'][-1],found);c.require(row['steps'][-1]['diagnostics']==[],'STORED_CATALOG_MASK20_NO_WARNINGS')
        row['actual_stored_test_inputs']=prior.compiled_inputs(config,expected,guard)
        c.require(not any(scratch.iterdir()),'CATALOG_MASK428_COMPILER_TEMP_EMPTY')
        final_attempted=True;q.finish();guard.check(force=True)
        row.update(state='PASS_PERSONAL_INFO_CATALOG_MASK_SOURCE30_RETAINED_STORED20_NOT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            current_distinct_cases=50,retained_source_cases=30,last_executed_stored_cases=20,prior_source_proof=base['compiled_test_inputs'][0])
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'CATALOG_MASK_RECOVERY_FAILURE_NO_RAW_VALUES')
        if q is not None and not final_attempted:
            final_attempted=True
            try:q.finish();row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
            except(ValueError,OSError,KeyError,TypeError,AttributeError):row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples
        row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','safe_error_variants','panic_locations','cleanup')},'cases':len(s.get('tests',[])),
                'failed_cases':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
