"""Twelve exact control-anchor cases and47 affected core cases, one owned resource-bounded binary."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_selector_style_product_components as prior
from run_stored_review_literal_focused import snapshot
from run_literal_text_atom_product_components import CAPTURE
harness,shared,c,a,audit=prior.harness,prior.shared,prior.c,prior.a,prior.audit
OUTPUT='implementation/p09/evidence/p09-361-selector-controls-components107.v1.json'
CORE='crates/hwpx-package/src/document_import/search/selector.rs'
GEOMETRY=CORE[:-3]+'/control_geometry.rs'
REVIEW='crates/hwpx-package/src/document_import/search/reviews/selector.rs'
CONTROL=REVIEW[:-3]+'/controls.rs'
INSPECT='crates/hwpx-package/src/document_import/search/inspection.rs'
NAV='crates/hwpx-package/src/document_import/search/navigation.rs'
TEST='crates/hwpx-package/tests/document_import_selector_controls.rs'
BUNDLE='crates/hwpx-package/tests/selector_controls_bundle.rs'
NEW={GEOMETRY,CONTROL,TEST,BUNDLE};CHANGED={CORE,REVIEW,INSPECT,NAV}
WRAPPER=('        self.resolve_index_selector_with_geometry(selector,supplemental,None)\n    }\n'
    '    pub(in crate::document_import::search) fn resolve_index_selector_with_geometry(&self,selector:SourceIndexScopeSelector<\'_>,supplemental:Option<&SupplementalNodes>,mut geometry:Option<&mut control_geometry::ControlGeometry>)->Result<(SourceIndexScopeReceipt,Windows),E> {\n')
CAPTURES=(
    '                if let Some(g)=geometry.as_deref_mut(){*g=control_geometry::ControlGeometry::Parts(parts.iter().map(|p|p.as_str().to_owned()).collect());}\n',
    '                if let Some(g)=geometry.as_deref_mut(){*g=control_geometry::ControlGeometry::Nodes(selected.iter().map(|(p,r)|(p.to_string(),r.clone())).collect());}\n',
    '                if let Some(g)=geometry.as_deref_mut(){*g=control_geometry::ControlGeometry::selection(self,start,end)?;}\n')


def inventory(check):return prior.inventory(check)|{TEST,BUNDLE}


def inverse(q,old):
    text=q.text(CORE)
    for addition in('pub(in crate::document_import::search) mod control_geometry;\n',WRAPPER,*CAPTURES):
        c.require(text.count(addition)==1,'ONLY_OPTIONAL_ORIGINAL_SCOPE_GEOMETRY_CAPTURE');text=text.replace(addition,'')
    audit.inverse(text,old[CORE],'WHOLE_ORIGINAL_TEXT_SCOPE_WINDOWS_ID_VALIDATION_HASH_AND_LIMITS_EXACT_INVERSE')
    for name,addition in((REVIEW,'pub mod controls;\n'),(INSPECT,'    pub(in crate::document_import::search) fn observed_controls(&self)->&[SourceControlMatch] {&self.controls}\n')):
        text=q.text(name);c.require(text.count(addition)==1,'ONE_ADDITIVE_TYPED_CONTROL_MODULE_OR_PRIVATE_INVENTORY_ACCESSOR')
        audit.inverse(text.replace(addition,''),old[name],'WHOLE_ORIGINAL_REVIEW_STYLE_CONTROL_INVENTORY_MATCHER_AND_LEGACY_SCOPE_UNCHANGED')
    text=q.text(NAV)
    replacements=(
        (",ControlRegions(&'a [SourceControlMatch],&'a [SourceTextRegion])",''),
        ('Self::Control(m)|Self::ControlRegions(m,_)','Self::Control(m)'),
        (',\n        Self::ControlRegions(m,r)=>hash(&("control_with_region",m.get(index).ok_or(E::Cursor)?,r.get(index).ok_or(E::Mapping)?),maximum)',''),
        ('Self::Text(_,Some(r))|Self::ControlRegions(_,r)','Self::Text(_,Some(r))'),
        ('    if let Occurrences::ControlRegions(m,r)=&matches {if m.len()!=r.len(){return Err(E::Mapping);}}\n',''))
    for current,previous in replacements:
        c.require(text.count(current)==(2 if current=='Self::Control(m)|Self::ControlRegions(m,_)'else 1),'ONLY_ADDITIVE_CONTROL_REGION_ENUM_ARMS')
        text=text.replace(current,previous)
    audit.inverse(text,old[NAV],'WHOLE_ORIGINAL_TEXT_AND_CONTROL_NAVIGATION_CURSOR_AND_FINAL_OUTPUT_BOUND_UNCHANGED')


def expected(q):
    paths=('document_import_selector_controls','document_import_search_selector','document_import_review_selector','document_import_selector_styles','document_import_search_inspection','document_import_search_navigation')
    modules=('selector_controls','text_selector','review_selector','selector_styles','inspection','navigation')
    groups=[{module+'::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text('crates/hwpx-package/tests/'+name+'.rs'))}for name,module in zip(paths,modules,strict=True)]
    c.require(tuple(map(len,groups))==(12,12,8,8,9,10),'EXACT_TWELVE_NEW_FORTY_SEVEN_AFFECTED_CORE_IDENTITIES')
    return set().union(*groups)


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SELECTOR_CONTROLS_IMMUTABLE_RUN_EXISTS');shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SELECTOR_CONTROLS_COMPONENTS',steps=[],actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False,stored_product_or_native_qualification_added=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        previous=q.json(prior.OUTPUT)
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='c19fabf88bccd64796e973d48d1eaff7e6ca69d0cdb0a6dc7622f8576271527d'
            and previous['state'].startswith('PASS_')and previous['total_executed_cases']==45 and previous['cleanup'],'EXACT_PREVIOUS_FORTY_FIVE_V7_PRODUCT_PASSES_RETAINED')
        old={p['path']:p for p in previous['source_pins']};old_names={n for n in old if n.startswith(('crates/','fixtures/'))or n in{'Cargo.toml','Cargo.lock','rust-toolchain.toml',CAPTURE}}
        c.require(names==old_names|NEW,'EXACT_TWO_NEW_CONTROL_MODULES_AND_TWO_FOCUSED_TEST_FILES')
        for name in names-NEW-CHANGED:c.require(q.snapshots[name]==old[name],'NO_UNRELATED_WRITER_AUTH_CRYPTO_PRODUCT_FIXTURE_OR_OLD_TEST_INPUT_CHANGE')
        inverse(q,old);cases=expected(q)
        print(json.dumps(dict(state='SELECTOR_CONTROLS_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),new_cases=12,affected_cases=47,test_binaries=1)),flush=True)
        harness.run_one('twelve_exact_control_and_forty_seven_affected_core_cases',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package',
            '--test','selector_controls_bundle','--','--test-threads=1'],cases,guard,audit.environment(),row,observe_capture=snapshot)
        c.require(inventory(guard.check)==names,'FINAL_SELECTOR_CONTROL_SOURCE_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_SELECTOR_CONTROLS_TWELVE_NEW_FORTY_SEVEN_AFFECTED_NOT_STORED_PRODUCT_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,new_core_cases=12,affected_cases=47,total_executed_cases=59,
            previous_forty_five_v7_products_and_unaffected_suites_reexecuted=False,original_scope_text_style_inspection_and_navigation_inverse_verified=True,
            actual_control_start_not_parent_paragraph_membership=True,source_nfc_reordering_ambiguity_rejected=True,
            policy_and_scope_exclusions_before_control_match_cap=True,control_regions_and_source_order_cursor_bound=True,
            next_work='Current_stored_service_and_strict_product_binding_of_exact_review_selector_controls_then_full_search_contract')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'SELECTOR_CONTROLS_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_SELECTOR_CONTROLS_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','diagnostics','locations','summaries','tests','panic_locations','safe_error_variants')}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
