"""378: current stored source + strict read-only detection/next/selection product32, affected mask3; no Native."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
shared,c,a,tools,compact,harness,audit=r.shared,r.c,r.a,r.tools,r.compact,r.harness,r.audit
OUTPUT='implementation/p09/evidence/p09-361-personal-info-detection-product378.v1.json';DRIVER='tools/p09/run_personal_info_detection_product.py'
BASE='implementation/p09/evidence/p09-361-personal-info-detection-recovery374.v1.json'
DOCS='implementation/p09/evidence/p09-361-personal-info-detection-sync-final377.v1.json'
STORE_PARENT='crates/product-cli/src/form_stored_provider/actual_import/source_search.rs';STORE=STORE_PARENT[:-3]+'/personal_info.rs'
PRODUCT_PARENT='crates/product-cli/src/form_product_request/stored_source_search.rs';PRODUCT=PRODUCT_PARENT[:-3]+'/personal_info.rs'
ROOT_TEST='crates/product-cli/tests/personal_info_mask_product.rs';TEST='crates/product-cli/tests/support/personal_info_detection_product.rs'
LINK='#[path="support/personal_info_detection_product.rs"]mod detection;\n'
NEW={DRIVER,STORE,PRODUCT,TEST};CHANGED={STORE_PARENT,PRODUCT_PARENT,ROOT_TEST}
AFFECTED={'borrowed_owned_and_product_share_one_original_mask_receipt_and_verified_output','preview_discards_output_never_calls_byte_consumer_and_keeps_same_prediction',
    'request_key_plan_policy_and_mode_bind_hashes_without_disclosing_private_body'}

def inverse(q,old):
    for path in (STORE_PARENT,PRODUCT_PARENT):
        text=q.text(path);c.require(text.count('pub mod personal_info;\n')==1,'ONE_EXPLICIT_READ_ONLY_PERSONAL_INFO_MODULE_EXPORT')
        audit.inverse(text.replace('pub mod personal_info;\n',''),old[path],'ALL_ORIGINAL_SOURCE_SEARCH_REQUESTS_ACCESS_GUARDS_RESULTS_AND_NAVIGATION_UNCHANGED')
    text=q.text(ROOT_TEST);c.require(text.count(LINK)==1,'ONE_DETECTION_PRODUCT_CHILD_LINK')
    audit.inverse(text.replace(LINK,''),old[ROOT_TEST],'ALL33_ORIGINAL_MASK_TESTS_AND_COMMON_COMPILED_CHILD_UNCHANGED')

def main(scratch_relative='target/p09-personal-info-detection-product-scratch-378'):
    c.require(not(c.ROOT/OUTPUT).exists(),'DETECTION_PRODUCT_IMMUTABLE')
    text=(c.ROOT/TEST).read_text(encoding='utf-8');c.require(len(text.encode())<=128*1024,'FINITE_DETECTION_PRODUCT_TEST_SOURCE')
    cases={'detection::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',text)}
    names=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',(c.ROOT/ROOT_TEST).read_text(encoding='utf-8')))
    c.require(len(cases)==32 and AFFECTED<=names,'EXACT_NEW32_AND_AFFECTED3_IDENTITIES_BEFORE_PREFLIGHT_OR_BUILD')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_PERSONAL_INFO_DETECTION_PRODUCT',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        Native011_executed=False,prior_Native_replayed=False,actual_DB_or_Hangul_or_COM_started=False,official249_replayed=False,old_suites_replayed=False,
        synthetic_markers_scanner_and_keys_not_actual_personal_data=True,source_document_mutation=False,output_ingest_commit_or_publication=False,
        whole_package_personal_data_removed=False,native_format_policy_or_execution_qualified=False)
    try:
        guard.acquire();scratch=c.ROOT/scratch_relative;c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'DETECTION_PRODUCT_EARLY_UNIQUE_TEMP')
        q=a.AcceptanceReader(c.ROOT,guard.check);before=compact.unpack(q.json(BASE));docs=q.json(DOCS)
        c.require(q.snapshots[BASE]['sha256']=='5175b077d5a205afab069064fc561fb06954476acc08ef2d401da3e042e1c9ba'and before['cleanup']and before['fresh_inputs']==before['final_fresh_hashes']==875
            and before['current_distinct_cases']==26 and before['retained_cases']==25,'EXACT374_CURRENT_SOURCE_DETECTION_AND_ORIGINAL_BOUNDARIES')
        c.require(q.snapshots[DOCS]['sha256']=='dc9a5efb9c3a645878ae064104d72861d66832fa16c6475699356c3e3df38ab4'and docs['cleanup']and docs['fresh_inputs']==docs['final_fresh_hashes']==31,'EXACT377_DOC_AUDIT_WITH375_376_FAILURES_RETAINED_NOT_RUNTIME_REPLAY')
        old={p['path']:p for p in before['source_pins']}
        for path in sorted(r.closure.inventory(guard.check)|set(old)|NEW|CHANGED):
            q.pin(path)
            if path in old and path not in CHANGED:c.require(q.snapshots[path]==old[path],'ALL_OTHER_CORE_MASKING_PROTECTION_SERVICE_PRODUCT_COMPILER_TESTS_AND_RESOURCE_GUARDS_UNCHANGED')
            elif path not in old:c.require(path in NEW,'ONLY_DETECTION_STORED_PRODUCT_TEST_DRIVER_ADDED')
        inverse(q,old)
        for module in tuple(sys.modules.values()):
            f=getattr(module,'__file__',None)
            if f:
                p=Path(f).absolute()
                if p.is_relative_to(c.ROOT/'tools/p09')and p.suffix=='.py':q.pin(p.relative_to(c.ROOT).as_posix())
        c.require(cases=={'detection::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(TEST))}and '#[ignore]'not in q.text(TEST),'FRESH32_IDENTITIES_AND_NO_IGNORES')
        scratch.mkdir();env=audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));print(json.dumps(dict(state='DETECTION_PRODUCT_PREFLIGHT',inputs=len(q.snapshots),new_cases=32,affected_cases=3)),flush=True)
        selected=cases|AFFECTED
        harness.run_one('personal_info_detection_product32_affected_mask3',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli','--test','personal_info_mask_product','--message-format=short','--',*sorted(selected),'--test-threads=1'],selected,guard,env,row,observe_capture=r.snapshot)
        tools.good_step(row['steps'][-1],selected);c.require(row['steps'][-1]['diagnostics']==[],'DETECTION_STORED_PRODUCT32_AND_ORIGINAL3_NO_WARNINGS')
        c.require(not any(scratch.iterdir()),'DETECTION_PRODUCT_TEMP_EMPTY');q.finish();guard.check(force=True)
        row.update(state='PASS_CURRENT_STORED_READ_ONLY_DETECTION_PRODUCT32_AFFECTED_MASK3_NOT_NATIVE_DEFAULTS_MUTATION_SANITIZATION_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_cases=32,affected_cases=3,retained_original_source_cases=23,whole_current_source_access_checks_preserved=True,
            next_work='qualified_native_format_policy_full_options_then_actual_execution_storage_and_target_contract')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'DETECTION_PRODUCT_FAILURE_NO_RAW_VALUES')
        if q is not None:
            try:q.finish();row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
            except(ValueError,OSError,KeyError,TypeError,AttributeError):row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'DETECTION_PRODUCT_LOSSLESS_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','safe_error_variants','panic_locations','bounded_output_observation','cleanup')},'case_count':len(s.get('tests',[])),
            'failed_cases':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
