"""316: standalone fixture callback fix, production unchanged; first actual product24 execution."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_stored_font_components as previous
shared,c,a,tools,compact,harness,audit=previous.shared,previous.c,previous.a,previous.tools,previous.compact,previous.harness,previous.audit
OUTPUT='implementation/p09/evidence/p09-361-stored-font-recovery316.v1.json';DRIVER='tools/p09/run_stored_font_recovery.py'
RUN_ASSERT='    assert_eq!(name(&output,refs(&output)?[0].1)?,TARGET);\n'
TEXT_ASSERT='    let output=out.with_verified_bytes(&p,5,<[u8]>::to_vec)?;assert_eq!(name(&output,values[1].2.ok_or("selected text style")?)?,TARGET);Ok(())\n'

def inverse(q,old):
    text=q.text(previous.TEST)
    for marker in (RUN_ASSERT,TEXT_ASSERT):c.require(text.count(marker)==1,'ONE_STRONGER_ACTUAL_OUTPUT_FONT_ASSERTION_PER_AXIS')
    text=text.replace(RUN_ASSERT,'').replace(TEXT_ASSERT,'')
    text=text.replace('assert_eq!(values[2].2,Some(1));\n','assert_eq!(values[2].2,Some(1));Ok(())\n')
    text=text.replace('use revision_service as rev;','use revision_service::{self as rev,RevisionRepository as _};')
    text=text.replace('|bytes|serde_json::from_slice::<Value>(bytes)','serde_json::from_slice::<Value>')
    audit.inverse(text,old,'ONLY_TEST_CALLBACK_UNUSED_IMPORT_AND_TWO_STRONGER_OUTPUT_CHECKS_CHANGED')

def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'STORED_FONT_RECOVERY_IMMUTABLE');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_STORED_FONT_RECOVERY',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        Native011_executed=False,prior_Native_replayed=False,actual_DB_or_Hangul_or_COM_started=False,old20_old24_official249_replayed=False,
        common_operation_compiler_or_dispatcher_qualified=False,output_ingest_commit_or_publication=False,full_SEARCH024_product_or_native_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);failed=compact.unpack(q.json(previous.OUTPUT))
        c.require(q.snapshots[previous.OUTPUT]['sha256']=='64d2e528c343302c9b08ab9b2ad83cb8cd623a2550e64446c9b603b098918055'and failed['cleanup']and failed['steps'][0]['tests']==[],'EXACT315_COMPILE_FAILURE_NO_TEST_EXECUTION_RETAINED')
        old={p['path']:p for p in failed['source_pins']}
        for n in sorted(old):
            q.pin(n)
            if n!=previous.TEST:c.require(q.snapshots[n]==old[n],'ALL_FONT_PRODUCT_KERNEL_PARSERS_SERVICE_AND_OTHER_TESTS_UNCHANGED')
        q.pin(DRIVER);inverse(q,old[previous.TEST])
        for module in tuple(sys.modules.values()):
            f=getattr(module,'__file__',None)
            if f:
                p=Path(f).absolute()
                if p.is_relative_to(c.ROOT/'tools/p09')and p.suffix=='.py':q.pin(p.relative_to(c.ROOT).as_posix())
        cases=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(previous.TEST)));c.require(len(cases)==24,'SAME24_PREVIOUSLY_UNEXECUTED_CASES')
        scratch=c.ROOT/'target/p09-stored-font-scratch-316';c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'STORED_FONT_RECOVERY_NEW_TEMP')
        scratch.mkdir();env=audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch))
        print(json.dumps(dict(state='STORED_FONT_RECOVERY_PREFLIGHT',inputs=len(q.snapshots),first_actual_cases=24,old_suites_replayed=False)),flush=True)
        harness.run_one('stored_font_product24_callback_recovery',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli','--test','scoped_font_product',
            '--message-format=short','--','--test-threads=1'],cases,guard,env,row,observe_capture=previous.snapshot)
        tools.good_step(row['steps'][-1],cases);c.require(not any(scratch.iterdir()),'STORED_FONT_RECOVERY_TEMP_EMPTY');q.finish();guard.check(force=True)
        row.update(state='PASS_SCOPED_FONT_CURRENT_STORED_AND_STRICT_PRODUCT24_NOT_COMMON_EXECUTION_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_cases=24,product_code_changed_from315=False,next_work='source_edit_inventory_and_common_operation_compiler_and_dispatcher')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'STORED_FONT_RECOVERY_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'STORED_FONT_RECOVERY_LOSSLESS_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','tests','diagnostics','safe_error_variants','panic_locations','bounded_output_observation','cleanup')}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
