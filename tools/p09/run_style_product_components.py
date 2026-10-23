"""18 additive character-style products only; original47 products and59 core cases are not replayed."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_style_replacement_target as prior
from run_regex_insertion_product_components import expected as original_product_expected
base=prior.base
harness,shared,c,a,audit,snapshot=prior.harness,prior.shared,prior.c,prior.a,prior.audit,prior.snapshot
OUTPUT='implementation/p09/evidence/p09-361-style-product-components129.v1.json'
ROOT_STORED='crates/product-cli/src/form_stored_provider/actual_import/literal_search_output.rs'
ROOT_PRODUCT='crates/product-cli/src/form_product_request/stored_literal_replacement.rs'
STORED=ROOT_STORED[:-3]+'/styles.rs';PRODUCT=ROOT_PRODUCT[:-3]+'/styles.rs'
PARENT='crates/product-cli/tests/form_stored_provider/actual_import/regex_replacement_product.rs'
TEST='crates/product-cli/tests/form_stored_provider/actual_import/style_replacement_product.rs'
NEW={STORED,PRODUCT,TEST};CHANGED={ROOT_STORED,ROOT_PRODUCT,PARENT}


def inventory(check):return base.inventory(check)|NEW


def inverse(q,old):
    for name in(ROOT_STORED,ROOT_PRODUCT):
        text=q.text(name);c.require(text.count('pub mod styles;\n')==1,'ONE_ADDITIVE_STYLE_MODULE_IN_UNCHANGED_LITERAL_AND_REGEX_ROOT')
        audit.inverse(text.replace('pub mod styles;\n',''),old[name],'WHOLE_ORIGINAL_CURRENT_ACCESS_LITERAL_REGEX_REQUEST_AND_OWNERSHIP_ROOT_UNCHANGED')
    text=q.text(PARENT);include='#[path="style_replacement_product.rs"] mod style_v1;\n'
    c.require(text.count(include)==1 and text.endswith(include),'ONE_CHILD_AFTER_EXISTING_MACRO_DEFINITIONS_REUSING_ORIGINAL_HELPERS')
    audit.inverse(text.replace(include,''),old[PARENT],'WHOLE_ORIGINAL_PRODUCT_TEST_BODIES_AND_FIXTURES_EXACT_INVERSE')
    stored=q.text(STORED);c.require(stored.count('self.fresh_source_reconstructed(provider,now)?')==1
        and stored.count('proof.lower_review_selector_style_candidate(&self.imported,query,selector,policy,filter,character_property,limits,writer)?')==1
        and stored.count('source:LiteralSource::Owned(Box::new(self))')==1 and stored.count('self.source.fresh_source(provider,now)?')==1,
        'ONE_ORIGINAL_PROOF_STYLE_COMPILER_AND_OWNER_TRANSFER_NO_REIMPORT_OR_QUERY_REPLAY')
    product=q.text(PRODUCT);c.require('super::selector::parse_selector_object(raw)'in product and 'request.operation.style_filter.validate()'in product
        and 'struct Replacement {axis:Axis,declaration_id:u32}'in product and 'enum Axis {RunCharacterProperty}'in product,
        'ORIGINAL_STRICT_OBJECT_PARSER_AND_REQUIRED_CLOSED_TARGET_AXIS_FILTER_POLICY')


def expected(q):
    names={'actual_import::regex_replacement_product::style_v1::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(TEST))}
    c.require(len(names)==18,'EXACT_EIGHTEEN_NEW_CHARACTER_STYLE_PRODUCT_IDENTITIES');return names


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'STYLE_PRODUCT_IMMUTABLE_RUN_EXISTS');selection=base.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_STYLE_PRODUCT_COMPONENTS',steps=[],actual_Hangul_or_COM=False,own_cpu_selection=selection,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False,full_style_or_native_qualification_added=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        previous=q.json(prior.OUTPUT);c.require(q.snapshots[prior.OUTPUT]['sha256']=='d2eec58ff9c8fbd2c73d929c4fd8889c842e406434d23916dbf3e72cd17bd75c'
            and previous['state'].startswith('PASS_')and previous['total_distinct_cases']==59 and previous['cleanup']
            and previous['fresh_inputs']==previous['final_fresh_hashes']==604,'EXACT_QUALIFIED_PARTIAL_STYLE_SOURCE_BASELINE')
        old={p['path']:p for p in previous['source_pins']};old_names={n for n in old if n.startswith(('crates/','fixtures/'))or n in{'Cargo.toml','Cargo.lock','rust-toolchain.toml',base.CAPTURE}}
        c.require(names==old_names|NEW,'EXACT_TWO_NEW_STYLE_STORED_PRODUCT_MODULES_AND_ONE_CHILD_TEST_FILE')
        for name in names-NEW-CHANGED:c.require(q.snapshots[name]==old[name],'NO_CORE_RENDER_MATCHER_PROTECTION_WRITER_GUARD_OR_ORIGINAL_PRODUCT_BODY_INPUT_CHANGE')
        inverse(q,old);cases=expected(q);c.require(len(original_product_expected(q))==47,'EXACT_UNCHANGED_FORTY_SEVEN_ORIGINAL_PRODUCT_CASES_RETAINED')
        print(json.dumps(dict(state='STYLE_PRODUCT_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),new_cases=18,original_products_retained=47,source_cases_not_reexecuted=59,one_cpu_mask=4)),flush=True)
        harness.run_one('eighteen_new_character_style_products_only',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli',
            '--test','regex_replacement_product','--message-format=short','--',*sorted(cases),'--exact','--test-threads=1'],cases,guard,audit.environment(),row,observe_capture=snapshot)
        limits=row['steps'][0]['owned_job']['limits_readback'];c.require(limits['verified']and limits['affinity_mask']==4 and limits['cpu_hard_cap_machine_percent']==6.25 and limits['priority_class']==16384,
            'ORIGINAL_ONE_CPU2_HARD_CAP_AND_BELOW_NORMAL_PRIORITY')
        c.require(inventory(guard.check)==names,'FINAL_STYLE_PRODUCT_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_STYLE_PRODUCT_EIGHTEEN_NEW_NOT_FULL_STYLE_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_product_cases=18,total_executed_cases=18,original_products_retained=47,original_products_reexecuted=False,source_core_and_unrelated_suites_reexecuted=False,
            original_root_and_test_whole_file_inverse_verified=True,one_proof_one_style_compiler_owner_transfer_without_reimport=True,
            current_output_does_not_repeat_search_or_style_lowering=True,explicit_axis_target_filter_policy_bound_to_canonical_and_scoped_request=True,
            next_work='Paragraph_named_text_style_replacement_and_effective_style_full_scope_then_remaining_transaction_native_contract')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'STYLE_PRODUCT_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_STYLE_PRODUCT_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations','safe_error_variants')},
                'warnings':s.get('bounded_output_observation',{}).get('safe_warning_locations',[]),'short_errors':s.get('bounded_output_observation',{}).get('short_error_locations',[]),
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
