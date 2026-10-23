"""396: LF/CRLF capture3; same readonly compiled21 worker once, no Hwp/ROT or Native replay."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import crossref_existing_owner_test_runtime as worker

OUTPUT='implementation/p09/evidence/p09-361-crossref-existing-owner-capture396.v1.json'
DRIVER='tools/p09/run_crossref_existing_owner_capture.py'
RUNTIME='tools/p09/crossref_existing_owner_test_runtime.py'
FAILED='implementation/p09/evidence/p09-361-crossref-existing-owner-recovery395.v1.json'
CORE='implementation/p09/tools/crossref-existing-owner.cs'
MODELS='implementation/p09/tools/test-crossref-existing-owner.cs'
EXTRACT="def parse_tests(stdout):\n    return re.findall(r'(?m)^test ([A-Za-z0-9_:]+) \\.\\.\\. (ok|FAILED)\\r?$',stdout)\n\n\n"


def main():
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/OUTPUT).exists(),'ROT_CAPTURE_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=image=None;started=time.monotonic();row=dict(state='FAILED_ROT_CAPTURE',steps=[],own_cpu_selection=selection,
        actual_Hangul_or_ROT_or_COM_queried=False,readonly_worker_reexecuted_for_changed_capture=True,
        fixed_eight_executed=False,native_startup_qualified=False,Native011_executed=False,prior_Native_replayed=False,
        accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();scratch=c.ROOT/'target/p09-crossref-existing-owner-scratch-396'
        c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'ROT_CAPTURE_UNIQUE_TEMP')
        q=a.AcceptanceReader(c.ROOT,guard.check);failed=r.compact.unpack(q.json(FAILED))
        c.require(q.snapshots[FAILED]['sha256']=='ccc0eeef8ecdc8d290427e0a074a90557f2541a60d22b24b7217f560f92309ae'
            and failed['state']=='FAILED_EXISTING_ROT_OWNER_RECOVERY'and failed['cleanup']
            and failed['fresh_inputs']==failed['final_fresh_hashes']==191 and len(failed['steps'])==1
            and failed['steps'][0]['exit_code']==0 and failed['steps'][0]['tests']==[]
            and failed['steps'][0]['summary_observed']is True and failed['steps'][0]['stderr_bytes']==0,
            'ORIGINAL395_CAPTURE_FAILURE_WITH_EXIT0_SUMMARY_NOT_RELABELED_SUCCESS')
        pins={p['path']:p for p in failed['source_pins']}
        for path,pin in sorted(pins.items()):
            q.pin(path)
            if path!=RUNTIME:c.require(q.snapshots[path]==pin,'ALL_CSHARP_MODEL_TEST_AND_NATIVE_PRODUCTION_INPUTS_UNCHANGED')
        text=q.text(RUNTIME);c.require(text.count(EXTRACT)==1,'ONE_EXPLICIT_LF_CRLF_PARSER')
        restored=text.replace(EXTRACT,'').replace('tests=parse_tests(stdout),',"tests=re.findall(r'(?m)^test ([A-Za-z0-9_:]+) \\.\\.\\. (ok|FAILED)$',stdout),")
        r.audit.inverse(restored,pins[RUNTIME],'ONLY_RESULT_CAPTURE_LINE_ENDINGS_ORIGINAL_GUARDS_OWNED_JOB_AND_COMMAND_UNCHANGED')
        q.pin(DRIVER)
        expected=[('rot_existing::'+n,'ok')for n in sorted(worker.NAMES)]
        lf='\n'.join('test '+name+' ... '+status for name,status in expected)+'\n'
        c.require(worker.parse_tests(lf)==expected and worker.parse_tests(lf.replace('\n','\r\n'))==expected,'ACTUAL_LF_CRLF_EXACT21_PARSER_CONTRACTS')
        c.require(worker.parse_tests('test wrong::case ... ignored\r\n')==[],'IGNORED_MARKERS_NEVER_CONVERTED_TO_PASSES');row['pure_capture_contracts_passed']=3
        for mod in tuple(sys.modules.values()):
            value=getattr(mod,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        image=a.AcceptanceReader(worker.SHELL.parent,guard.check);image.pin(worker.SHELL.name)
        scratch.mkdir();env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch),PYTHONDONTWRITEBYTECODE='1')
        print(json.dumps(dict(state='ROT_CAPTURE_PREFLIGHT',inputs=len(q.snapshots),pure_capture_contracts=3,unchanged_compiled_cases=21)),flush=True)
        worker.run(guard,env,row)
        contents=list(scratch.iterdir());c.require(len(contents)<=32,'BOUNDED_COMPILER_SCRATCH_CONTENTS');row['retained_compiler_scratch_entries']=len(contents)
        image.finish();q.finish();guard.check(force=True);row.update(state='PASS_CAPTURE3_COMPILED_X86_EXISTING_OWNER_MODELS20_KERNEL_SELF1_NOT_ACTUAL_ROT_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,external_shell_final_hashes=image.final_fresh_hashes,
            next_work='resource_bound_worker_and_descriptor_protocol_owner_factory_integration_then_live_existing_ROT_attachment_qualification')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'ROT_CAPTURE_FAILURE_NO_RAW_VALUES')
        if q is not None:
            try:
                if image is not None:image.finish();row['external_shell_final_hashes']=image.final_fresh_hashes
                q.finish();row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
            except(ValueError,OSError,KeyError,TypeError,AttributeError):row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),external_shell_pins=[]if image is None else list(image.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,OUTPUT,r.compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','external_shell_final_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','safe_error_codes','cleanup')},'cases':len(s.get('tests',[])),
                'failed_cases':[name for name,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
