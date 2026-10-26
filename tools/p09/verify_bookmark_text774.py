"""Fix only the failed768 text options; preserve consumed code/results and guards."""
import json,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_prepared_bookmark_native773 as entry
import prepared_bookmark_native768 as previous_runtime
import resource_bundle714 as journal
from cursor_model_capture771 import command
from verify_prepared_bookmark631 import ReadyDenial
r=entry.r;m=entry.runtime
SELF='tools/p09/verify_bookmark_text774.py'
TEST='tools/p09/tests/test_bookmark_text775.py'
PS_TEST='implementation/p09/tools/test-bookmark-cursor775.ps1'
SYNTAX='implementation/p09/tools/inspect-bookmark-cursor774-syntax.ps1'
QUERY='implementation/p09/tools/bookmark-target-cursor773.ps1'
PRIOR='implementation/p09/evidence/p09-361-bookmark-cursor772-code001.v1.json'
FAILED='implementation/p09/evidence/p09-361-prepared-bookmark768-native001.v1.json'

def require(ok,code):
    if not ok:raise ValueError('XREF_TEXT774_'+code)

def main():
    require(sys.argv[1:]==['--code-only-no-native']and not(r.c.ROOT/entry.CODE).exists(),'MODE_NEW_PROOF')
    r.tools.select_own_single_cpu();r.shared.host.configure_host_policy(r.c)
    guard=r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))()
    q=shell=observer=None;start=time.monotonic()
    row=dict(state='FAILED774_CURSOR_TEXT_CODE',steps=[],actual_native_started=False,all_new_tests_passed=False,consumed768_or_product766_replayed=False,old_unaffected_models_replayed=False,P09_complete=False)
    try:
        observer=journal.Attached(guard);guard.acquire();observer.phase('input_binding');q=r.a.AcceptanceReader(r.c.ROOT,guard.check)
        for name in(SELF,TEST,PS_TEST,SYNTAX,QUERY,entry.SELF,m.TARGET,m.PORTS,m.CHANNEL):q.pin(name)
        old=entry.codec.unpack(q.json(PRIOR),guard.check)
        require(q.snapshots[PRIOR]['sha256']=='e031368b1ead123659e19852a5637a2a3df763df714b33f9c883c2059bc73898'
            and old['cleanup']is True and old['all_new_tests_passed']is True and old['fresh_inputs']==old['final_fresh_hashes']==1408,'EXACT_772_CODE_BASELINE')
        shell_path=Path(m.base.candidate.original.SHELL);shell=r.a.AcceptanceReader(shell_path.parent,guard.check)
        row['shell_pin']=shell.pin(shell_path.name);require(row['shell_pin']==old['shell_pin'],'UNCHANGED_FIXED_SHELL')
        observer.phase('model_checks')
        early=command(guard,[str(shell_path),'-NoLogo','-NoProfile','-NonInteractive','-File',str(r.c.ROOT/SYNTAX),'-SyntaxOnly'],r.audit.environment(),row,'early_syntax5_before_full_input_binding')
        require({k:early[k]for k in('run','errors','failures','skipped')}==dict(run=5,errors=0,failures=0,skipped=0)and early['actual_native_started']is False,'EARLY_SYNTAX')
        observer.phase('input_binding')
        failed=entry.codec.unpack(q.json(FAILED),guard.check)
        require(q.snapshots[FAILED]['sha256']=='08cd85dacfa68a15aef48829ec5f51ac9b2976ada09754262f1c02ede10b8e3a'
            and failed['cleanup']is True and failed['fixed_eight_executed']is False and failed['native_claim_created']is True
            and failed['capture_worker']['result']['completed_callback_cases']==0
            and failed['capture_worker']['result']['case_failure']==dict(case_index=1,phase='initial_image',error_code='P09_XREF_BIND_CURSOR768_WHOLE_TEXT_BEFORE'),'FAILED768_PRESERVED_ZERO_COMPLETED_CASES')
        row['preserved768_failure']=q.snapshots[FAILED]
        row['failed768_resource_summary']=dict(samples=len(failed['resource_samples']),system_CPU_max=max(v['system_cpu_percent']for v in failed['resource_samples']),available_RAM_min_percent=min(v['available_ram_percent']for v in failed['resource_samples']),cleanup=True)
        for pin in old['source_pins']:require(q.pin(pin['path'])==pin,'CONSUMED_CODE_AND_INPUTS_IMMUTABLE')
        for oldpath,newpath in((previous_runtime.SELF,m.SELF),(previous_runtime.PORTS,m.PORTS),(previous_runtime.CHANNEL,m.CHANNEL),('tools/p09/prepared_bookmark768_sections.py','tools/p09/prepared_bookmark773_sections.py')):
            require(q.text(newpath)==q.text(oldpath).replace('768','773'),'OWNER_GUARD_CHANNEL_AND_RESOURCE_NAMESPACE_ONLY')
        row['retained_unaffected772_contracts']=dict(source=q.snapshots[PRIOR],models_replayed=False,original_guard_and_lifecycle_preserved=True)
        row['prepared_files']=m.prepared.validate_prepared(q)
        paths=m.SOURCES|m.prepared.loaded_dependencies(r.c.ROOT)|{entry.SELF,SELF,TEST,PS_TEST,SYNTAX,m.prepared.PREPARED,m.prepared.INPUTS,m.prepared.PROOF,m.prepared.NATIVE,m.prepared.SOURCE_PIN['path'],'tools/p09/prepared_bookmark690_receipt.py'}
        paths|={pin['path']for case in row['prepared_files']['cases']for pin in(case['output'],case['reopened'])}
        paths={path for path in paths if not path.startswith('crates/')and'/source-archive/'not in path}
        row['execution_dependency_paths']=sorted(paths)
        for name in sorted(paths):q.pin(name)
        native=m.base.session.startup;before=native.hwp_pids(guard.windows,guard.check);require(not before,'NO_HWP_BEFORE')
        observer.phase('model_checks')
        for args,count,label in(([sys.executable,'-B',str(r.c.ROOT/TEST)],8,'new_text_diagnostics_evidence_and_XZ_entry_models8'),([str(shell_path),'-NoLogo','-NoProfile','-NonInteractive','-File',str(r.c.ROOT/PS_TEST),'-ModelsOnly'],13,'affected_text_call_and_failure_boundary_models13')):
            result=command(guard,args,r.audit.environment(),row,label)
            require({k:result[k]for k in('run','errors','failures','skipped')}==dict(run=count,errors=0,failures=0,skipped=0)and result['actual_native_started']is False,'TEXT_OPTION_MODELS')
        observer.phase('readback');worker=m.Worker(guard);handler=ReadyDenial(worker,lambda:shell.fresh_pin(shell_path.name));attempt={};row['ready_denial']=attempt
        value=m.io.run(guard,worker,q,worker.start_fixed_worker,handler,'hwpx-agent.private.crossref-fixed-worker-result/v1',r.audit.environment(),lambda v:None,attempt)
        require(attempt['exit_code']==2 and attempt['cleanup']is True and attempt['requests']==1 and handler.calls==1 and value['planned_cases']==8
            and value['completed_callback_cases']==0 and value['retained_live_or_uncertain_owners']==0,'ACTUAL_READY_DENIAL_ZERO_NATIVE')
        probe=dict(row,state=entry.STATE,cleanup=True,all_new_tests_passed=True,fresh_inputs=len(q.snapshots),final_fresh_hashes=len(q.snapshots),source_pins=list(q.snapshots.values()))
        packet=entry.codec.pack(probe,guard.check)
        def read(name):require(name==entry.CODE,'CURRENT_NEW_CODE_ONLY');return packet
        entry.load_code(NS(json=read,pin=q.pin,checkpoint=guard.check))
        require(native.hwp_pids(guard.windows,guard.check)==before,'NO_NATIVE_PROCESS_CHANGE');m.absent()
        observer.phase('final_binary');shell.finish()
        observer.phase('final_source');q.finish()
        observer.phase('final_resource');guard.check(force=True)
        row.update(state=entry.STATE,all_new_tests_passed=True,current_code_models=26,actual_READY_frames=1,actual_case_frames=0,actual_entry_load_code_exercised=True,Native_process_set_unchanged=True)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError,KeyboardInterrupt)as error:row.update(**m.io.safe_failure(error))
    finally:
        guard.close();observer_cleanup=True if observer is None else observer.close()
        if observer is not None:row['phase_resources']=observer.packet()
        row.update(cleanup=guard.cleanup and observer_cleanup and all(s['cleanup']for s in row['steps'])and row.get('ready_denial',{}).get('cleanup',True),source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,shell_final_fresh_hashes=0 if shell is None else shell.final_fresh_hashes,resource_samples=len(guard.samples),elapsed_seconds=round(time.monotonic()-start,3),system_CPU_max=max((s['system_cpu_percent']for s in guard.samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in guard.samples),default=None))
        value,_=entry.publisher.retention.retain(r.c.ROOT,'implementation/p09/evidence/private/p09-361-bookmark-cursor774-code001-forensic',row);pin=entry.publish(entry.CODE,value)
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','cleanup','fresh_inputs','final_fresh_hashes','resource_samples','system_CPU_max','available_RAM_min_percent','elapsed_seconds')},'steps':[{k:s.get(k)for k in('stage','exit_code','result')}for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state']==entry.STATE and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
