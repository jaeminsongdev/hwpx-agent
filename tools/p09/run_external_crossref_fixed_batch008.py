"""Fixed008 external one-shot entry. Code/readiness and CURRENT session qualification remain mandatory.

No past Native/run is retried, no case subset or saved approval/session is accepted.
Not connected to P09 semantic acceptance. Never invoke execute from the Codex parent Job.
"""
import argparse,json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import crossref_external_host_inspection as installed
import crossref_startup_prerequisites as prerequisites
import crossref_external008_runtime as runtime
import crossref_runtime004_admission as host_profile
import crossref_generation008_publication as publication
import crossref_inline_receipt567 as layout

SELF='tools/p09/run_external_crossref_fixed_batch008.py'
CODE_STATE='PASS_CAPTURE008_ENTRY_CODE_CONTRACTS_NOT_NATIVE_OR_GATE'
READY_STATE='PASS_CAPTURE008_ENTRY_RUNTIME_PREPARATION_NOT_NATIVE_OR_GATE'
NAMES=dict(code='implementation/p09/evidence/p09-361-capture008-entry-code596.v1.json',
    ready='implementation/p09/evidence/p09-361-capture008-entry-ready597.v1.json',
    claim='implementation/p09/evidence/p09-361-external-qualified-fixed-eight-claim008.v1.json',output=publication.OUTPUT,
    preflight='implementation/p09/evidence/p09-361-external-qualified-generation008-preflight.v1.json',
    scratch='target/p09-external-qualified-fixed-eight-scratch-008')

def parser():
    value=argparse.ArgumentParser(description='Fixed008 current qualification then fixed-eight capture; never P09 acceptance.')
    group=value.add_mutually_exclusive_group(required=True)
    group.add_argument('--preflight-generation-008',action='store_true')
    group.add_argument('--execute-generation-008-fixed-eight',action='store_true')
    return value

def loaded_paths(exclude=()):
    result=set()
    for module in tuple(sys.modules.values()):
        name=getattr(module,'__file__',None)
        if name:
            path=Path(name).absolute()
            if path.is_relative_to(r.c.ROOT/'tools/p09')and path.suffix=='.py':
                name=path.relative_to(r.c.ROOT).as_posix()
                if name not in exclude and '/tests/'not in name:result.add(name)
    return result

def load_manifest(reader,require_runtime_ready=False):
    runtime.require(type(require_runtime_ready)is bool,'CAPTURE008_EXACT_READY_REQUIREMENT')
    proof=layout.unpack(reader.json(NAMES['code']))
    runtime.require(proof['state']==CODE_STATE and proof['generation']==8 and proof['cleanup']is True
        and proof['fresh_inputs']==proof['final_fresh_hashes']>0 and proof['contracts']['run']>=24
        and proof['contracts']['errors']==proof['contracts']['failures']==proof['contracts']['skipped']==0,'CAPTURE008_VERIFIED_CURRENT_CODE_REQUIRED')
    pins={p['path']:p for p in proof['source_pins']};paths=proof['entry_dependency_paths']
    runtime.require(type(paths)is list and len(paths)==len(set(paths))and SELF in paths and set(paths)<=set(pins)
        and loaded_paths()<=set(paths)and runtime.CASE_PATHS<=set(paths),'CAPTURE008_COMPLETE_IMPORT_AND_CASE_SOURCE_CLOSURE')
    for name in paths:runtime.require(reader.pin(name)==pins[name],'CAPTURE008_CODE_CHANGED_REQUALIFY')
    if require_runtime_ready:
        ready=layout.unpack(reader.json(NAMES['ready']))
        runtime.require(ready['state']==READY_STATE and ready['generation']==8 and ready['cleanup']is True
            and ready['code_proof_sha256']==reader.snapshots[NAMES['code']]['sha256']and ready['native_startup_qualified']is False,
            'CAPTURE008_CURRENT_READINESS_NOT_A_NATIVE_PERMIT')
        current={p['path']:p for p in ready['source_pins']}
        runtime.require(set(paths)<=set(current),'CAPTURE008_READINESS_SOURCE_CLOSURE')
        for name in paths:runtime.require(reader.pin(name)==current[name],'CAPTURE008_READINESS_SOURCE_CHANGED')
    fixed=runtime.fixed_input_pins()
    for name,(size,sha)in fixed.items():
        pin=reader.pin(name);runtime.require((pin['bytes'],pin['sha256'])==(size,sha),'CAPTURE008_FIXED_CURRENT_INPUTS')
    return proof,pins,set(paths)|set(fixed)

def publish_small(path,row):
    return r.shared.publisher.publish(r.c.ROOT,path,layout.pack(row),NS(require=r.c.require,exact=r.a.exact))

def notify_stage(stage,value,record):
    runtime.require(stage in('qualification','fixed_eight'),'CAPTURE008_EXACT_NOTICE_STAGE')
    print(json.dumps(value),flush=True)
    state=value.get('state')
    if state in('NATIVE_WORKER_RESULT_RECORDED_BEFORE_CLEANUP','NATIVE_TRANSPORT_FAILED_BEFORE_CLEANUP'):
        key=stage+'_early_worker_notice'
        if key not in record:
            name=f'implementation/p09/evidence/p09-361-external-qualified-fixed-eight-{stage}-worker-notice008.v1.json'
            record[key]=publish_small(name,dict(value,generation=8,current_run_output=NAMES['output'],force_kill_forbidden=True))
    if state=='WAITING_SAME_OWNED_NATIVE_EXIT_NO_FORCE_KILL':
        key=stage+'_live_cleanup_notice'
        if key not in record:
            name=f'implementation/p09/evidence/p09-361-external-qualified-fixed-eight-{stage}-live-cleanup008.v1.json'
            record[key]=publish_small(name,dict(state=state,generation=8,process_id=value['process_id'],force_kill_forbidden=True,
                rerun_forbidden=True,current_run_output=NAMES['output'],native_execution_authorized=False,P09_complete=False))

def main(argv=None):
    args=parser().parse_args(argv);preflight=args.preflight_generation_008;output=NAMES['preflight']if preflight else NAMES['output']
    c,a,shared=r.c,r.a,r.shared
    c.require(Path(sys.executable)==installed.fixed.PYTHON,'CAPTURE008_FIXED_RUNTIME_PATH')
    c.require(not(c.ROOT/output).exists()and not(c.ROOT/output).is_symlink(),'CAPTURE008_IMMUTABLE_OUTPUT')
    if not preflight:
        c.require(not(c.ROOT/NAMES['claim']).exists()and not(c.ROOT/NAMES['claim']).is_symlink(),'CAPTURE008_ONE_NATIVE_BUNDLE_NO_REPLAY')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.final.guard_type(a.Guard))()
    q=image=shell=python=None;started=time.monotonic()
    row=dict(state='FAILED_EXTERNAL_QUALIFIED_ENTRY',own_cpu_selection=selection,mode='preflight_only'if preflight else'current_qualification_then_fixed_eight',
        generation=8,native_claim_created=False,fixed_eight_executed=False,native_startup_qualified=False,crossref_semantics_qualified=False,
        accepted_count_delta=0,P09_gate='OPEN',P10_started=False,Native011_executed=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);proof,manifest,paths=load_manifest(q,require_runtime_ready=not preflight)
        row['python_host_qualification']=host_profile.require_qualification(q)
        image=a.AcceptanceReader(Path(installed.native.EXECUTABLE).parent,guard.check)
        shell=a.AcceptanceReader(Path(runtime.original.candidate.original.SHELL).parent,guard.check)
        python=a.AcceptanceReader(installed.fixed.PYTHON.parent,guard.check)
        shell_expected=shell.pin(Path(runtime.original.candidate.original.SHELL).name)
        c.require(shell_expected==proof['external_shell_pins'][0],'CAPTURE008_EXACT_VERIFIED_SHELL')
        row['current_python_images']=host_profile.verify_current_reader(python);before=installed.current_identity(guard.windows)
        row['prerequisites']=prerequisites.inspect(guard.windows,guard.check,lambda:image.fresh_pin(Path(installed.native.EXECUTABLE).name))
        runtime.absent_attempts();passed=row['prerequisites']['all_observed_prerequisites_passed']
        if not passed:row['state']='DENIED_CURRENT_EXTERNAL_ENTRY_PREREQUISITES_NO_NATIVE_OR_CLAIM'
        elif preflight:row['state']='OBSERVED_CURRENT_EXTERNAL_ENTRY_PREFLIGHT_NOT_NATIVE_SESSION_OR_PERMIT'
        else:
            c.require(installed.current_identity(guard.windows)==before,'CAPTURE008_SAME_CREATOR_BEFORE_CLAIM')
            row['claim']=publish_small(NAMES['claim'],dict(state='ONE_CURRENT_NATIVE_BUNDLE_CLAIMED_NO_RETRY',generation=8,creator=before,
                code_proof=NAMES['code'],source_digest=q.snapshots[NAMES['code']]['sha256'],native_execution_authorized=False,P09_complete=False))
            row['native_claim_created']=True;scratch=c.ROOT/NAMES['scratch']
            c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'CAPTURE008_UNIQUE_TEMP')
            scratch.mkdir();env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch),PYTHONDONTWRITEBYTECODE='1')
            artifacts=runtime.execute(guard,manifest,paths,shell_expected,env,lambda stage,value:notify_stage(stage,value,row),row)
            row.update(state='CAPTURED_CURRENT_NATIVE_FIXED_EIGHT_SEMANTICS_AND_P09_UNQUALIFIED',fixed_eight_executed=True,
                native_startup_qualified=False,crossref_semantics_qualified=False,captured_cases=len(artifacts['cases']))
        image.finish();shell.finish();python.finish();q.finish();guard.check(force=True)
        row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,external_native_final_hashes=image.final_fresh_hashes,
            external_shell_final_hashes=shell.final_fresh_hashes,external_runtime_final_hashes=python.final_fresh_hashes)
    except KeyboardInterrupt:
        row.update(error_type='KeyboardInterrupt',error_code='EXTERNAL_ENTRY_INTERRUPTED_WITH_UNCONFIRMED_CLEANUP',interrupted=True,rerun_forbidden=True)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'CAPTURE008_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples
        row.update(cleanup=guard.cleanup and all(value.get('cleanup')is True for key,value in row.items()if key in('qualification_worker','fixed_worker')),
            elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((sample['system_cpu_percent']for sample in samples),default=None),available_RAM_min_percent=min((sample['available_ram_percent']for sample in samples),default=None))
        pin=publish_small(output,row)if preflight else publication.publish_final(c.ROOT,row)
        print(json.dumps({**{key:row.get(key)for key in('state','error_code','native_claim_created','fixed_eight_executed','captured_cases','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'receipt':pin}),flush=True)
    return 0 if row['cleanup']and row['state'].startswith(('OBSERVED_','CAPTURED_'))else 2

if __name__=='__main__':raise SystemExit(main())
