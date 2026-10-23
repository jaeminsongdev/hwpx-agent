"""329: inherit observed paragraph/run tracking once per part; recover3 + affected13 + new4."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_font_tracking_diagnostic as previous
shared,c,a,tools,compact,harness,audit=previous.shared,previous.c,previous.a,previous.tools,previous.compact,previous.harness,previous.audit
OUTPUT='implementation/p09/evidence/p09-361-font-tracking-recovery329.v1.json';DRIVER='tools/p09/run_font_tracking_recovery.py'
CORE='crates/hwpx-package/src/document_import/search/replacement/atoms/styles/fonts.rs';TEST=previous.previous.previous.TEST
TRACKING='''                    let inherited=node.parent().map(|i|tracked.get(i).copied().ok_or(E::Selection)).transpose()?.unwrap_or(false);
                    let marker=match node.name().local_name(){"p"=>Some("paraTcId"),"run"=>Some("charTcId"),_=>None};
                    let observed=node.name().namespace()==Some(crate::HANCOM_2020_PARAGRAPH_NAMESPACE)
                        &&marker.is_some_and(|name|node.attributes().iter().any(|a|a.name().namespace().is_none()&&a.name().local_name()==name));
                    tracked.push(inherited||observed);}
'''

def inverse(q,old):
    text=q.text(CORE);c.require(text.count(TRACKING)==1,'ONE_LINEAR_PARENT_TRACKING_PROPAGATION')
    text=text.replace(TRACKING,'')
    for marker in ('                let mut tracked=Vec::with_capacity(xml.elements().len());\n','            if guards[part.path()].2[text]{return Err(E::Protection.into());}\n'):
        c.require(text.count(marker)==1,'ONE_TRACKING_MAP_AND_PRE_MATCH_SELECTION_GUARD');text=text.replace(marker,'')
    text=text.replace('uncertain.push(parent||local);\n','uncertain.push(parent||local);}\n').replace('(protected,uncertain,tracked)','(protected,uncertain)')
    audit.inverse(text,old[CORE],'ALL_OTHER_MATCH_SELECTOR_FIELD_PROTECTION_RENDER_PATCH_WRITER_READBACK_RECEIPT_ALGORITHMS_UNCHANGED')
    text=q.text(TEST);start=text.index('// Ancestor tracking on the explicit text axis and common compiler begin.\n');end=text.index('// Ancestor tracking on the explicit text axis and common compiler end.\n',start)+len('// Ancestor tracking on the explicit text axis and common compiler end.\n')
    audit.inverse(text[:start]+text[end:],old[TEST],'ALL_PREVIOUS20_REVIEW_TESTS_AND_FOUR_RETAINED_SOURCE_ADMISSION_CASES_UNCHANGED')

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'FONT_TRACKING_RECOVERY_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_FONT_TRACKING_RECOVERY',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        Native011_executed=False,prior_Native_replayed=False,actual_DB_or_Hangul_or_COM_started=False,official249_replayed=False,previous56_replayed=False,
        output_ingest_commit_or_publication=False,full_SEARCH024_product_or_native_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);failed=compact.unpack(q.json(previous.OUTPUT))
        c.require(q.snapshots[previous.OUTPUT]['sha256']=='13cf6b199291c354c8a5d5bf4638af7bc953e661c8dd37353f1999561d033a7c'and failed['cleanup']
            and failed['state']=='FAILED_FONT_ANCESTOR_TRACKING_THREE_UNEXPECTED_ACCEPTANCES_CONFIRMED'and failed['fresh_inputs']==failed['final_fresh_hashes']==763
            and failed['unexpected_tracking_acceptances']==3 and failed['source_admission_passes']==4,'EXACT328_THREE_UNSAFE_CANDIDATES_AND_FOUR_SOURCE_DENIALS_RETAINED')
        old={p['path']:p for p in failed['source_pins']}
        for n in sorted(set(old)|{DRIVER}):
            q.pin(n)
            if n in old and n not in {CORE,TEST}:c.require(q.snapshots[n]==old[n],'ALL_PREVIOUS_PRODUCTION_AND_TEST_INPUTS_EXCEPT_SCOPED_GUARD_UNCHANGED')
        inverse(q,old)
        for module in tuple(sys.modules.values()):
            f=getattr(module,'__file__',None)
            if f:
                p=Path(f).absolute()
                if p.is_relative_to(c.ROOT/'tools/p09')and p.suffix=='.py':q.pin(p.relative_to(c.ROOT).as_posix())
        all_cases={'font_review_v1::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(TEST))};retained={'font_review_v1::'+n for n in previous.SOURCE};cases=all_cases-retained
        c.require(len(all_cases)==24 and len(cases)==20 and retained<all_cases and {'font_review_v1::'+n for n in previous.TRACKING}<=cases,'EXACT_FAILED3_AFFECTED13_NEW4_RETAINED_SOURCE4')
        scratch=c.ROOT/'target/p09-font-tracking-scratch-329';c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'FONT_TRACKING_RECOVERY_NEW_TEMP')
        scratch.mkdir();env=audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));print(json.dumps(dict(state='FONT_TRACKING_RECOVERY_PREFLIGHT',inputs=len(q.snapshots),recover_failed=3,affected_pass_cases=13,new_text_and_common_cases=4,retained_source_passes=4)),flush=True)
        harness.run_one('font_inherited_tracking_failed3_affected13_new4',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli','--test','scoped_font_product',
            '--message-format=short','--',*sorted(cases),'--test-threads=1'],cases,guard,env,row,observe_capture=previous.snapshot)
        tools.good_step(row['steps'][-1],cases);c.require(not any(scratch.iterdir()),'FONT_TRACKING_RECOVERY_TEMP_EMPTY');q.finish();guard.check(force=True)
        row.update(state='PASS_FONT_INHERITED_TRACKING_RECOVERED3_AFFECTED13_NEW4_RETAINED_SOURCE4_NOT_FULL_OPTIONS_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            executed_cases=20,retained_source_cases=4,distinct_review_cases=24,guard_checks_before_name_match_clone_or_writer=True,
            next_work='remaining_font_style_filter_preview_and_qualified_execution_storage')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'FONT_TRACKING_RECOVERY_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'FONT_TRACKING_RECOVERY_LOSSLESS_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','safe_error_variants','panic_locations','bounded_output_observation','cleanup')},'case_count':len(s.get('tests',[])),'failed_cases':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
