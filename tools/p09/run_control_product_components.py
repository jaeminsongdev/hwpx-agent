"""24 current-store/strict-control products; retain36 source/selector and242 older product passes."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_control_source_components as prior
harness,shared,c,a,audit,snapshot=prior.harness,prior.shared,prior.c,prior.a,prior.audit,prior.snapshot
OUTPUT='implementation/p09/evidence/p09-361-control-product-components194.v1.json'
STORED_PARENT='crates/product-cli/src/form_stored_provider/actual_import/literal_search_output.rs'
PRODUCT_PARENT='crates/product-cli/src/form_product_request/stored_literal_replacement.rs'
PARENT='crates/product-cli/tests/form_stored_provider/actual_import/unicode_normalization_product.rs'
STORED=STORED_PARENT[:-3]+'/controls.rs';PRODUCT=PRODUCT_PARENT[:-3]+'/controls.rs'
TEST='crates/product-cli/tests/form_stored_provider/actual_import/control_replacement_product.rs';CORE=prior.CORE
NEW={STORED,PRODUCT,TEST};CHANGED={STORED_PARENT,PRODUCT_PARENT,PARENT,CORE}
PREFIX='actual_import::regex_replacement_product::unicode_v1::controls_v1::'


def inventory(check):return prior.inventory(check)|NEW


def inverse(q,old):
    for name in(STORED_PARENT,PRODUCT_PARENT):
        text=q.text(name);marker='pub mod controls;\n';c.require(text.count(marker)==1,'ONE_ADDITIVE_CONTROL_PRODUCT_MODULE')
        audit.inverse(text.replace(marker,''),old[name],'ENTIRE_OLD_LITERAL_REGEX_STYLE_UNICODE_CASE_WIDTH_WHITESPACE_AND_ACCESS_BODIES_UNCHANGED')
    text=q.text(PARENT);marker='#[path="control_replacement_product.rs"] mod controls_v1;\n'
    c.require(text.count(marker)==1 and text.endswith(marker),'ONE_APPENDED_CONTROL_PRODUCT_CHILD');audit.inverse(text.replace(marker,''),old[PARENT],'ENTIRE_OLD_PRODUCT_TEST_BODIES_AND_HELPERS_UNCHANGED')
    text=q.text(CORE);start=text.index('/// Immutable validated parameters only.');end=text.index('impl ImportedDocumentForms {',start);addition=text[start:end]
    c.require(addition.count('plan::validate_output(output,limits)?')==1 and 'output:&\'a [TextAtom]'in addition and 'limits:SourceSearchLimits'in addition
        and 'proof.lower_control_validated(original,selector,body,self.kind,max_results,self.output,self.limits,writer,self.expected,self.validated)'in addition,
        'VALIDATED_BORROWED_PARAMETERS_AND_LIMITS_NOT_SOURCE_OR_EXECUTION_AUTHORITY')
    audit.inverse(text[:start]+text[end:],old[CORE],'ENTIRE_OLD_CONTROL_SOURCE_PUBLIC_APIS_PRIVATE_COMPILER_PROOF_GUARDS_AND_READBACK_UNCHANGED')
    stored=q.text(STORED)
    for marker in('self.fresh_source_reconstructed(provider,now)?','input.lower(&proof,&self.imported,selector,body,max_results,writer)?',
        'source:LiteralSource::Owned(Box::new(self))','self.source.fresh_source(provider,now)?','let mut selected=search.controls().iter();','selected.any('):
        c.require(stored.count(marker)==1,'ONE_CURRENT_PROOF_COMPILER_OWNER_MOVE_LINEAR_ANCHOR_SUBSET_AND_NO_SEARCH_REPLAY')
    product=q.text(PRODUCT)
    for marker in('super::selector::parse_selector_object(raw)','enum Kind{ReplaceTextControls}','#[serde(with="atom_wire")] output:Vec<TextAtom>',
        'Vec::<Owned>::deserialize(d)?.into_iter()','TextAtom::Text(value)','ser::SerializeSeq','drop(input);','source.into_control_input(',
        'ValidatedTextControlOutput::new(request.operation.control_kind,&request.operation.output,limits)'):
        c.require(marker in product,'STRICT_UNIQUE_JSON_TYPED_OUTPUT_OWNERSHIP_MOVE_BORROWED_SERIALIZATION_AND_ONE_VALIDATION')


def expected(q):
    names=re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(TEST));c.require(len(names)==len(set(names))==24,'EXACT24_NEW_CONTROL_PRODUCTS');return{PREFIX+n for n in names}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'CONTROL_PRODUCT_IMMUTABLE_RUN_EXISTS');selection=prior.prior.base.prior.prior.base.prior.base.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_CONTROL_PRODUCT_COMPONENTS',steps=[],own_cpu_selection=selection,actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False,all_control_kinds_transaction_native_contract_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        baseline=q.json(prior.OUTPUT)
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='2c5c3182775ea96039baade96a89bf232420296c1cc2cbaab6757e5fa0aca604'
            and baseline['state']=='PASS_CONTROL_SOURCE24_SELECTOR12_NOT_OTHER_KINDS_STORE_PRODUCT_NATIVE_OR_GATE'and baseline['cleanup']
            and baseline['fresh_inputs']==baseline['final_fresh_hashes']==712 and baseline['new_source_cases']==24
            and baseline['affected_selector_cases']==12 and baseline['total_executed_cases']==36,'EXACT192_CONTROL_SOURCE24_SELECTOR12_BASELINE')
        old={p['path']:p for p in baseline['source_pins']};c.require(NEW.isdisjoint(old),'NEW_CONTROL_PRODUCT_FILES_ADDITIVE')
        for name in names-NEW-CHANGED:c.require(q.snapshots[name]==old[name],'ALL_OTHER_SOURCE_COMPILERS_GUARDS_READBACK_PATCHES_OLD_PRODUCTS_TESTS_AND_FIXTURES_UNCHANGED')
        inverse(q,old);cases=expected(q)
        print(json.dumps(dict(state='CONTROL_PRODUCT_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),new_product_cases=24,source36_and_old242_products_reexecuted=False,one_cpu_mask=4)),flush=True)
        harness.run_one('twenty_four_current_store_strict_control_product_cases',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli',
            '--test','regex_replacement_product','--message-format=short','--',PREFIX,'--test-threads=1'],cases,guard,audit.environment(),row,observe_capture=snapshot)
        prior.prior.base.prior.prior.base.prior.base.good_step(row['steps'][0],cases);c.require(inventory(guard.check)==names,'FINAL_CONTROL_PRODUCT_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_CONTROL_TWENTY_FOUR_PRODUCTS_NOT_OTHER_KINDS_TRANSACTION_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_product_cases=24,source36_reexecuted=False,old242_products_reexecuted=False,original_product_and_control_source_bodies_inverse_verified=True,
            one_borrowed_validated_output_current_source_proof_compiler_and_no_search_replay=True,linear_forward_anchor_subset_no_quadratic_revalidation=True,
            moved_wire_payload_borrowed_canonical_serialization_no_native_output_vector_clone=True,
            next_work='SEARCH009_other_qualified_control_families_reference_ID_preservation_and_remaining_P09_full_contract_transaction_native_gates')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'CONTROL_PRODUCT_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_CONTROL_PRODUCT_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations','safe_error_variants')},
                'observation':{k:s.get('bounded_output_observation',{}).get(k)for k in('safe_warning_locations','short_error_locations','rust_error_codes')},
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
