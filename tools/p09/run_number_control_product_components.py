"""26 strict current-store number-control products; retain unchanged source67 and older266 product cases."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_number_control_review_components as prior
harness,shared,c,a,audit,snapshot,tools=prior.harness,prior.shared,prior.c,prior.a,prior.audit,prior.snapshot,prior.tools
OUTPUT='implementation/p09/evidence/p09-361-number-control-product-components203.v1.json'
STORED_PARENT='crates/product-cli/src/form_stored_provider/actual_import/literal_search_output.rs'
PRODUCT_PARENT='crates/product-cli/src/form_product_request/stored_literal_replacement.rs'
PARENT='crates/product-cli/tests/form_stored_provider/actual_import/unicode_normalization_product.rs'
STORED=STORED_PARENT[:-3]+'/number_controls.rs';PRODUCT=PRODUCT_PARENT[:-3]+'/number_controls.rs'
TEST='crates/product-cli/tests/form_stored_provider/actual_import/number_control_product.rs';CORE=prior.CORE
DISCOVERY=prior.source.DISCOVERY
NEW={STORED,PRODUCT,TEST};CHANGED={STORED_PARENT,PRODUCT_PARENT,PARENT,CORE,DISCOVERY}
PREFIX='actual_import::regex_replacement_product::unicode_v1::number_controls_v1::'
GETTERS='''    #[must_use] pub const fn policy(&self)->SourceReviewTextPolicy {self.policy}
    #[must_use] pub const fn kind(&self)->SourceControlKind {self.kind}
    #[must_use] pub const fn max_results(&self)->usize {self.max_results}
'''


def inventory(check):return prior.inventory(check)|NEW


def inverse(q,old):
    for name in(STORED_PARENT,PRODUCT_PARENT):
        text=q.text(name);marker='pub mod number_controls;\n';c.require(text.count(marker)==1,'ONE_ADDITIVE_NUMBER_PRODUCT_MODULE')
        audit.inverse(text.replace(marker,''),old[name],'ENTIRE_OLD_LITERAL_REGEX_STYLE_UNICODE_WIDTH_WHITESPACE_TEXT_CONTROL_AND_ACCESS_BODIES_UNCHANGED')
    text=q.text(PARENT);marker='#[path="number_control_product.rs"] mod number_controls_v1;\n'
    c.require(text.count(marker)==1 and text.endswith(marker),'ONE_APPENDED_NUMBER_PRODUCT_TEST_CHILD');audit.inverse(text.replace(marker,''),old[PARENT],'ENTIRE_OLD266_PRODUCT_TESTS_AND_HELPERS_UNCHANGED')
    text=q.text(CORE);start=text.index('/// Immutable validated values and limits only;');end=text.index('impl ImportedDocumentForms {',start);addition=text[start:end]
    c.require(addition.count('qualified(kind)?')==addition.count('format_digest(format,limits)?')==1
        and 'format:NativeNumberFormatReplacement<\'a>'in addition and 'search_limits:SourceSearchLimits,limits:ReferenceAuxiliaryLimits'in addition
        and 'proof.lower_number_control_validated(original,selector,body,self.kind,self.expected,max_results,self.stored_number,self.format,self.format_sha,self.search_limits,self.limits,writer)'in addition,
        'IMMUTABLE_BORROWED_VALUES_BOTH_LIMITS_AND_ORIGINAL_PRIVATE_COMPILER_NOT_AUTHORITY')
    audit.inverse(text[:start]+text[end:],old[CORE],'ENTIRE_ORIGINAL67_NUMBER_SOURCE_PUBLIC_APIS_PRIVATE_COMPILER_GUARDS_AND_REVIEW_READBACK_UNCHANGED')
    text=q.text(DISCOVERY);c.require(text.count(GETTERS)==1,'THREE_ADDITIVE_READONLY_SEARCH_REQUEST_GETTERS')
    audit.inverse(text.replace(GETTERS,''),old[DISCOVERY],'ENTIRE_ORIGINAL_CONTROL_MATCHER_SCOPE_POLICY_CAP_ORDER_HASH_AND_RESULT_BODIES_UNCHANGED')
    stored=q.text(STORED)
    for marker in('self.fresh_source_reconstructed(provider,now)?','input.lower(&proof,&self.imported,selector,body,max_results,writer)?',
        'source:LiteralSource::Owned(Box::new(self))','self.source.fresh_source(provider,now)?','let mut selected=search.controls().iter();',
        'for node in &sequence.nodes','counts.get_mut(','input.request_sha256(r.search.request_sha256())?'):
        c.require(stored.count(marker)==1,'ONE_CURRENT_PROOF_COMPILER_OWNER_MOVE_FORWARD_SUBSET_NODE_AGGREGATION_AND_NO_SEARCH_REPLAY')
    product=q.text(PRODUCT)
    for marker in('super::selector::parse_selector_object(raw)','enum Kind{ReplaceNumberControls}',
        'enum Format{Preserve{},Replace{','fn native(&self)->NativeNumberFormatReplacement',
        'let(request,canonical)=Request::parse(raw)?','Request::scoped_sha(scope,&canonical)?','let canonical=request.canonical_sha()?',
        'ValidatedNumberControlValues::new(','source.into_number_control_candidate(','drop(input);'):
        c.require(marker in product,'STRICT_NESTED_UNIQUE_JSON_BORROWED_FORMAT_ONE_VALIDATION_AND_ONE_CANONICAL_SERIALIZATION_PER_CHECK')
    formats=re.findall(r'\(([A-Za-z0-9]+),"([A-Z0-9_]+)"\)',product)
    c.require(len(formats)==len(set(formats))==22,'EXACT22_CLOSED_TYPED_NUMBER_FORMAT_WIRE_MAPPINGS')


def expected(q):
    names=re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(TEST));c.require(len(names)==len(set(names))==26,'EXACT26_NUMBER_PRODUCT_CASE_IDENTITIES');return{PREFIX+n for n in names}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'NUMBER_CONTROL_PRODUCT_IMMUTABLE_RUN_EXISTS');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_NUMBER_CONTROL_PRODUCT_COMPONENTS',steps=[],own_cpu_selection=selection,actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False,native_counter_full_control_transaction_or_gate_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        baseline=q.json(prior.OUTPUT)
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='a8a32399ec72474a03f8672dc6530e661b0108f1c09e941232460c2808250450'
            and baseline['state']=='PASS_REVIEW_BOUND_NUMBER_SOURCE30_DIAGNOSTIC1_AFFECTED36_NOT_STORE_PRODUCT_NATIVE_OR_GATE'and baseline['cleanup']
            and baseline['fresh_inputs']==baseline['final_fresh_hashes']==723 and baseline['total_executed_cases']==67,'EXACT200_REVIEW_BOUND_SOURCE67_AND_FRESH_CLOSURE')
        old={p['path']:p for p in baseline['source_pins']};c.require(NEW.isdisjoint(old),'NEW_NUMBER_PRODUCT_FILES_ADDITIVE')
        for name in names-NEW-CHANGED:c.require(q.snapshots[name]==old[name],'ALL_OTHER_STREAM_IMPORTS_COMPILERS_GUARDS_READBACK_PRODUCTS_TESTS_AND_FIXTURES_UNCHANGED')
        inverse(q,old);cases=expected(q)
        print(json.dumps(dict(state='NUMBER_CONTROL_PRODUCT_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),new_product_cases=26,source67_and_old266_products_reexecuted=False,one_cpu_mask=4)),flush=True)
        harness.run_one('twenty_six_current_store_strict_number_control_products',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli',
            '--test','regex_replacement_product','--message-format=short','--',PREFIX,'--test-threads=1'],cases,guard,audit.environment(),row,observe_capture=snapshot)
        tools.good_step(row['steps'][0],cases);c.require(inventory(guard.check)==names,'FINAL_NUMBER_PRODUCT_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_NUMBER_CONTROL_TWENTY_SIX_PRODUCTS_NOT_NATIVE_COUNTER_FULL_TRANSACTION_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_product_cases=26,source67_reexecuted=False,old266_products_reexecuted=False,original_source_compiler_search_and_old_product_bodies_inverse_verified=True,
            one_borrowed_validated_format_current_source_proof_compiler_owner_move_and_no_search_replay=True,
            forward_anchor_subset_and_bounded_number_node_aggregation=True,canonical_payload_serialized_once_per_binding_check=True,
            next_work='SEARCH009_other_control_families_reference_ID_preservation_and_remaining_full_P09_contract_transaction_native_gates')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'NUMBER_CONTROL_PRODUCT_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_NUMBER_PRODUCT_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations','safe_error_variants')},
                'observation':{k:s.get('bounded_output_observation',{}).get(k)for k in('safe_warning_locations','short_error_locations','rust_error_codes')},
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
