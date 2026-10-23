"""Six owned file-sharing models + five new common recovery cases, no SQL or Native replay."""
import ast,hashlib,json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import verify_paragraph_detail_search as inventory
import verify_style_predicate_search as includes
import verify_character_detail_search as tests
import verify_source_field_semantics as deps
import crossref_inline_receipt567 as layout

SELF='tools/p09/verify_source_lease_and_common_recovery568.py'
OUTPUT='implementation/p09/evidence/p09-361-source-lease-and-common-recovery568.v1.json'
PRIOR=OUTPUT
RECOVERY_ARCHIVE='implementation/p09/source-archive/p361-source-lease569/'
ACTIVE='implementation/p09/tools/crossref-owned-active-source.ps1'
MODEL='implementation/p09/tools/test-crossref-source-lease568.ps1'
FIXTURE='implementation/p09/tools/fixtures/source-lease-share568.txt'
BEFORE='implementation/p09/source-archive/p361-source-lease568/active-source-before.ps1'
HOST='crates/product-cli/tests/stored_https_target_product.rs'
TEST='crates/product-cli/tests/support/stored_https_common_recovery566.rs'
REQUEST='crates/product-cli/tests/support/stored_https_request.rs'
DISPATCH='crates/product-cli/src/form_product_request/stored_operations/https_targets/dispatch.rs'
RECOVERY=DISPATCH[:-3]+'/recovery.rs'
ARCHIVE='implementation/p09/source-archive/p361-common-request-recovery566/'
PS='C:/Windows/SysWOW64/WindowsPowerShell/v1.0/powershell.exe'
PS_CASES={'lease568::'+v for v in('five_closed_hresult_categories','wrapped_exception_keeps_closed_inner_category',
    'unknown_and_overdeep_errors_fail_closed_without_raw_values','existing_writer_rejects_read_only_share_even_without_writes',
    'two_shared_read_handles_are_compatible','owned_fixture_bytes_unchanged_and_all_handles_disposed')}

def models(guard,row,after569=False):
    owned=capture=None;started=time.monotonic();step=dict(stage='closed_lease_errors_and_owned_file_sharing',cleanup=False);row['steps'].append(step)
    try:
        command=[PS,'-NoLogo','-NoProfile','-NonInteractive','-STA','-File',str(r.c.ROOT/MODEL),'-ModelsOnly']
        if after569:command.append('-FileSharingOnlyAfter569')
        expected=PS_CASES-{'lease568::'+v for v in('five_closed_hresult_categories','wrapped_exception_keeps_closed_inner_category','unknown_and_overdeep_errors_fail_closed_without_raw_values')}if after569 else PS_CASES
        owned=r.shared.OwnedSQLJobProcess(command,
            windows=guard.windows,allowed_executables=[PS],cwd=r.c.ROOT,checkpoint=guard.check,env=r.audit.environment())
        capture=r.shared.BoundedProcessCapture(owned,output_limit=32768,parse_markers=False)
        while True:
            guard.check();r.c.require(time.monotonic()-started<30,'LEASE568_MODELS_DEADLINE')
            try:out,err=capture.communicate(timeout=.5);owned.observe();break
            except subprocess.TimeoutExpired:capture.progress();owned.observe()
        found=re.findall(r'(?m)^test ([A-Za-z0-9_:]+) \.\.\. (ok|FAILED)\r?$',out)
        step.update(exit_code=owned.returncode,tests=found,stdout_bytes=len(out.encode()),stderr_bytes=len(err.encode()),
            stdout_sha256=hashlib.sha256(out.encode()).hexdigest(),stderr_sha256=hashlib.sha256(err.encode()).hexdigest(),
            closed_model_errors=re.findall(r'LEASE_MODEL_RUNTIME_[A-Za-z0-9]+_LINE_[0-9]{1,6}',err))
        r.c.require(owned.returncode==0 and not err and len(found)==len(expected) and {n for n,s in found}==expected
            and all(s=='ok'for n,s in found),'LEASE568_SIX_NEW_MODELS_PASS_NO_RAW_EXCEPTIONS')
    finally:
        if owned is not None:
            # This Job can own only the mock-model PowerShell, never Hancom.
            owned.kill();owned.wait(timeout=2)
            if capture is not None:capture.close()
            owned.close();step.update(cleanup=owned.profile['cleanup_confirmed'],owned_job=owned.profile)
        step['elapsed_seconds']=round(time.monotonic()-started,3)

def main():
    c,a,shared=r.c,r.a,r.shared;recover=sys.argv[1:]==['--after568-model-fixture-only'];after569=sys.argv[1:]==['--after569-remaining-models-and-five']
    c.require(after569 or recover or sys.argv[1:]==['--new-models-and-five-product-cases'],'LEASE568_CLOSED_MODE')
    output=OUTPUT.replace('568.v1','570.v1'if after569 else'569.v1')if recover or after569 else OUTPUT
    c.require(not(c.ROOT/output).exists(),'LEASE568_IMMUTABLE_RESULT')
    selected=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    started=time.monotonic();q=artifact=None
    row=dict(state='FAILED_SOURCE_LEASE_AND_COMMON_RECOVERY',steps=[],own_cpu_selection=selected,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        actual_Hancom_COM_SQL_or_Native_started=False,previous_Native_or_249_or_passed_product_bodies_replayed=False,
        original004_receipt_reconstructed=False,external005_authorized=False,actual004_sharing_violation_confirmed=False,
        original_owner_source_lease_or_policy_guards_weakened=False,operating_registry_worker_route_or_custody_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        names=inventory.inventory(guard)|includes.test_inputs((HOST,),guard)|{SELF,ACTIVE,MODEL,FIXTURE,BEFORE,
            'implementation/p09/tools/sdk-baseline-owned-session.ps1',DISPATCH,RECOVERY,REQUEST,TEST,
            ARCHIVE+'dispatch-before.rs',ARCHIVE+'request-tests-before.rs',
            'tools/p09/crossref_inline_receipt567.py','tools/p09/test_crossref_inline_receipt567.py',
            'implementation/p09/evidence/p09-361-external004-postmortem567.v1.json'}
        if recover:names|={PRIOR,RECOVERY_ARCHIVE+'models568.ps1',RECOVERY_ARCHIVE+'verifier568.py'}
        if after569:names|={PRIOR.replace('568.v1','569.v1'),'implementation/p09/source-archive/p361-source-lease570/models569.ps1','implementation/p09/source-archive/p361-source-lease570/verifier569.py'}
        for module in tuple(sys.modules.values()):
            name=getattr(module,'__file__',None)
            if name:
                path=Path(name).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':names.add(path.relative_to(c.ROOT).as_posix())
        for name in sorted(names):q.pin(name)
        if recover:
            failed=layout.unpack(q.json(PRIOR))
            c.require(q.snapshots[PRIOR]['sha256']=='c10b0b7626a21bff38ef1216e883753fc76d33a43ad48e3126145cf3ca08fcaa'
                and failed['cleanup']is True and failed['final_fresh_hashes']==0 and len(failed['steps'])==1
                and failed['steps'][0]['tests']==[],'LEASE569_ORIGINAL568_FAILURE_NO_PASSED_BODY_OR_PRODUCT_EXECUTION')
            corrected=q.text(MODEL).replace('''trap {
    [Console]::Error.WriteLine(('LEASE_MODEL_RUNTIME_{0}_LINE_{1}' -f $_.Exception.GetType().Name,$_.InvocationInfo.ScriptLineNumber))
    exit 1
}
''','',1).replace('$leaseException','$error')
            r.audit.inverse(corrected,q.snapshots[RECOVERY_ARCHIVE+'models568.ps1'],'LEASE569_ONLY_AUTOMATIC_ERROR_VARIABLE_COLLISION_AND_CLOSED_DIAGNOSTICS_FIXED')
            row.update(prior568_failure_preserved=True,original568_product_not_run=True)
        if after569:
            source=PRIOR.replace('568.v1','569.v1');failed=layout.unpack(q.json(source));step,=failed['steps']
            kept=PS_CASES-{'lease568::'+v for v in('existing_writer_rejects_read_only_share_even_without_writes','two_shared_read_handles_are_compatible','owned_fixture_bytes_unchanged_and_all_handles_disposed')}
            c.require(q.snapshots[source]['sha256']=='5b16b96f68edc6fb77440190957666c2f34740ae895ff50a99c469c3dd374a22'
                and failed['cleanup']is True and failed['final_fresh_hashes']==0 and step['exit_code']==1
                and {n for n,s in step['tests']if s=='ok'}==kept and len(step['tests'])==3
                and step['closed_model_errors']==['LEASE_MODEL_RUNTIME_CommandNotFoundException_LINE_28'],'LEASE570_EXACT_THREE_PASSED_BEFORE_MISSING_GETFILEHASH')
            original=q.text('implementation/p09/source-archive/p361-source-lease570/models569.ps1');current=q.text(MODEL)
            start=original.index('$cases=@{');end=original.index("$path=Join-Path",start)
            c.require(original[start:end]==current[current.index('$cases=@{'):current.index("}\n$path=Join-Path")], 'LEASE570_RETAINED_THREE_MODEL_BODIES_IDENTICAL')
            oldpins={p['path']:p for p in failed['source_pins']}
            c.require(q.snapshots[ACTIVE]==oldpins[ACTIVE]and q.snapshots[FIXTURE]==oldpins[FIXTURE],'LEASE570_SAME_ACTIVE_DIAGNOSTIC_AND_OWNED_FIXTURE')
            row.update(prior569_failure_preserved=True,retained_569_model_cases=3,retained_model_names=sorted(kept))
        text=q.text(ACTIVE);begin=text.index('function Get-P09XrefSourceReadLeaseFailureCode(');end=text.index('function Observe-P09XrefOwnedActiveSource {',begin)
        restored=(text[:begin]+text[end:]).replace("catch {throw (Get-P09XrefSourceReadLeaseFailureCode $_.Exception)}", "catch {throw 'P09_XREF_BIND_SOURCE_READ_LEASE_FAILED'}",1)
        r.audit.inverse(restored,q.snapshots[BEFORE],'LEASE568_ENTIRE_ORIGINAL_SOURCE_OWNER_HASH_AND_FILE_SHARE_BODY_PRESERVED')
        r.audit.inverse(q.text(DISPATCH).replace('pub mod recovery;\n','',1),q.snapshots[ARCHIVE+'dispatch-before.rs'],'LEASE568_OLD_COMMON_DISPATCH_AND_SQL_BRIDGE_PRESERVED')
        r.audit.inverse(q.text(REQUEST).replace('#[path="stored_https_common_recovery566.rs"]mod common_recovery;\n','',1),
            q.snapshots[ARCHIVE+'request-tests-before.rs'],'LEASE568_OLD_REQUEST_TEST_BODIES_UNCHANGED_NOT_REPLAYED')
        cases=tests.tests(q,TEST,'requests::common_recovery::');c.require(len(cases)==5,'LEASE568_EXACT_FIVE_NEW_COMMON_RECOVERY_CASES')
        ast.parse(q.text(SELF));ast.parse(q.text('tools/p09/crossref_inline_receipt567.py'))
        models(guard,row,after569=after569);guard.check(force=True)
        scratch=c.ROOT/'target/p09-common-recovery568-scratch';c.require(not scratch.exists(),'LEASE568_FRESH_COMPILER_TEMP');scratch.mkdir()
        env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));artifact=a.AcceptanceReader(c.ROOT,guard.check)
        print(json.dumps(dict(state='COMMON_RECOVERY_FIVE_NEW_CASES_READY',inputs=len(q.snapshots),new_product_cases=5,prior_passed_cases_replayed=0)),flush=True)
        args=[r.harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli','--test','stored_https_target_product','--message-format=short',
            '--',*sorted(cases),'--exact','--test-threads=1']
        r.harness.run_one('common_policy_bound_recovery_five',args,cases,guard,env,row,observe_capture=r.snapshot)
        r.tools.good_step(row['steps'][-1],cases);c.require(not row['steps'][-1]['diagnostics'],'LEASE568_NO_COMPILER_WARNINGS')
        found=[]
        for path in(c.ROOT/'target/debug/deps').glob('stored_https_target_product-*.d'):
            declared=deps.dependencies(path);c.require(declared<=set(q.snapshots),'LEASE568_ACTUAL_COMPILER_INPUTS_PREPINNED')
            found.append(dict(dep_info=artifact.pin(path.relative_to(c.ROOT).as_posix()),dependency_count=len(declared)))
        c.require(len(found)==1,'LEASE568_ONE_HOST_DEP_INFO');row['actual_compile_inputs']=found
        c.require(not any(scratch.iterdir()),'LEASE568_COMPILER_TEMP_EMPTY');artifact.finish();q.finish();guard.check(force=True)
        row.update(state='PASS_SIX_CLOSED_LEASE_MODELS_AND_FIVE_COMMON_RECOVERY_PRODUCT_CASES_NOT_NATIVE_OR_GATE',
            new_file_sharing_models=6,new_common_product_cases=5,compiled_artifact_final_fresh_hashes=artifact.final_fresh_hashes)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        code=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'LEASE568_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),
            source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),
            final_fresh_hashes=0 if q is None else q.final_fresh_hashes,resource_samples=guard.samples,
            elapsed_seconds=round(time.monotonic()-started,3),system_CPU_max=max((s['system_cpu_percent']for s in guard.samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in guard.samples),default=None))
        proof=shared.publisher.publish(c.ROOT,output,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[dict(stage=s['stage'],exit_code=s.get('exit_code'),cleanup=s['cleanup'],diagnostics=s.get('diagnostics',[]))for s in row['steps']],'receipt':proof}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2

if __name__=='__main__':raise SystemExit(main())
