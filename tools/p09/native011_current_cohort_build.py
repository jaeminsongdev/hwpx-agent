"""One build-only generation, preserving old binaries and all product authority."""
import ast
import ctypes
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from types import SimpleNamespace as NS
from unittest.mock import patch

SELF='tools/p09/native011_current_cohort_build.py'
TEST='tools/p09/tests/test_native011_current_cohort_build.py'
PLAN=dict(path='implementation/p09/evidence/p09-361-native011-current-cohort-build-plan001.v1.json',
    bytes=171124,sha256='a12d930bc4d5ecba1451ea8ad76cb7c83e03f973d33fbc2baae27edb6a5f9f83')
PLAN2=dict(path='implementation/p09/evidence/p09-361-native011-current-cohort-build-plan002.v1.json',
    bytes=171138,sha256='1cded389269aba44e29830be23185c19246e7638647ad56f21e4a9edb441c537')
OUTPUT='implementation/p09/evidence/p09-361-native011-current-cohort-build001.v1.json'
INTENT='implementation/p09/evidence/p09-361-native011-current-cohort-build-intent001.v1.json'
OVERRIDES=('RUSTFLAGS','CARGO_ENCODED_RUSTFLAGS','RUSTC_WRAPPER','RUSTC_WORKSPACE_WRAPPER','RUSTC','CARGO_BUILD_TARGET')
START=b'P09_NATIVE011_BUILD_ONLY\n'


def require(ok,code):
    if not ok:raise ValueError('CURRENT_COHORT_BUILD_'+code)


def generation_context(plan,generation):
    target=plan.target_for(generation)
    return NS(**{**vars(plan),'TARGET':target}),PLAN2 if generation==2 else PLAN


def build_environment(environ):
    require(all(not environ.get(n) for n in OVERRIDES),'NO_AMBIENT_COMPILER_OVERRIDE')
    env=dict(environ,CARGO_BUILD_JOBS='1',RUSTUP_AUTO_INSTALL='0',CARGO_INCREMENTAL='0',RUST_TEST_THREADS='1',
        CARGO_PROFILE_TEST_OPT_LEVEL='0',CARGO_PROFILE_TEST_DEBUG='0',CARGO_PROFILE_TEST_CODEGEN_UNITS='16',
        CARGO_PROFILE_TEST_DEBUG_ASSERTIONS='true',CARGO_PROFILE_TEST_OVERFLOW_CHECKS='true',
        CARGO_PROFILE_DEV_DEBUG='0',CARGO_PROFILE_DEV_CODEGEN_UNITS='16',
        CARGO_PROFILE_DEV_DEBUG_ASSERTIONS='true',CARGO_PROFILE_DEV_OVERFLOW_CHECKS='true')
    for name in ('P150_BLOB_ROOT','P150_BLOB_RUN_ID','P150_BLOB_MODE'):env.pop(name,None)
    return env


def check_plan_dependencies(snapshots,pins,fresh,exact):
    """Check declared plan dependencies once, without recursive history expansion."""
    for pin in pins:
        actual=snapshots.get(pin['path'])
        if actual is None:actual=fresh(pin['path'])
        exact(actual,pin,'EXACT_NAMED_PLAN_DEPENDENCY')


def read_build_start(read):
    token=bytearray()
    for _ in range(len(START)+1):
        value=read(1);require(value,'WORKER_BUILD_TOKEN_REQUIRED');token.extend(value)
        if value==b'\n':break
    require(bytes(token) in (START,START.replace(b'\n',b'\r\n')),'WORKER_BUILD_TOKEN_REQUIRED')


def start_capture(owned,guard,factory):
    """Send the fixed build-only token before the original EOF capture closes stdin."""
    owned.observe();guard.check(force=True)
    text=START.decode('ascii')
    require(owned.stdin.write(text)==len(text),'COMPLETE_BUILD_START_WRITE')
    owned.stdin.flush()
    return factory(owned,output_limit=32768,parse_markers=False)


def definitions(raw,a,c,profile,stream,plan):
    """Original complete parser/class bodies; change only two output identities."""
    old=('form_stored_provider-p361-case112-r','extra-filename=-p361-case112-r')
    new=('form_stored_provider-p361-native011-g','extra-filename=-p361-native011-g')
    tree=ast.parse(raw);counts=[0,0]
    class Identities(ast.NodeTransformer):
        def visit_Constant(self,node):
            if type(node.value) is str:
                for i,value in enumerate(old):
                    if node.value==value:
                        counts[i]+=1;return ast.copy_location(ast.Constant(new[i]),node)
            return node
    transformed=Identities().visit(tree);require(counts==[1,1],'EXACT_TWO_IDENTITY_CONSTANTS')
    projected=ast.unparse(transformed)
    inverse=ast.parse(projected)
    class Undo(ast.NodeTransformer):
        def visit_Constant(self,node):
            if type(node.value) is str and node.value in new:
                return ast.copy_location(ast.Constant(old[new.index(node.value)]),node)
            return node
    require(ast.dump(Undo().visit(inverse),include_attributes=False)==ast.dump(ast.parse(raw),include_attributes=False),
        'WHOLE_SOURCE_AST_INVERSE')
    namespace=dict(c=c,profile=profile,stream=stream,json=json,re=re,Path=Path,
        TARGET=c.ROOT/plan.TARGET,RAW_STREAM=stream.CargoStream,
        ARGS=['rustc','-p','hwpx-agent-cli','--test','form_stored_provider','--profile','test'],
        EXPECTED_PROFILE=dict(opt_level='1',debuginfo='line-tables-only',debug_assertions=True,
            overflow_checks=True,test=True))
    return a.native.definitions(projected,('require','task_for','executable_name','direct_path','profile_scope',
        'recipe','CargoStream','parse_build'),namespace)


def worker(*,smoke=False,generation=1):
    if smoke:
        def deny(event,args):
            if event in ('subprocess.Popen','os.system','os.startfile','os.exec','os.posix_spawn','os.fork'):
                raise ValueError('BUILD_START_SMOKE_NO_PROCESS')
        sys.addaudithook(deny)
    import accept_case112_current_epoch as a,conservative_maintenance as c
    import native011_current_cohort_plan as plan,stored_test_profile81 as profile
    import signed_durable_build_stream as stream
    plan,plan_pin=generation_context(plan,generation)
    windows=c.Windows();member=ctypes.c_int()
    require(windows.k.IsProcessInJob(windows.k.GetCurrentProcess(),None,ctypes.byref(member))
        and member.value,'WORKER_INSIDE_OWNED_JOB')
    limits=windows.verify_job_limits(None)
    require(limits['verified'],'WORKER_CURRENT_JOB_LIMITS')
    read_build_start(lambda n:os.read(sys.stdin.fileno(),n))
    if smoke:
        print(json.dumps(dict(state='PASS_OWNED_BUILD_START_TOKEN_ONLY_NOT_CARGO_OR_PRODUCT',
            limits=limits,Cargo_executed=False,product_tests_executed=False)),flush=True)
        return 0
    # Parent has already fresh-checked these exact bytes and placed this child in its Job.
    raw=(c.ROOT/plan.BUILD).read_text(encoding='utf-8')
    module=definitions(raw,a,c,profile,stream,plan)
    expected=json.loads((c.ROOT/plan_pin['path']).read_text(encoding='utf-8'))
    require(module.recipe(generation)==expected['recipe'],'ORIGINAL_RECIPE_EQUALS_PINNED_PLAN')
    executable=c.ROOT/module.executable_name(generation)
    require(not executable.exists(),'FRESH_OUTPUT_ONLY')
    cargo=shutil.which('cargo');require(cargo is not None,'CARGO_AVAILABLE')
    with patch.object(stream,'CargoStream',module.CargoStream):
        return stream.run_command([cargo,*module.recipe(generation)],
            dict(cwd=c.ROOT,stdin=subprocess.DEVNULL,env=build_environment(os.environ)),
            lambda payload:module.parse_build(payload,generation))


def main(generation=1):
    require(sys.argv[1:]==([] if generation==1 else ['--generation2']),'NO_ARBITRARY_PARENT_ARGUMENTS')
    import accept_case112_current_epoch as a,conservative_maintenance as c
    import prepared_run_closure_v1 as host,owned_cpu_baseline_v1 as baseline
    import preparation_attributed_cpu_v1 as policy,distinct_final_sample_guard_v1 as final
    import successor_preparation_workspace_v1 as publisher,current_stored_runtime_scope as scope
    import native011_current_cohort_plan as plan,stored_test_profile81 as profile
    import signed_durable_build_stream as stream,locked_runtime_inputs as locks
    import native011_source_generation_audit as audit,native011_owned_preparation as cleanup
    from owned_sql_job import OwnedSQLJobProcess
    from bounded_process_progress import BoundedProcessCapture
    plan,plan_pin=generation_context(plan,generation)
    output=OUTPUT.replace('build001','build%03d'%generation)
    intent_path=INTENT.replace('intent001','intent%03d'%generation)
    host.configure_host_policy(c)
    g=baseline.guard_type(policy.guard_type(final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;owned=capture=None;primary=None;started=time.monotonic()
    row=dict(state='FAILED_CURRENT805_BUILD_ONLY_NOT_PRODUCT',official_accepted_count=158,
        accepted_count_delta=0,GO_authorized=False,product_tests_executed=False,
        automatic_retry=False,owned=dict(constructor_entered=False,cleanup=False),intent_consumed=False,
        build_generation=generation)
    announcement=time.monotonic()
    def checkpoint():
        nonlocal announcement
        g.check()
        if time.monotonic()-announcement>=15:
            sample=g.samples[-1]
            print(json.dumps(dict(stage=row.get('phase','BUILD_SOURCE_PREPARATION'),
                system_CPU=sample['system_cpu_percent'],available_RAM_percent=sample['available_ram_percent'])),flush=True)
            announcement=time.monotonic()
    try:
        g.acquire();q=a.AcceptanceReader(c.ROOT,checkpoint)
        require(not (c.ROOT/output).exists() and not (c.ROOT/intent_path).exists(),'ONE_BUILD_GENERATION_ONLY')
        declaration=a.read_exact(q,plan_pin)
        require(declaration['state']=='PREPARED_CURRENT805_COHORT_BUILD_PLAN_NOT_BUILD_LIST_OR_RUNTIME'
            and declaration['full805_current_freshness_qualified'] is False,'PLAN_NOT_RUNTIME')
        expected=scope.pins(declaration['expected_Rust_inputs'],805)
        for name in (SELF,TEST,plan.SELF,plan.TEST,plan.BUILD,'tools/p09/current_issuer_build_inputs.py',
                     'Cargo.toml','Cargo.lock','rust-toolchain.toml'):q.pin(name)
        # Every currently imported project helper is explicit build input, never hidden.
        for module in tuple(sys.modules.values()):
            source=getattr(module,'__file__',None)
            if source:
                path=Path(source).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09') and path.suffix=='.py':
                    q.pin(path.relative_to(c.ROOT).as_posix())
        code=a.native.definitions(q.text('tools/p09/current_issuer_build_inputs.py'),('rust_inputs',),
            dict(require=c.require,Path=Path,os=os))
        pacer=locks.OpenPacer(g.check,rate=20)
        require(code.rust_inputs(c.ROOT,pacer.reserve)==set(expected),'LIVE_SOURCE805_BEFORE')
        for name,pin in sorted(expected.items()):a.exact(q.pin(name),pin,'FRESH_CURRENT805_BEFORE_BUILD')
        check_plan_dependencies(q.snapshots,declaration['source_pins'],q.pin,a.exact)
        a.exact(q.pin(scope.EXE_PIN['path']),scope.EXE_PIN,'OLD_BINARY_UNCHANGED_BEFORE')
        module=definitions(q.text(plan.BUILD),a,c,profile,stream,plan)
        require(module.recipe(generation)==declaration['recipe'],'RECIPE_PLAN_MATCH')
        module.direct_path(c.ROOT/plan.TARGET)
        require(not (c.ROOT/plan.TARGET).exists(),'FRESH_ISOLATED_TARGET')
        env=build_environment(os.environ);g.check(force=True)
        intent=dict(state='CONSUMED_CURRENT805_BUILD_ONLY_INTENT_NOT_PRODUCT',plan_pin=plan_pin,
            product_tests_authorized=False,automatic_retry=False,official_accepted_count=158)
        row['intent_pin']=publisher.publish(c.ROOT,intent_path,intent,NS(require=c.require,exact=a.exact))
        row['intent_consumed']=True;row['owned']['constructor_entered']=True
        command=[sys.executable,'-B',str(c.ROOT/SELF),'--build-worker' if generation==1 else '--build-worker-g002']
        owned=OwnedSQLJobProcess(command,windows=g.windows,allowed_executables=[sys.executable],
            cwd=c.ROOT,checkpoint=g.check,env=env)
        capture=start_capture(owned,g,BoundedProcessCapture)
        row['phase']='BUILD_ONLY_NO_PRODUCT'
        announcement=time.monotonic()
        while True:
            g.check()
            try:out,err=capture.communicate(timeout=.5)
            except subprocess.TimeoutExpired:
                capture.progress();accounting=owned.observe()
                if time.monotonic()-announcement>=15:
                    sample=g.samples[-1]
                    print(json.dumps(dict(stage='BUILD_ONLY_NO_PRODUCT',system_CPU=sample['system_cpu_percent'],
                        available_RAM_percent=sample['available_ram_percent'],
                        job_private_mib=accounting['peak_job_private_mib'])),flush=True)
                    announcement=time.monotonic()
                continue
            owned.observe();row.update(build_exit_code=owned.returncode,stderr_bytes=len(err.encode()),
                stderr_sha256=hashlib.sha256(err.encode()).hexdigest(),
                worker_closed_errors=re.findall(r'(?m)^ValueError: ([A-Z][A-Z0-9_]{1,159})$',err)[-8:])
            require(owned.returncode==0 and not err,'CLEAN_BUILD_ONLY_WORKER')
            build=module.parse_build(out,generation);row['build_proof']=build
            artifact=module.executable_name(generation);row['artifact_pin']=q.pin(artifact)
            break
        row['phase']='BUILD_SOURCE_CLOSING'
        require(code.rust_inputs(c.ROOT,pacer.reserve)==set(expected),'LIVE_SOURCE805_AFTER')
        q.finish();g.check(force=True)
        require(q.final_fresh_hashes==len(q.snapshots),'FULL_CURRENT_CLOSING')
        row.update(state='PASS_CURRENT805_BUILD_ONLY_NOT_LISTING_RUNTIME_OR_GATE',
            full805_current_source_bytes_verified=True,current_test_binary_built=True,
            old_binary_preserved=True,source_inventory_before_after=True,
            full249_current_qualified=False,official158_preserved_not_replayed=True,
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,IndexError,TypeError,AttributeError,ArithmeticError,subprocess.SubprocessError) as error:
        primary=error;row['first_failure']=cleanup.failure_record(error,g.samples)
    finally:
        try:cleanup.cleanup_owned(owned,capture,row['owned'],primary)
        except (ValueError,OSError,subprocess.SubprocessError) as error:
            row.update(state='FAILED_CURRENT805_BUILD_CLEANUP_NOT_PRODUCT',
                cleanup_failure=cleanup.failure_record(error,[]))
        finally:
            g.close();row.update(cleanup_confirmed=g.cleanup and row['owned'].get('cleanup',False),
                elapsed_seconds=time.monotonic()-started,source_pins=[] if q is None else list(q.snapshots.values()),
                resource_summary=audit.sample_summary(g.samples))
        receipt=publisher.publish(c.ROOT,output,row,NS(require=c.require,exact=a.exact))
        print(json.dumps(dict(state=row['state'],failure=row.get('first_failure'),
            cleanup=row['cleanup_confirmed'],elapsed=row['elapsed_seconds'],intent_consumed=row['intent_consumed'],
            artifact=row.get('artifact_pin'),fresh=row.get('fresh_inputs'),final=row.get('final_fresh_hashes'),
            receipt=receipt)),flush=True)
    return 0 if row['state'].startswith('PASS_') and row['cleanup_confirmed'] else 2


if __name__=='__main__':
    if sys.argv[1:]==['--start-smoke-worker']:raise SystemExit(worker(smoke=True))
    if sys.argv[1:]==['--build-worker']:raise SystemExit(worker())
    if sys.argv[1:]==['--build-worker-g002']:raise SystemExit(worker(generation=2))
    raise SystemExit(main(2 if sys.argv[1:]==['--generation2'] else 1))
