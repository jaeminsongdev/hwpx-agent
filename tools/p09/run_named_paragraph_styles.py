"""337: actual named paragraph-style batch output including empties; new19 + affected original7."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_compiled_font_options as previous
import run_sql23_storage as closure
shared,c,a,tools,compact,harness,audit=previous.shared,previous.c,previous.a,previous.tools,previous.compact,previous.harness,previous.audit
OUTPUT='implementation/p09/evidence/p09-361-named-paragraph-styles337.v1.json';DRIVER='tools/p09/run_named_paragraph_styles.py'
CORE='crates/hwpx-package/src/document_import/search/replacement/atoms/styles/paragraphs.rs';NAMED=CORE[:-3]+'/named.rs'
PARENT='crates/hwpx-package/tests/document_import_paragraph_style_replacement.rs';TEST='crates/hwpx-package/tests/support/named_paragraph_style_replacement.rs'
NEW={NAMED,TEST,DRIVER};LINK='#[path="support/named_paragraph_style_replacement.rs"]mod named;\n'
EXTRACT='''    compile_matched(index,fields,context,matched,target)
}
fn compile_matched(index:&SourceTextIndex<'_>,fields:&ImportedDocumentFields<'_>,context:&review::ReviewWriteContext,
    matched:BTreeMap<PackagePath,BTreeMap<usize,SourceAnchorHandle>>,target:SourceParagraphStyleTarget)->Result<Plan,R>{
    let source=index.original.source();
'''
AFFECTED={'paragraph_style_two_axes_change_only_the_selected_original_reference_value','paragraph_style_four_scopes_require_the_whole_paragraph_and_reject_partial_selection',
    'paragraph_style_nested_hidden_and_memo_policies_never_modify_outer_cache_or_paragraph','paragraph_style_unqueried_cached_field_inside_the_matched_paragraph_still_blocks',
    'paragraph_style_unqueried_locked_descendant_protects_whole_paragraph_including_noop','paragraph_style_tracked_paragraph_run_and_unqueried_marker_fail_before_noop_elimination',
    'paragraph_style_many_paragraphs_share_one_linear_protection_map_and_keep_private_text_hidden'}

def inverse(q,old):
    text=q.text(CORE);c.require(text.count('pub mod named;\n')==1 and text.count(EXTRACT)==1,'ONE_NAMED_MODULE_AND_SHARED_PARAGRAPH_COMPILER_EXTRACTION')
    audit.inverse(text.replace('pub mod named;\n','').replace(EXTRACT,''),old[CORE],'ALL_ORIGINAL_PARAGRAPH_SCOPE_PROTECTION_FIELD_GUARDS_PATCHES_WRITER_READBACK_AND_RECEIPTS_UNCHANGED')
    text=q.text(PARENT);c.require(text.count(LINK)==1,'ONE_NAMED_STYLE_TEST_MODULE_LINK');audit.inverse(text.replace(LINK,''),old[PARENT],'ALL_ORIGINAL_PARAGRAPH_STYLE_TEST_BODIES_UNCHANGED')

def snapshot(capture,expected):
    result=previous.previous.previous.previous.previous.snapshot(capture,expected)
    with capture.lock:raw=(bytes(capture.buffers['stdout'])+bytes(capture.buffers['stderr'])).decode('utf-8','replace')
    result['closed_named_style_errors']=sorted(set(re.findall(r'\bNAMED_PARAGRAPH_STYLE_[A-Z_]{1,64}\b',raw)));return result

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'NAMED_PARAGRAPH_STYLES_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_NAMED_PARAGRAPH_STYLES',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        Native011_executed=False,prior_Native_replayed=False,actual_DB_or_Hangul_or_COM_started=False,official249_replayed=False,
        output_ingest_commit_or_publication=False,full_SEARCH025_product_or_native_qualified=False,stored_product_common_dispatch_or_preview_connected=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=compact.unpack(q.json(previous.OUTPUT))
        c.require(q.snapshots[previous.OUTPUT]['sha256']=='47073d385a8453f7d306dc36d15fda6d63765d4390c417e367db1280629e2d78'and passed['cleanup']
            and passed['fresh_inputs']==passed['final_fresh_hashes']==779 and passed['new_cases']==23,'EXACT335_SOURCE_BASELINE')
        old={p['path']:p for p in passed['source_pins']};names=closure.inventory(guard.check)|set(old)|NEW
        for n in sorted(names):
            q.pin(n)
            if n in old and n not in {CORE,PARENT}:c.require(q.snapshots[n]==old[n],'ALL_OTHER_FONT_STORED_PRODUCT_COMMON_GUARDS_READBACK_AND_TESTS_UNCHANGED')
            elif n not in old:c.require(n in NEW,'ONLY_DECLARED_NAMED_PARAGRAPH_SOURCE_TEST_AND_DRIVER_ADDED')
        inverse(q,old)
        for module in tuple(sys.modules.values()):
            f=getattr(module,'__file__',None)
            if f:
                p=Path(f).absolute()
                if p.is_relative_to(c.ROOT/'tools/p09')and p.suffix=='.py':q.pin(p.relative_to(c.ROOT).as_posix())
        cases={'named::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(TEST))}|AFFECTED
        c.require(len(cases)==26 and len(AFFECTED)==7,'EXACT_NEW19_AFFECTED_ORIGINAL7')
        scratch=c.ROOT/'target/p09-named-paragraph-style-scratch-337';c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'NAMED_PARAGRAPH_STYLES_NEW_TEMP')
        scratch.mkdir();env=audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));print(json.dumps(dict(state='NAMED_PARAGRAPH_STYLES_PREFLIGHT',inputs=len(q.snapshots),new_cases=19,affected_cases=7,official249_replayed=False)),flush=True)
        harness.run_one('named_paragraph_styles19_affected_original7',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package','--test','document_import_paragraph_style_replacement',
            '--message-format=short','--',*sorted(cases),'--test-threads=1'],cases,guard,env,row,observe_capture=snapshot)
        tools.good_step(row['steps'][-1],cases);c.require(not any(scratch.iterdir()),'NAMED_PARAGRAPH_STYLES_TEMP_EMPTY');q.finish();guard.check(force=True)
        row.update(state='PASS_NAMED_PARAGRAPH_STYLE_SOURCE_BATCH19_AFFECTED7_NOT_FULL_SEARCH025_PRODUCT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_cases=19,affected_cases=7,original_shared_paragraph_compiler_guards_and_reader_unchanged=True,
            next_work='named_style_current_stored_product_preview_and_character_style_support')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'NAMED_PARAGRAPH_STYLE_FAILURE_NO_RAW_VALUES')
        if q is not None:
            try:q.finish();row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
            except(ValueError,OSError,KeyError,TypeError,AttributeError):row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'NAMED_PARAGRAPH_STYLE_LOSSLESS_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','safe_error_variants','panic_locations','bounded_output_observation','cleanup')},'case_count':len(s.get('tests',[])),'failed_cases':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
