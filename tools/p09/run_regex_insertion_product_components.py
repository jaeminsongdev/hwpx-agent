"""18 new v2 products and29 affected original products; one owned CPU2 binary, no core replay."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_regex_insertion_linear as prior
from run_regex_product_components import STORED as OLD_STORED,PRODUCT as OLD_PRODUCT,TEST as OLD_TEST,expected as original_expected
harness,shared,c,a,audit,snapshot=prior.harness,prior.shared,prior.c,prior.a,prior.audit,prior.snapshot
OUTPUT='implementation/p09/evidence/p09-361-regex-insertion-product-components123.v1.json'
STORED=OLD_STORED[:-3]+'/insertions.rs';PRODUCT=OLD_PRODUCT[:-3]+'/insertions.rs'
TEST='crates/product-cli/tests/form_stored_provider/actual_import/regex_insertion_product.rs'
NEW={STORED,PRODUCT,TEST};CHANGED={OLD_STORED,OLD_PRODUCT,OLD_TEST}
HELPER='''pub(crate) fn source_receipt_matches(outer:&SourceSelectorRegexReceipt,source_sha256:[u8;32],profile:&str,atom_profile:&str)->bool {
    let output=&outer.output;
    !(outer.profile!=profile||output.profile!=atom_profile||output.source_package_sha256!=source_sha256
        ||outer.selector.index_sha256!=output.source_index_sha256||outer.selector.scope_sha256!=output.scope_sha256
        ||outer.expansion_sha256!=output.replacement_sha256||outer.expanded_replacement_bytes!=output.replacement_bytes
        ||outer.match_regions.len()!=output.matched_occurrences||outer.expansion_work_limit==0||outer.expansion_work_units>outer.expansion_work_limit
        ||!outer.captures_from_one_original_match_pass||!outer.capture_values_are_index_nfc_text||!outer.scope_window_enforced
        ||outer.zero_width_control_or_field_cache_edit_qualified||outer.native_or_execution_authority||outer.selector.whole_document_visibility_native_flow_or_revision_authority
        ||output.full_protection_native_or_execution_authority||output.field_cached_content_edit_qualified
        ||output.control_atom_replacement_qualified||!output.original_control_bytes_preserved||!output.original_selection_contiguity_verified
        ||!output.outside_selected_text_atoms_exact||!output.output_text_span_values_verified)
}
'''
FRESH='''        let fresh=self.source.fresh_source(provider,now)?;let outer=&self.receipt.output;
        if self.receipt.source!=self.source.receipt||outer!=self.output.receipt()||self.receipt.profile!=STORED_SELECTOR_REGEX_PROFILE
            ||!source_receipt_matches(outer,*fresh.digest.as_bytes(),SOURCE_SELECTOR_REGEX_PROFILE,SOURCE_REGEX_TEXT_ATOM_PROFILE)
            ||self.receipt.issuer_execution_publication_authority{return Err(R::Binding);}Ok(())
'''
ORIGINAL='''        let fresh=self.source.fresh_source(provider,now)?;let outer=&self.receipt.output;let output=&outer.output;
        if self.receipt.source!=self.source.receipt||outer!=self.output.receipt()||self.receipt.profile!=STORED_SELECTOR_REGEX_PROFILE
            ||outer.profile!=SOURCE_SELECTOR_REGEX_PROFILE||output.profile!=SOURCE_REGEX_TEXT_ATOM_PROFILE||output.source_package_sha256!=*fresh.digest.as_bytes()
            ||outer.selector.index_sha256!=output.source_index_sha256||outer.selector.scope_sha256!=output.scope_sha256
            ||outer.expansion_sha256!=output.replacement_sha256||outer.expanded_replacement_bytes!=output.replacement_bytes
            ||outer.match_regions.len()!=output.matched_occurrences||outer.expansion_work_limit==0||outer.expansion_work_units>outer.expansion_work_limit
            ||!outer.captures_from_one_original_match_pass||!outer.capture_values_are_index_nfc_text||!outer.scope_window_enforced
            ||outer.zero_width_control_or_field_cache_edit_qualified||outer.native_or_execution_authority||outer.selector.whole_document_visibility_native_flow_or_revision_authority
            ||self.receipt.issuer_execution_publication_authority||output.full_protection_native_or_execution_authority||output.field_cached_content_edit_qualified
            ||output.control_atom_replacement_qualified||!output.original_control_bytes_preserved||!output.original_selection_contiguity_verified
            ||!output.outside_selected_text_atoms_exact||!output.output_text_span_values_verified{return Err(R::Binding);}Ok(())
'''
PARSE='''        Self::parse_value(value,REGEX_REPLACEMENT_PRODUCT_REQUEST_SCHEMA)
    }
    fn parse_value(value:serde_json::Value,schema:&str)->Result<Self,R> {
'''


def inventory(check):return prior.base.inventory(check)|NEW


def inverse(q,old):
    text=q.text(OLD_STORED);c.require(text.count('pub mod insertions;\n')==1 and text.count(HELPER)==1 and text.count(FRESH)==1,
        'ONLY_EXACT_ORIGINAL_REGEX_OUTPUT_PREDICATE_EXTRACTION_AND_V2_MODULE')
    audit.inverse(text.replace('pub mod insertions;\n','').replace(HELPER,'').replace(FRESH,ORIGINAL),old[OLD_STORED],
        'WHOLE_ORIGINAL_V1_SOURCE_OWNERSHIP_PREPARE_CURRENT_ACCESS_WRITER_AND_FINAL_HEAD_EXACT_INVERSE')
    text=q.text(OLD_PRODUCT);c.require(text.count('pub mod insertions;\n')==1 and text.count(PARSE)==1 and text.count('if request.schema_version!=schema||')==1,
        'ONLY_EXISTING_STRICT_TYPED_REQUEST_VALIDATOR_SHARED_WITH_EXPLICIT_SCHEMA')
    audit.inverse(text.replace('pub mod insertions;\n','').replace(PARSE,'').replace('if request.schema_version!=schema||','if request.schema_version!=REGEX_REPLACEMENT_PRODUCT_REQUEST_SCHEMA||'),
        old[OLD_PRODUCT],'WHOLE_ORIGINAL_V1_STRICT_PARSER_CANONICAL_BINDINGS_AND_PRODUCT_BOUNDARY_EXACT_INVERSE')
    text=q.text(OLD_TEST);include='#[path="regex_insertion_product.rs"] mod insertion_v2;\n'
    c.require(text.count(include)==1,'ONE_ADDITIVE_TEST_MODULE_REUSING_ORIGINAL_HELPERS');audit.inverse(text.replace(include,''),old[OLD_TEST],'ALL_THIRTEEN_ORIGINAL_REGEX_PRODUCT_CASE_BODIES_AND_FIXTURES_UNCHANGED')
    stored=q.text(STORED);c.require(stored.count('self.fresh_source_reconstructed(provider,now)?')==1
        and stored.count('proof.lower_review_selector_regex_insertion_candidate(&self.imported,query,selector,policy,replacement,run_policy,insertion_policy,limits,writer)?')==1
        and stored.count('source:LiteralSource::Owned(Box::new(self))')==1 and stored.count('self.source.fresh_source(provider,now)?')==1,
        'ONE_ORIGINAL_PROOF_COMPILER_OWNER_TRANSFER_AND_FRESH_DELIVERY_NO_REIMPORT_OR_QUERY_REPLAY')
    c.require('RegexRequest::parse_value(value,REGEX_INSERTION_PRODUCT_REQUEST_SCHEMA)'in q.text(PRODUCT)
        and 'REGEX_INSERTION_PRODUCT_REQUEST_SCHEMA,self.policy,&self.inner'in q.text(PRODUCT),'MANDATORY_POLICY_AND_SCHEMA_BOUND_TO_COMPLETE_CANONICAL_REQUEST')


def expected(q):
    new={'actual_import::regex_replacement_product::insertion_v2::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(TEST))}
    old=original_expected(q);c.require(len(new)==18 and len(old)==29 and not(new&old),'EXACT_EIGHTEEN_NEW_TWENTY_NINE_AFFECTED_PRODUCT_IDENTITIES');return new|old


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'REGEX_INSERTION_PRODUCT_IMMUTABLE_RUN_EXISTS');selection=prior.base.prior.prior.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_REGEX_INSERTION_PRODUCT_COMPONENTS',steps=[],actual_Hangul_or_COM=False,own_cpu_selection=selection,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False,full_product_or_native_qualification_added=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        previous=q.json(prior.OUTPUT);c.require(q.snapshots[prior.OUTPUT]['sha256']=='9488aacb48a5217973ab47b17411e5b6fbac23d92c49f17df21172880d4322ea'
            and previous['state'].startswith('PASS_')and previous['actual_current_cases']==19 and previous['cleanup']
            and previous['fresh_inputs']==previous['final_fresh_hashes']==592,'EXACT_QUALIFIED_SOURCE_V2_LINEAR_BASELINE')
        old={p['path']:p for p in previous['source_pins']};old_names={n for n in old if n.startswith(('crates/','fixtures/'))or n in{'Cargo.toml','Cargo.lock','rust-toolchain.toml',prior.base.CAPTURE}}
        c.require(names==old_names|NEW,'EXACT_TWO_NEW_V2_MODULES_AND_ONE_CHILD_TEST_FILE')
        for name in names-NEW-CHANGED:c.require(q.snapshots[name]==old[name],'ALL_CORE_SOURCE_V2_PATCH_WRITER_GUARD_PROTECTION_AND_UNRELATED_INPUTS_UNCHANGED')
        inverse(q,old);cases=expected(q)
        print(json.dumps(dict(state='REGEX_INSERTION_PRODUCT_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),new_cases=18,affected_cases=29,test_binaries=1,one_cpu_mask=4)),flush=True)
        harness.run_one('eighteen_v2_insertions_and_twenty_nine_original_products',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli',
            '--test','regex_replacement_product','--','--test-threads=1'],cases,guard,audit.environment(),row,observe_capture=snapshot)
        limits=row['steps'][0]['owned_job']['limits_readback'];c.require(limits['verified']and limits['affinity_mask']==4 and limits['cpu_hard_cap_machine_percent']==6.25 and limits['priority_class']==16384,
            'ORIGINAL_ONE_CPU2_HARD_CAP_AND_BELOW_NORMAL_PRIORITY_VERIFIED')
        c.require(inventory(guard.check)==names,'FINAL_REGEX_INSERTION_PRODUCT_SOURCE_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_REGEX_INSERTION_PRODUCT_EIGHTEEN_NEW_TWENTY_NINE_AFFECTED_NOT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_product_cases=18,affected_product_cases=29,total_executed_cases=47,source_v2_core_and_unaffected_suites_reexecuted=False,
            original_v1_stored_and_product_whole_file_inverse_verified=True,one_proof_one_capture_compiler_owner_transfer_without_reimport=True,
            current_output_does_not_repeat_query_capture_or_lowering=True,strict_v2_policy_in_canonical_and_scoped_request=True,
            next_work='Remaining_effective_style_visibility_full_scope_and_style_control_conversion_then_full_transaction_native_contract')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'REGEX_INSERTION_PRODUCT_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_INSERTION_PRODUCT_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','locations','summaries','panic_locations','safe_error_variants')},
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
