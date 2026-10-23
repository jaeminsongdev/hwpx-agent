"""Source TextSpan atom patch prerequisite: ten new and nine affected scalar cases."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_literal_replacement_product_components as prior
harness,shared,c,a=prior.harness,prior.shared,prior.c,prior.a
OUTPUT='implementation/p09/evidence/p09-361-text-atom-patch-components072.v1.json'
PRIOR=prior.OUTPUT
TEST='crates/hwpx-package/tests/patch_text_atom_ranges.rs'
PATCH='crates/hwpx-package/src/patch.rs'
LIB='crates/hwpx-package/src/lib.rs'
LEAF='crates/hwpx-package/src/patch/leaf_scalar_ranges.rs'
FLOW='crates/hwpx-package/src/text_flow.rs'
NEW={TEST,'crates/hwpx-package/src/patch/text_atom_ranges.rs','crates/hwpx-package/src/text_flow/source_text_span.rs'}
CHANGED={PATCH,LIB,LEAF,FLOW}
PATCH_ADDITIONS=(
    'mod text_atom_ranges;\npub use text_atom_ranges::TextAtomRangeReplacement;\n',
    '    /// Source TextSpan atom/scalar coordinates. Original tab/lineBreak children remain exact.\n'
    '    ReplaceTextAtomScalarRanges {\n        target: XmlElementSelector,\n        ranges: Vec<TextAtomRangeReplacement>,\n    },\n',
    '            Self::ReplaceTextAtomScalarRanges { .. } => formatter.write_str("ReplaceTextAtomScalarRanges(<redacted>)"),\n',
    '        text_atom_ranges::preflight(self.intents, self.patch_limits)?;\n',
    '                PatchIntent::ReplaceTextAtomScalarRanges { target, ranges } => {\n'
    '                    self.plan_text_atom_scalar_ranges(target, ranges, origin, &mut edits)?;\n                }\n')
LEAF_BRIDGE=('    token_boundaries(xml,index,node.start_token()+1..node.end_token().ok_or(PatchError::SelectorStale)?,content.end(),points)\n'
    '}\npub(super) fn token_boundaries(xml:&PreservingXmlDocument,index:usize,tokens:std::ops::Range<usize>,content_end:usize,points:&[u32])->Result<Vec<usize>,PatchError> {\n')


def inventory(check):return prior.inventory(check)|{TEST}


def inverse(q,old):
    text=q.text(PATCH)
    for addition in PATCH_ADDITIONS:
        c.require(text.count(addition)==1,'ONLY_ADDITIVE_TEXT_ATOM_PATCH_BRANCH');text=text.replace(addition,'')
    prior.prior.base.inverse(text,old[PATCH],'ORIGINAL_PATCH_INTENT_AND_VALIDATOR_BODIES_EXACT_INVERSE')
    for name,addition in ((LIB,', TextAtomRangeReplacement'),(FLOW,'mod source_text_span;\npub(crate) use source_text_span::read_source_text_span;\n')):
        text=q.text(name);c.require(text.count(addition)==1,'ONE_INTERNAL_READER_OR_PUBLIC_ATOM_RANGE_DECLARATION')
        prior.prior.base.inverse(text.replace(addition,''),old[name],'ORIGINAL_TEXT_FLOW_READER_WRITER_POLICY_AND_LIBRARY_EXACT_INVERSE')
    text=q.text(LEAF)
    for current,original in (
        ('    pub(super) fn data(&self)->(u32,u32,&str) {(self.start,self.end,self.value.value())}\n',''),
        (LEAF_BRIDGE,''),
        ('    let mut scalar=0_u32;\n','    let mut scalar=0_u32;let end=node.end_token().ok_or(PatchError::SelectorStale)?;\n'),
        ('    for token in xml.tokens().get(tokens).ok_or(PatchError::SelectorStale)? {\n','    for token in &xml.tokens()[node.start_token()+1..end] {\n'),
        ('    record(&mut offsets,scalar,content_end);\n','    record(&mut offsets,scalar,content.end());\n')):
        c.require(text.count(current)==1,'ONLY_ORIGINAL_SCALAR_BOUNDARY_HELPER_EXTRACTION');text=text.replace(current,original)
    prior.prior.base.inverse(text,old[LEAF],'ORIGINAL_SCALAR_TOKEN_DECODING_ENDPOINT_AND_EDIT_BODY_EXACT_INVERSE')


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'TEXT_ATOM_PATCH_IMMUTABLE_RUN_EXISTS');shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_TEXT_ATOM_PATCH_COMPONENTS',steps=[],actual_Hangul_or_COM=False,
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
        previous=q.json(PRIOR);c.require(q.snapshots[PRIOR]['sha256']=='cacd9b8ef647792299c661d3a5f107fa9b5e516b081e8485c653f4e6900449df'
            and previous['state'].startswith('PASS_')and previous['cleanup'],'EXACT_PREVIOUS_STRICT_LITERAL_PRODUCT_PASS')
        old={p['path']:p for p in previous['source_pins']};old_names={n for n in old if n.startswith(('crates/','fixtures/'))or n in {'Cargo.toml','Cargo.lock','rust-toolchain.toml',prior.prior.scalar.CAPTURE}}
        c.require(names==old_names|NEW,'EXACT_THREE_NEW_ATOM_PATCH_READER_AND_TEST_FILES')
        for name in names-NEW-CHANGED:c.require(q.snapshots[name]==old[name],'NO_OTHER_SOURCE_COMPILER_SERVICE_PRODUCT_OR_TEST_CHANGE')
        inverse(q,old)
        new=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(TEST)))
        old_tests=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(prior.prior.scalar.TEST)))
        c.require(len(new)==10 and len(old_tests)==9,'EXACT_TEN_NEW_AND_NINE_AFFECTED_ORIGINAL_SCALAR_TESTS')
        env=prior.prior.base.environment();common=[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package']
        print(json.dumps(dict(state='TEXT_ATOM_PATCH_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),new_cases=10,affected_cases=9,original_reader_and_value_policy_preserved=True)),flush=True)
        harness.run_one('ten_source_text_atom_preserving_patch_cases',common+['--test','patch_text_atom_ranges','--','--test-threads=1'],new,guard,env,row)
        harness.run_one('nine_affected_original_scalar_boundary_cases',common+['--test','patch_leaf_scalar_ranges','--','--test-threads=1'],old_tests,guard,env,row)
        c.require(inventory(guard.check)==names,'FINAL_TEXT_ATOM_PATCH_INPUT_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_TEXT_ATOM_PATCH_TEN_NEW_NINE_AFFECTED_NOT_SEARCH_COMPILER_PRODUCT_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,new_cases=10,affected_cases=9,total_executed_cases=19,
            original_reader_value_policy_and_patch_bodies_inverse_verified=True,original_control_and_unselected_part_bytes_preserved=True,
            actual_search_atom_and_scalar_coordinates_exercised=True,combined_scalar_intent_budgets_enforced=True,
            per_match_source_reimport_or_whole_leaf_scan_added=False,old_literal_core_stored_and_product_tests_reexecuted=False,
            next_work='Explicit_v2_literal_candidate_compiler_preserving_controls_and_output_atom_readback')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'TEXT_ATOM_PATCH_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_TEXT_ATOM_PATCH_RESOURCE_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','diagnostics','locations','summaries','tests','panic_locations','safe_error_variants')}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
