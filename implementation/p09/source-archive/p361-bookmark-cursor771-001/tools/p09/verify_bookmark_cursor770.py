"""New direct-cursor query models and actual READY denial; no Native starts."""
import json,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_prepared_bookmark_native768 as entry
import resource_bundle714 as journal
from verify_prepared_bookmark631 import ReadyDenial
from cursor_model_capture771 import command
r=entry.r;m=entry.runtime
SELF='tools/p09/verify_bookmark_cursor770.py'
TEST='tools/p09/tests/test_bookmark_cursor769.py'
PS_TEST='implementation/p09/tools/test-bookmark-cursor769.ps1'
PRIOR='implementation/p09/evidence/p09-361-renamed-bookmark762-code001.v1.json'

def require(ok,code):
    if not ok:raise ValueError('XREF_CURSOR771_'+code)

def main():
    require(sys.argv[1:]==['--code-only-no-native']and not(r.c.ROOT/entry.CODE).exists(),'MODE_NEW_PROOF')
    r.tools.select_own_single_cpu();r.shared.host.configure_host_policy(r.c)
    guard=r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))()
    q=shell=observer=None;begin=time.monotonic()
    row=dict(state='FAILED771_BOOKMARK_CURSOR_CODE',steps=[],actual_native_started=False,all_new_tests_passed=False,Native761_or_product766_replayed=False,retained_python15_replayed=False,failed770_promoted_to_whole_success=False,P09_complete=False)
    try:
        observer=journal.Attached(guard);guard.acquire();observer.phase('input_binding');q=r.a.AcceptanceReader(r.c.ROOT,guard.check)
        prepared=m.prepared.validate_prepared(q);row['prepared_files']=prepared
        previous=entry.codec.unpack(q.json(PRIOR),guard.check)
        require(q.snapshots[PRIOR]['sha256']=='4912f86a4fb67f4716753540c4a52d4272ec448a58798b5c93cef666f2cc4873'
            and previous['cleanup']is True and previous['state']=='QUALIFIED762_RENAMED_ENTRY_CODEC_RETAINED760_NOT_NATIVE'
            and previous['fresh_inputs']==previous['final_fresh_hashes']==1319,'RETAINED_READINESS_LIFECYCLE_CODE_NOT_REPLAY')
        for pin in previous['source_pins']:require(q.pin(pin['path'])==pin,'UNCHANGED_PREVIOUS_GUARD_AND_EXECUTION_INPUTS')
        product=entry.codec.unpack(q.json(m.prepared.PROOF),guard.check)
        for pin in product['source_pins']:require(q.pin(pin['path'])==pin,'CURRENT_PRODUCT766_INPUTS_NO_REPLAY')
        failure='implementation/p09/evidence/p09-361-bookmark-cursor770-code001.v1.json'
        failed=entry.codec.unpack(q.json(failure),guard.check)
        require(q.snapshots[failure]['sha256']=='681eda12da533fb4188650036fc05e306d68f7032590a76f6165da442c83d0a5'
            and failed['cleanup']is True and failed['error_type']=='JSONDecodeError'and 'ready_denial'not in failed
            and failed['steps'][0]['exit_code']==0 and failed['steps'][0]['result']==dict(run=15,errors=0,failures=0,skipped=0,actual_native_started=False,failed_test_ids=[]),'RETAIN_PYTHON15_ONLY_NOT_FAILED_BUNDLE')
        archive='implementation/p09/source-archive/p361-bookmark-cursor770-001/'
        changed={entry.SELF,SELF,PS_TEST,m.PORTS,m.TARGET}
        for pin in failed['source_pins']:
            name=archive+pin['path']if pin['path']in changed else pin['path'];current=q.pin(name)
            require((current['bytes'],current['sha256'])==(pin['bytes'],pin['sha256']),'EXACT_FAILED_INPUTS_AND_CHANGED_SOURCE_ARCHIVES')
        expected=q.text(archive+entry.SELF).replace('bookmark-cursor770-code001','bookmark-cursor771-code001').replace('QUALIFIED770_BOOKMARK_CURSOR_CODE_AND_READY_DENIAL_NOT_NATIVE',entry.STATE)
        require(q.text(entry.SELF)==expected,'ONLY_CODE_RECEIPT_NAMESPACE_CHANGED_KEEP_PYTHON15')
        oldports=q.text(archive+m.PORTS)
        marker="                [void](New-Item -ItemType Directory -Path $State.run);$State.slot_created=$true\n"
        parent="                $parent=Get-Item -LiteralPath (Split-Path -Parent $State.run) -Force\n                while ($null -ne $parent) {\n                    Assert-P09XrefBinding ($parent -is [IO.DirectoryInfo] -and ($parent.Attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0) 'PREPARED_OUTPUT_PARENT'\n                    $parent=$parent.Parent\n                }\n"
        require(oldports.count(marker)==1 and q.text(m.PORTS)==oldports.replace(marker,parent+marker),'ONLY_ORIGINAL_OUTPUT_ANCESTOR_GUARD_ADDED')
        oldworker=q.text(archive+m.TARGET)
        old="            $case.output.sha256 -cmatch '^[0-9a-f]{64}$') 'PREPARED_FIXED_CANDIDATE'"
        new="            $case.output.sha256 -cmatch '^[0-9a-f]{64}$' -and\n            $case.reopened.path -ceq ('implementation/p09/evidence/private/p09-361-prepared-bookmark755-native001-c'+$sourceIndex.ToString('00')+'/reopened.hwpx') -and\n            $case.reopened.sha256 -cmatch '^[0-9a-f]{64}$') 'PREPARED_FIXED_CANDIDATE'"
        require(oldworker.count(old)==1 and q.text(m.TARGET)==oldworker.replace(old,new),'ONLY_SECOND_SOURCE_PATH_GUARD_ADDED')
        row['retained_python15_observations']=dict(receipt=q.snapshots[failure],tests=failed['steps'][0]['result'],whole_failed_bundle_promoted=False,tests_replayed=False)
        paths=m.SOURCES|m.prepared.loaded_dependencies(r.c.ROOT)|{entry.SELF,SELF,TEST,PS_TEST,m.prepared.PREPARED,m.prepared.INPUTS,m.prepared.PROOF,m.prepared.NATIVE,m.prepared.SOURCE_PIN['path'],'tools/p09/prepared_bookmark690_receipt.py'}
        paths|={pin['path']for case in prepared['cases']for pin in(case['output'],case['reopened'])}
        # Historical Rust inputs bind the bundle only; no Rust runs in Native768.
        paths={path for path in paths if not path.startswith('crates/')}
        row['execution_dependency_paths']=sorted(paths)
        for path in sorted(paths):q.pin(path)
        native=m.base.session.startup;before=native.hwp_pids(guard.windows,guard.check);require(not before,'NO_HWP_BEFORE')
        shell_path=Path(m.base.candidate.original.SHELL);shell=r.a.AcceptanceReader(shell_path.parent,guard.check)
        row['shell_pin']=shell.pin(shell_path.name);require(row['shell_pin']==previous['shell_pin'],'SAME_NATIVE_SHELL')
        observer.phase('model_checks')
        for args,count,label in(([str(shell_path),'-NoLogo','-NoProfile','-NonInteractive','-File',str(r.c.ROOT/PS_TEST),'-ModelsOnly'],15,'typed_goto_selection_structured_transport_and_real_junction_denial15'),):
            value=command(guard,args,r.audit.environment(),row,label)
            require({k:value[k]for k in('run','errors','failures','skipped')}==dict(run=count,errors=0,failures=0,skipped=0)and value['actual_native_started']is False,'NEW_CURSOR_MODELS_PASSED')
        observer.phase('readback');worker=m.Worker(guard);handler=ReadyDenial(worker,lambda:shell.fresh_pin(shell_path.name));attempt={};row['ready_denial']=attempt
        value=m.io.run(guard,worker,q,worker.start_fixed_worker,handler,'hwpx-agent.private.crossref-fixed-worker-result/v1',r.audit.environment(),lambda v:None,attempt)
        require(attempt['exit_code']==2 and attempt['cleanup']is True and attempt['requests']==1 and handler.calls==1
            and value['planned_cases']==8 and value['completed_callback_cases']==0 and value['retained_live_or_uncertain_owners']==0,'REAL_READY_DENIAL_ZERO_NATIVE')
        # Exercise entry.load_code itself with the new XZ packet, not only the codec.
        probe=dict(row,state=entry.STATE,cleanup=True,all_new_tests_passed=True,fresh_inputs=len(q.snapshots),final_fresh_hashes=len(q.snapshots),source_pins=list(q.snapshots.values()))
        packet=entry.codec.pack(probe,guard.check)
        def read(name):require(name==entry.CODE,'ONLY_NEW_CODE_PACKET');return packet
        entry.load_code(NS(json=read,pin=q.pin,checkpoint=guard.check))
        require(native.hwp_pids(guard.windows,guard.check)==before,'NO_NATIVE_PROCESS_CHANGE');m.absent()
        observer.phase('final_binary');shell.finish()
        observer.phase('final_source');q.finish()
        observer.phase('final_resource');guard.check(force=True)
        row.update(state=entry.STATE,all_new_tests_passed=True,current_code_models=15,retained_python_observations=15,actual_READY_frames=1,actual_case_frames=0,actual_entry_load_code_exercised=True,Native_process_set_unchanged=True)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError,KeyboardInterrupt)as error:row.update(**m.io.safe_failure(error))
    finally:
        guard.close();observer_cleanup=True if observer is None else observer.close()
        if observer is not None:row['phase_resources']=observer.packet()
        row.update(cleanup=guard.cleanup and observer_cleanup and all(s['cleanup']for s in row['steps'])and row.get('ready_denial',{}).get('cleanup',True),source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,shell_final_fresh_hashes=0 if shell is None else shell.final_fresh_hashes,elapsed_seconds=round(time.monotonic()-begin,3),resource_samples=len(guard.samples),system_CPU_max=max((s['system_cpu_percent']for s in guard.samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in guard.samples),default=None))
        normalized,_=entry.publisher.retention.retain(r.c.ROOT,'implementation/p09/evidence/private/p09-361-bookmark-cursor771-code001-forensic',row);pin=entry.publish(entry.CODE,normalized)
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','cleanup','fresh_inputs','final_fresh_hashes','resource_samples','system_CPU_max','available_RAM_min_percent','elapsed_seconds')},'steps':[{k:s.get(k)for k in('stage','exit_code','result')}for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state']==entry.STATE and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
