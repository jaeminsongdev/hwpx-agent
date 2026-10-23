"""External one-shot current-session qualification -> original fixed-eight capture.

No saved inspection/approval flag permits execution. The one current jobless
caller must qualify its own session, close current inputs, consume a live handoff
once, and retain exact handles on failure. Gate/semantic acceptance stays OPEN.
"""
import argparse,json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import crossref_external_host_inspection as installed
import crossref_startup_prerequisites as prerequisites
import crossref_external_batch_runtime as runtime

SELF='tools/p09/run_external_crossref_fixed_batch.py'
CODE='implementation/p09/evidence/p09-361-crossref-qualified-entry-code411.v1.json'
CODE_STATE='PASS_QUALIFIED_BATCH_ENTRY_CODE_CONTRACTS_NOT_NATIVE_OR_GATE'
READY='implementation/p09/evidence/p09-361-crossref-qualified-entry-runtime-ready413.v1.json'
CLAIM='implementation/p09/evidence/p09-361-external-qualified-fixed-eight-claim001.v1.json'
OUTPUT='implementation/p09/evidence/p09-361-external-qualified-fixed-eight-run001.v1.json'


def generation_names(current002=False):
    # Fixed second scope only; never a caller-supplied retry number, path, source or case subset.
    r.c.require(type(current002)is bool,'EXTERNAL_ENTRY_EXACT_GENERATION_FLAG')
    if not current002:return dict(code=CODE,ready=READY,claim=CLAIM,output=OUTPUT,
        notice='implementation/p09/evidence/p09-361-external-qualified-fixed-eight-worker-notice001.v1.json',
        cleanup_notice='implementation/p09/evidence/p09-361-external-qualified-fixed-eight-live-cleanup001.v1.json',
        scratch='target/p09-external-qualified-fixed-eight-scratch-001')
    return dict(code='implementation/p09/evidence/p09-361-crossref-generation-code478.v1.json',
        ready='implementation/p09/evidence/p09-361-crossref-generation-ready479.v1.json',
        claim='implementation/p09/evidence/p09-361-external-qualified-fixed-eight-claim002.v1.json',
        output='implementation/p09/evidence/p09-361-external-qualified-fixed-eight-run002.v1.json',
        notice='implementation/p09/evidence/p09-361-external-qualified-fixed-eight-worker-notice002.v1.json',
        cleanup_notice='implementation/p09/evidence/p09-361-external-qualified-fixed-eight-live-cleanup002.v1.json',
        scratch='target/p09-external-qualified-fixed-eight-scratch-002')


def parser():
    value=argparse.ArgumentParser(description='Current external jobless session qualification and one fixed-eight capture; never P09 acceptance.')
    group=value.add_mutually_exclusive_group(required=True)
    group.add_argument('--preflight-only',action='store_true')
    group.add_argument('--execute-qualified-fixed-eight',action='store_true')
    group.add_argument('--preflight-generation-002',action='store_true')
    group.add_argument('--execute-generation-002-fixed-eight',action='store_true')
    value.add_argument('--inspection-run',type=int,choices=range(1,9))
    return value


def output_name(args):
    if args.preflight_generation_002 or args.execute_generation_002_fixed_eight:
        r.c.require(args.inspection_run is None,'EXTERNAL_ENTRY_NO_CURRENT_GENERATION_RETRY_SELECTOR')
        return 'implementation/p09/evidence/p09-361-external-qualified-generation002-preflight.v1.json'if args.preflight_generation_002 else generation_names(True)['output']
    if args.preflight_only:
        r.c.require(type(args.inspection_run)is int and 1<=args.inspection_run<=8,'EXTERNAL_ENTRY_PREFLIGHT_RUN_REQUIRED')
        return f'implementation/p09/evidence/p09-361-external-qualified-entry-preflight{args.inspection_run:03}.v1.json'
    r.c.require(args.inspection_run is None,'EXTERNAL_ENTRY_NO_NATIVE_RETRY_RUN_SELECTOR')
    return OUTPUT


def loaded_paths(exclude=()):
    result=set()
    for mod in tuple(sys.modules.values()):
        name=getattr(mod,'__file__',None)
        if name:
            path=Path(name).absolute()
            if path.is_relative_to(r.c.ROOT/'tools/p09')and path.suffix=='.py':
                relative=path.relative_to(r.c.ROOT).as_posix()
                if relative not in exclude and '/tests/'not in relative:result.add(relative)
    return result


def load_manifest(reader,require_runtime_ready=False,current_generation002=False):
    names=generation_names(current_generation002);code,ready_path=names['code'],names['ready']
    proof=r.compact.unpack(reader.json(code))
    runtime.require(proof['state']==CODE_STATE and proof['cleanup']is True and proof['fresh_inputs']==proof['final_fresh_hashes']>0
        and proof['contracts']['run']>=20 and proof['contracts']['errors']==proof['contracts']['failures']==proof['contracts']['skipped']==0,
        'VERIFIED_CURRENT_ENTRY_CODE_REQUIRED')
    manifest={p['path']:p for p in proof['source_pins']};paths=proof['entry_dependency_paths']
    runtime.require(type(paths)is list and len(paths)==len(set(paths))and SELF in paths and set(paths)<=set(manifest)
        and loaded_paths()<=set(paths),'COMPLETE_CURRENT_ENTRY_IMPORT_SOURCE_MANIFEST')
    for path in paths:runtime.require(reader.pin(path)==manifest[path],'CURRENT_ENTRY_CODE_CHANGED_REQUALIFY')
    if require_runtime_ready:
        ready=r.compact.unpack(reader.json(ready_path))
        runtime.require(ready['state']=='PASS_PUBLIC_ENTRY_PREFLIGHT_AND_FIXED_WORKER_DENIAL_PACKAGE_NOT_NATIVE'
            and ready['cleanup']is True and ready['code_proof_sha256']==reader.snapshots[code]['sha256']
            and ready['native_startup_qualified']is False,'VERIFIED_IMPLEMENTATION_RUNTIME_PACKAGE_REQUIRED_NOT_NATIVE_PERMIT')
        current={p['path']:p for p in ready['source_pins']}
        runtime.require(set(paths)<=set(current),'COMPLETE_IMPLEMENTATION_READINESS_SOURCE_SET')
        for path in paths:runtime.require(reader.pin(path)==current[path],'IMPLEMENTATION_READINESS_SOURCE_CHANGED')
    for path in runtime.INPUT_PINS:
        pin=reader.pin(path);size,sha=runtime.INPUT_PINS[path]
        runtime.require((pin['bytes'],pin['sha256'])==(size,sha),'FIXED_CURRENT_CAPTURE_INPUTS')
    return proof,manifest,set(paths)|set(runtime.INPUT_PINS)


def publish(path,value):
    return r.shared.publisher.publish(r.c.ROOT,path,r.compact.pack(value),NS(require=r.c.require,exact=r.a.exact))


def main(argv=None):
    args=parser().parse_args(argv);output=output_name(args);c,a,shared=r.c,r.a,r.shared
    current002=args.preflight_generation_002 or args.execute_generation_002_fixed_eight
    preflight=args.preflight_only or args.preflight_generation_002;execute=args.execute_qualified_fixed_eight or args.execute_generation_002_fixed_eight
    names=generation_names(current002)
    c.require(Path(sys.executable)==installed.fixed.PYTHON,'EXTERNAL_ENTRY_FIXED_RUNTIME_PATH')
    c.require(not(c.ROOT/output).exists()and not(c.ROOT/output).is_symlink(),'EXTERNAL_ENTRY_IMMUTABLE_OUTPUT')
    if execute:
        c.require(not(c.ROOT/names['claim']).exists()and not(c.ROOT/names['claim']).is_symlink(),'EXTERNAL_ENTRY_ONE_NATIVE_BUNDLE_NO_REPLAY')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.final.guard_type(a.Guard))()
    q=image=shell=python=None;started=time.monotonic();row=dict(state='FAILED_EXTERNAL_QUALIFIED_ENTRY',own_cpu_selection=selection,
        mode='preflight_only'if preflight else'current_qualification_then_fixed_eight',generation=2 if current002 else 1,native_claim_created=False,
        fixed_eight_executed=False,native_startup_qualified=False,crossref_semantics_qualified=False,
        accepted_count_delta=0,P09_gate='OPEN',P10_started=False,Native011_executed=False)
    def notify(value):
        print(json.dumps(value),flush=True)
        if value.get('state')in('NATIVE_WORKER_RESULT_RECORDED_BEFORE_CLEANUP','NATIVE_TRANSPORT_FAILED_BEFORE_CLEANUP')and 'early_worker_notice'not in row:
            row['early_worker_notice']=publish(names['notice'],dict(value,current_run_output=names['output'],force_kill_forbidden=True))
        if value.get('state')=='WAITING_SAME_OWNED_NATIVE_EXIT_NO_FORCE_KILL'and 'live_cleanup_notice'not in row:
            row['live_cleanup_notice']=publish(names['cleanup_notice'],
                dict(state=value['state'],process_id=value['process_id'],force_kill_forbidden=True,rerun_forbidden=True,
                    current_run_output=names['output'],native_execution_authorized=False,P09_complete=False))
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        if current002:proof,manifest,paths=load_manifest(q,require_runtime_ready=execute,current_generation002=True)
        else:proof,manifest,paths=load_manifest(q,require_runtime_ready=execute)
        image=a.AcceptanceReader(Path(installed.native.EXECUTABLE).parent,guard.check)
        shell=a.AcceptanceReader(Path(runtime.candidate.original.SHELL).parent,guard.check)
        python=a.AcceptanceReader(installed.fixed.PYTHON.parent,guard.check)
        shell_expected=shell.pin(Path(runtime.candidate.original.SHELL).name)
        c.require(shell_expected==proof['external_shell_pins'][0],'EXACT_VERIFIED_SHELL_EXECUTABLE')
        installed.runtime_pin_matches(python.pin(installed.fixed.PYTHON.name))
        before=installed.current_identity(guard.windows)
        row['prerequisites']=prerequisites.inspect(guard.windows,guard.check,lambda:image.fresh_pin(Path(installed.native.EXECUTABLE).name))
        runtime.absent_attempts()
        passed=row['prerequisites']['all_observed_prerequisites_passed']
        if not passed:
            row['state']='DENIED_CURRENT_EXTERNAL_ENTRY_PREREQUISITES_NO_NATIVE_OR_CLAIM'
        elif preflight:
            row['state']='OBSERVED_CURRENT_EXTERNAL_ENTRY_PREFLIGHT_NOT_NATIVE_SESSION_OR_PERMIT'
        else:
            c.require(installed.current_identity(guard.windows)==before,'SAME_CREATOR_BEFORE_CLAIM')
            row['claim']=publish(names['claim'],dict(state='ONE_CURRENT_NATIVE_BUNDLE_CLAIMED_NO_RETRY',creator=before,
                code_proof=names['code'],source_digest=q.snapshots[names['code']]['sha256'],native_execution_authorized=False,P09_complete=False))
            row['native_claim_created']=True
            scratch=c.ROOT/names['scratch']
            c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'EXTERNAL_ENTRY_UNIQUE_COMPILER_TEMP')
            scratch.mkdir();env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch),PYTHONDONTWRITEBYTECODE='1')
            artifacts=runtime.execute(guard,manifest,paths,shell_expected,env,notify,row)
            row.update(state='CAPTURED_CURRENT_NATIVE_FIXED_EIGHT_SEMANTICS_AND_P09_UNQUALIFIED',fixed_eight_executed=True,
                native_startup_qualified=False,crossref_semantics_qualified=False,captured_cases=len(artifacts['cases']))
        image.finish();shell.finish();python.finish();q.finish();guard.check(force=True)
        row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            external_native_final_hashes=image.final_fresh_hashes,external_shell_final_hashes=shell.final_fresh_hashes,
            external_runtime_final_hashes=python.final_fresh_hashes)
    except KeyboardInterrupt:
        # The claim stays consumed. Do not fake final freshness, close a live
        # native, replay Close/Quit, or turn a failed worker into a passing run.
        row.update(error_type='KeyboardInterrupt',error_code='EXTERNAL_ENTRY_INTERRUPTED_WITH_UNCONFIRMED_CLEANUP',
            interrupted=True,rerun_forbidden=True)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'EXTERNAL_ENTRY_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples
        row.update(cleanup=guard.cleanup and all(v.get('cleanup')is True for k,v in row.items()if k in('qualification_worker','fixed_worker')),
            elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=publish(output,row)
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','native_claim_created','fixed_eight_executed','captured_cases','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'receipt':pin}),flush=True)
    return 0 if row['cleanup']and row['state'].startswith(('OBSERVED_','CAPTURED_'))else 2


if __name__=='__main__':raise SystemExit(main())
