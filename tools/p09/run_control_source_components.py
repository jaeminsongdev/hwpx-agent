"""24 exact-control source cases plus12 affected selector regressions; no18-patch/242-product replay."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_text_control_patch_recovery as prior
harness,shared,c,a,audit,snapshot=prior.harness,prior.shared,prior.c,prior.a,prior.audit,prior.snapshot
OUTPUT='implementation/p09/evidence/p09-361-control-source-components192.v1.json'
PARENT='crates/hwpx-package/src/document_import/search/replacement/atoms.rs'
CORE=PARENT[:-3]+'/controls.rs';PLAN=PARENT[:-3]+'/controls/plan.rs'
WS=PARENT[:-3]+'/whitespace.rs';WPLAN=PARENT[:-3]+'/whitespace/plan.rs';READBACK=PARENT[:-3]+'/whitespace/readback.rs'
DISCOVERY='crates/hwpx-package/src/document_import/search/reviews/selector/controls.rs'
TEST='crates/hwpx-package/tests/document_import_control_replacement.rs';BUNDLE='crates/hwpx-package/tests/control_replacement_focused.rs'
OLD_TEST='crates/hwpx-package/tests/document_import_selector_controls.rs'
NEW={CORE,PLAN,TEST,BUNDLE};CHANGED={PARENT,WS,WPLAN,READBACK,DISCOVERY}
SPAN='''pub(in crate::document_import::search::replacement::atoms) struct Span {
    pub(in crate::document_import::search::replacement::atoms) element:usize,
    pub(in crate::document_import::search::replacement::atoms) expected:TextSpan,
    pub(in crate::document_import::search::replacement::atoms) lexical:Vec<LexicalEdit>,
}
'''
EXTRA='''        self.find_control_with_windows(selector,policy,kind,max_results).map(|(result,_)|result)
    }
    pub(in crate::document_import::search) fn find_control_with_windows(&self,selector:SourceIndexScopeSelector<'_>,policy:SourceReviewTextPolicy,kind:SourceControlKind,max_results:usize)
        ->Result<(SourceReviewSelectorControlResult,BTreeMap<usize,(usize,usize)>),E> {
'''


def inventory(check):return prior.base.inventory(check)|NEW


def change(text,new,old):
    c.require(text.count(new)==1,'ONE_MECHANICAL_CONTROL_SHARED_BODY_CHANGE');return text.replace(new,old)


def inverse(q,old):
    audit.inverse(change(q.text(PARENT),'pub mod controls;\n',''),old[PARENT],'ENTIRE_OLD_SOURCE_COMPILERS_AND_ATOM_BODIES_UNCHANGED')
    text=q.text(WS)
    for name in('plan','readback','lexical'):text=change(text,'pub(super) mod '+name+';\n','mod '+name+';\n')
    audit.inverse(text,old[WS],'ENTIRE_OLD_WHITESPACE_SOURCE_API_EXCEPT_PRIVATE_MODULE_VISIBILITY')
    audit.inverse(change(q.text(WPLAN),SPAN,'pub(super) struct Span {pub(super) element:usize,pub(super) expected:TextSpan,pub(super) lexical:Vec<LexicalEdit>}\n'),old[WPLAN],
        'ENTIRE_OLD_WHITESPACE_PLANNER_AND_GUARDS_EXCEPT_SHARED_READBACK_SPAN_VISIBILITY')
    audit.inverse(change(q.text(READBACK),'pub(in crate::document_import::search::replacement::atoms) fn verify(','pub(super) fn verify('),old[READBACK],
        'ENTIRE_OLD_SPARSE_BYTE_REVIEW_IMPORT_AND_STABLE_TEXT_SPAN_READBACK_BODY_UNCHANGED')
    text=change(q.text(DISCOVERY),EXTRA,'');text=change(text,'let(scope,windows)=','let(scope,_)=');text=change(text,'Ok((value,windows))','Ok(value)')
    audit.inverse(text,old[DISCOVERY],'EXACT_OLD_CONTROL_SEARCH_GEOMETRY_REVIEW_CAP_ORDER_HASH_AND_RESULT_BODY_MECHANICALLY_FORWARDED_WITH_SAME_WINDOWS')
    code=q.text(CORE);plan=q.text(PLAN)
    for marker in('find_control_with_windows(selector,body_policy,kind,max_results)','whitespace::readback::verify(',
        'self.lower_control_validated(original,selector,body_policy,kind,max_results,output,limits,writer,expected,validated)'):
        c.require(marker in code,'ONE_ORIGINAL_SCOPE_MATCHER_VALIDATED_OUTPUT_AND_SHARED_COMPLETE_READBACK')
    for marker in('wanted_parents.contains','index.usage.get(origin)!=Some(&(a+pos,a+pos))','allowed.contains(',
        'unicode::plan::guard(xml)','context.field_intervals(source,fields)','Check actual namespace/escaping and aggregate output BEFORE any per-control clone.',
        'encoded.get(&prefix)','TextFlowLimits::default().config().input_bytes'):
        c.require(marker in plan,'COMPLETE_ORIGINAL_ATOM_SELECTION_GUARD_FIELD_CACHE_AND_PRECLONE_OUTPUT_BOUND')


def expected(q):
    result=set()
    for name,module,count in[(TEST,'replacement',24),(OLD_TEST,'discovery',12)]:
        names=re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(name));c.require(len(names)==len(set(names))==count,'EXACT24_NEW12_ORIGINAL_CONTROL_IDENTITIES');result.update(module+'::'+n for n in names)
    return result


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'CONTROL_SOURCE_IMMUTABLE_RUN_EXISTS');selection=prior.base.prior.prior.base.prior.base.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_CONTROL_SOURCE_COMPONENTS',steps=[],own_cpu_selection=selection,actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False,all_control_kinds_store_product_native_or_gate_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        baseline=q.json(prior.OUTPUT)
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='db43378fce7e924fed7bac34a0b1f9f4e5822cac8911ecf91d4462676c2ac68f'
            and baseline['state']=='PASS_TEXT_CONTROL_PATCH18_NOT_SOURCE_STORE_PRODUCT_NATIVE_OR_GATE'and baseline['cleanup']
            and baseline['fresh_inputs']==baseline['final_fresh_hashes']==708 and baseline['new_patch_cases']==18,'EXACT190_ORIGINAL_TEXT_CONTROL_PATCH_BASELINE')
        old={p['path']:p for p in baseline['source_pins']};c.require(NEW.isdisjoint(old),'NEW_CONTROL_SOURCE_FILES_ADDITIVE')
        for name in names-NEW-CHANGED:c.require(q.snapshots[name]==old[name],'ALL_OTHER_PATCH_GUARDS_WRITERS_OLD_SOURCE_PRODUCTS_TESTS_FIXTURES_UNCHANGED')
        inverse(q,old);cases=expected(q)
        print(json.dumps(dict(state='CONTROL_SOURCE_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),new_source_cases=24,affected_selector_cases=12,one_cpu_mask=4)),flush=True)
        harness.run_one('twenty_four_control_source_and_twelve_original_selector_cases',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package',
            '--test','control_replacement_focused','--message-format=short','--','--test-threads=1'],cases,guard,audit.environment(),row,observe_capture=snapshot)
        prior.base.prior.prior.base.prior.base.good_step(row['steps'][0],cases);c.require(inventory(guard.check)==names,'FINAL_CONTROL_SOURCE_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_CONTROL_SOURCE24_SELECTOR12_NOT_OTHER_KINDS_STORE_PRODUCT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_source_cases=24,affected_selector_cases=12,total_executed_cases=36,old18_patch_whitespace24_products242_or_official249_reexecuted=False,
            original_selector_body_and_shared_readback_guard_bodies_inverse_verified=True,one_scope_resolution_and_preclone_output_budget=True,
            complete_atomic_original_control_selection_not_just_discovery_start=True,
            next_work='SEARCH009_current_store_strict_product_and_other_control_families_then_remaining_full_P09_contract_native_and_gates')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'CONTROL_SOURCE_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_CONTROL_SOURCE_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations','safe_error_variants')},
                'observation':{k:s.get('bounded_output_observation',{}).get(k)for k in('safe_warning_locations','short_error_locations','rust_error_codes')},
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
