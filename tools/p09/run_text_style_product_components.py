"""18 additive text-axis products only; retain65 prior products and source components without replay."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_text_style_id_recovery as prior
from run_style_product_components import expected as run_style_expected
from run_regex_insertion_product_components import expected as legacy_expected
harness,shared,c,a,audit=prior.harness,prior.shared,prior.c,prior.a,prior.audit
OUTPUT='implementation/p09/evidence/p09-361-text-style-product-components138.v1.json'
ROOT_STORED='crates/product-cli/src/form_stored_provider/actual_import/literal_search_output.rs'
ROOT_PRODUCT='crates/product-cli/src/form_product_request/stored_literal_replacement.rs'
STORED=ROOT_STORED[:-3]+'/text_styles.rs';PRODUCT=ROOT_PRODUCT[:-3]+'/text_styles.rs'
PARENT='crates/product-cli/tests/form_stored_provider/actual_import/regex_replacement_product.rs'
TEST='crates/product-cli/tests/form_stored_provider/actual_import/text_style_product.rs'
NEW={STORED,PRODUCT,TEST};CHANGED={ROOT_STORED,ROOT_PRODUCT,PARENT}


def inventory(check):return prior.inventory(check)|NEW


def inverse(q,old):
    for name in(ROOT_STORED,ROOT_PRODUCT):
        text=q.text(name);c.require(text.count('pub mod text_styles;\n')==1,'ONE_ADDITIVE_TEXT_MODULE_IN_UNCHANGED_STORED_AND_PRODUCT_ROOTS')
        audit.inverse(text.replace('pub mod text_styles;\n',''),old[name],'WHOLE_ORIGINAL_LITERAL_REGEX_AND_RUN_STYLE_ROOT_BODY_UNCHANGED')
    text=q.text(PARENT);marker='#[path="text_style_product.rs"] mod text_style_v1;\n'
    c.require(text.count(marker)==1 and text.endswith(marker),'ONE_TEXT_CHILD_DECLARED_AFTER_ORIGINAL_MACROS_AND_RUN_STYLE_MODULE')
    audit.inverse(text.replace(marker,''),old[PARENT],'WHOLE_PREVIOUS_PRODUCT_TEST_BODIES_AND_FIXTURES_UNCHANGED')
    stored=q.text(STORED)
    for marker in('self.fresh_source_reconstructed(provider,now)?',
        'proof.lower_review_selector_text_style_candidate(&self.imported,query,selector,policy,filter,text_character_style,limits,writer)?',
        'source:LiteralSource::Owned(Box::new(self))','self.source.fresh_source(provider,now)?'):
        c.require(stored.count(marker)==1,'ONE_ORIGINAL_PROOF_TEXT_COMPILER_AND_OWNER_TRANSFER_NO_QUERY_REPLAY_OR_REIMPORT')
    product=q.text(PRODUCT)
    c.require('super::selector::parse_selector_object(raw)'in product and 'request.operation.style_filter.validate()'in product
        and 'enum Axis {TextCharacterStyle}'in product and 'enum Kind {ReplaceTextCharacterStyle}'in product,
        'ORIGINAL_STRICT_PARSER_AND_REQUIRED_TEXT_AXIS_KIND_FILTER_POLICY')


def expected(q):
    names={'actual_import::regex_replacement_product::text_style_v1::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(TEST))}
    c.require(len(names)==18,'EXACT_EIGHTEEN_NEW_TEXT_STYLE_PRODUCT_IDENTITIES');return names


def snapshot(capture,expected):
    result=prior.base.snapshot(capture,expected)
    with capture.lock:raw=(bytes(capture.buffers['stdout'])+bytes(capture.buffers['stderr'])).decode('utf-8','replace')
    allowed={'Source','Search','Value','Selection','Protection','FieldContent','NoMatches','NoChange','Limit','Patch','Writer','Readback','Preservation'}
    result['closed_compile_error_variants']=[n for n in re.findall(r'Compile\(([A-Za-z_]+)',raw)if n in allowed][:32]
    result['closed_static_patch_codes']=[n for n in re.findall(r'Patch\("([a-z_]{1,96})"\)',raw)
        if n in {'id_index_validation_failed','patch_conflict','patch_selector_stale','patch_limit_exceeded','patch_preservation_rejected'}][:16]
    return result


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'TEXT_STYLE_PRODUCT_IMMUTABLE_RUN_EXISTS')
    selection=prior.base.prior.base.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_TEXT_STYLE_PRODUCT_COMPONENTS',steps=[],actual_Hangul_or_COM=False,own_cpu_selection=selection,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False,full_effective_style_or_native_qualification_added=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        source=q.json(prior.OUTPUT)
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='f6e09fcba44c43862eb35bd41592d8fb8d1975a60a528c3161cb69ece48a7c30'
            and source['state'].startswith('PASS_')and source['cleanup']and source['fresh_inputs']==source['final_fresh_hashes']==616
            and source['current_cases']==17 and source['retained_unaffected_cases']==4 and source['total_distinct_cases']==21,
            'EXACT_QUALIFIED_TEXT_STYLE_SOURCE_BASELINE_NOT_STORED_PRODUCT_AUTHORITY')
        old={p['path']:p for p in source['source_pins']}
        old_names={n for n in old if n.startswith(('crates/','fixtures/'))or n in{'Cargo.toml','Cargo.lock','rust-toolchain.toml',prior.base.prior.base.CAPTURE}}
        c.require(names==old_names|NEW,'EXACT_TWO_NEW_TEXT_STYLE_ADAPTERS_AND_ONE_NEW_PRODUCT_TEST_FILE')
        for name in names-NEW-CHANGED:c.require(q.snapshots[name]==old[name],'NO_SOURCE_ID_PROFILE_RENDERER_MATCHER_PROTECTION_WRITER_OR_PRIOR_PRODUCT_BODY_CHANGE')
        inverse(q,old);cases=expected(q)
        c.require(len(legacy_expected(q))==47 and len(run_style_expected(q))==18,'SIXTY_FIVE_ORIGINAL_PRODUCTS_RETAINED_NOT_REEXECUTED')
        print(json.dumps(dict(state='TEXT_STYLE_PRODUCT_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),new_cases=18,retained_products=65,one_cpu_mask=4)),flush=True)
        harness.run_one('eighteen_new_text_style_product_cases_only',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli',
            '--test','regex_replacement_product','--message-format=short','--',*sorted(cases),'--exact','--test-threads=1'],cases,guard,audit.environment(),row,observe_capture=snapshot)
        limits=row['steps'][0]['owned_job']['limits_readback']
        c.require(limits['verified']and limits['affinity_mask']==4 and limits['cpu_hard_cap_machine_percent']==6.25 and limits['priority_class']==16384,
            'ORIGINAL_ONE_CPU2_HARD_CAP_AND_BELOW_NORMAL_PRIORITY')
        c.require(inventory(guard.check)==names,'FINAL_TEXT_STYLE_PRODUCT_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_TEXT_STYLE_PRODUCT_EIGHTEEN_NEW_NOT_FULL_STYLE_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_product_cases=18,total_executed_cases=18,retained_original_products=65,original_products_reexecuted=False,source_core_and_unrelated_suites_reexecuted=False,
            original_root_and_test_whole_file_inverse_verified=True,one_proof_one_text_compiler_owner_transfer_without_reimport=True,
            current_output_does_not_repeat_search_or_text_lowering=True,explicit_text_axis_filter_policy_bound_to_canonical_scoped_request=True,
            next_work='Paragraph_named_style_replacement_then_effective_style_full_scope_transaction_native_contract')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'TEXT_STYLE_PRODUCT_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_TEXT_STYLE_PRODUCT_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations','safe_error_variants')},
                'observation':{k:s.get('bounded_output_observation',{}).get(k)for k in('safe_warning_locations','short_error_locations','closed_compile_error_variants','closed_static_patch_codes')},
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
