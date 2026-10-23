"""348: whole-paragraph original style filter; new18 + affected source6/product3, no old suite replay."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_compiled_named_styles_recovery as previous
import run_sql23_storage as closure
shared,c,a,tools,compact,harness,audit=previous.shared,previous.c,previous.a,previous.tools,previous.compact,previous.harness,previous.audit
OUTPUT='implementation/p09/evidence/p09-361-filtered-named-styles348.v1.json';DRIVER='tools/p09/run_filtered_named_styles.py'
NAMED='crates/hwpx-package/src/document_import/search/replacement/atoms/styles/paragraphs/named.rs';FILTERED=NAMED[:-3]+'/filtered.rs'
PARENT='crates/hwpx-package/tests/support/named_paragraph_style_replacement.rs';TEST='crates/hwpx-package/tests/support/filtered_named_paragraph_style.rs'
NEW={DRIVER,FILTERED,TEST};CHANGED={NAMED,PARENT};LINK='#[path="filtered_named_paragraph_style.rs"]mod filtered;\n'
AFFECTED_SOURCE={'named::two_original_named_styles_replace_simultaneously_without_editing_definitions_or_other_references',
    'named::admitted_empty_run_paragraphs_change_and_runless_source_stays_rejected','named::four_scope_kinds_limit_actual_paragraphs_and_partial_selection_never_widens',
    'named::field_cache_anywhere_in_changed_paragraph_blocks_the_whole_batch','named::ancestor_or_descendant_tracking_and_locked_table_block_without_partial_candidate',
    'named::many_paragraphs_reuse_one_part_guard_and_preserve_original_header'}
AFFECTED_PRODUCT={'compiled_named::common_mutation_receipt_and_output_match_standalone_without_repreparing_owner','compiled_named::separate_preview_metadata_matches_standalone_and_has_no_output',
    'compiled_named::two_named_paragraphs_compile_to_two_actual_owners_not_first_node'}

def inverse(q,old):
    text=q.text(NAMED);c.require(text.count('pub mod filtered;\n')==1,'ONE_FILTERED_NAMED_MODULE');text=text.replace('pub mod filtered;\n','')
    marker='''        self.lower_named_paragraph_style_candidate_checked(original,query,selector,policy,None,limits,writer).map(|(candidate,_)|candidate)
    }
    fn lower_named_paragraph_style_candidate_checked(&self,original:&ImportedDocumentForms,query:SourceNamedParagraphStyleQuery<'_>,selector:SourceIndexScopeSelector<'_>,
        policy:SourceReviewTextPolicy,filter:Option<SourceReviewStyleFilter>,limits:SourceSearchLimits,writer:WriterLimits)->Result<(SourceNamedParagraphStyleCandidate,Option<filtered::SourceNamedParagraphFilterReceipt>),N>{
        if let Some(filter)=filter{filter.validate()?;}
''';c.require(text.count(marker)==1,'ONE_SHARED_NAMED_PREPARATION_EXTRACTION');text=text.replace(marker,'')
    for marker in('        let filtered=filter.map(|filter|filtered::select(index,&windows,filter)).transpose()?;\n','            if filtered.as_ref().is_some_and(|(allowed,_)|!allowed.contains(id)){continue;}\n'):
        c.require(text.count(marker)==1,'ONLY_DECLARED_ORIGINAL_FILTER_SELECTION_ADDED');text=text.replace(marker,'')
    text=text.replace('Ok((SourceNamedParagraphStyleCandidate{artifact,receipt},filtered.map(|(_,receipt)|receipt)))','Ok(SourceNamedParagraphStyleCandidate{artifact,receipt})')
    audit.inverse(text,old[NAMED],'ALL_V1_NAME_RESOLUTION_SCOPE_PROTECTION_PATCH_WRITER_READBACK_HASHES_AND_RECEIPTS_UNCHANGED')
    text=q.text(PARENT);c.require(text.count(LINK)==1,'ONE_FILTERED_NAMED_TEST_LINK');audit.inverse(text.replace(LINK,''),old[PARENT],'ALL_PREVIOUS19_NAMED_SOURCE_TEST_BODIES_UNCHANGED')

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'FILTERED_NAMED_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_FILTERED_NAMED',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        Native011_executed=False,prior_Native_replayed=False,actual_DB_or_Hangul_or_COM_started=False,official249_replayed=False,old_suites_replayed=False,
        output_ingest_commit_or_publication=False,full_SEARCH025_product_or_native_qualified=False,filtered_stored_product_or_preview_connected=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=compact.unpack(q.json(previous.OUTPUT))
        c.require(q.snapshots[previous.OUTPUT]['sha256']=='e3e66e16e0eb259a3d9eddba7c8973d99b2d13e4d019f1b848d1dfa5f3cefa58'and passed['cleanup']
            and passed['fresh_inputs']==passed['final_fresh_hashes']==806 and passed['new_cases']==19 and passed['affected_cases']==12,'EXACT346_NAMED_COMMON_BASELINE')
        old={p['path']:p for p in passed['source_pins']};names=closure.inventory(guard.check)|set(old)|NEW
        for n in sorted(names):
            q.pin(n)
            if n in old and n not in CHANGED:c.require(q.snapshots[n]==old[n],'ALL_OTHER_SOURCE_PRODUCT_COMPILER_TEST_AND_RESOURCE_GUARDS_UNCHANGED')
            elif n not in old:c.require(n in NEW,'ONLY_DECLARED_FILTER_SOURCE_TEST_AND_DRIVER_ADDED')
        inverse(q,old)
        for module in tuple(sys.modules.values()):
            f=getattr(module,'__file__',None)
            if f:
                p=Path(f).absolute()
                if p.is_relative_to(c.ROOT/'tools/p09')and p.suffix=='.py':q.pin(p.relative_to(c.ROOT).as_posix())
        cases={'named::filtered::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(TEST))};c.require(len(cases)==18 and len(AFFECTED_SOURCE)==6 and len(AFFECTED_PRODUCT)==3,'EXACT_NEW18_AFFECTED_SOURCE6_PRODUCT3')
        scratch=c.ROOT/'target/p09-filtered-named-styles-scratch-348';c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'FILTERED_NAMED_NEW_TEMP')
        scratch.mkdir();env=audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));print(json.dumps(dict(state='FILTERED_NAMED_PREFLIGHT',inputs=len(q.snapshots),new_cases=18,affected_cases=9)),flush=True)
        for package,binary,label,selected in [('hwpx-package','document_import_paragraph_style_replacement','filtered_named_source18_affected6',cases|AFFECTED_SOURCE),
            ('hwpx-agent-cli','named_style_product','affected_named_common_product3',AFFECTED_PRODUCT)]:
            harness.run_one(label,[harness.CARGO,'test','--offline','--locked','-j','1','-p',package,'--test',binary,'--message-format=short','--',*sorted(selected),'--test-threads=1'],selected,guard,env,row,
                observe_capture=previous.base.previous.previous.previous.base.snapshot)
            tools.good_step(row['steps'][-1],selected)
        c.require(not any(scratch.iterdir()),'FILTERED_NAMED_TEMP_EMPTY');q.finish();guard.check(force=True)
        row.update(state='PASS_FILTERED_NAMED_SOURCE18_AFFECTED_SOURCE6_PRODUCT3_NOT_FILTERED_PRODUCT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_cases=18,affected_source_cases=6,affected_product_cases=3,original_unfiltered_paths_preserved=True,predicate_cache_is_per_source_segment=True,
            next_work='filtered_named_current_stored_product_preview_common_connection_and_character_style_semantics')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'FILTERED_NAMED_FAILURE_NO_RAW_VALUES')
        if q is not None:
            try:q.finish();row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
            except(ValueError,OSError,KeyError,TypeError,AttributeError):row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'FILTERED_NAMED_LOSSLESS_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','safe_error_variants','panic_locations','bounded_output_observation','cleanup')},'case_count':len(s.get('tests',[])),'failed_cases':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
