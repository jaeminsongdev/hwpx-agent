"""Close fixed008 preparation with a real READY denial, never Native/session authority.

The production entry is not called. The unchanged Native guard and original
worker transport are used, but READY is unconditionally denied before cases.
Passed code/model bodies are retained with fresh inputs, not executed again.
"""
import ast,json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
import named_style_verification_runtime as r
import run_external_crossref_fixed_batch008 as entry
import crossref_capture008_worker as fixed
import crossref_external_host_inspection as historic
import crossref_python_current555 as profile
import crossref_runtime004_admission as admission
import crossref_session_qualification as session
import crossref_native_worker_io as io
from run_crossref_fixed_worker_denial import DenialHandler

SELF='tools/p09/qualify_capture008_ready597.py'
AUDIT='implementation/p09/evidence/p09-361-capture008-ready597-audit001.v1.json'
SCRATCH='target/p09-capture008-ready597-scratch'
CODE_SHA='09162bfc8d056c3d245ac1ff51f15e1d5a9c5b045cc7986078052f49d9530a04'
PREFLIGHT_SHA='975c5882bc881377c701e96ca20cc1d3aa4ad1842bec0d0a9d0eca09cbc520f5'
SHELL=Path(fixed.original.prior.original.SHELL)


def unused_namespace():
    fixed.namespace.require_absent(r.c.ROOT)
    for name in(entry.NAMES['claim'],entry.NAMES['output'],entry.NAMES['scratch'],entry.publication.SPOOL):
        path=r.c.ROOT/name
        r.c.require(not(path.exists()or path.is_symlink()or path.is_junction()),'P597_NATIVE008_NAMESPACE_UNUSED')


def main():
    c,a,shared=r.c,r.a,r.shared
    c.require(sys.argv[1:]==['--ready-denial-only'],'P597_CLOSED_NON_NATIVE_SCOPE')
    c.require(Path(sys.executable)==profile.fixed.PYTHON,'P597_FIXED_CURRENT_RUNTIME')
    for name in(AUDIT,entry.NAMES['ready']):
        path=c.ROOT/name;c.require(not(path.exists()or path.is_symlink()or path.is_junction()),'P597_IMMUTABLE_READINESS')
    unused_namespace()
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    # Do not use the preparation-role guard: the original worker requires this exact Native guard.
    guard=shared.baseline.guard_type(shared.final.guard_type(a.Guard))()
    q=runtime_image=shell=native=None;passed=False;started=time.monotonic()
    row=dict(state='FAILED_CAPTURE008_ENTRY_RUNTIME_PREPARATION',generation=8,steps=[],own_cpu_selection=selection,
        actual_Hancom_ROT_COM_or_native_started=False,fixed_eight_executed=False,native_startup_qualified=False,
        actual008_entry_executed=False,new008_execution_authorized=False,prior_runs_replayed=False,
        accepted_count_delta=0,P09_gate='OPEN',P10_started=False,Native011_executed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        proof=entry.layout.unpack(q.json(entry.NAMES['code']))
        c.require(q.snapshots[entry.NAMES['code']]['sha256']==CODE_SHA and proof['state']==entry.CODE_STATE
            and proof['generation']==8 and proof['cleanup']is True and proof['fresh_inputs']==proof['final_fresh_hashes']==len(proof['source_pins'])
            and proof['contracts']==dict(run=50,errors=0,failures=0,skipped=0) and proof['real_windows_models']==30,'P597_CURRENT_CODE596_WITHOUT_MODEL_REPLAY')
        pins={p['path']:p for p in proof['source_pins']};paths=proof['entry_dependency_paths']
        c.require(len(pins)==len(proof['source_pins']) and len(paths)==len(set(paths)) and set(paths)<=set(pins)
            and entry.runtime.CASE_PATHS<=set(paths) and entry.SELF in paths,'P597_COMPLETE_ENTRY_SOURCE_CLOSURE')
        for name,pin in pins.items():c.require(q.pin(name)==pin,'P597_VERIFIED_CODE_INPUT_UNCHANGED')
        preflight=entry.layout.unpack(q.json(entry.NAMES['preflight']));pre=preflight['prerequisites']
        c.require(q.snapshots[entry.NAMES['preflight']]['sha256']==PREFLIGHT_SHA
            and preflight['state']=='DENIED_CURRENT_EXTERNAL_ENTRY_PREREQUISITES_NO_NATIVE_OR_CLAIM'
            and preflight['cleanup']is True and preflight['fresh_inputs']==preflight['final_fresh_hashes']==len(preflight['source_pins'])
            and preflight['native_claim_created']is False and preflight['fixed_eight_executed']is False
            and pre['failed_prerequisites']==['caller_lifecycle_native_safe']
            and pre['closed_errors']==dict(caller_lifecycle_native_safe='XREF_NATIVE_STARTUP_PARENT_LIFECYCLE_NOT_NATIVE_SAFE')
            and pre['preexisting_hwp_processes']==0 and pre['process_created']is False and pre['COM_activated']is False
            and pre['document_opened']is False and pre['permission_dialog_requested']is False,
            'P597_ACTUAL_PREFLIGHT_EXPECTED_PARENT_DENIAL_NOT_NATIVE_QUALIFICATION')
        for pin in preflight['source_pins']:c.require(q.pin(pin['path'])==pin,'P597_PREFLIGHT_INPUTS_STILL_CURRENT')
        for name in sorted(entry.loaded_paths()|{SELF}):q.pin(name)
        ast.parse(q.text(SELF));row['python_host_qualification']=admission.require_qualification(q)
        runtime_image=a.AcceptanceReader(profile.fixed.PYTHON.parent,guard.check)
        runtime_pins={name:runtime_image.pin(name)for name in profile.specifications()};loaded=profile.observe_loaded_images()
        row['current_runtime']=profile.validate(runtime_pins,loaded);before=historic.current_identity(guard.windows)
        shell=a.AcceptanceReader(SHELL.parent,guard.check)
        c.require(shell.pin(SHELL.name)==proof['external_shell_pins'][0],'P597_CURRENT_QUALIFIED_SHELL')
        native=a.AcceptanceReader(Path(historic.native.EXECUTABLE).parent,guard.check)
        native.pin(Path(historic.native.EXECUTABLE).name)
        current=entry.prerequisites.inspect(guard.windows,guard.check,lambda:native.fresh_pin(Path(historic.native.EXECUTABLE).name))
        c.require(current['preexisting_hwp_processes']==0 and current['failed_prerequisites']==['caller_lifecycle_native_safe']
            and current['closed_errors']==pre['closed_errors'],'P597_SAME_EXPECTED_NON_NATIVE_HOST_BOUNDARY')
        unused_namespace();scratch=c.ROOT/SCRATCH
        c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()
            and not scratch.parent.is_junction(),'P597_UNIQUE_COMPILER_SCRATCH');scratch.mkdir()
        env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch),PYTHONDONTWRITEBYTECODE='1')
        worker=fixed.Fixed008Worker(guard);handler=DenialHandler(worker,lambda:shell.fresh_pin(SHELL.name))
        attempt={};row['steps'].append(attempt);constructor=session.startup.PreassignedNativeStartup
        print(json.dumps(dict(state='CAPTURE008_ORIGINAL_GUARD_READY_DENIAL_ONLY',inputs=len(q.snapshots),
            Native_constructor_trapped=True,actual008_entry_executed=False)),flush=True)
        with patch.object(session.startup,'PreassignedNativeStartup',side_effect=ValueError('P597_NATIVE_CONSTRUCTOR_TRAP'))as trap:
            value=io.run(guard,worker,q,worker.start_fixed_worker,handler,'hwpx-agent.private.crossref-fixed-worker-result/v1',env,
                lambda notice:print(json.dumps(notice),flush=True),attempt)
            row['native_constructor_trap_calls']=trap.call_count;c.require(trap.call_count==0,'P597_NATIVE_CONSTRUCTOR_NOT_REACHED')
        c.require(session.startup.PreassignedNativeStartup is constructor,'P597_CONSTRUCTOR_TRAP_RESTORED')
        c.require(attempt['exit_code']==2 and attempt['requests']==1 and attempt['cleanup']is True and attempt['io_threads_joined']is True
            and attempt['owned_job']['owned_tree_empty']is True and attempt['owned_job']['forced_termination_invoked']is False
            and handler.denied and handler.lease.closed and value['state']=='fixed_eight_worker_failed_or_uncertain'
            and value['phase']=='current_live_release'and value['completed_callback_cases']==0
            and value['retained_live_or_uncertain_owners']==0 and value['probe_lease_closed']is True
            and value['native_startup_qualified']is False,'P597_ACTUAL008_READY_DENIED_BEFORE_CASES_AND_CLOSED')
        unused_namespace();c.require(historic.current_identity(guard.windows)==before,'P597_SAME_CURRENT_CREATOR_AFTER_WORKER')
        c.require(profile.observe_loaded_images()==loaded,'P597_SAME_LOADED_RUNTIME_PATHS_AND_ABI')
        after=entry.prerequisites.inspect(guard.windows,guard.check,lambda:native.fresh_pin(Path(historic.native.EXECUTABLE).name))
        c.require(after['preexisting_hwp_processes']==0 and after['failed_prerequisites']==current['failed_prerequisites']
            and after['closed_errors']==current['closed_errors'],'P597_NO_HANCOM_PROCESS_AFTER_DENIAL')
        row.update(code_proof_sha256=CODE_SHA,code_contracts=proof['contracts'],code_models_reexecuted=False,
            retained_actual_preflight_sha256=PREFLIGHT_SHA,actual_prefight_reexecuted=False,
            all_eight_native_directories_claim_final_and_spool_absent=True,constructor_trap_restored=True,
            same_live_kernel_before_after=True,external_execution_still_requires_new_user_authorization=True,
            entry_dependency_paths=paths,current_runtime_image_pins=list(runtime_image.snapshots.values()))
        native.finish();runtime_image.finish();shell.finish();q.finish();guard.check(force=True)
        row.update(state=entry.READY_STATE,external_native_final_hashes=native.final_fresh_hashes,
            external_runtime_final_hashes=runtime_image.final_fresh_hashes,external_shell_final_hashes=shell.final_fresh_hashes);passed=True
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        code=error.args[0]if error.args else None
        row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'P597_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup and all(s.get('cleanup')is True for s in row['steps']),
            source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),
            final_fresh_hashes=0 if q is None else q.final_fresh_hashes,external_shell_pins=[]if shell is None else list(shell.snapshots.values()),
            resource_samples=guard.samples,elapsed_seconds=round(time.monotonic()-started,3),
            system_CPU_max=max((s['system_cpu_percent']for s in guard.samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in guard.samples),default=None))
        audit=shared.publisher.publish(c.ROOT,AUDIT,entry.layout.pack(row),NS(require=c.require,exact=a.exact));canonical=None
        if passed and row['cleanup']:
            canonical=shared.publisher.publish(c.ROOT,entry.NAMES['ready'],entry.layout.pack(dict(row,readiness_audit_receipt=audit)),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds',
            'system_CPU_max','available_RAM_min_percent','native_constructor_trap_calls')},
            'steps':[dict(exit_code=s.get('exit_code'),requests=s.get('requests'),cleanup=s.get('cleanup'))for s in row['steps']],
            'audit':audit,'canonical_readiness':canonical}),flush=True)
    return 0 if passed and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
