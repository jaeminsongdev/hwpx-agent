"""365: fresh service/strict selected mask product33 + affected original named service3; no Native/DB."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
shared,c,a,tools,compact,harness,audit=r.shared,r.c,r.a,r.tools,r.compact,r.harness,r.audit
OUTPUT='implementation/p09/evidence/p09-361-personal-info-mask-product365.v1.json';DRIVER='tools/p09/run_personal_info_mask_product.py'
BASE='implementation/p09/evidence/p09-361-personal-info-mask-recovery363.v1.json';DOCS='implementation/p09/evidence/p09-361-personal-info-mask-sync364.v1.json'
STORE_PARENT='crates/product-cli/src/form_stored_provider/actual_import/literal_search_output.rs';PRODUCT_PARENT='crates/product-cli/src/form_product_request/stored_literal_replacement.rs'
STORE=STORE_PARENT[:-3]+'/personal_info.rs';PRODUCT=PRODUCT_PARENT[:-3]+'/personal_info.rs';TEST='crates/product-cli/tests/personal_info_mask_product.rs'
NEW={DRIVER,STORE,PRODUCT,TEST};AFFECTED={'borrowed_owned_and_product_share_original_named_candidate_receipt_and_output',
    'preview_predicts_same_result_but_discards_output_and_never_calls_byte_consumer','write_scope_is_required_for_preparation_and_retained_preview_metadata'}

def inverse(q,old):
    for path in(STORE_PARENT,PRODUCT_PARENT):
        text=q.text(path);line='pub mod personal_info;\n';c.require(text.count(line)==1,'ONE_SELECTED_MASK_SERVICE_AND_PRODUCT_EXPORT')
        audit.inverse(text.replace(line,''),old[path],'ALL_ORIGINAL_SOURCE_ACCESS_WRITER_COMPILER_PREVIEW_STRICT_PARSERS_AND_EXISTING_PRODUCTS_UNCHANGED')

def snapshot(capture,expected):
    result=r.snapshot(capture,expected)
    with capture.lock:raw=(bytes(capture.buffers['stdout'])+bytes(capture.buffers['stderr'])).decode('utf-8','replace')
    result['closed_personal_info_mask_errors']=sorted(set(re.findall(r'\b(?:STORED_PERSONAL_INFO_MASK|PERSONAL_INFO_MASK)_[A-Z_]{1,64}\b',raw)));return result

def main(scratch_relative='target/p09-personal-info-mask-product-scratch-365'):
    c.require(not(c.ROOT/OUTPUT).exists(),'PERSONAL_INFO_MASK_PRODUCT_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_PERSONAL_INFO_MASK_PRODUCT',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        Native011_executed=False,prior_Native_replayed=False,actual_DB_or_Hangul_or_COM_started=False,official249_replayed=False,old_suites_replayed=False,
        synthetic_markers_not_actual_personal_data=True,source_document_mutation=False,output_ingest_commit_or_publication=False,whole_package_personal_data_removed=False,native_mask_semantics_qualified=False)
    try:
        guard.acquire();scratch=c.ROOT/scratch_relative
        c.require(scratch.parent==c.ROOT/'target'and not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'PERSONAL_INFO_PRODUCT_EARLY_UNIQUE_TEMP')
        q=a.AcceptanceReader(c.ROOT,guard.check);before=compact.unpack(q.json(BASE));docs=q.json(DOCS)
        c.require(q.snapshots[BASE]['sha256']=='ffd4119fb913ff0bcdc8d67a142be08e646745db1310c1ae77c909d7c9814a8c'and before['cleanup']and before['fresh_inputs']==before['final_fresh_hashes']==850,'EXACT363_FULL_SOURCE_MASK25_SHARED3_TERMINAL')
        c.require(q.snapshots[DOCS]['sha256']=='23b83be5e323a5ffd72dd77ee785336d0ab5aa5f7b59ddf73f206d302c98dae2'and docs['cleanup'],'EXACT364_SOURCE_ONLY_DOC_BASELINE_NO_NATIVE_PROMOTION')
        old={p['path']:p for p in before['source_pins']}
        for path in sorted(r.closure.inventory(guard.check)|set(old)|NEW):
            q.pin(path)
            if path in old and path not in{STORE_PARENT,PRODUCT_PARENT}:c.require(q.snapshots[path]==old[path],'ALL_OTHER_ORIGINAL_MASK_SOURCE_POLICIES_WRITERS_TESTS_PARSERS_AND_RESOURCE_GUARDS_UNCHANGED')
            elif path not in old:c.require(path in NEW,'ONLY_CURRENT_SELECTED_MASK_SERVICE_PRODUCT_TEST_DRIVER_ADDED')
        inverse(q,old)
        for module in tuple(sys.modules.values()):
            path=getattr(module,'__file__',None)
            if path:
                p=Path(path).absolute()
                if p.is_relative_to(c.ROOT/'tools/p09')and p.suffix=='.py':q.pin(p.relative_to(c.ROOT).as_posix())
        cases=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(TEST)));c.require(len(cases)==33,'EXACT33_CURRENT_MASK_SERVICE_PRODUCT_PREVIEW_AND_HEAD_BOUNDARIES')
        scratch.mkdir();env=audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));print(json.dumps(dict(state='PERSONAL_INFO_MASK_PRODUCT_PREFLIGHT',inputs=len(q.snapshots),new_cases=33,affected_cases=3)),flush=True)
        for binary,label,selected in [('personal_info_mask_product','personal_info_mask_current_service_product33',cases),('named_style_product','affected_original_named_owner_preview_permission3',AFFECTED)]:
            harness.run_one(label,[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli','--test',binary,'--message-format=short','--',*sorted(selected),'--test-threads=1'],selected,guard,env,row,observe_capture=snapshot)
            tools.good_step(row['steps'][-1],selected)
        c.require(not any(scratch.iterdir()),'PERSONAL_INFO_PRODUCT_TEMP_EMPTY');q.finish();guard.check(force=True)
        row.update(state='PASS_CURRENT_PERSONAL_INFO_MASK_SERVICE_PRODUCT33_AFFECTED_NAMED3_NOT_NATIVE_SANITIZATION_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_cases=33,affected_cases=3,current_access_rechecked_not_cached_authority=True,strict_request_bytes=16384,whole_service_and_product_metadata_limit=True,
            next_work='mutation_only_compiler_owner_common_dispatch_and_actual_execution_with_separate_preview_and_full_privacy_target_contract')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'PERSONAL_INFO_MASK_PRODUCT_FAILURE_NO_RAW_VALUES')
        if q is not None:
            try:q.finish();row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
            except(ValueError,OSError,KeyError,TypeError,AttributeError):row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'PERSONAL_INFO_PRODUCT_LOSSLESS_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','safe_error_variants','panic_locations','bounded_output_observation','cleanup')},'case_count':len(s.get('tests',[])),'failed_cases':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
