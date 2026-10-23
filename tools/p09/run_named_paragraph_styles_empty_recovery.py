"""341: one remaining empty-input expectation; keep25 passes and all production unchanged."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_named_paragraph_styles_fixture_recovery as previous
base=previous.base
shared,c,a,tools,compact,harness,audit=previous.shared,previous.c,previous.a,previous.tools,previous.compact,previous.harness,previous.audit
OUTPUT='implementation/p09/evidence/p09-361-named-paragraph-styles-empty-recovery341.v1.json';DRIVER='tools/p09/run_named_paragraph_styles_empty_recovery.py'
CASE='named::admitted_empty_run_paragraphs_change_and_runless_source_stays_rejected'
BEFORE='''    for body in ["<hp:p id='1' paraPrIDRef='0' styleIDRef='0'/>","<hp:p id='1' paraPrIDRef='0' styleIDRef='0'><hp:run charPrIDRef='0'><hp:t/></hp:run></hp:p>"]{
        assert!(matches!(lower(&package(body)?,q(),Scope::Document),Err(N::Source)));}
    let bytes=package("<hp:p id='1' paraPrIDRef='0' styleIDRef='0'><hp:run charPrIDRef='0'/></hp:p><hp:p id='2' paraPrIDRef='0' styleIDRef='1'><hp:run charPrIDRef='0'><hp:t></hp:t></hp:run></hp:p>")?;
    let out=lower(&bytes,q(),Scope::Document)?;let after=output(&bytes,&out)?;assert_eq!(out.receipt().matched_paragraphs,2);
    assert_eq!(references(&after)?,vec![(1,Some(0),Some(2)),(2,Some(0),Some(2))]);Ok(())
'''
AFTER='''    let runless=package("<hp:p id='1' paraPrIDRef='0' styleIDRef='0'/>")?;
    assert!(matches!(lower(&runless,q(),Scope::Document),Err(N::Source)));
    let bytes=package("<hp:p id='1' paraPrIDRef='0' styleIDRef='0'><hp:run charPrIDRef='0'/></hp:p><hp:p id='2' paraPrIDRef='0' styleIDRef='1'><hp:run charPrIDRef='0'><hp:t></hp:t></hp:run></hp:p><hp:p id='3' paraPrIDRef='0' styleIDRef='0'><hp:run charPrIDRef='0'><hp:t/></hp:run></hp:p>")?;
    let out=lower(&bytes,q(),Scope::Document)?;let after=output(&bytes,&out)?;assert_eq!(out.receipt().matched_paragraphs,3);
    assert_eq!(references(&after)?,vec![(1,Some(0),Some(2)),(2,Some(0),Some(2)),(3,Some(0),Some(2))]);Ok(())
'''

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'NAMED_PARAGRAPH_EMPTY_RECOVERY_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_NAMED_PARAGRAPH_EMPTY_RECOVERY',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        Native011_executed=False,prior_Native_replayed=False,actual_DB_or_Hangul_or_COM_started=False,official249_replayed=False,
        output_ingest_commit_or_publication=False,full_SEARCH025_product_or_native_qualified=False,stored_product_common_dispatch_or_preview_connected=False,production_unchanged_from339=True)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);failed=compact.unpack(q.json(previous.OUTPUT));mixed=compact.unpack(q.json(previous.previous.OUTPUT))
        c.require(q.snapshots[previous.OUTPUT]['sha256']=='ed2f436f2e1a95cf9d945fca9b7984a0ce2c06cd1997d5b3ae210b035dc0a49b'and failed['cleanup']
            and failed['fresh_inputs']==failed['final_fresh_hashes']==791 and len(failed['steps'])==1 and len(failed['steps'][0]['tests'])==3,'EXACT340_TWO_PASS_ONE_INPUT_EXPECTATION_FAILURE')
        c.require(q.snapshots[previous.previous.OUTPUT]['sha256']=='a395c5cf0cba82bca54e801c640f18b809a75cab0c2f9a65c4e385d4fd3667e8'and mixed['cleanup'],'EXACT339_ORIGINAL23_PASSES_RETAINED')
        retained={n for n,status in mixed['steps'][0]['tests']if status=='ok'}|{n for n,status in failed['steps'][0]['tests']if status=='ok'}
        c.require(len(retained)==25 and {n for n,status in failed['steps'][0]['tests']if status!='ok'}=={CASE},'EXACT25_PASS_IDENTITIES_AND_ONE_REMAINING_CASE')
        old={p['path']:p for p in failed['source_pins']}
        for n in sorted(set(old)|{DRIVER}):
            q.pin(n)
            if n in old and n!=base.TEST:c.require(q.snapshots[n]==old[n],'ALL_PRODUCTION_GUARDS_AND_25_PASSED_INPUTS_UNCHANGED')
        text=q.text(base.TEST);c.require(text.count(AFTER)==1,'ONLY_REMAINING_EMPTY_SHAPE_EXPECTATION_CORRECTED_AND_POSITIVE_COVERAGE_EXPANDED')
        audit.inverse(text.replace(AFTER,BEFORE),old[base.TEST],'ALL25_PASS_BODIES_AND_EVERY_OTHER_TEST_ASSERTION_UNCHANGED')
        for module in tuple(sys.modules.values()):
            f=getattr(module,'__file__',None)
            if f:
                p=Path(f).absolute()
                if p.is_relative_to(c.ROOT/'tools/p09')and p.suffix=='.py':q.pin(p.relative_to(c.ROOT).as_posix())
        all_cases={'named::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',text)}|base.AFFECTED
        c.require(all_cases==retained|{CASE}and len(all_cases)==26,'EXACT_CURRENT26_IDENTITY_COVERAGE')
        scratch=c.ROOT/'target/p09-named-paragraph-style-scratch-341';c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'NAMED_PARAGRAPH_EMPTY_RECOVERY_NEW_TEMP')
        scratch.mkdir();env=audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));print(json.dumps(dict(state='NAMED_PARAGRAPH_EMPTY_RECOVERY_PREFLIGHT',inputs=len(q.snapshots),recovered_cases=1,retained_cases=25,production_unchanged=True)),flush=True)
        harness.run_one('named_paragraph_style_only_remaining_empty_shape_case',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package','--test','document_import_paragraph_style_replacement',
            '--message-format=short','--',CASE,'--exact','--test-threads=1'],{CASE},guard,env,row,observe_capture=base.snapshot)
        tools.good_step(row['steps'][-1],{CASE});c.require(not any(scratch.iterdir()),'NAMED_PARAGRAPH_EMPTY_RECOVERY_TEMP_EMPTY');q.finish();guard.check(force=True)
        row.update(state='PASS_NAMED_PARAGRAPH_STYLE_SOURCE_RECOVERED1_RETAINED25_NOT_FULL_SEARCH025_PRODUCT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            executed_cases=1,retained_cases=25,distinct_cases=26,new_named_cases=19,affected_original_cases=7,next_work='named_style_current_stored_product_preview_and_character_style_support')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'NAMED_PARAGRAPH_EMPTY_RECOVERY_FAILURE_NO_RAW_VALUES')
        if q is not None:
            try:q.finish();row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
            except(ValueError,OSError,KeyError,TypeError,AttributeError):row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'NAMED_PARAGRAPH_EMPTY_RECOVERY_LOSSLESS_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','safe_error_variants','panic_locations','bounded_output_observation','cleanup')},'case_count':len(s.get('tests',[])),'failed_cases':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
