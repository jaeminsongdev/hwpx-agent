"""Actual final style splices:12 new,36 affected old products and2 affected common dispatcher cases."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_search_mutation_budget_strengthening as prior
harness,shared,c,a,audit,tools=prior.harness,prior.shared,prior.c,prior.a,prior.audit,prior.tools
snapshot=prior.recovery.snapshot
OUTPUT='implementation/p09/evidence/p09-361-style-splice-inventory-components209.v1.json'
CORE='crates/hwpx-package/src/document_import/search/replacement/atoms/styles.rs'
TEXT=CORE[:-3]+'/text.rs';MODEL=CORE[:-3]+'/intents.rs'
STORED='crates/product-cli/src/form_stored_provider/actual_import/literal_search_output/styles.rs'
STORED_TEXT=STORED.replace('/styles.rs','/text_styles.rs')
PRODUCT='crates/product-cli/src/form_product_request/stored_literal_replacement/styles.rs'
PRODUCT_TEXT=PRODUCT.replace('/styles.rs','/text_styles.rs')
PARENT=prior.base.TEST;TEST='crates/product-cli/tests/form_stored_provider/actual_import/style_splice_inventory_product.rs'
DRIVER='tools/p09/run_style_splice_inventory_components.py'
NEW={MODEL,TEST,DRIVER};CHANGED={CORE,TEXT,STORED,STORED_TEXT,PRODUCT,PRODUCT_TEXT,PARENT}
PREFIX=prior.base.PREFIX+'style_inventory_v1::'
OLD_STYLE='crates/product-cli/tests/form_stored_provider/actual_import/style_replacement_product.rs'
OLD_TEXT=OLD_STYLE.replace('/style_replacement_product.rs','/text_style_product.rs')
OLD_PREFIX='actual_import::regex_replacement_product::'


def inventory(check):return prior.inventory(check)|NEW


def inverse(q,old):
    getter='''    /// Metadata only. Stored consumers must use their current-access verified delivery method.
    #[must_use] pub const fn splice_inventory(&self)->&intents::SourceStyleSpliceInventory {&self.splice_inventory}
'''
    finish='        let splice_inventory=splice_targets.finish(receipt.source_package_sha256,receipt.output_package_sha256,&receipt,intents.len(),limits.0.result_bytes)?;\n'
    for file,axis,candidate in ((CORE,'RunCharacterProperty','SourceStyleReplacementCandidate'),(TEXT,'TextCharacterStyle','SourceTextStyleReplacementCandidate')):
        text=q.text(file)
        for marker in (getter,finish,'                splice_targets.observe(part,i,edit)?;\n',
            f'        let mut splice_targets=intents::Builder::new(intents::StyleSpliceAxis::{axis});\n'):
            c.require(text.count(marker)==1,'ONE_TYPED_FINAL_SPLICE_OBSERVATION_AND_INVENTORY_FINALIZATION_PER_STYLE_PATH');text=text.replace(marker,'')
        text=text.replace('pub mod intents;\n','').replace(',splice_inventory:intents::SourceStyleSpliceInventory','').replace(
            f'Ok({candidate} {{artifact,receipt,splice_inventory}})',f'Ok({candidate} {{artifact,receipt}})')
        audit.inverse(text,old[file],'ENTIRE_ORIGINAL_STYLE_MATCHER_COMPILER_NOOP_PROTECTION_RENDER_OVERLAY_PATCH_WRITER_READBACK_AND_RECEIPT_WIRE_PRESERVED')
    for file in (STORED,STORED_TEXT,PRODUCT,PRODUCT_TEXT):
        text=q.text(file);phrase='    /// Reuses original fresh source/integrity/consumer-final head checks, without replaying the search.'if file in(STORED,STORED_TEXT)else'    /// Original product binding and current stored delivery checks; metadata is not execution authority.'
        start=text.index('    /// # Errors\n'+phrase);end=text.index('    #[must_use] pub const fn receipt(',start);addition=text[start:end]
        c.require(addition.count('pub fn with_verified_splice_inventory')==1,'ONE_ADDITIVE_CURRENT_VERIFIED_INVENTORY_DELIVERY_METHOD')
        c.require('self.with_verified_bytes(provider,now,|_|consume(self.output.splice_inventory()))'in addition if file in(STORED,STORED_TEXT)
            else'self.check(provider)?;Ok(self.candidate.with_verified_splice_inventory(provider,now,consume)?)'in addition,'REUSE_CURRENT_ORIGINAL_BINDING_AND_CONSUMER_FINAL_HEAD_NOT_METADATA_AS_AUTHORITY')
        audit.inverse(text[:start]+text[end:],old[file],'ALL_ORIGINAL_STORED_AND_PRODUCT_PREPARATION_RECEIPT_BINDING_ACCESS_DELIVERY_AND_ROUTE_BODIES_UNCHANGED')
    text=q.text(PARENT);marker='#[path="style_splice_inventory_product.rs"] mod style_inventory_v1;\n'
    c.require(text.count(marker)==1 and text.endswith(marker),'ONE_ADDITIVE_STYLE_INVENTORY_TEST_CHILD')
    audit.inverse(text.replace(marker,''),old[PARENT],'ALL26_COMMON_DISPATCH_TEST_BODIES_AND_FIXTURES_UNCHANGED')
    model=q.text(MODEL)
    for marker in ('splices.len() >= PatchLimits::default().config().max_intents','outer.end() != edit.end',
        'part.element_anchor(element)','Sha256::digest(&edit.bytes)','self.splices.len() != expected_intents',
        'legacy_receipt_sha256: bounded_hash(receipt, receipt_limit)?','bounded_hash(&inventory, MAX_INVENTORY_BYTES)?',
        'self.bytes.checked_add(bytes.len())','#[serde(skip)] canonical_sha256'):
        c.require(model.count(marker)==1,'EXACT_FINAL_SOURCE_TARGET_BOUNDED_STREAM_HASHES_AND_LEGACY_RECEIPT_BINDING')
    c.require('ImportedSourcePackage::import'not in model and 'Vec<u8>'not in model and 'String'not in model,'NO_EXTRA_PACKAGE_IMPORT_SERIALIZED_BUFFER_OR_FRAGMENT_TEXT_RETAINED')


def expected(q):
    cases=set()
    for file,prefix,count in ((TEST,PREFIX,12),(OLD_STYLE,OLD_PREFIX+'style_v1::',18),(OLD_TEXT,OLD_PREFIX+'text_style_v1::',18)):
        names=re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(file));c.require(len(names)==len(set(names))==count,'EXACT12_NEW_AND36_AFFECTED_LEGACY_PRODUCT_IDENTITIES');cases.update(prefix+n for n in names)
    cases|={prior.base.PREFIX+'dispatch_character_style_v1',prior.base.PREFIX+'dispatch_text_style_v1'}
    c.require(len(cases)==50,'EXACT50_NEW_AND_ACTUALLY_AFFECTED_CASES');return cases


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'STYLE_SPLICE_INVENTORY_IMMUTABLE_RUN_EXISTS');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_STYLE_SPLICE_INVENTORY_COMPONENTS',steps=[],own_cpu_selection=selection,actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,output_ingest_commit_or_publication=False,
        compiled_queue_reexecuted=False,compiled_operation_route_full_transaction_or_gate_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        baseline=q.json(prior.OUTPUT)
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='ad44c36f7a5fc14c10e3156f584dba9f7be120a3be0ca04eab1dd6485a003f57'
            and baseline['state']=='PASS_COMMON_DISPATCH_BUDGET_POSITIVE_AND_TIGHT_CONTROLS_NOT_TRANSACTION_NATIVE_OR_GATE'
            and baseline['cleanup']and baseline['fresh_inputs']==baseline['final_fresh_hashes']==733,'EXACT207_CURRENT_PREPARED_PRODUCT_BASELINE')
        old={p['path']:p for p in baseline['source_pins']};c.require(NEW.isdisjoint(old),'STYLE_INVENTORY_MODEL_TEST_DRIVER_ADDITIVE')
        for name in names-NEW-CHANGED:c.require(q.snapshots[name]==old[name],'ALL_OTHER_FORM_SOURCE_COMPILERS_WRITERS_PRODUCTS_DISPATCH_AND_FIXTURES_UNCHANGED')
        inverse(q,old);cases=expected(q)
        filters=[PREFIX,OLD_PREFIX+'style_v1::',OLD_PREFIX+'text_style_v1::',prior.base.PREFIX+'dispatch_character_style_v1',prior.base.PREFIX+'dispatch_text_style_v1']
        print(json.dumps(dict(state='STYLE_SPLICE_INVENTORY_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),new_cases=12,affected_cases=38,other_common24_reexecuted=False,one_cpu_mask=4)),flush=True)
        harness.run_one('twelve_exact_style_inventory_and_thirty_eight_affected_products',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli',
            '--test','regex_replacement_product','--message-format=short','--',*filters,'--test-threads=1'],cases,guard,audit.environment(),row,observe_capture=snapshot)
        tools.good_step(row['steps'][0],cases);q.finish();guard.check(force=True)
        row.update(state='PASS_STYLE_SPLICE_INVENTORY12_AFFECTED38_NOT_COMPILED_OPERATION_NATIVE_TRANSACTION_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_product_cases=12,affected_legacy_product_cases=36,affected_common_dispatch_cases=2,total_executed_cases=50,other_common24_reexecuted=False,
            original_style_algorithms_old_receipt_wire_and_service_product_bodies_inverse_verified=True,actual_final_nonoverlapping_patch_splices_retained=True,
            streamed_bounded_receipt_inventory_and_fragment_hashes_without_reimport_or_raw_xml_retention=True,
            next_work='source_anchor_to_actual_operation_targets_compiler_then_real_route_manifest_durable_commit_CAS_and_remaining_P09_contracts')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'STYLE_SPLICE_INVENTORY_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_STYLE_INVENTORY_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations')},
                'observation':{k:s.get('bounded_output_observation',{}).get(k)for k in('safe_warning_locations','short_error_locations','rust_error_codes','closed_nested_error_variants','closed_patch_codes')},
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
