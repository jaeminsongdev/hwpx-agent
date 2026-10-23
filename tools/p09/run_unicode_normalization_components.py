"""Actual source normalization; new24 and only shared readback/selector affected originals."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_control_style_context_recovery as prior
from run_regex_replacement_focused import select_own_single_cpu
from run_style_replacement_sync import good_step
harness,shared,c,a,audit,snapshot=prior.harness,prior.shared,prior.c,prior.a,prior.audit,prior.snapshot
OUTPUT='implementation/p09/evidence/p09-361-unicode-normalization-components157.v1.json'
ROOT='crates/hwpx-package/src/document_import/search/'
ATOMS=ROOT+'replacement/atoms.rs';SELECTOR=ROOT+'reviews/selector.rs';READBACK=ROOT+'replacement/atoms/readback.rs'
TEXT=ROOT+'replacement/atoms/styles/text.rs';WRITER=ROOT+'replacement/atoms/styles/text/output.rs'
CORE=ROOT+'replacement/atoms/unicode.rs';PLAN=ROOT+'replacement/atoms/unicode/plan.rs';TRANSFORM=ROOT+'replacement/atoms/unicode/transform.rs'
TEST='crates/hwpx-package/tests/document_import_unicode_normalization.rs';BUNDLE='crates/hwpx-package/tests/unicode_normalization_focused.rs'
NEW={CORE,PLAN,TRANSFORM,TEST,BUNDLE};CHANGED={ATOMS,SELECTOR,READBACK,TEXT,WRITER}
WINDOW_HELPER='''    /// Move the original exact windows; transformations must not reconstruct or widen a selection.
    pub(in crate::document_import::search) fn transformation_windows(&self,selector:SourceIndexScopeSelector<'_>,policy:SourceReviewTextPolicy)
        ->Result<(SourceIndexScopeReceipt,BTreeMap<usize,(usize,usize)>,usize,usize),E> {
        let selected=self.resolve_windows(selector,policy)?;
        Ok((selected.scope,selected.windows,selected.hidden,selected.memo))
    }
'''
READBACK_HELPER='''    let output_review=verify_artifact(source,&artifact,plans,review)?;Ok((artifact,output_review))
}

/// The same complete value/outside-slot verifier for an explicitly selected preserving writer profile.
pub(super) fn verify_artifact(source:&ImportedSourcePackage,artifact:&PackageArtifact,plans:&BTreeMap<&PackagePath,Vec<PlannedSpan>>,
    review:Option<&review::ReviewWriteContext>)->Result<Option<review::ReviewBodyImportReceipt>,E> {
    artifact.with_verified_bytes(|bytes|->Result<Option<review::ReviewBodyImportReceipt>,E>{
'''


def inventory(check):return prior.base.inventory(check)|NEW


def inverse(q,old):
    # Local count checks avoid depending on a historical helper-chain implementation.
    def restore(text,new,previous):
        c.require(text.count(new)==1,'EXACT_ONE_NORMALIZATION_DECLARED_COMMON_CHANGE');return text.replace(new,previous)
    for name,new,previous in[(ATOMS,'pub mod unicode;\n',''),(SELECTOR,WINDOW_HELPER,''),
        (TEXT,'pub(in crate::document_import::search::replacement::atoms) mod output;','pub(super) mod output;'),
        (WRITER,'pub(in crate::document_import::search::replacement::atoms) fn build<T>','pub(in crate::document_import::search::replacement::atoms::styles) fn build<T>')]:
        audit.inverse(restore(q.text(name),new,previous),old[name],'EXACT_ORIGINAL_BODY_OUTSIDE_DECLARED_ADDITIONS_OR_VISIBILITY')
    text=restore(q.text(READBACK),READBACK_HELPER,'    let output_review=artifact.with_verified_bytes(|bytes|->Result<Option<review::ReviewBodyImportReceipt>,E>{\n')
    text=restore(text,'    }).map_err(|_|E::Writer)?\n','    }).map_err(|_|E::Writer)??;Ok((artifact,output_review))\n')
    audit.inverse(text,old[READBACK],'ENTIRE_ORIGINAL_READBACK_BODY_EXACTLY_RECONSTRUCTED_WITHOUT_WEAKENING')
    text=q.text(CORE)
    for marker in('ImportedDocumentFields::import(original)','ImportedDocumentReviewBodies::import_bound_fields(original,&fields)',
        'SourceReviewScopeIndex::from_review(original,&review,limits)','index.transformation_windows(selector,policy)',
        'styles::text::output::build(','readback::verify_artifact('):
        c.require(text.count(marker)==1,'ONE_PROOF_FIELDS_REVIEW_INDEX_WINDOW_WRITER_AND_OUTPUT_READBACK')


def expected(q):
    groups=[('unicode',TEST,24),('atom_literal','crates/hwpx-package/tests/document_import_search_atom_replacement.rs',12),
        ('review_literal','crates/hwpx-package/tests/document_import_search_review_replacement.rs',12),
        ('selector_literal','crates/hwpx-package/tests/document_import_review_selector_replacement.rs',8),
        ('regex_replacement','crates/hwpx-package/tests/document_import_regex_replacement.rs',17),
        ('review_selector','crates/hwpx-package/tests/document_import_review_selector.rs',8)]
    result=set()
    for module,name,count in groups:
        names=re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(name));c.require(len(names)==len(set(names))==count,'EXACT_NORMALIZATION_AND_AFFECTED_CASE_IDENTITIES')
        result.update(module+'::'+n for n in names)
    return result


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'UNICODE_NORMALIZATION_IMMUTABLE_RUN_EXISTS');selection=select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_UNICODE_NORMALIZATION_COMPONENTS',steps=[],own_cpu_selection=selection,actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False,full_search022_product_contract_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        baseline=q.json(prior.OUTPUT)
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='bc2c563a3074e79bd4d6f7630f99ca5491b2247fbe997ea26ac2cbd66c6fd622'
            and baseline['state']=='PASS_CONTROL_CONTEXT_2_REPAIRED_24_RETAINED_26_PRODUCTS_NOT_CASCADE_NATIVE_OR_GATE'
            and baseline['fresh_inputs']==baseline['final_fresh_hashes']==645 and baseline['cleanup'],'EXACT_PRIOR_CONTROL_CONTEXT_RECOVERY_RETAINED')
        old={p['path']:p for p in baseline['source_pins']}
        c.require(NEW.isdisjoint(old),'NEW_NORMALIZATION_FILES_NOT_OVERWRITING_PRIOR_SOURCE')
        for name in names-NEW-CHANGED:c.require(q.snapshots[name]==old[name],'ALL_OTHER_PRODUCT_PROTECTION_MATCHER_WRITER_FIXTURE_AND_TEST_INPUTS_EXACTLY_UNCHANGED')
        inverse(q,old);cases=expected(q)
        print(json.dumps(dict(state='UNICODE_NORMALIZATION_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),new_cases=24,affected_original_cases=57,one_cpu_mask=4)),flush=True)
        harness.run_one('twenty_four_normalization_and_fifty_seven_shared_readback_selector_cases',
            [harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package','--test','unicode_normalization_focused','--message-format=short','--','--test-threads=1'],
            cases,guard,audit.environment(),row,observe_capture=snapshot)
        good_step(row['steps'][0],cases);c.require(inventory(guard.check)==names,'FINAL_NORMALIZATION_SOURCE_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_UNICODE_NORMALIZATION_24_NEW_57_AFFECTED_NOT_STORED_PRODUCT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_source_cases=24,affected_source_cases=57,total_executed_cases=81,original_common_code_and_test_bodies_inverse_verified=True,
            explicit_four_forms_and_minimal_original_components=True,original_nfc_index_unchanged=True,
            next_work='Current_stored_service_strict_product_request_and_full_SEARCH022_contract_binding')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'UNICODE_NORMALIZATION_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_NORMALIZATION_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations','safe_error_variants')},
                'observation':{k:s.get('bounded_output_observation',{}).get(k)for k in('safe_warning_locations','short_error_locations','rust_error_codes')},
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
