"""374: retain373's25 PASS and immutable failure; fix invalid synthetic tab and unused import, run only affected1."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import run_personal_info_detection as base
shared,c,a,tools,compact,harness,audit=r.shared,r.c,r.a,r.tools,r.compact,r.harness,r.audit
OUTPUT='implementation/p09/evidence/p09-361-personal-info-detection-recovery374.v1.json';DRIVER='tools/p09/run_personal_info_detection_recovery.py'
CASE='detection::control_and_paragraph_barriers_are_not_joined_into_private_candidates'
OLD_TAB="BEG<hp:tab/>IN BEG<hp:lineBreak/>IN";NEW_TAB="BEG<hp:tab width='1' leader='0' type='0'> </hp:tab>IN BEG<hp:lineBreak/>IN"

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'DETECTION_RECOVERY_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_PERSONAL_INFO_DETECTION_RECOVERY',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        Native011_executed=False,prior_Native_replayed=False,actual_DB_or_Hangul_or_COM_started=False,official249_replayed=False,old_suites_replayed=False,
        source_document_mutation=False,output_ingest_commit_or_publication=False,whole_package_personal_data_removed=False,native_format_policy_or_execution_qualified=False)
    try:
        guard.acquire();scratch=c.ROOT/'target/p09-personal-info-detection-scratch-374';c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'DETECTION_RECOVERY_UNIQUE_TEMP')
        q=a.AcceptanceReader(c.ROOT,guard.check);failed=compact.unpack(q.json(base.OUTPUT))
        c.require(q.snapshots[base.OUTPUT]['sha256']=='7fb46d31b2255f7b90d46bdcefc0235e6b470c58a20ed35d43c5870a521298e2'and failed['cleanup']
            and failed['fresh_inputs']==failed['final_fresh_hashes']==873 and len(failed['steps'])==1,'EXACT373_FAILED_SOURCE_BODY_ADMISSION_AND_FINAL_FRESH_RETAINED')
        step=failed['steps'][0];c.require(step['exit_code']==101 and len(step['tests'])==26 and [(n,v)for n,v in step['tests']if v!='ok']==[(CASE,'FAILED')]
            and step['safe_error_variants']==['Body'],'EXACT373_ONLY_ONE_INVALID_SYNTHETIC_TAB_FAILURE_RETAINED25_PASS')
        pins={p['path']:p for p in failed['source_pins']}
        for path in sorted(r.closure.inventory(guard.check)|set(pins)|{DRIVER}):
            q.pin(path)
            if path in pins and path not in {base.CORE,base.TEST}:c.require(q.snapshots[path]==pins[path],'ALL_OTHER_WRITERS_PROTECTION_PRODUCT_TESTS_RUNTIME_AND_GUARDS_UNCHANGED')
            elif path not in pins:c.require(path==DRIVER,'ONLY_RECOVERY_DRIVER_ADDED')
        core=q.text(base.CORE);c.require(core.count('SourceReviewTextPolicy,selector::')==1,'ONE_UNUSED_IMPORT_CORRECTION')
        audit.inverse(core.replace('SourceReviewTextPolicy,selector::','SourceReviewTextPolicy,SourceTextRegion,selector::'),pins[base.CORE],'ONLY_UNUSED_IMPORT_REMOVED_NO_DETECTION_ALGORITHM_OR_OUTPUT_CHANGE')
        text=q.text(base.TEST);c.require(text.count(NEW_TAB)==1 and OLD_TAB not in text,'ONE_VALID_TAB_FIXTURE_WITH_REQUIRED_ATTRIBUTES')
        audit.inverse(text.replace(NEW_TAB,OLD_TAB),pins[base.TEST],'ONLY_INVALID_TAB_FIXTURE_REPAIRED_ALL25_PASSED_TEST_BODIES_UNCHANGED')
        original=compact.unpack(q.json(base.BASE));base.inverse(q,{p['path']:p for p in original['source_pins']})
        for module in tuple(sys.modules.values()):
            f=getattr(module,'__file__',None)
            if f:
                p=Path(f).absolute()
                if p.is_relative_to(c.ROOT/'tools/p09')and p.suffix=='.py':q.pin(p.relative_to(c.ROOT).as_posix())
        scratch.mkdir();env=audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));print(json.dumps(dict(state='DETECTION_RECOVERY_PREFLIGHT',inputs=len(q.snapshots),affected_cases=1,retained_cases=25)),flush=True)
        harness.run_one('personal_info_valid_control_barrier_affected1',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package','--test','personal_info_mask','--message-format=short','--',CASE,'--exact','--test-threads=1'],{CASE},guard,env,row,observe_capture=r.snapshot)
        tools.good_step(row['steps'][-1],{CASE});c.require(row['steps'][-1]['diagnostics']==[],'REPAIRED_TAB_BARRIER_AND_REMOVED_IMPORT_NO_WARNINGS')
        c.require(not any(scratch.iterdir()),'DETECTION_RECOVERY_TEMP_EMPTY');q.finish();guard.check(force=True)
        row.update(state='PASS_SOURCE_FORMAT_DETECTION_REPAIRED1_RETAINED25_CURRENT26_NOT_NATIVE_DEFAULTS_STORED_PRODUCT_SANITIZATION_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,affected_cases=1,retained_cases=25,new_detection_cases=23,affected_original_cases=3,current_distinct_cases=26,
            next_work='current_stored_access_and_strict_read_only_product_then_native_format_policy_execution_and_target_contract')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'DETECTION_RECOVERY_FAILURE_NO_RAW_VALUES')
        if q is not None:
            try:q.finish();row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
            except(ValueError,OSError,KeyError,TypeError,AttributeError):row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'DETECTION_RECOVERY_LOSSLESS_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','safe_error_variants','panic_locations','cleanup')},'case_count':len(s.get('tests',[])),
            'failed_cases':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
