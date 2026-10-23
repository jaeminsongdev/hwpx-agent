"""20 selected auto/restart source cases plus36 affected control source/selector cases, serial guarded."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_control_product_components as prior
harness,shared,c,a,audit,snapshot=prior.harness,prior.shared,prior.c,prior.a,prior.audit,prior.snapshot
source=prior.prior;tools=source.prior.base.prior.prior.base.prior.base
OUTPUT='implementation/p09/evidence/p09-361-number-control-source-components197.v1.json'
PARENT=source.PARENT;DISCOVERY=source.DISCOVERY;GEOMETRY='crates/hwpx-package/src/document_import/search/selector/control_geometry.rs'
CORE=PARENT[:-3]+'/number_controls.rs';TEST='crates/hwpx-package/tests/document_import_number_control_replacement.rs';BUNDLE=source.BUNDLE
NEW={CORE,TEST};CHANGED={PARENT,DISCOVERY,GEOMETRY,BUNDLE}
EXTRA='''        self.find_control_with_geometry(selector,policy,kind,max_results).map(|(result,windows,_)|(result,windows))
    }
    pub(in crate::document_import::search) fn find_control_with_geometry(&self,selector:SourceIndexScopeSelector<'_>,policy:SourceReviewTextPolicy,kind:SourceControlKind,max_results:usize)
        ->Result<(SourceReviewSelectorControlResult,BTreeMap<usize,(usize,usize)>,ControlGeometry),E> {
'''


def inventory(check):return prior.inventory(check)|NEW


def inverse(q,old):
    audit.inverse(q.text(PARENT).replace('pub mod number_controls;\n',''),old[PARENT],'ENTIRE_OLD_LITERAL_REGEX_STYLE_UNICODE_WIDTH_WHITESPACE_AND_TEXT_CONTROL_BODIES_UNCHANGED')
    text=q.text(DISCOVERY);c.require(text.count(EXTRA)==1,'ONE_CONTROL_GEOMETRY_RETURN_EXTRACTION')
    audit.inverse(text.replace(EXTRA,'').replace('Ok((value,windows,geometry))','Ok((value,windows))'),old[DISCOVERY],
        'ENTIRE_OLD_CONTROL_MATCHER_GEOMETRY_CAP_REVIEW_ORDER_HASH_AND_RESULT_BODY_UNCHANGED')
    text=q.text(GEOMETRY);start=text.index('    /// Whole original outer range,');end=text.index('    pub(super) fn selection(',start)
    audit.inverse(text[:start]+text[end:],old[GEOMETRY],'ENTIRE_OLD_CONTROL_START_GEOMETRY_NFC_BOUNDARIES_AND_ATOM_DECODER_UNCHANGED')
    marker='#[path="document_import_number_control_replacement.rs"] mod numbers;\n';text=q.text(BUNDLE)
    c.require(text.count(marker)==1 and text.endswith(marker),'ONE_APPENDED_NUMBER_CONTROL_TEST_CHILD');audit.inverse(text.replace(marker,''),old[BUNDLE],'ENTIRE_OLD36_CONTROL_TEST_BUNDLE_UNCHANGED')
    code=q.text(CORE)
    for marker in('geometry.contains_whole(text,&m.control_anchor)','unicode::plan::guard(xml)?','for value in guard',
        'BEFORE semantic no-op elimination','context.field_intervals(source,&fields)?','state.context().ordered_controls()',
        'self.lower_caption_state_sequence_batch_candidate(original,&state,fresh,&[],&[],&[],&request,limits,writer)?',
        'if !selected.contains_key(&node.source_control_id)','context.readback(&forms,&fields)',
        'NativeNumberFormatReplacement::Preserve','native_recalculation_full_search_service_or_execution_authority:false'):
        c.require(marker in code,'WHOLE_SCOPE_ONE_GUARD_PREFIX_FIELD_PROTECTION_COMPLETE_ORIGINAL_STREAM_AND_NO_NEW_AUTHORITY')


def expected(q):
    result=source.expected(q);names=re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(TEST))
    c.require(len(names)==len(set(names))==20,'EXACT20_NEW_NUMBER_CONTROL_SOURCE_IDENTITIES');result.update('numbers::'+n for n in names);return result


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'NUMBER_CONTROL_SOURCE_IMMUTABLE_RUN_EXISTS');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_NUMBER_CONTROL_SOURCE_COMPONENTS',steps=[],own_cpu_selection=selection,actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False,number_control_store_product_native_or_gate_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        baseline=q.json(prior.OUTPUT)
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='f12fe3c49d3dc91f50d65ad106954cdd7ba648817ecf57a43ac01ef4c7fbad81'
            and baseline['state']=='PASS_CONTROL_TWENTY_FOUR_PRODUCTS_NOT_OTHER_KINDS_TRANSACTION_NATIVE_OR_GATE'and baseline['cleanup']
            and baseline['fresh_inputs']==baseline['final_fresh_hashes']==716 and baseline['new_product_cases']==24,'EXACT194_CONTROL_PRODUCT24_BASELINE')
        old={p['path']:p for p in baseline['source_pins']};c.require(NEW.isdisjoint(old),'NEW_NUMBER_CONTROL_SOURCE_FILES_ADDITIVE')
        for name in names-NEW-CHANGED:c.require(q.snapshots[name]==old[name],'ALL_OTHER_STREAM_COMPILER_ID_PROFILES_READBACK_PATCHES_PRODUCTS_TESTS_AND_FIXTURES_UNCHANGED')
        inverse(q,old);cases=expected(q)
        print(json.dumps(dict(state='NUMBER_CONTROL_SOURCE_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),new_source_cases=20,affected_cases=36,one_cpu_mask=4)),flush=True)
        harness.run_one('twenty_number_control_source_and_thirty_six_affected_control_cases',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package',
            '--test','control_replacement_focused','--message-format=short','--','--test-threads=1'],cases,guard,audit.environment(),row,observe_capture=snapshot)
        tools.good_step(row['steps'][0],cases);c.require(inventory(guard.check)==names,'FINAL_NUMBER_CONTROL_SOURCE_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_NUMBER_CONTROL_SOURCE20_AFFECTED36_NOT_STORE_PRODUCT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_source_cases=20,affected_control_cases=36,total_executed_cases=56,old266_products_and_official249_reexecuted=False,
            original_matcher_geometry_stream_compiler_and_old_test_bodies_inverse_verified=True,one_scope_geometry_and_part_guard_prefix_before_noop=True,
            complete_original_number_stream_preserved=True,next_work='SEARCH009_number_control_current_store_strict_product_other_families_full_contract_native_and_gates')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'NUMBER_CONTROL_SOURCE_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_NUMBER_CONTROL_SOURCE_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations','safe_error_variants')},
                'observation':{k:s.get('bounded_output_observation',{}).get(k)for k in('safe_warning_locations','short_error_locations','rust_error_codes')},
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
