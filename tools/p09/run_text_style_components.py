"""16 new text-style source cases only, unchanged run-style bodies and original guards."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_style_product_components as prior
harness,shared,c,a,audit,snapshot=prior.harness,prior.shared,prior.c,prior.a,prior.audit,prior.snapshot
OUTPUT='implementation/p09/evidence/p09-361-text-style-components131.v1.json'
STYLE='crates/hwpx-package/src/document_import/search/replacement/atoms/styles.rs'
RENDER=STYLE[:-3]+'/render.rs';VERIFY=STYLE[:-3]+'/verify.rs'
TEXT=STYLE[:-3]+'/text.rs';TEXT_RENDER=TEXT[:-3]+'/render.rs';TEST='crates/hwpx-package/tests/text_style_replacement.rs'
NEW={TEXT,TEXT_RENDER,TEST};CHANGED={STYLE,RENDER,VERIFY}


def inventory(check):return prior.inventory(check)|NEW


def inverse(q,old):
    text=q.text(STYLE);c.require(text.count('pub mod text;\n')==1,'ONE_ADDITIVE_EXPLICIT_TEXT_STYLE_MODULE')
    audit.inverse(text.replace('pub mod text;\n',''),old[STYLE],'WHOLE_QUALIFIED_RUN_STYLE_COMPILER_BODY_UNCHANGED')
    text=q.text(RENDER);marker='pub(super) fn namespaces('
    c.require(text.count(marker)==1,'ONLY_NAMESPACE_HELPER_VISIBILITY_FOR_SOURCE_TEXT_FRAGMENTS')
    audit.inverse(text.replace(marker,'fn namespaces('),old[RENDER],'WHOLE_QUALIFIED_RUN_STYLE_RENDERER_UNCHANGED')
    text=q.text(VERIFY)
    for original,replacement in[
        ('pub(super) enum Scalar','enum Scalar'),
        ('pub(super) struct PointValue {pub(super) scalar:Scalar,pub(super) run:Option<u32>,pub(super) text:Option<u32>}',
         'struct PointValue {scalar:Scalar,run:Option<u32>,text:Option<u32>}'),
        ('pub(super) fn values(','fn values(')]:
        c.require(text.count(original)==1,'ONLY_EXISTING_SCALAR_READBACK_HELPER_VISIBILITY');text=text.replace(original,replacement)
    audit.inverse(text,old[VERIFY],'WHOLE_QUALIFIED_RUN_STYLE_READBACK_BODY_UNCHANGED')
    core=q.text(TEXT)
    for marker in('ImportedDocumentFields::import(original)','ImportedDocumentReviewBodies::import_bound_fields(original,&fields)',
        'SourceReviewScopeIndex::from_review(original,&review,limits)','find_style_for_character_replacement(query,selector,policy,filter,text_character_style)',
        'output::build_artifact(','let output=ImportedSourcePackage::import('):
        c.require(core.count(marker)==1,'ONE_PROOF_FIELD_REVIEW_INDEX_MATCH_WRITER_AND_OUTPUT_IMPORT')
    c.require('super::verify::values(index)'in core and 'super::render::reference(&xml.elements()[text],"charStyleIDRef")'in core
        and 'before.run!=after.run'in core and 'context.readback_receipt(review.receipt())'in core,
        'ORIGINAL_SCALAR_READER_AND_ORIGINAL_RUN_REFERENCES_WITH_ONE_REVIEW_READBACK')


def expected(q):
    names=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(TEST)))
    c.require(len(names)==16,'EXACT_SIXTEEN_NEW_TEXT_STYLE_CASE_IDENTITIES');return names


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'TEXT_STYLE_IMMUTABLE_RUN_EXISTS');selection=prior.base.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_TEXT_STYLE_COMPONENTS',steps=[],actual_Hangul_or_COM=False,own_cpu_selection=selection,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        stored_or_product_text_style_qualification_added=False,output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        previous=q.json(prior.OUTPUT)
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='bfcece3d80b9a8cf588ca019744537554c51328f401d165c95f30bb8ce8d5c56'
            and previous['state'].startswith('PASS_')and previous['cleanup']and previous['total_executed_cases']==18
            and previous['fresh_inputs']==previous['final_fresh_hashes']==608,'EXACT_QUALIFIED_RUN_STYLE_SOURCE_AND_PRODUCT_BASELINE')
        old={p['path']:p for p in previous['source_pins']};old_names={n for n in old if n.startswith(('crates/','fixtures/'))or n in{'Cargo.toml','Cargo.lock','rust-toolchain.toml',prior.base.CAPTURE}}
        c.require(names==old_names|NEW,'EXACT_TWO_SOURCE_FILES_AND_SIXTEEN_CASE_TEXT_STYLE_TARGET_ADDED')
        for name in names-NEW-CHANGED:c.require(q.snapshots[name]==old[name],'NO_MATCHER_PROTECTION_PATCH_STORED_PRODUCT_OR_ORIGINAL_CASE_CHANGE')
        inverse(q,old);cases=expected(q)
        print(json.dumps(dict(state='TEXT_STYLE_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),new_cases=16,old_cases_reexecuted=False,one_cpu_mask=4)),flush=True)
        harness.run_one('sixteen_new_text_style_source_cases_only',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package',
            '--test','text_style_replacement','--message-format=short','--',*sorted(cases),'--exact','--test-threads=1'],cases,guard,audit.environment(),row,observe_capture=snapshot)
        limits=row['steps'][0]['owned_job']['limits_readback']
        c.require(limits['verified']and limits['affinity_mask']==4 and limits['cpu_hard_cap_machine_percent']==6.25 and limits['priority_class']==16384,
            'ORIGINAL_ONE_CPU2_HARD_CAP_AND_BELOW_NORMAL_PRIORITY')
        c.require(inventory(guard.check)==names,'FINAL_TEXT_STYLE_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_TEXT_STYLE_SIXTEEN_SOURCE_COMPONENTS_NOT_STORED_PRODUCT_EFFECTIVE_STYLE_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_text_style_cases=16,total_executed_cases=16,previous_original_and_style_cases_reexecuted=False,original_run_style_bodies_inverse_verified=True,
            next_work='Current_stored_and_strict_product_binding_for_text_style_then_paragraph_named_style_effective_style_full_contract')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'TEXT_STYLE_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_TEXT_STYLE_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations','safe_error_variants')},
                'warnings':s.get('bounded_output_observation',{}).get('safe_warning_locations',[]),'short_errors':s.get('bounded_output_observation',{}).get('short_error_locations',[]),
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
