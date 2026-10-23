"""357: current sealed source and strict declaration metadata product26 + affected existing named3."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
shared,c,a,tools,compact,harness,audit=r.shared,r.c,r.a,r.tools,r.compact,r.harness,r.audit
OUTPUT='implementation/p09/evidence/p09-361-named-declarations-product357.v1.json';DRIVER='tools/p09/run_named_declarations_product.py'
BASE='implementation/p09/evidence/p09-361-named-style-declarations-recovery355.v1.json'
DOCS='implementation/p09/evidence/p09-361-named-style-declarations-sync356.v1.json'
STORE_PARENT='crates/product-cli/src/form_stored_provider/actual_import.rs';PRODUCT_PARENT='crates/product-cli/src/form_product_request.rs'
CORE='crates/hwpx-package/src/document_import/fields/semantics/catalog/named_styles.rs'
STORE='crates/product-cli/src/form_stored_provider/actual_import/named_style_declarations.rs';PRODUCT='crates/product-cli/src/form_product_request/named_style_declarations.rs'
TEST='crates/product-cli/tests/named_style_declarations_product.rs'
NEW={DRIVER,STORE,PRODUCT,TEST}
AFFECTED={'borrowed_owned_and_product_share_original_named_candidate_receipt_and_output','preview_predicts_same_result_but_discards_output_and_never_calls_byte_consumer',
    'write_scope_is_required_for_preparation_and_retained_preview_metadata'}

def inverse(q,old):
    for path in(STORE_PARENT,PRODUCT_PARENT):
        text=q.text(path);line='pub mod named_style_declarations;\n';c.require(text.count(line)==1,'ONE_DECLARATION_MODULE_EXPORT_PER_PARENT')
        audit.inverse(text.replace(line,''),old[path],'ALL_ORIGINAL_SOURCE_ACCESS_PRODUCT_STRICT_PARSERS_AND_WRITER_LOGIC_PRESERVED')
    text=q.text(CORE);line='    #[must_use]pub const fn maximum_result_bytes(self)->usize{self.result_bytes}\n'
    c.require(text.count(line)==1,'ONE_SERVER_RESULT_LIMIT_GETTER');audit.inverse(text.replace(line,''),old[CORE],'ALL_ORIGINAL_RESOLVER_LIMITS_MATCHER_TYPED_IDS_BINDING_AND_HASH_PAYLOAD_UNCHANGED')

def snapshot(capture,expected):
    out=r.snapshot(capture,expected)
    with capture.lock:raw=(bytes(capture.buffers['stdout'])+bytes(capture.buffers['stderr'])).decode('utf-8','replace')
    out['closed_named_declaration_errors']=sorted(set(re.findall(r'\b(?:NAMED_DECLARATIONS_PRODUCT|STORED_NAMED_DECLARATIONS|NAMED_STYLE_NAME)_[A-Z_]{1,64}\b',raw)));return out

def main(scratch_relative='target/p09-named-declarations-product-scratch-357'):
    c.require(not(c.ROOT/OUTPUT).exists(),'NAMED_DECLARATIONS_PRODUCT_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_NAMED_DECLARATIONS_PRODUCT',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        Native011_executed=False,prior_Native_replayed=False,actual_DB_or_Hangul_or_COM_started=False,official249_replayed=False,old_suites_replayed=False,
        body_occurrences_or_target_semantics_qualified=False,source_document_mutation=False,output_ingest_commit_or_publication=False)
    try:
        guard.acquire();scratch=c.ROOT/scratch_relative
        c.require(scratch.parent==c.ROOT/'target'and not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'NAMED_DECLARATIONS_PRODUCT_EARLY_NEW_TEMP')
        q=a.AcceptanceReader(c.ROOT,guard.check);old_run=compact.unpack(q.json(BASE));docs=q.json(DOCS)
        c.require(q.snapshots[BASE]['sha256']=='805f9edd4cbd317522faa1cd7ce57458ac851dc8931a988ef66f4345cb8f8b92'and old_run['cleanup']and old_run['fresh_inputs']==old_run['final_fresh_hashes']==832,'EXACT355_TERMINAL_RESOLVER19_CATALOG3')
        c.require(docs['state']=='PASS_NAMED_DECLARATION19_CATALOG3_CURRENT_DOC_SYNC_NOT_CHARACTER_BODY_BINDING_NATIVE_OR_GATE'and docs['cleanup'],'EXACT356_DECLARATION_ONLY_SCOPE_NO_NATIVE_APPROVAL')
        old={p['path']:p for p in old_run['source_pins']}
        for path in sorted(r.closure.inventory(guard.check)|set(old)|NEW):
            q.pin(path)
            if path in old and path not in{STORE_PARENT,PRODUCT_PARENT,CORE}:c.require(q.snapshots[path]==old[path],'ALL_OTHER_CATALOG_SERVICE_WRITER_PARSERS_TESTS_AND_RESOURCE_GUARDS_UNCHANGED')
            elif path not in old:c.require(path in NEW,'ONLY_CURRENT_DECLARATION_SERVICE_PRODUCT_TEST_DRIVER_ADDED')
        inverse(q,old)
        for module in tuple(sys.modules.values()):
            path=getattr(module,'__file__',None)
            if path:
                p=Path(path).absolute()
                if p.is_relative_to(c.ROOT/'tools/p09')and p.suffix=='.py':q.pin(p.relative_to(c.ROOT).as_posix())
        cases=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(TEST)));c.require(len(cases)==26,'EXACT26_CURRENT_SERVICE_PRODUCT_AND_HEAD_RACE_CASES')
        c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'NAMED_DECLARATIONS_PRODUCT_NEW_TEMP')
        scratch.mkdir();env=audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));print(json.dumps(dict(state='NAMED_DECLARATIONS_PRODUCT_PREFLIGHT',inputs=len(q.snapshots),new_cases=len(cases),affected_cases=3)),flush=True)
        for binary,label,selected in [('named_style_declarations_product','named_declarations_service_product26',cases),('named_style_product','affected_original_named_service_preview_permission3',AFFECTED)]:
            harness.run_one(label,[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli','--test',binary,'--message-format=short','--',*sorted(selected),'--test-threads=1'],selected,guard,env,row,observe_capture=snapshot)
            tools.good_step(row['steps'][-1],selected)
        c.require(not any(scratch.iterdir()),'NAMED_DECLARATIONS_PRODUCT_TEMP_EMPTY');q.finish();guard.check(force=True)
        row.update(state='PASS_CURRENT_NAMED_DECLARATIONS_SERVICE_PRODUCT26_AFFECTED_NAMED3_NOT_BODY_BINDING_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_cases=len(cases),affected_cases=3,current_access_is_rechecked_not_cached_authority=True,strict_request_bytes=16384,whole_response_limit_enforced=True,
            next_work='qualified_character_style_before_after_sources_then_body_mapping_and_full_product_execution')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'NAMED_DECLARATIONS_PRODUCT_FAILURE_NO_RAW_VALUES')
        if q is not None:
            try:q.finish();row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
            except(ValueError,OSError,KeyError,TypeError,AttributeError):row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'NAMED_DECLARATIONS_PRODUCT_LOSSLESS_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','safe_error_variants','panic_locations','bounded_output_observation','cleanup')},'case_count':len(s.get('tests',[])),'failed_cases':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
