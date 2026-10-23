"""Explicit v2 source literal compiler: twelve new cases and ten affected original v1 cases."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_text_atom_patch_recovery as prior
harness,shared,c,a=prior.harness,prior.shared,prior.c,prior.a
OUTPUT='implementation/p09/evidence/p09-361-literal-text-atom-components075.v1.json'
PRIOR=prior.OUTPUT
TEST='crates/hwpx-package/tests/document_import_search_atom_replacement.rs'
LOWER=prior.base.prior.LOWER
OUTPUT_MODULE='crates/hwpx-package/src/document_import/search/replacement/output.rs'
NEW={TEST,'crates/hwpx-package/src/document_import/search/replacement/atoms.rs',
    'crates/hwpx-package/src/document_import/search/replacement/atoms/readback.rs'}
CHANGED={LOWER,OUTPUT_MODULE}
ORIGINS=('        if m.zero_width||!m.source_scalar_selection_exact{return Err(E::Selection);}\n'
    '        let block=index.blocks.get(m.block_index).ok_or(E::Selection)?;let mut origins=BTreeSet::new();\n'
    '        for unit in block.units.get(m.start_normalized_scalar..m.end_normalized_scalar).ok_or(E::Selection)? {origins.extend(unit.origins.iter().copied());}\n'
    '        let first=*origins.first().ok_or(E::Selection)?;let last=*origins.last().ok_or(E::Selection)?;\n'
    '        if last-first+1!=origins.len(){return Err(E::Selection);}\n')
ORIGINS_HELPER=("fn selected_origins(index:&SourceTextIndex<'_>,m:&super::SourceSearchMatch)->Result<BTreeSet<usize>,E> {\n"+ORIGINS+'    Ok(origins)\n}\n')
WRITER=('    let zip=source.limits.zip().map_err(|_|E::Source)?;let mut reader=BoundedZipReader::open(Cursor::new(fresh),zip).map_err(|_|E::Source)?;\n'
    '    let patch=PreservingPatchEngine::apply_with_limits_and_preservation_profile(&mut reader,&source.graph,PackageGraphLimits::default(),\n'
    '        IdRuleProfile::hwpml_2011_shape_v6(),IdIndexLimits::default(),PatchLimits::default(),PreservationRuleProfile::Hangul2020PreviewTextV2,intents)\n'
    '        .map_err(|e|E::Patch(e.code()))?;\n'
    '    if patch.changed_parts()!=plans.len()||patch.added_parts()!=0||patch.parts().iter().any(|p|!plans.contains_key(p.path())&&p.source_sha256()!=Some(p.output_sha256())){return Err(E::Preservation);}\n'
    '    let artifact=PreservingWriter::build(&patch,zip,PackageGraphLimits::default(),IdIndexLimits::default(),writer).map_err(|_|E::Writer)?;\n')
WRITER_HELPER=('pub(super) fn build_artifact<T>(source:&ImportedSourcePackage,fresh:&[u8],intents:&[PatchIntent],plans:&BTreeMap<&PackagePath,T>,writer:WriterLimits)->Result<PackageArtifact,E> {\n'
    +WRITER+'    Ok(artifact)\n}\n')


def inventory(check):return prior.base.inventory(check)|{TEST}


def inverse(q,old):
    text=q.text(LOWER)
    for current,original in (('pub mod atoms;\n',''),(ORIGINS_HELPER,''),('        let origins=selected_origins(index,m)?;\n',ORIGINS)):
        c.require(text.count(current)==1,'ONLY_ADDITIVE_ATOM_MODULE_AND_ORIGINAL_NFC_SELECTION_HELPER_EXTRACTION');text=text.replace(current,original)
    prior.base.prior.prior.base.inverse(text,old[LOWER],'ORIGINAL_V1_LITERAL_COMPILER_PROVENANCE_GUARDS_AND_RECEIPT_EXACT_INVERSE')
    text=q.text(OUTPUT_MODULE)
    for current,original in ((WRITER_HELPER,''),('    let artifact=build_artifact(source,fresh,intents,plans,writer)?;\n',WRITER)):
        c.require(text.count(current)==1,'ONLY_ORIGINAL_PATCH_WRITER_PREFIX_EXTRACTION');text=text.replace(current,original)
    prior.base.prior.prior.base.inverse(text,old[OUTPUT_MODULE],'ORIGINAL_V1_WRITER_ID_PRESERVATION_AND_READBACK_BODY_EXACT_INVERSE')


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'LITERAL_ATOM_IMMUTABLE_RUN_EXISTS');shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_LITERAL_TEXT_ATOM_COMPONENTS',steps=[],actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False,full_literal_search_product_or_native_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        previous=q.json(PRIOR);c.require(q.snapshots[PRIOR]['sha256']=='46f5b0cbf46024e650f046370b6569e1b20bee686e3e12ad7299a24d89bdbb84'
            and previous['state'].startswith('PASS_')and previous['cleanup'],'EXACT_PRIOR_TEXT_ATOM_PATCH_PASS')
        old={p['path']:p for p in previous['source_pins']};old_names={n for n in old if n.startswith(('crates/','fixtures/'))or n in {'Cargo.toml','Cargo.lock','rust-toolchain.toml',prior.base.prior.prior.scalar.CAPTURE}}
        c.require(names==old_names|NEW,'EXACT_THREE_NEW_LITERAL_ATOM_COMPILER_READBACK_AND_TEST_FILES')
        for name in names-NEW-CHANGED:c.require(q.snapshots[name]==old[name],'NO_OTHER_SOURCE_SCALAR_READER_SERVICE_PRODUCT_OR_TEST_CHANGE')
        inverse(q,old)
        new=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(TEST)))
        original=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(prior.base.prior.prior.TEST)))
        c.require(len(new)==12 and len(original)==10,'EXACT_TWELVE_NEW_AND_TEN_AFFECTED_V1_LITERAL_TESTS')
        env=prior.base.prior.prior.base.environment();common=[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package']
        print(json.dumps(dict(state='LITERAL_ATOM_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),new_cases=12,affected_cases=10,original_guards_and_writer_preserved=True)),flush=True)
        harness.run_one('twelve_v2_source_literal_atom_candidate_cases',common+['--test','document_import_search_atom_replacement','--','--test-threads=1'],new,guard,env,row)
        harness.run_one('ten_affected_original_v1_literal_candidate_cases',common+['--test','document_import_search_replacement','--','--test-threads=1'],original,guard,env,row)
        c.require(inventory(guard.check)==names,'FINAL_LITERAL_ATOM_INPUT_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_LITERAL_TEXT_ATOM_V2_TWELVE_NEW_TEN_AFFECTED_NOT_STORED_PRODUCT_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,new_cases=12,affected_cases=10,total_executed_cases=22,
            original_v1_compiler_guards_patch_writer_and_readback_inverse_verified=True,original_control_and_outside_selected_atom_bytes_verified=True,
            source_bound_nfc_contiguous_selection_and_original_run_policy_verified=True,field_cache_and_control_atom_edits_unqualified=True,
            whole_output_reimport_per_candidate=1,per_match_source_reimport_added=False,source_protection_map_shared_per_part=True,
            old_stored_product_and_scalar_cases_reexecuted=False,stored_service_or_product_json_route_added=False,
            next_work='Bind_v2_text_atom_candidate_to_current_stored_scope_head_and_output_delivery')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'LITERAL_ATOM_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_LITERAL_ATOM_RESOURCE_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','diagnostics','locations','summaries','tests','panic_locations','safe_error_variants')}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
