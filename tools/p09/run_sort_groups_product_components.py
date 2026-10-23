"""Actual current stored and strict multi-parent JSON sort candidate; no old or Native cases replay."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_sort_groups_serialization_recovery as prior
harness,shared,c,a,audit,tools=prior.harness,prior.shared,prior.c,prior.a,prior.audit,prior.tools
OUTPUT='implementation/p09/evidence/p09-361-sort-groups-product-components246.v1.json'
DRIVER='tools/p09/run_sort_groups_product_components.py'
DOC_BASE='implementation/p09/evidence/p09-361-sort-groups-sync245.v1.json'
STORED_ROOT='crates/product-cli/src/form_stored_provider/actual_import/literal_search_output.rs'
STORED=STORED_ROOT[:-3]+'/sort_groups.rs'
PRODUCT_ROOT='crates/product-cli/src/form_product_request/stored_literal_replacement.rs'
PRODUCT=PRODUCT_ROOT[:-3]+'/sort_groups.rs'
PARENT='crates/product-cli/tests/form_stored_provider/actual_import/paragraph_sort_product.rs'
TEST='crates/product-cli/tests/form_stored_provider/actual_import/paragraph_sort_groups_product.rs'
NEW={DRIVER,STORED,PRODUCT,TEST};CHANGED={STORED_ROOT,PRODUCT_ROOT,PARENT}
CHILD='#[path="paragraph_sort_groups_product.rs"]mod groups_v1;\n'
PREFIX='actual_import::regex_replacement_product::unicode_v1::sort_v1::groups_v1::'


def inventory(check):return prior.inventory(check)|NEW|{'tools/p09/run_sort_groups_sync.py','protocol/migrations/p09-paragraph-sort-groups-v1.md'}


def expected(q):
    cases=re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(TEST))
    c.require(len(cases)==len(set(cases))==20,'EXACT20_NEW_CURRENT_STORED_MULTIGROUP_PRODUCT_CASES')
    return{PREFIX+name for name in cases}


def inverse(q,old):
    for name in(STORED_ROOT,PRODUCT_ROOT):
        text=q.text(name);marker='pub mod sort_groups;\n';c.require(text.count(marker)==1,'ONE_ADDITIVE_MULTIGROUP_SERVICE_OR_PRODUCT_CHILD')
        audit.inverse(text.replace(marker,''),old[name],'ALL_ORIGINAL_CURRENT_ACCESS_AND_EXISTING_PRODUCT_BODIES_UNCHANGED')
    text=q.text(PARENT);c.require(text.endswith(CHILD)and text.count(CHILD)==1,'ONE_NEW_TEST_CHILD_ONLY')
    audit.inverse(text[:-len(CHILD)],old[PARENT],'ALL_ORIGINAL20_SINGLE_GROUP_PRODUCT_CASES_AND_HELPERS_PRESERVED')
    text=q.text(STORED)
    for marker in('AuthScope::DocumentWrite','self.fresh_source_reconstructed(provider,now)','proof.lower_selector_paragraph_sort_groups_candidate(',
        'LiteralSource::Borrowed(self)','LiteralSource::Owned(Box::new(self))','self.source.fresh_source(provider,now)',
        'total.checked_add(n).filter','work.checked_add(group.comparison_bytes).filter','group.moved_paragraphs!=actual',
        'r.changed_parts==parts.len()','provider.check_head(self.source.source.head)','Err(C::RouteUnqualified)'):
        c.require(marker in text,'EXACT_RETAINED_CURRENT_ACCESS_GLOBAL_GROUP_RECEIPT_SOURCE_WRITER_AND_FINAL_HEAD_BOUNDARIES')
    c.require(text.count('proof.lower_selector_paragraph_sort_groups_candidate(')==1,'SORT_ONLY_DURING_INITIAL_CURRENT_PREPARATION')
    text=q.text(PRODUCT)
    for marker in('hwpx-agent.product-paragraph-sort-groups-request/v1','enum Kind{SortParagraphGroups}','parse_selector_object(raw)',
        'Scope::shape','request.selector.validate_shape','provider.source_search_product_scope','source.into_paragraph_sort_groups_candidate',
        'self.receipt.scoped_request_sha256!=request.scoped_sha(scope)?','self.candidate.with_verified_bytes(provider,now,consume)',
        'Err(C::RouteUnqualified)'):
        c.require(marker in text,'CLOSED_EXPLICIT_SCHEMA_POLICY_FOUR_SELECTORS_AND_CURRENT_SCOPED_REQUEST_BINDINGS')
    for name in(STORED,PRODUCT):
        c.require(all(marker not in q.text(name)for marker in('std::fs::','std::process::','SignatureVerified','unsafe','commit_success(','WorkspaceTransaction::create')),
            'NO_EXTERNAL_IO_TRUST_PROMOTION_OR_COMMIT')


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SORT_GROUPS_PRODUCT_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SORT_GROUPS_PRODUCT_COMPONENTS',steps=[],own_cpu_selection=selection,
        actual_Hangul_or_COM=False,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        SEARCH021_complete=False,multigroup_common_dispatcher_compiler_or_execution_qualified=False,output_ingest_commit_or_publication=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);source=q.json(prior.OUTPUT);docs=q.json(DOC_BASE)
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='cbda1142d600e2054606f2d402412ab24521c89c34c725155492649a1376e779'
            and source['cleanup']and source['fresh_inputs']==source['final_fresh_hashes']==818 and source['total_executed_cases']==16,'EXACT244_SOURCE16_AND_TERMINAL_CLOSURE')
        c.require(q.snapshots[DOC_BASE]['sha256']=='a1f1ba526da2298097011642339365c87b2ba5a7a6c576408155e229fe6f7d04'
            and docs['cleanup']and docs['fresh_inputs']==docs['final_fresh_hashes']==28,'EXACT245_SOURCE_GROUPS_DOC_CLOSURE')
        old={p['path']:p for p in source['source_pins']};documented={p['path']:p for p in docs['source_pins']}
        for name in sorted(inventory(guard.check)):
            q.pin(name)
            if name not in NEW|CHANGED:
                pin=documented.get(name,old.get(name));c.require(pin is not None and q.snapshots[name]==pin,'ALL_OTHER_CURRENT_SOURCE_GROUPS_PROTECTION_COMPILER_ROUTER_AND_TESTS_UNCHANGED')
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        inverse(q,old);cases=expected(q)
        print(json.dumps(dict(state='SORT_GROUPS_PRODUCT_PREFLIGHT',inputs=len(q.snapshots),new_cases=len(cases),old_source16_sort19_product20_compiler21_official249_reexecuted=False)),flush=True)
        harness.run_one('twenty_actual_current_stored_multigroup_sort_and_strict_JSON_cases',
            [harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli','--test','regex_replacement_product','--message-format=short','--',PREFIX,'--test-threads=1'],
            cases,guard,audit.environment(),row,observe_capture=prior.base.base.base.prior.prior.base.prior.base.prior.base.base.snapshot)
        tools.good_step(row['steps'][-1],cases);q.finish();guard.check(force=True)
        row.update(state='PASS_CURRENT_STORED_MULTIGROUP_SORT_AND_STRICT_PRODUCT20_NOT_COMMON_EXECUTION_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,total_executed_cases=20,
            original_single_group_api_and_current_security_preserved=True,retained_multigroup_source_without_repeated_sort=True,
            old_source16_sort19_product20_compiler21_and_official249_reexecuted=False,
            next_work='sealed_exact_multigroup_moved_slots_and_shared_compiler_dispatch_manifest_then_actual_trusted_execution_and_remaining_sort_semantics')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'SORT_GROUPS_PRODUCT_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_SORT_GROUPS_PRODUCT_RESOURCE_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations','safe_error_variants')},
                'observation':{k:s.get('bounded_output_observation',{}).get(k)for k in('safe_warning_locations','short_error_locations','rust_error_codes','closed_nested_error_variants','closed_patch_codes')},
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
