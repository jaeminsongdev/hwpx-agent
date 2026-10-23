"""328: explicit closed acceptance witnesses before any production fix; original failures stay FAILED."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_font_review_fixture_recovery as previous
shared,c,a,tools,compact,harness,audit=previous.shared,previous.c,previous.a,previous.tools,previous.compact,previous.harness,previous.audit
OUTPUT='implementation/p09/evidence/p09-361-font-tracking-diagnostic328.v1.json';DRIVER='tools/p09/run_font_tracking_diagnostic.py'
TRACKING={'ancestor_paragraph_tracking_marker_protects_selected_memo_payload','ancestor_run_tracking_marker_cannot_be_bypassed_by_selecting_hidden_payload','paragraph_tracking_marker_protects_selected_ordinary_text'}
SOURCE={'invalid_paragraph_lock_attributes_reject_before_hidden_selection','invalid_memo_paragraph_lock_attributes_reject_at_import','unselected_invalid_paragraph_lock_is_still_source_import_error','nested_date_inside_memo_is_rejected_by_existing_source_admission'}

def snapshot(capture,expected):
    result=previous.snapshot(capture,expected)
    with capture.lock:raw=bytes(capture.buffers['stdout']).decode('utf-8','replace')
    result['unexpected_tracking_candidate_acceptance_witnesses']=raw.count('FONT_TRACKING_UNEXPECTED_ACCEPTANCE');return result

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'FONT_TRACKING_DIAGNOSTIC_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_FONT_TRACKING_DIAGNOSTIC',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        production_changed=False,Native011_executed=False,actual_DB_or_Hangul_or_COM_started=False,official249_replayed=False,previous56_replayed=False,output_ingest_commit_or_publication=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);failed=compact.unpack(q.json(previous.OUTPUT))
        c.require(q.snapshots[previous.OUTPUT]['sha256']=='7fad485b01e74369225a7b1afb32561674193768959602545a8d6d6bdf72bb4e'and failed['cleanup']and len(failed['steps'][0]['tests'])==20
            and sum(s=='ok'for _,s in failed['steps'][0]['tests'])==14,'EXACT327_FOURTEEN_PASS_SIX_FAILURES_PRESERVED')
        old={p['path']:p for p in failed['source_pins']}
        for n in sorted(set(old)|{DRIVER}):
            q.pin(n)
            if n in old and n!=previous.previous.TEST:c.require(q.snapshots[n]==old[n],'ALL_PRODUCTION_GUARDS_AND_OTHER_INPUTS_UNCHANGED_BEFORE_DIAGNOSIS')
        text=q.text(previous.previous.TEST);c.require(text.count('assert!(!result.is_ok(),"FONT_TRACKING_UNEXPECTED_ACCEPTANCE")')==1,'ONE_EXPLICIT_REDACTED_CANDIDATE_ACCEPTANCE_WITNESS')
        identities={'font_review_v1::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',text)};cases={'font_review_v1::'+n for n in TRACKING|SOURCE};c.require(cases<=identities and len(cases)==7,'EXACT_THREE_TRACKING_AND_FOUR_SOURCE_ADMISSION_DIAGNOSTICS')
        for module in tuple(sys.modules.values()):
            f=getattr(module,'__file__',None)
            if f:
                p=Path(f).absolute()
                if p.is_relative_to(c.ROOT/'tools/p09')and p.suffix=='.py':q.pin(p.relative_to(c.ROOT).as_posix())
        scratch=c.ROOT/'target/p09-font-tracking-scratch-328';c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'FONT_TRACKING_NEW_TEMP')
        scratch.mkdir();env=audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));print(json.dumps(dict(state='FONT_TRACKING_DIAGNOSTIC_PREFLIGHT',inputs=len(q.snapshots),selected=7,production_changed=False)),flush=True)
        harness.run_one('font_tracking_explicit_acceptance_and_source_admission7',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli','--test','scoped_font_product',
            '--message-format=short','--',*sorted(cases),'--test-threads=1'],cases,guard,env,row,observe_capture=snapshot)
        # An unexpected all-pass needs review; this run is not a product acceptance certificate.
        q.finish();row.update(state='DIAGNOSTIC_NO_EXPECTED_ACCEPTANCE_FAILURE_OBSERVED',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'FONT_TRACKING_DIAGNOSTIC_FAILURE_NO_RAW_VALUES')
        if row['steps']:
            step=row['steps'][-1];passed={n for n,s in step.get('tests',[])if s=='ok'};failed_names={n for n,s in step.get('tests',[])if s!='ok'}
            if passed=={'font_review_v1::'+n for n in SOURCE}and failed_names=={'font_review_v1::'+n for n in TRACKING}and step.get('bounded_output_observation',{}).get('unexpected_tracking_candidate_acceptance_witnesses')==3:
                q.finish();guard.check(force=True);row.update(state='FAILED_FONT_ANCESTOR_TRACKING_THREE_UNEXPECTED_ACCEPTANCES_CONFIRMED',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
                    source_admission_passes=4,unexpected_tracking_acceptances=3,failed_test_statuses_preserved=True,next_work='inherit_observed_run_and_paragraph_tracking_flags_before_any_font_edit')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'FONT_TRACKING_LOSSLESS_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent','unexpected_tracking_acceptances','source_admission_passes')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','safe_error_variants','panic_locations','bounded_output_observation','cleanup')},'case_count':len(s.get('tests',[])),'failed_cases':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 2
if __name__=='__main__':raise SystemExit(main())
