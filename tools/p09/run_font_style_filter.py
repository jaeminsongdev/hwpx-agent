"""331: explicit original style-filter core, NFC provenance and affected v1 paths only."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_font_tracking_recovery as previous
import run_sql23_storage as closure
shared,c,a,tools,compact,harness,audit=previous.shared,previous.c,previous.a,previous.tools,previous.compact,previous.harness,previous.audit
OUTPUT='implementation/p09/evidence/p09-361-font-style-filter331.v1.json';DRIVER='tools/p09/run_font_style_filter.py'
CORE=previous.CORE;FILTER=CORE[:-3]+'/filtered.rs';PARENT='crates/hwpx-package/tests/document_import_scoped_fonts.rs';TEST='crates/hwpx-package/tests/support/scoped_font_filter.rs'
LINK='#[path="support/scoped_font_filter.rs"]mod filtered;\n'
WRAPPER='''        self.lower_scoped_font_candidate_checked(original,query,selector,policy,axis,None,limits,writer).map(|(candidate,_)|candidate)
    }
    fn lower_scoped_font_candidate_checked(&self,original:&ImportedDocumentForms,query:FontNameReplacementQuery<'_>,selector:SourceIndexScopeSelector<'_>,
        policy:SourceReviewTextPolicy,axis:SourceFontStyleAxis,filter:Option<crate::document_import::search::reviews::selector::styles::SourceReviewStyleFilter>,
        limits:SourceSearchLimits,writer:WriterLimits)->Result<(SourceFontReplacementCandidate,Option<filtered::SourceFontFilterReceipt>),F>{
'''
BEFORE='''        let before=verify::values(index)?;let mut origins=BTreeSet::new();
        for(&block,&(a,b))in &windows {for unit in index.blocks.get(block).and_then(|block|block.units.get(a..b)).ok_or(E::Selection)?{
            origins.extend(unit.origins.iter().copied());}}
'''
AFTER='''        let before=verify::values(index)?;
        let(origins,filter_receipt)=if let Some(filter)=filter{let(origins,receipt)=filtered::select(index,&windows,filter)?;(origins,Some(receipt))}
        else{let mut origins=BTreeSet::new();
            for(&block,&(a,b))in &windows {for unit in index.blocks.get(block).and_then(|block|block.units.get(a..b)).ok_or(E::Selection)?{
                origins.extend(unit.origins.iter().copied());}}(origins,None)};
'''
AFFECTED={'partial_run_clones_shared_property_and_preserves_nonselected_scalars_and_entities',
    'explicit_text_style_splits_text_without_changing_run_or_unselected_text_axis',
    'selected_nfc_scalar_keeps_all_original_hangul_contributors_and_outside_spelling',
    'controls_retain_original_bytes_and_are_not_counted_as_changed_text',
    'finite_scalar_and_writer_limits_never_return_partial_candidates',
    'a_verified_reconstruction_cannot_be_rebound_to_another_import_instance'}

def inverse(q,old):
    text=q.text(CORE)
    for marker in ('pub mod filtered;\n',WRAPPER,AFTER,'        Ok((SourceFontReplacementCandidate{artifact,receipt,edit_inventory},filter_receipt))\n'):
        c.require(text.count(marker)==1,'ONE_EXPLICIT_CORE_FILTER_ADDITION')
    text=text.replace('pub mod filtered;\n','').replace(WRAPPER,'').replace(AFTER,BEFORE).replace(
        '        Ok((SourceFontReplacementCandidate{artifact,receipt,edit_inventory},filter_receipt))\n','        Ok(SourceFontReplacementCandidate{artifact,receipt,edit_inventory})\n')
    audit.inverse(text,old[CORE],'ORIGINAL_V1_QUERY_SCOPE_PROTECTION_MATCHER_CLONE_RENDER_WRITER_READBACK_RECEIPT_UNCHANGED')
    text=q.text(PARENT);c.require(text.count(LINK)==1,'ONE_FILTER_TEST_MODULE_LINK');audit.inverse(text.replace(LINK,''),old[PARENT],'ALL_ORIGINAL20_SOURCE_TESTS_UNCHANGED')

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'FONT_STYLE_FILTER_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_FONT_STYLE_FILTER',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        Native011_executed=False,prior_Native_replayed=False,actual_DB_or_Hangul_or_COM_started=False,official249_replayed=False,
        output_ingest_commit_or_publication=False,full_SEARCH024_product_or_native_qualified=False,filtered_stored_product_or_preview_implemented=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=compact.unpack(q.json(previous.OUTPUT))
        c.require(q.snapshots[previous.OUTPUT]['sha256']=='dacb11c37cd9280830b6b78c89092ec9ddf65f0290e3afea0d462019461fadf5'and passed['cleanup']
            and passed['fresh_inputs']==passed['final_fresh_hashes']==765 and passed['state'].startswith('PASS_'),'EXACT329_TRACKING_BASELINE')
        old={p['path']:p for p in passed['source_pins']};new={FILTER,TEST,DRIVER};names=closure.inventory(guard.check)|set(old)|new
        for n in sorted(names):
            q.pin(n)
            if n in old and n not in {CORE,PARENT}:c.require(q.snapshots[n]==old[n],'ALL_OTHER_PRODUCTION_TEST_AND_VERIFIER_INPUTS_UNCHANGED')
            elif n not in old:c.require(n in new,'ONLY_DECLARED_STYLE_FILTER_SOURCE_TEST_AND_DRIVER_ADDED')
        inverse(q,old)
        for module in tuple(sys.modules.values()):
            f=getattr(module,'__file__',None)
            if f:
                p=Path(f).absolute()
                if p.is_relative_to(c.ROOT/'tools/p09')and p.suffix=='.py':q.pin(p.relative_to(c.ROOT).as_posix())
        cases={'filtered::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(TEST))}|{'scoped::'+n for n in AFFECTED}
        c.require(len(cases)==24 and len(AFFECTED)==6,'EXACT_NEW18_AFFECTED6_SOURCE_CASES')
        scratch=c.ROOT/'target/p09-font-style-filter-scratch-331';c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'FONT_STYLE_FILTER_NEW_TEMP')
        scratch.mkdir();env=audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch))
        print(json.dumps(dict(state='FONT_STYLE_FILTER_PREFLIGHT',inputs=len(q.snapshots),new_cases=18,affected_cases=6,official249_replayed=False)),flush=True)
        harness.run_one('font_style_filter18_affected_v1_source6',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package','--test','document_import_scoped_fonts',
            '--message-format=short','--',*sorted(cases),'--test-threads=1'],cases,guard,env,row,observe_capture=previous.previous.snapshot)
        tools.good_step(row['steps'][-1],cases);c.require(not any(scratch.iterdir()),'FONT_STYLE_FILTER_TEMP_EMPTY');q.finish();guard.check(force=True)
        row.update(state='PASS_FONT_STYLE_FILTER_CORE18_AFFECTED_V1_SOURCE6_NOT_STORED_PRODUCT_PREVIEW_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_cases=18,affected_cases=6,filter_definition_resolved_once_per_index=True,filter_predicate_cached_once_per_source_segment=True,
            v1_receipt_schema_and_original_test_bodies_unchanged=True,next_work='stored_filtered_font_and_strict_product_preview_request')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'FONT_STYLE_FILTER_FAILURE_NO_RAW_VALUES')
        if q is not None:
            try:q.finish();row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
            except(ValueError,OSError,KeyError,TypeError,AttributeError):row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'FONT_STYLE_FILTER_LOSSLESS_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','safe_error_variants','panic_locations','bounded_output_observation','cleanup')},'case_count':len(s.get('tests',[])),'failed_cases':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
