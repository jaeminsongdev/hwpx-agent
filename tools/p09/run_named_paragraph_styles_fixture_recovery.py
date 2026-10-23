"""340: retain23 actual passes; recover3 using admitted empty runs and a real bookmark barrier."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_named_paragraph_styles_compile_recovery as previous
base=previous.base
shared,c,a,tools,compact,harness,audit=previous.shared,previous.c,previous.a,previous.tools,previous.compact,previous.harness,previous.audit
OUTPUT='implementation/p09/evidence/p09-361-named-paragraph-styles-fixture-recovery340.v1.json';DRIVER='tools/p09/run_named_paragraph_styles_fixture_recovery.py'
FAILED={'named::controls_and_all_blocks_must_fit_scope_before_whole_paragraph_edit','named::empty_and_self_closing_paragraphs_are_real_style_uses_not_missing_text_matches','named::empty_selection_is_not_authority_to_change_empty_paragraph_style'}
RECOVERED=(FAILED-{'named::empty_and_self_closing_paragraphs_are_real_style_uses_not_missing_text_matches'})|{'named::admitted_empty_run_paragraphs_change_and_runless_source_stays_rejected'}
OLD_EMPTY='''fn empty_and_self_closing_paragraphs_are_real_style_uses_not_missing_text_matches()->TestResult{
    let bytes=package("<hp:p id='1' paraPrIDRef='0' styleIDRef='0'/><hp:p id='2' paraPrIDRef='0' styleIDRef='1'><hp:run charPrIDRef='0'><hp:t/></hp:run></hp:p>")?;
'''
NEW_EMPTY='''fn admitted_empty_run_paragraphs_change_and_runless_source_stays_rejected()->TestResult{
    for body in ["<hp:p id='1' paraPrIDRef='0' styleIDRef='0'/>","<hp:p id='1' paraPrIDRef='0' styleIDRef='0'><hp:run charPrIDRef='0'><hp:t/></hp:run></hp:p>"]{
        assert!(matches!(lower(&package(body)?,q(),Scope::Document),Err(N::Source)));}
    let bytes=package("<hp:p id='1' paraPrIDRef='0' styleIDRef='0'><hp:run charPrIDRef='0'/></hp:p><hp:p id='2' paraPrIDRef='0' styleIDRef='1'><hp:run charPrIDRef='0'><hp:t></hp:t></hp:run></hp:p>")?;
'''
OLD_SELECTION='''    let bytes=package("<hp:p id='1' paraPrIDRef='0' styleIDRef='0'/>")?;let f=forms(&bytes)?;let inv=f.source_review_scope_index(&bytes,Default::default())?.scope_inventory()?;
'''
NEW_SELECTION='''    let bytes=package("<hp:p id='1' paraPrIDRef='0' styleIDRef='0'><hp:run charPrIDRef='0'/></hp:p>")?;let f=forms(&bytes)?;let inv=f.source_review_scope_index(&bytes,Default::default())?.scope_inventory()?;
'''
OLD_CONTROL='''    let bytes=package(&para(1,0,&format!("ABC{TAB}DEF")))?;let f=forms(&bytes)?;let inv=f.source_review_scope_index(&bytes,Default::default())?.scope_inventory()?;let b=&inv.inventory.blocks[0];
'''
NEW_CONTROL='''    let bytes=package(&para(1,0,&format!("ABC{TAB}</hp:t><hp:ctrl><hp:bookmark name='BOOK'/></hp:ctrl><hp:t>DEF")))?;let f=forms(&bytes)?;let inv=f.source_review_scope_index(&bytes,Default::default())?.scope_inventory()?;let b=&inv.inventory.blocks[0];
'''

def inverse(q,old):
    text=q.text(base.TEST)
    for before,after in((OLD_EMPTY,NEW_EMPTY),(OLD_SELECTION,NEW_SELECTION),(OLD_CONTROL,NEW_CONTROL)):
        c.require(text.count(after)==1,'EXACT_THREE_FAILED_INPUT_REPAIRS_WITH_ORIGINAL_DENIALS_RETAINED');text=text.replace(after,before)
    audit.inverse(text,old[base.TEST],'ALL_23_PASSED_TEST_BODIES_AND_EVERY_PRODUCTION_ALGORITHM_UNCHANGED')

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'NAMED_PARAGRAPH_FIXTURE_RECOVERY_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_NAMED_PARAGRAPH_FIXTURE_RECOVERY',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        Native011_executed=False,prior_Native_replayed=False,actual_DB_or_Hangul_or_COM_started=False,official249_replayed=False,
        output_ingest_commit_or_publication=False,full_SEARCH025_product_or_native_qualified=False,stored_product_common_dispatch_or_preview_connected=False,
        production_unchanged_from339=True)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);failed=compact.unpack(q.json(previous.OUTPUT))
        c.require(q.snapshots[previous.OUTPUT]['sha256']=='a395c5cf0cba82bca54e801c640f18b809a75cab0c2f9a65c4e385d4fd3667e8'and failed['cleanup']
            and failed['fresh_inputs']==failed['final_fresh_hashes']==789 and len(failed['steps'])==1 and len(failed['steps'][0]['tests'])==26,'EXACT339_MIXED_ACTUAL26_RESULTS_PRESERVED')
        tests=failed['steps'][0]['tests'];retained={n for n,status in tests if status=='ok'}
        c.require(len(retained)==23 and {n for n,status in tests if status!='ok'}==FAILED,'EXACT23_PASSES_THREE_FAILED_IDENTITIES')
        old={p['path']:p for p in failed['source_pins']}
        for n in sorted(set(old)|{DRIVER}):
            q.pin(n)
            if n in old and n!=base.TEST:c.require(q.snapshots[n]==old[n],'ALL_PRODUCTION_READER_GUARDS_WRITER_AND_OTHER_TEST_INPUTS_UNCHANGED')
        inverse(q,old)
        for module in tuple(sys.modules.values()):
            f=getattr(module,'__file__',None)
            if f:
                p=Path(f).absolute()
                if p.is_relative_to(c.ROOT/'tools/p09')and p.suffix=='.py':q.pin(p.relative_to(c.ROOT).as_posix())
        all_cases={'named::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(base.TEST))}|base.AFFECTED
        c.require(all_cases==retained|RECOVERED and len(all_cases)==26,'ALL23_RETAINED_AND_THREE_RECOVERED_CASES_EXACT')
        scratch=c.ROOT/'target/p09-named-paragraph-style-scratch-340';c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'NAMED_PARAGRAPH_FIXTURE_RECOVERY_NEW_TEMP')
        scratch.mkdir();env=audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));print(json.dumps(dict(state='NAMED_PARAGRAPH_FIXTURE_RECOVERY_PREFLIGHT',inputs=len(q.snapshots),recovered_cases=3,retained_cases=23,production_unchanged=True)),flush=True)
        harness.run_one('named_paragraph_styles_only_failed3_admitted_inputs',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package','--test','document_import_paragraph_style_replacement',
            '--message-format=short','--',*sorted(RECOVERED),'--test-threads=1'],RECOVERED,guard,env,row,observe_capture=base.snapshot)
        tools.good_step(row['steps'][-1],RECOVERED);c.require(not any(scratch.iterdir()),'NAMED_PARAGRAPH_FIXTURE_RECOVERY_TEMP_EMPTY');q.finish();guard.check(force=True)
        row.update(state='PASS_NAMED_PARAGRAPH_STYLE_SOURCE_RECOVERED3_RETAINED23_NOT_FULL_SEARCH025_PRODUCT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            executed_cases=3,retained_cases=23,distinct_cases=26,new_named_cases=19,affected_original_cases=7,next_work='named_style_current_stored_product_preview_and_character_style_support')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'NAMED_PARAGRAPH_FIXTURE_RECOVERY_FAILURE_NO_RAW_VALUES')
        if q is not None:
            try:q.finish();row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
            except(ValueError,OSError,KeyError,TypeError,AttributeError):row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'NAMED_PARAGRAPH_FIXTURE_RECOVERY_LOSSLESS_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','safe_error_variants','panic_locations','bounded_output_observation','cleanup')},'case_count':len(s.get('tests',[])),'failed_cases':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
