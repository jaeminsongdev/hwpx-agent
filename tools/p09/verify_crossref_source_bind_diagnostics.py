"""485: admission equivalence and closed source-bind diagnostics; no Native execution."""
import ast,hashlib,json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import resource_sample_table as layout
import crossref_native_worker_io as io

SELF='tools/p09/verify_crossref_source_bind_diagnostics.py'
OUTPUT='implementation/p09/evidence/p09-361-source-bind-diagnostics485.v1.json'
ROOT='implementation/p09/tools/'
ACTIVE=ROOT+'crossref-owned-active-source.ps1'
MODEL=ROOT+'test-crossref-source-bind-diagnostics.ps1'
ARCHIVE='implementation/p09/source-archive/p361-source-bind-diagnostics485/active-source.ps1'
BASE='implementation/p09/evidence/p09-361-crossref-case-diagnostics484.v1.json'
RUN002='implementation/p09/evidence/p09-361-external-qualified-fixed-eight-run002.v1.json'
PS='C:/Windows/SysWOW64/WindowsPowerShell/v1.0/powershell.exe'
RECOVER=sys.argv[1:]==['--after-model485']
RECOVER486=sys.argv[1:]==['--after-model486']
RECOVER=RECOVER or RECOVER486

def original_body(text):
    block="""    $failureCodes=@{owner_verified='SOURCE_OWNER_MISMATCH';application_bound='SOURCE_APPLICATION_IDENTITY_MISMATCH';
        collection_bound='SOURCE_COLLECTION_IDENTITY_MISMATCH';document_bound='SOURCE_ACTIVE_DOCUMENT_IDENTITY_MISMATCH';
        document_application_bound='SOURCE_DOCUMENT_APPLICATION_IDENTITY_MISMATCH';full_name_matches='SOURCE_ACTIVE_PATH_MISMATCH';
        version_matches='SOURCE_VERSION_MISMATCH';source_digest_matches='SOURCE_DIGEST_MISMATCH'}
"""
    r.c.require(text.count(block)==1,'EXACT_CLOSED_FAILURE_CODE_DICTIONARY')
    text=text.replace(block,'').replace('$failureCodes[$name]',"'OBSERVATION_MISMATCH'")
    comment='    # Keep the original direct assignments, getter order and IUnknown comparisons.\n    # Never put returned document values or arbitrary exception strings into diagnostics.\n'
    r.c.require(text.count(comment)==1,'EXACT_GETTER_DIAGNOSTIC_COMMENT');text=text.replace(comment,'')
    def unwrap(match):
        assignment,variable,code,catch_code=match.groups()
        r.c.require(assignment.split('=')[0]==variable and code==catch_code,'SAME_GETTER_NULL_GUARD_AND_CATCH_CODE')
        return '    '+assignment
    text,n=re.subn(r"    try \{(\$(?:collection|active|application|documentApplication|count|modified|name|activeName|version)=[^\n{};]+);Assert-P09XrefBinding \(\$null -ne (\$[A-Za-z]+)\) '(SOURCE_READ_[A-Z_]+_FAILED)'\} catch \{throw 'P09_XREF_BIND_(SOURCE_READ_[A-Z_]+_FAILED)'\}",unwrap,text)
    r.c.require(n==9,'EXACT_NINE_GETTERS_SAME_ORDER_AND_ASSIGNMENTS')
    text=text.replace('    $count=$collection.Count\n    $modified=$Document.Modified\n    $name=$Document.FullName\n    $activeName=$active.FullName',
        '    $count=$collection.Count;$modified=$Document.Modified;$name=$Document.FullName;$activeName=$active.FullName')
    lease="        try {$stream=[IO.File]::Open($path,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)}\n        catch {throw 'P09_XREF_BIND_SOURCE_READ_LEASE_FAILED'}"
    r.c.require(text.count(lease)==1,'EXACT_UNCHANGED_SOURCE_LEASE_FLAGS')
    return text.replace(lease,'        $stream=[IO.File]::Open($path,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::Read)')

def ps_models(guard,row,expected):
    owned=capture=None;started=time.monotonic();step=dict(stage='source_bind_models_only',cleanup=False);row['steps'].append(step)
    try:
        command=[PS,'-NoLogo','-NoProfile','-NonInteractive','-STA','-File',str(r.c.ROOT/MODEL),'-ModelsOnly']
        if RECOVER:command.append('-GetterFaultsAfter485')
        owned=r.shared.OwnedSQLJobProcess(command,
            windows=guard.windows,allowed_executables=[PS],cwd=r.c.ROOT,checkpoint=guard.check,env=r.audit.environment())
        capture=r.shared.BoundedProcessCapture(owned,output_limit=32768,parse_markers=False)
        while True:
            guard.check();r.c.require(time.monotonic()-started<90,'STOP_SOURCE_BIND_MODELS_DEADLINE')
            try:stdout,stderr=capture.communicate(timeout=.5);owned.observe();break
            except subprocess.TimeoutExpired:capture.progress();owned.observe()
        tests=re.findall(r'(?m)^test ([A-Za-z0-9_:]+) \.\.\. (ok|FAILED)\r?$',stdout)
        errors=re.findall(r'(?m)^Error: (P09_XREF_BIND_[A-Z_]+)\r?$',stdout)
        step.update(exit_code=owned.returncode,tests=tests,closed_model_errors=errors,stdout_bytes=len(stdout.encode()),stderr_bytes=len(stderr.encode()),
            stdout_sha256=hashlib.sha256(stdout.encode()).hexdigest(),stderr_sha256=hashlib.sha256(stderr.encode()).hexdigest())
        marker='P09_SOURCE_BIND_RETAINED_PAIRS=77;GETTER_FAULTS=9'if RECOVER else'P09_SOURCE_BIND_PAIRS=77;GETTER_FAULTS=9'
        r.c.require(owned.returncode==0 and not stderr and len(tests)==len(expected) and {n for n,s in tests}==expected and all(s=='ok'for n,s in tests)
            and marker in stdout,'EXACT_NEW_GROUPS_NO_REPLAY_OF_RETAINED_77_PAIRS')
    finally:
        if owned is not None:
            # This Job owns only read-only mock models, never a Hancom process.
            owned.kill();owned.wait(timeout=2)
            if capture is not None:capture.close()
            owned.close();step.update(cleanup=owned.profile['cleanup_confirmed'],owned_job=owned.profile)
        step['elapsed_seconds']=round(time.monotonic()-started,3)

def main():
    c,a,shared=r.c,r.a,r.shared
    c.require(sys.argv[1:]in([],['--after-model485'],['--after-model486']),'SOURCE_BIND_CLOSED_MODE')
    output=OUTPUT.replace('485.v1','487.v1'if RECOVER486 else'486.v1')if RECOVER else OUTPUT
    c.require(not(c.ROOT/output).exists(),'SOURCE_BIND_IMMUTABLE')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    started=time.monotonic();q=shell=None
    row=dict(state='FAILED_SOURCE_BIND_DIAGNOSTIC_MODELS',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        actual_Hancom_COM_ROT_or_Native_started=False,run002_replayed=False,official249_replayed=False,source_bind_runtime_root_cause_confirmed=False,
        original_source_bind_admission_weakened=False,new_native_generation_authorized=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        paths={SELF,ACTIVE,MODEL,ARCHIVE,BASE,RUN002,ROOT+'sdk-baseline-owned-session.ps1','tools/p09/crossref_native_worker_io.py'}
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':paths.add(path.relative_to(c.ROOT).as_posix())
        for path in sorted(paths):q.pin(path)
        retained=set()
        if RECOVER:
            failed=layout.unpack(q.json(OUTPUT))
            c.require(q.snapshots[OUTPUT]['sha256']=='63d3886529ab8e13291c1c713a68e51bb2fd4233fb23aff5a5407bb407e5422c'
                and failed['state']=='FAILED_SOURCE_BIND_DIAGNOSTIC_MODELS'and failed['cleanup']is True,'EXACT_ORIGINAL485_FAILURE_RETAINED')
            for pin in failed['source_pins']:
                if pin['path']not in(SELF,MODEL,ACTIVE):c.require(q.pin(pin['path'])==pin,'ALL_RETAINED485_MODEL_DEPENDENCIES_UNCHANGED')
            for path,oldpath in((SELF,'runner485.py'),(MODEL,'models485.ps1')):
                old=next(p for p in failed['source_pins']if p['path']==path);saved=q.pin(str(Path(ARCHIVE).parent/oldpath).replace('\\','/'))
                c.require((old['bytes'],old['sha256'])==(saved['bytes'],saved['sha256']),'EXACT_FAILED485_RUNNER_AND_MODELS_ARCHIVED')
            retained={n for n,s in failed['steps'][0]['tests']if s=='ok'}
            c.require(len(retained)==2,'RETAIN_EXACT_FIRST_TWO_GROUPS_NOT_FULL485_PASS')
            oldmodels=q.text(str(Path(ARCHIVE).parent/'models485.ps1').replace('\\','/'))
            first=oldmodels.index('    $archive=');last=oldmodels.index("    $original=(Get-Command")
            unchanged=oldmodels[first:last].rstrip()
            c.require(unchanged in q.text(MODEL),'RETAINED_MODEL_BODIES_IDENTICAL_NOT_REGENERATED')
            row.update(retained_groups_from485=sorted(retained),passed_groups_replayed=False,original485_missing_final_closure_preserved=True)
            if RECOVER486:
                failure486=OUTPUT.replace('485.v1','486.v1');packet486=layout.unpack(q.json(failure486))
                c.require(q.snapshots[failure486]['sha256']=='b4d293609b3dfa8814988f2d5b88989f2dbe454929d12db40d51504ea55c38b0'
                    and packet486['cleanup']is True and packet486['steps'][0]['tests']==[],'EXACT486_GETTER_MODEL_FAILURE_PRESERVED')
                for current,oldpath in((SELF,'runner486.py'),(MODEL,'models486.ps1'),(ACTIVE,'active486.ps1')):
                    old=next(p for p in packet486['source_pins']if p['path']==current);saved=q.pin(str(Path(ARCHIVE).parent/oldpath).replace('\\','/'))
                    c.require((old['bytes'],old['sha256'])==(saved['bytes'],saved['sha256']),'EXACT486_CODE_ARCHIVES')
        c.require(q.snapshots[BASE]['sha256']=='42fe05e38f612af1008040d6b30657f49c71fd82452d7a098ca787444aa3447e','EXACT_PREVIOUS_DIAGNOSTIC484')
        c.require(q.snapshots[RUN002]['sha256']=='937f7e344845513faf0316e581a52657d803fce026ab6ae05f175dad353fe7da','ORIGINAL_RUN002_FAILURE_BYTES_UNCHANGED')
        baseline=layout.unpack(q.json(BASE));old=next(p for p in baseline['source_pins']if p['path']==ACTIVE)
        c.require((old['bytes'],old['sha256'])==(q.snapshots[ARCHIVE]['bytes'],q.snapshots[ARCHIVE]['sha256']),'EXACT_ORIGINAL_ACTIVE_SOURCE_ARCHIVE')
        r.audit.inverse(original_body(q.text(ACTIVE)),q.snapshots[ARCHIVE],'ORIGINAL_BODY_RESTORED_EXCEPT_CLOSED_DIAGNOSTICS_AND_EARLY_NULL_REJECTION')
        # Read the literal closed codes, not arbitrary runtime values.
        codes=set(re.findall(r"'(SOURCE_[A-Z_]+_MISMATCH)'",q.text(ACTIVE)))|set(re.findall(r"'P09_XREF_BIND_(SOURCE_READ_[A-Z_]+_FAILED)'",q.text(ACTIVE)))
        c.require(len(codes)==18,'EIGHT_BOOLEAN_NINE_GETTERS_ONE_SOURCE_LEASE_CODES')
        for code in sorted(codes):
            notice=io.result_notice(dict(state='fixed_eight_callbacks_failed_or_partial',phase='fixed_eight',
                case_failure=dict(case_index=1,phase='source_bind',error_code='P09_XREF_BIND_'+code)))
            c.require(notice['failed_case_error_code']=='P09_XREF_BIND_'+code and notice['native_execution_authorized']is False
                and notice['rerun_forbidden']is True,'ALL_EIGHTEEN_CODES_SURVIVE_CLOSED_NOTICE_WITHOUT_AUTHORITY')
        row['closed_notice_codes_verified']=len(codes);ast.parse(q.text(SELF))
        expected=set(re.findall(r"test (source_bind_diagnostic::[A-Za-z0-9_]+) \.\.\. ok",q.text(MODEL)))
        c.require(len(expected)==5,'FIVE_FIXED_MODEL_GROUPS')
        expected-=retained
        shell=a.AcceptanceReader(Path(PS).parent,guard.check);shell.pin(Path(PS).name)
        ps_models(guard,row,expected);shell.finish();q.finish();guard.check(force=True)
        row.update(state='PASS_SOURCE_BIND_DIAGNOSTICS_77_EQUIVALENT_PAIRS_NINE_GETTER_FAULTS_NOT_NATIVE_OR_GATE',
            admission_pairs=77,getter_faults=9,model_groups=5,external_shell_final_fresh_hashes=shell.final_fresh_hashes,
            full_original_body_inverse_verified=True,early_null_getter_rejection_added=True,raw_document_values_or_exception_messages_emitted=False)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'SOURCE_BIND_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),source_pins=[]if q is None else list(q.snapshots.values()),
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,resource_samples=samples,
            elapsed_seconds=round(time.monotonic()-started,3),system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,output,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[dict(stage=s['stage'],exit_code=s.get('exit_code'),cases=len(s.get('tests',[])),errors=s.get('closed_model_errors',[]),cleanup=s['cleanup'])for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2

if __name__=='__main__':raise SystemExit(main())
