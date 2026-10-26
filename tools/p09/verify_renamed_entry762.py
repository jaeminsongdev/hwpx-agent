"""Bind retained760 once, test actual entry codec, keep original resource guard."""
import json,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_prepared_bookmark_native761 as entry
import resource_bundle714 as journal
from verify_prepared_bookmark631 import command
r=entry.r;m=entry.runtime
SELF='tools/p09/verify_renamed_entry762.py'
TEST='tools/p09/tests/test_renamed_entry761.py'
PRIOR='implementation/p09/evidence/p09-361-renamed-bookmark760-code001.v1.json'
FAILURE='implementation/p09/evidence/p09-361-prepared-bookmark755-native001.v1.json'

def require(ok,code):
    if not ok:raise ValueError('XREF_ENTRY762_'+code)

def main():
    require(sys.argv[1:]==['--code-only-no-native']and not(r.c.ROOT/entry.CODE).exists(),'MODE_AND_NEW_PROOF')
    r.tools.select_own_single_cpu();r.shared.host.configure_host_policy(r.c)
    guard=r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))()
    observer=q=shell=None;begin=time.monotonic()
    row=dict(state='FAILED762_RENAMED_ENTRY_CODEC',steps=[],actual_native_started=False,all_new_tests_passed=False,actual_READY_frames=0,actual_case_frames=0,old27_models_replayed=False,old_READY_denial_replayed=False,P09_complete=False)
    try:
        observer=journal.Attached(guard);guard.acquire();observer.phase('input_binding');q=r.a.AcceptanceReader(r.c.ROOT,guard.check)
        prior=entry.codec.unpack(q.json(PRIOR),guard.check)
        require(q.snapshots[PRIOR]['sha256']=='213634045eb75100c3ed92963a88ad4ef8c25bc5b6c46937185a3660a7da7972','EXACT_RETAINED760')
        require(prior['state']=='QUALIFIED760_RENAMED_EIGHT_SAVED_RENDER_CODE_READY_DENIAL_NOT_NATIVE'and prior['cleanup']is True
            and prior['all_new_tests_passed']is True and prior['fresh_inputs']==prior['final_fresh_hashes']==1314
            and prior['actual_native_started']is False and prior['actual_READY_frames']==1 and prior['actual_case_frames']==0,'RETAINED760_NOT_NATIVE')
        for pin in prior['source_pins']:require(q.pin(pin['path'])==pin,'RETAINED_RUNTIME_INPUTS_UNCHANGED')
        failure=entry.codec.unpack(q.json(FAILURE),guard.check)
        require(q.snapshots[FAILURE]['sha256']=='ec9326440f4915e60b83be1ee0b5966a6beaba824ffcd8956c25d0fc36036a45'
            and failure['error_code']=='XREF_LOSSLESS610_ENVELOPE'and failure['cleanup']is True and failure['native_claim_created']is False
            and failure['fresh_inputs']==1,'PRESERVE_FAILURE_BEFORE_NATIVE')
        row['preserved_failure']=q.snapshots[FAILURE]
        row['retained_code_and_ready_denial_source']=q.snapshots[PRIOR]
        row['ready_denial']=prior['ready_denial']
        paths=set(prior['execution_dependency_paths'])|m.prepared.loaded_dependencies(r.c.ROOT)|{entry.SELF,SELF,TEST}
        row['execution_dependency_paths']=sorted(paths)
        for path in sorted(paths):q.pin(path)
        row['prepared_files']=m.prepared.validate_prepared(q,entry.publisher.codec.unpack)
        native=m.base.session.startup;before=native.hwp_pids(guard.windows,guard.check);require(not before,'NO_HWP_BEFORE')
        shell_path=Path(m.base.candidate.original.SHELL);shell=r.a.AcceptanceReader(shell_path.parent,guard.check)
        row['shell_pin']=shell.pin(shell_path.name);require(row['shell_pin']==prior['shell_pin'],'SAME_NATIVE_SHELL')
        observer.phase('model_checks')
        value=command(guard,[sys.executable,'-B',str(r.c.ROOT/TEST)],r.audit.environment(),row,'actual_entry_codec_regressions12')
        require({k:value[k]for k in('run','errors','failures','skipped')}==dict(run=12,errors=0,failures=0,skipped=0)and value['actual_native_started']is False,'NEW_READER_REGRESSIONS_PASSED')
        # Exercise the public reader against the actual new envelope, before any
        # qualification/claim/Native path. Every referenced file is the held reader.
        observer.phase('readback')
        probe=dict(row,state=entry.STATE,cleanup=True,all_new_tests_passed=True,fresh_inputs=len(q.snapshots),final_fresh_hashes=len(q.snapshots),source_pins=list(q.snapshots.values()))
        packet=entry.codec.pack(probe,guard.check)
        def read(name):
            require(name==entry.CODE,'ONLY_NEW_CODE_PACKET');return packet
        view=NS(json=read,pin=q.pin,checkpoint=guard.check)
        pins,loaded_paths,decoded=entry.load_code(view)
        require(decoded==probe and loaded_paths==paths and len(pins)==len(q.snapshots),'ACTUAL_ENTRY_NEW_PROOF_WHOLE_READ_PATH')
        row['actual_entry_load_code_exercised']=True
        require(native.hwp_pids(guard.windows,guard.check)==before,'NO_NATIVE_PROCESS_CHANGE');m.absent()
        for path in (entry.OUTPUT,entry.CLAIM,entry.SCRATCH):require(not(r.c.ROOT/path).exists(),'NEW_CAPTURE_NOT_RUN')
        observer.phase('final_binary');shell.finish()
        observer.phase('final_source');q.finish()
        observer.phase('final_resource');guard.check(force=True)
        row.update(state=entry.STATE,all_new_tests_passed=True,new_code_models=12,Native_process_set_unchanged=True)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError,KeyboardInterrupt)as error:row.update(**m.io.safe_failure(error))
    finally:
        guard.close();observer_cleanup=True if observer is None else observer.close()
        if observer is not None:row['phase_resources']=observer.packet()
        row.update(cleanup=guard.cleanup and observer_cleanup and all(s['cleanup']for s in row['steps']),source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,shell_final_fresh_hashes=0 if shell is None else shell.final_fresh_hashes,elapsed_seconds=round(time.monotonic()-begin,3),resource_samples=len(guard.samples),system_CPU_max=max((s['system_cpu_percent']for s in guard.samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in guard.samples),default=None))
        normalized,_=entry.publisher.retention.retain(r.c.ROOT,'implementation/p09/evidence/private/p09-361-renamed-entry762-code001-forensic',row)
        pin=entry.publish(entry.CODE,normalized)
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','cleanup','fresh_inputs','final_fresh_hashes','resource_samples','system_CPU_max','available_RAM_min_percent','elapsed_seconds')},'steps':[{k:s.get(k)for k in('stage','exit_code','result')}for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state']==entry.STATE and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
