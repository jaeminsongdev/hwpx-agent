"""Four inventory core + ten v5 product +33 existing search/navigation cases, serial bounded Jobs."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_search_selector_closure as prior
base=prior.base
harness,shared,c,a=prior.harness,prior.shared,prior.c,prior.a
OUTPUT='implementation/p09/evidence/p09-361-source-scope-product-components092.v1.json'
CORE=base.MODULE
INVENTORY=CORE[:-3]+'/inventory.rs'
CORE_TEST='crates/hwpx-package/tests/document_import_search_selector_inventory.rs'
FIXTURE='crates/hwpx-package/tests/support/source_scope_fixture.rs'
SERVICE='crates/product-cli/src/form_stored_provider/actual_import/source_search.rs'
NAV=SERVICE[:-3]+'/navigation.rs'
STORED=SERVICE[:-3]+'/selector.rs'
PARENT='crates/product-cli/src/form_product_request/stored_source_search.rs'
PRODUCT=PARENT[:-3]+'/selector.rs'
TARGET='crates/product-cli/tests/source_scope_product.rs'
WRAPPER='crates/product-cli/tests/source_scope_product/actual_import.rs'
TEST='crates/product-cli/tests/form_stored_provider/actual_import/source_scope_product.rs'
OLD_SEARCH='crates/product-cli/tests/form_stored_provider/actual_import/source_search.rs'
OLD_NAV='crates/product-cli/tests/form_stored_provider/actual_import/source_search_navigation.rs'
NEW={INVENTORY,CORE_TEST,FIXTURE,STORED,PRODUCT,TARGET,WRAPPER,TEST}
CHANGED={CORE,SERVICE,NAV,PARENT,base.TEST}


def inventory(check):return base.inventory(check)|{CORE_TEST,TARGET,WRAPPER}


def inverse(q,old,recovered):
    text=q.text(CORE)
    for current,previous in (('pub mod inventory;\n',''),('use serde::Deserialize;\n',''),
        ('#[derive(Clone,Debug,Eq,PartialEq,Deserialize,Serialize)]\n#[serde(deny_unknown_fields)]\n','#[derive(Clone,Debug,Eq,PartialEq,Serialize)]\n')):
        c.require(text.count(current)==1,'ONLY_ADDITIVE_INVENTORY_AND_STRICT_BOUNDARY_DESERIALIZATION');text=text.replace(current,previous)
    base.prior.prior.base.prior.audit.inverse(text,old[CORE],'ORIGINAL_FOUR_SCOPE_RESOLUTION_WINDOW_BOUNDARY_AND_GRAPH_FUNCTIONS_UNCHANGED')
    text=q.text(SERVICE)
    for current in ('pub mod selector;\n',',Scope(selector::ScopeResult)',',Self::Scope(r)=>r.index()',',Self::Scope(r)=>&r.scope',
        ',Self::Scope(r)=>r.request_sha',',Self::Scope(r)=>r.json()',',Self::Scope(_)=>"hwpx-agent.stored-source-search/v5"'):
        c.require(text.count(current)==1,'ONLY_PRIVATE_SCOPE_RESULT_VARIANT_AND_TYPED_ACCESSORS');text=text.replace(current,'')
    base.prior.prior.base.prior.audit.inverse(text,old[SERVICE],'ORIGINAL_PREPARE_FINISH_FRESH_JSON_AUTH_SOURCE_AND_FINAL_CONSUMER_HEAD_BODIES_UNCHANGED')
    for name,addition in ((NAV,',Self::Scope(_)=>Err(SourceSearchError::Cursor)'),(PARENT,'pub mod selector;\n')):
        text=q.text(name);c.require(text.count(addition)==1,'ADDITIVE_PROFILE_ONLY_OLD_SEARCH_AND_NAVIGATION_CONTRACTS_RETAINED')
        base.prior.prior.base.prior.audit.inverse(text.replace(addition,''),old[name],'LEGACY_PRODUCT_PARSER_AND_NAVIGATION_BODY_EXACT_INVERSE')
    c.require(q.snapshots[base.TEST]==recovered[base.TEST],'WARNING_FREE_PREVIOUS_TEST_INPUT_RETAINED_NO_REPLAY')


def test_names(q,path,prefix=''):return {prefix+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(path))}


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SOURCE_SCOPE_PRODUCT_IMMUTABLE_RUN_EXISTS');shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SOURCE_SCOPE_PRODUCT_COMPONENTS',steps=[],actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False,full_selector_or_native_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        previous,recovery=q.json(base.OUTPUT),q.json(prior.OUTPUT)
        c.require(q.snapshots[base.OUTPUT]['sha256']=='f20ba266c903118cbaac7e74f6dfd4747a0b007621be2ca617601f4bd5c08f95'
            and q.snapshots[prior.OUTPUT]['sha256']=='12855c79ece143d3b4435a2258ce494c565d9485ae7a4bd35ba5cd8517339bfd'
            and previous['state'].startswith('PASS_')and previous['total_executed_cases']==50 and previous['cleanup']
            and recovery['state'].startswith('PASS_')and recovery['retained_source_cases']==50 and recovery['cleanup'],'EXACT_PREVIOUS_FIFTY_PASSES_AND_WARNING_FREE_CLOSURE')
        old={p['path']:p for p in previous['source_pins']};recovered={p['path']:p for p in recovery['source_pins']}
        old_names={n for n in old if n.startswith(('crates/','fixtures/'))or n in {'Cargo.toml','Cargo.lock','rust-toolchain.toml',base.prior.prior.base.prior.prior.CAPTURE}}
        c.require(names==old_names|NEW,'EXACT_EIGHT_NEW_INVENTORY_SERVICE_PRODUCT_AND_FOCUSED_TEST_FILES')
        for name in names-NEW-CHANGED:c.require(q.snapshots[name]==old[name],'NO_OTHER_MATCHER_PROVIDER_PROOF_OR_EXISTING_TEST_BODY_CHANGE')
        inverse(q,old,recovered)
        core=test_names(q,CORE_TEST);new=test_names(q,TEST,'actual_import::source_scope_product::')
        old_search=test_names(q,OLD_SEARCH,'actual_import::source_search::');old_nav=test_names(q,OLD_NAV,'actual_import::source_search_navigation::')
        c.require(tuple(map(len,(core,new,old_search,old_nav)))==(4,10,26,7),'EXACT_FOUR_CORE_TEN_PRODUCT_AND_THIRTY_THREE_AFFECTED_IDENTITIES')
        env=base.prior.prior.base.prior.audit.environment()
        print(json.dumps(dict(state='SOURCE_SCOPE_PRODUCT_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),new_core_cases=4,new_product_cases=10,affected_cases=33,
            original_authorization_final_head_and_old_scope_bodies_verified=True)),flush=True)
        harness.run_one('four_inventory_descriptor_and_boundary_core_cases',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package',
            '--test','document_import_search_selector_inventory','--','--test-threads=1'],core,guard,env,row,observe_capture=base.prior.prior.snapshot)
        harness.run_one('ten_v5_product_twenty_six_old_search_seven_old_navigation',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli',
            '--test','source_scope_product','--','--test-threads=1'],new|old_search|old_nav,guard,env,row,observe_capture=base.prior.prior.snapshot)
        c.require(inventory(guard.check)==names,'FINAL_SOURCE_SCOPE_PRODUCT_INPUT_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_SCOPE_INVENTORY_FOUR_CORE_TEN_PRODUCT_THIRTY_THREE_AFFECTED_NOT_FULL_SELECTOR_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,new_core_cases=4,new_product_cases=10,affected_cases=33,total_executed_cases=47,
            previous_fifty_scope_cases_reexecuted=False,original_search_authorization_finish_and_final_head_bodies_preserved=True,
            selector_revision_bound_to_requested_current_source_and_head=True,descriptors_without_raw_text_from_one_operation_local_index=True,
            retained_verify_does_not_rebuild_inventory_or_search=True,legacy_v1_v4_parsers_and_navigation_preserved=True,
            idempotency_claim_or_cas_or_dispatcher_added=False,review_policy_editing_or_native_flow_scope_qualified=False,
            next_work='Review_policy_and_literal_replacement_reuse_validated_selector_windows')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'SOURCE_SCOPE_PRODUCT_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_SCOPE_PRODUCT_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','diagnostics','locations','summaries','tests','panic_locations','safe_error_variants')}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
