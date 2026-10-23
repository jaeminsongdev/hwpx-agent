"""22 Unicode-default casing cases and42 affected normalization cases under original resource bounds."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_unicode_match_product_components as prior
from run_regex_replacement_focused import select_own_single_cpu
from run_style_replacement_sync import good_step
harness,shared,c,a,audit,snapshot=prior.harness,prior.shared,prior.c,prior.a,prior.audit,prior.snapshot
OUTPUT='implementation/p09/evidence/p09-361-case-conversion-components169.v1.json'
FAILED='implementation/p09/evidence/p09-361-case-conversion-components168.v1.json'
ROOT='crates/hwpx-package/src/document_import/search/replacement/atoms'
ATOMS=ROOT+'.rs';UNICODE=ROOT+'/unicode.rs';PLAN=ROOT+'/unicode/plan.rs';TRANSFORM=ROOT+'/unicode/transform.rs'
CORE=ROOT+'/case.rs';MAPPING=ROOT+'/case/mapping.rs';TEST='crates/hwpx-package/tests/document_import_case_conversion.rs'
BUNDLE='crates/hwpx-package/tests/case_conversion_focused.rs';NEW={CORE,MAPPING,TEST,BUNDLE};CHANGED={ATOMS,UNICODE,PLAN,TRANSFORM}
STD_ROOT=Path('D:/devdata/Rustup/toolchains/1.96.0-x86_64-pc-windows-msvc/lib/rustlib/src/rust/library')
STD_FILES={'alloc/src/str.rs','core/src/char/methods.rs','core/src/unicode/unicode_data.rs'}
OLD_PLAN='''pub(super) struct Plan<'a> {pub(super) intents:Vec<PatchIntent>,pub(super) spans:BTreeMap<&'a PackagePath,Vec<PlannedSpan>>,
    pub(super) selected:usize,pub(super) groups:usize,pub(super) decomposed:usize,pub(super) components:usize,pub(super) ranges:usize,
    pub(super) changes:Vec<SourceReplacementTextSpanChange>,pub(super) protection_parts:usize,pub(super) visits:usize}
'''
EXTRACTION='''    compile_mapped(index,fields,context,groups,selected,|chars,_ids,remaining,bytes|transform::normalize(chars,form,remaining,bytes))
}
pub(in crate::document_import::search::replacement::atoms) fn compile_mapped<'a,F>(index:&'a SourceTextIndex<'_>,fields:&ImportedDocumentFields<'_>,context:&review::ReviewWriteContext,
    groups:Vec<Vec<usize>>,selected:BTreeSet<usize>,mut mapper:F)->Result<Plan<'a>,E>
where F:FnMut(&[char],&[usize],usize,usize)->Result<(Vec<transform::Change>,usize),E> {
'''


def inventory(check):return prior.inventory(check)|NEW


def one(text,new,old):
    c.require(text.count(new)==1,'ONE_DECLARED_CASE_MAPPING_COMMON_EXTRACTION_OR_VISIBILITY');return text.replace(new,old)


def inverse(q,old):
    audit.inverse(one(q.text(ATOMS),'pub mod case;\n',''),old[ATOMS],'WHOLE_ORIGINAL_LITERAL_REGEX_STYLE_UNICODE_ROOT_UNCHANGED')
    text=q.text(UNICODE)
    for name in('transform','plan'):text=one(text,'pub(super) mod '+name+';','mod '+name+';')
    audit.inverse(text,old[UNICODE],'ENTIRE_UNICODE_V1_SCOPE_RECEIPT_HASH_AND_COMPILER_BODY_UNCHANGED')
    text=q.text(TRANSFORM);start=text.index('pub(in crate::document_import::search::replacement::atoms) struct Change {');end=text.index('pub(super) fn normalize',start)
    text=text[:start]+'pub(super) struct Change {pub(super) input:Range<usize>,pub(super) value:String}\n'+text[end:]
    audit.inverse(text,old[TRANSFORM],'ENTIRE_ORIGINAL_FOUR_FORM_NORMALIZATION_AND_PROVENANCE_CLOSURE_UNCHANGED')
    text=q.text(PLAN);start=text.index("pub(in crate::document_import::search::replacement::atoms) struct Plan<'a> {");end=text.index('fn guard(',start)
    text=text[:start]+OLD_PLAN+text[end:];text=one(text,EXTRACTION,'')
    c.require(text.count('&mut mapper,&mut plan')==2,'TWO_ORIGINAL_CONTROL_SEPARATED_GROUP_CALLS_RETAINED');text=text.replace('&mut mapper,&mut plan','form,&mut plan')
    text=one(text,"fn lower_group<F>(index:&SourceTextIndex<'_>,chars:&[char],ids:&[usize],mapper:&mut F,plan:&mut Plan<'_>,\n"
        '    edits:&mut BTreeMap<usize,Vec<Edit>>,ranges:&mut usize,bytes:&mut usize)->Result<(),E>\n'
        'where F:FnMut(&[char],&[usize],usize,usize)->Result<(Vec<transform::Change>,usize),E> {\n',
        "fn lower_group(index:&SourceTextIndex<'_>,chars:&[char],ids:&[usize],form:SourceUnicodeNormalizationForm,plan:&mut Plan<'_>,\n"
        '    edits:&mut BTreeMap<usize,Vec<Edit>>,ranges:&mut usize,bytes:&mut usize)->Result<(),E> {\n')
    text=one(text,'let(changes,count)=mapper(chars,ids,','let(changes,count)=transform::normalize(chars,form,')
    audit.inverse(text,old[PLAN],'ENTIRE_ORIGINAL_SCOPE_MATCH_SELECTION_GUARDS_PATCH_READBACK_PLAN_AND_LIMITS_RECONSTRUCTED_EXACTLY')
    source=q.text(CORE)
    for marker in('ImportedDocumentFields::import(original)','ImportedDocumentReviewBodies::import_bound_fields(original,&fields)',
        'SourceReviewScopeIndex::from_review(original,&review,limits)','unicode::plan::compile_mapped(',
        'styles::text::output::build(','readback::verify_artifact('):
        c.require(source.count(marker)==1,'ONE_CASE_SOURCE_PROOF_FIELDS_REVIEW_INDEX_PLAN_WRITER_AND_OUTPUT_IMPORT')
    mapping=q.text(MAPPING)
    c.require(mapping.count('source.to_uppercase()')==1 and mapping.count('source.to_lowercase()')==1
        and 'p.segment==point.segment&&p.atom==point.atom'in mapping and 'Regex'not in mapping and 'unicode_casefold'not in mapping,
        'ONE_WHOLE_STRING_MAPPING_BRANCH_AND_SAME_ATOM_COALESCING_WITHOUT_OLDER_UNICODE_PROPERTY_TABLES')


def expected(q):
    result=set()
    for name,module,count in[(TEST,'case',22),('crates/hwpx-package/tests/document_import_unicode_normalization.rs','scope',24),
        ('crates/hwpx-package/tests/document_import_unicode_match_normalization.rs','matches',18)]:
        names=re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(name));c.require(len(names)==len(set(names))==count,'EXACT22_NEW_AND42_AFFECTED_UNICODE_TEST_IDENTITIES')
        result.update(module+'::'+n for n in names)
    return result


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'CASE_CONVERSION_IMMUTABLE_RUN_EXISTS');selection=select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;stdlib=None;started=time.monotonic();row=dict(state='FAILED_CASE_CONVERSION_COMPONENTS',steps=[],own_cpu_selection=selection,actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False,case_stored_product_or_native_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        baseline=q.json(prior.OUTPUT)
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='e2a13d4286f7890d0b6eed330b1b1c0c33ecbb3505eef2fb85724f6c18199133'
            and baseline['state']=='PASS_UNICODE_MATCH_TWENTY_TWO_V2_PRODUCTS_NOT_FULL_TRANSACTION_NATIVE_OR_GATE'and baseline['cleanup']
            and baseline['fresh_inputs']==baseline['final_fresh_hashes']==666 and baseline['new_product_cases']==22,'EXACT_PRIOR22_MATCH_PRODUCTS_AND42_SOURCE_BASELINE_RETAINED')
        old={p['path']:p for p in baseline['source_pins']};c.require(NEW.isdisjoint(old),'NEW_CASE_CONVERSION_FILES_ARE_ADDITIVE')
        for name in names-NEW-CHANGED:c.require(q.snapshots[name]==old[name],'ALL_OTHER_SOURCE_MATCHER_PROTECTION_WRITER_PRODUCTS_FIXTURES_AND_TESTS_UNCHANGED')
        failed=q.json(FAILED);c.require(failed['state']=='FAILED_CASE_CONVERSION_COMPONENTS'and failed['cleanup']and len(failed['steps'])==1,'ORIGINAL168_FAILED_COMPILE_EVIDENCE_PRESERVED')
        step=failed['steps'][0];c.require(step['exit_code']==101 and not step['tests']and step['cleanup']and step['owned_job']['owned_tree_empty']and step['owned_job']['job_handle_closed']
            and step['bounded_output_observation']['rust_error_codes']==['E0425']and step['bounded_output_observation']['short_error_locations']==[[MAPPING,'21','46']],
            'ORIGINAL168_POINT_IMPORT_COMPILE_ERROR_WITH_ZERO_TESTS_AND_TERMINAL_JOB')
        failed_pins={p['path']:p for p in failed['source_pins']}
        for name in names-{MAPPING}:c.require(q.snapshots[name]==failed_pins[name],'ALL_OTHER_PRODUCTION_TESTS_FIXTURES_AND_LIMITS_UNCHANGED_AFTER168')
        audit.inverse(one(q.text(MAPPING),'use crate::document_import::search::Point;\n',''),failed_pins[MAPPING],'EXACT168_MAPPING_RESTORED_BY_REMOVING_ONLY_MISSING_POINT_IMPORT')
        inverse(q,old);cases=expected(q);stdlib=a.AcceptanceReader(STD_ROOT,guard.check)
        for name in sorted(STD_FILES):stdlib.pin(name)
        stdtext=stdlib.text('alloc/src/str.rs');data=stdlib.text('core/src/unicode/unicode_data.rs')
        c.require('pub const UNICODE_VERSION: (u8, u8, u8) = (17, 0, 0);'in data and 'map_uppercase_sigma(self, prefix_len + i)'in stdtext
            and 'case_ignorable_then_cased(from[..i].chars().rev())'in stdtext,'EXACT_PINNED_LOCAL_STD_UNICODE17_AND_DEFAULT_SIGMA_MAPPING_SOURCE_REFERENCE')
        print(json.dumps(dict(state='CASE_CONVERSION_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),stdlib_reference_inputs=len(stdlib.snapshots),new_cases=22,affected_cases=42,one_cpu_mask=4)),flush=True)
        harness.run_one('twenty_two_case_and_forty_two_affected_unicode_source_cases',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package',
            '--test','case_conversion_focused','--message-format=short','--','--test-threads=1'],cases,guard,audit.environment(),row,observe_capture=snapshot)
        good_step(row['steps'][0],cases);c.require(inventory(guard.check)==names,'FINAL_CASE_CONVERSION_INVENTORY_DRIFT');q.finish();stdlib.finish();guard.check(force=True)
        row.update(state='PASS_CASE22_UNICODE42_NOT_CASE_STORED_PRODUCT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            stdlib_reference_inputs=len(stdlib.snapshots),stdlib_final_fresh_hashes=stdlib.final_fresh_hashes,new_source_cases=22,affected_source_cases=42,total_executed_cases=64,
            old172_products_and_unrelated57_source_reexecuted=False,original_unicode_and_guard_patch_bodies_inverse_verified=True,
            whole_string_default_mapping_not_older_casefold_or_regex_properties=True,adjacent_changes_coalesced_only_within_original_text_atom=True,
            next_work='Current_stored_and_strict_product_binding_of_explicit_default_case_conversion_then_remaining_P09_contract_and_native_gates')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'CASE_CONVERSION_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),stdlib_reference_root=str(STD_ROOT),stdlib_reference_pins=[]if stdlib is None else list(stdlib.snapshots.values()),
            resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_CASE_CONVERSION_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','stdlib_reference_inputs','stdlib_final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations','safe_error_variants')},
                'observation':{k:s.get('bounded_output_observation',{}).get(k)for k in('safe_warning_locations','short_error_locations','rust_error_codes')},
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
