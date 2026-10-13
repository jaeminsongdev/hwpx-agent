"""Current durable adapter example tests only; original source/executables preserved.

Not a SQL build admission and never restamps historical executables. The exact
two original source bodies are restored before accepting the declared delta.
"""
import argparse
import base64
import hashlib
import json
import re
import subprocess
import sys
import time
from unittest.mock import patch

import run_aead_dependency_signed_tests as base
import run_compression_full_stored as capture
from current_issuer_build_inputs import rust_inputs
from issuer_sql_build_contract import CURRENT_BUILD_PIN
from live_sql_evidence_reader import LiveSQLReader
from sql_owned_execution import scoped_path
from sql_runtime_supervision import SQLRuntimeResources,finish_watcher

c = base.c
SELF = 'tools/p09/run_signed_durable_example_tests.py'
TASK = 'p150-signed-durable-example-tests'
DIRECT_ROOT = 'p150-signed-durable-direct-root-tests'
DIRECT_CRATE = 'p150-signed-durable-direct-crate-tests'
ARGS = ['test','-p','hwpx-agent-cli','--example','formula_issuer_product_postgres_probe']
TARGET = c.ROOT/'target/p09-150-signed-durable/build'
BINARY = 'target/p09-150-signed-durable/build/debug/examples/formula_issuer_product_postgres_probe-05e8ead2b3796168.exe'
ROOT_SOURCE = 'crates/product-cli/examples/formula_issuer_product_postgres_probe.rs'
PROVIDER_SOURCE = 'crates/product-cli/examples/formula_issuer_product_postgres_probe/source.rs'
BACKEND_SOURCE = 'crates/product-cli/examples/formula_issuer_product_postgres_probe/durable.rs'
ARCHIVE = 'implementation/p09/source-archive/p09-150-pre-durable-consumer-r26/example-preimages.v1.json'
DRIVERS = 'implementation/p09/source-archive/p09-150-pre-durable-consumer-r27/driver-build-preimages.v1.json'
BASE_INVENTORY = 'implementation/p09/evidence/p09-149-aead-dependency.inventory-run02.v1.json'
TEST_NAMES = (
    'legacy_memory_mode_and_shared_clone_unchanged','partial_or_noncanonical_driver_selection_denied',
    'root_owner_mismatch_or_extra_initial_files_denied','local_publish_duplicate_reopen_and_whole_bytes',
    'local_quarantine_relocation_retains_whole_bytes','owner_change_denies_reopen_and_reads',
    'local_ciphertext_bound_retained','debug_never_discloses_owned_path')
ORIGINAL_TEST_COUNT = 11
TOTAL_TEST_COUNT = ORIGINAL_TEST_COUNT+len(TEST_NAMES)


def strip_extension(text,label):
    pattern = r'(?m)^    // P150 owned-local extension: '+re.escape(label)+r'\n.*?^    // End P150 owned-local extension\.\n'
    result,count = re.subn(pattern,'',text,flags=re.DOTALL)
    c.require(count == 1,'P150_EXACT_EXTENSION_SCOPE');return result


def restore_original(name,text):
    if name == ROOT_SOURCE:
        module = '#[path = "formula_issuer_product_postgres_probe/durable.rs"]\nmod durable;\nuse durable::ProbeBlobStore;\n'
        c.require(text.count(module)==1 and text.count('            blobs: &blobs,\n')==1,'P150_ROOT_DECLARED_DELTA_SCOPE')
        text = text.replace(module,'').replace('            blobs: &blobs,\n','')
        text = strip_extension(text,'original RAM mode and assertions are unchanged.')
        for new,old,count in (
            ('ArtifactService<LocalPostgresMetadataRepository, ProbeBlobStore, ProbeRootScanner>','ArtifactService<LocalPostgresMetadataRepository, InMemoryBlobStore, ProbeRootScanner>',1),
            ('Result<(Service, ProbeBlobStore)>','Result<(Service, InMemoryBlobStore)>',1),
            ('let blobs = ProbeBlobStore::from_driver_env()?;','let blobs = InMemoryBlobStore::default();',1)):
            c.require(text.count(new)==count,'P150_ROOT_REPLACEMENT_SCOPE');text=text.replace(new,old)
        return text
    c.require(name == PROVIDER_SOURCE and text.count("    pub blobs: &'a super::ProbeBlobStore,\n")==1
        and text.count('    super::ProbeBlobStore,\n')==1,'P150_PROVIDER_DECLARED_DELTA_SCOPE')
    return strip_extension(text,"retain original fresh signed authority checks.").replace(
        "    pub blobs: &'a super::ProbeBlobStore,\n",'').replace('    super::ProbeBlobStore,\n','    super::InMemoryBlobStore,\n')


def load_binding():
    r = SQLRuntimeResources();row = {}
    try:
        r.admit();q = LiveSQLReader(r);old = q.json(BASE_INVENTORY)
        c.require(old['state']=='PASS_SCOPED_NOT_GATE' and old['compiled_inventory_exact']
            and old['cleanup_confirmed'] and old['owned_tree_empty'],'P150_HISTORICAL_SOURCE_BASE_REQUIRED')
        expected = {p['path']:p for p in old['source_freeze']}
        c.require(len(expected)==len(old['source_freeze']),'P150_SOURCE_BASE_DUPLICATE')
        archive = q.json(ARCHIVE);seen = set()
        for p in archive['files']:
            name=p['path'];raw=base64.b64decode(p['base64'],validate=True);pin={k:p[k] for k in ('path','bytes','sha256')}
            c.require(name in (ROOT_SOURCE,PROVIDER_SOURCE) and name not in seen and expected[name]==pin
                and len(raw)==p['bytes'] and hashlib.sha256(raw).hexdigest()==p['sha256'],'P150_ORIGINAL_WHOLE_PREIMAGE_DRIFT')
            current=q.text(name);restored=restore_original(name,current)
            # Input originals use CRLF. Restore their WHOLE original byte identity.
            recovered=restored.replace('\n','\r\n').encode('utf-8') if b'\r\n' in raw else restored.encode('utf-8')
            c.require(recovered==raw,'P150_ORIGINAL_BODY_OR_ASSERTION_CHANGED')
            expected[name]=q.pin(name);seen.add(name)
        c.require(seen=={ROOT_SOURCE,PROVIDER_SOURCE},'P150_ORIGINAL_PREIMAGE_SCOPE')
        for name,pin in expected.items():c.require(q.pin(name)==pin,'P150_UNDECLARED_SOURCE_DRIFT')
        drivers=q.json(DRIVERS)
        for p in drivers['files']:
            raw=base64.b64decode(p['base64'],validate=True);pin={k:p[k] for k in ('path','bytes','sha256')}
            c.require(len(raw)==p['bytes'] and hashlib.sha256(raw).hexdigest()==p['sha256']
                and q.pin(p['path'])==pin,'P150_ORIGINAL_BUILD_RUNTIME_HELPER_DRIFT')
            expected[p['path']]=pin
        source=q.text(BACKEND_SOURCE)
        c.require(set(re.findall(r'#\[test\]\s+fn ([a-z_]+)\(',source))==set(TEST_NAMES)
            and len(re.findall(r'#\[test\]',source))==8,'P150_EXACT_BACKEND_TEST_SOURCE_REQUIRED')
        c.require(len(re.findall(r'#\[test\]',q.text(PROVIDER_SOURCE)))==ORIGINAL_TEST_COUNT,
            'SIGNED_DURABLE_ORIGINAL_SOURCE_TESTS_RETAINED')
        expected[BACKEND_SOURCE]=q.pin(BACKEND_SOURCE)
        selected={n for n in expected if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/')) and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
        c.require(rust_inputs(c.ROOT,r.checkpoint_io)==selected and len(selected)==784,'P150_COMPLETE_CURRENT_RUST_INPUTS_REQUIRED')
        c.require(q.pin(CURRENT_BUILD_PIN['path'])==CURRENT_BUILD_PIN,'P150_PROTECTED_HISTORY_RECEIPT_DRIFT')
        history=q.json(CURRENT_BUILD_PIN['path']);protected=history['protected_executables']
        c.require(len(protected)==50 and history['protected_executables_exact_after']
            and len({p['path'] for p in protected})==50,'P150_PROTECTED_HISTORY_SCOPE')
        for p in protected:
            c.require(q.pin(p['path'])==p and not (c.ROOT/p['path']).is_relative_to(TARGET),'P150_PROTECTED_EXECUTABLE_DRIFT')
            c.require(p['path'] not in expected or expected[p['path']]==p,'P150_PROTECTED_EXECUTABLE_CONFLICT')
            expected[p['path']]=p
        for name in (SELF,ARCHIVE,DRIVERS,BASE_INVENTORY,CURRENT_BUILD_PIN['path']):expected[name]=q.pin(name)
        q.finish();return expected,protected
    finally:c.require(finish_watcher(r,row),'P150_SOURCE_WATCHER_CLEANUP_FAILED')


def validate_output(output):
    c.require(re.findall(r'(?m)^running ([0-9]+) tests\r?$',output)==[str(TOTAL_TEST_COUNT)] and
        re.findall(r'test result: ok\. (\d+) passed; (\d+) failed; (\d+) ignored; (\d+) measured; (\d+) filtered out;',output)==[(str(TOTAL_TEST_COUNT),'0','0','0','0')],
        'SIGNED_DURABLE_EXACT_COMPLETE_EXAMPLE_TEST_RESULT_REQUIRED')


def worker(task):
    c.require(task in (TASK,DIRECT_ROOT,DIRECT_CRATE),'P150_WORKER_TASK_SCOPE')
    call=subprocess.call
    def selected(args,**kw):
        c.require(args[1:]==[*ARGS,'--locked','--offline','--jobs','1','--color=never','--target-dir',str(TARGET),'--','--test-threads=1'],
            'P150_WORKER_EXACT_SCOPE')
        env=dict(kw['env'])
        for name in ('P150_BLOB_ROOT','P150_BLOB_RUN_ID','P150_BLOB_MODE'):env.pop(name,None)
        env['RUST_TEST_NOCAPTURE']='0';kw['env']=env
        if task != TASK:
            kw['cwd']=c.ROOT if task == DIRECT_ROOT else c.ROOT/'crates/product-cli'
            return call([str(c.ROOT/BINARY),'--test-threads=1','--format=terse'],**kw)
        # No ambient compiler override may silently replace the declared assertion/profile flags.
        c.require(all(not env.get(k) for k in ('RUSTFLAGS','CARGO_ENCODED_RUSTFLAGS','RUSTC_WRAPPER','RUSTC_WORKSPACE_WRAPPER')),
            'SIGNED_DURABLE_AMBIENT_COMPILER_OVERRIDE_DENIED')
        compile_args=[args[0],*[v for e in base.CONFIG for v in ('--config',e)],*args[1:-2],'--no-run']
        process=subprocess.Popen(compile_args,cwd=c.ROOT,env=env,stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=kw['creationflags'])
        bounded=base.signed.bounded.BoundedProcessCapture(process)
        try:
            while True:
                try:output,errors=bounded.communicate(timeout=0.5);break
                except subprocess.TimeoutExpired:bounded.progress()
            if process.returncode!=0:
                for code in sorted(set(re.findall(r'(?m)^error\[(E[0-9]{4})\]:',errors))):
                    print('P150_COMPILER_ERROR:'+code,file=sys.stderr)
                raise ValueError('SIGNED_DURABLE_COMPILE_ONLY_FAILED')
            artifacts=re.findall(r'(?m)^\s*Executable\s+unittests[^\r\n]*\(([^\r\n]+\.exe)\)\r?$',errors)
            c.require(len(artifacts)==1,'SIGNED_DURABLE_EXACT_COMPILED_TEST_ARTIFACT_REQUIRED')
            artifact=scoped_path((c.ROOT/artifacts[0]).relative_to(c.ROOT).as_posix())
            c.require(artifact.is_file() and artifact.parent==TARGET/'debug/examples'
                and re.fullmatch(r'formula_issuer_product_postgres_probe-[0-9a-f]{16}\.exe',artifact.name),
                'SIGNED_DURABLE_TEST_ARTIFACT_SCOPE')
            from audit_evidence_io import AuditEvidenceReader
            reader=AuditEvidenceReader(c.ROOT,lambda:None);pin=reader.fresh_pin(artifact.relative_to(c.ROOT).as_posix());reader.finish()
            print('P150_COMPILED_TEST:'+artifact.name+':'+str(pin['bytes'])+':'+pin['sha256'],flush=True)
            print('P150_COMPILE_ONLY_OK',file=sys.stderr,flush=True)
        finally:bounded.close()
        # Keep the production root guard intact. Cargo's package CWD is not the driver's CWD.
        return call([str(artifact),'--test-threads=1','--format=terse'],**kw)
    with patch.object(c,'TARGET',TARGET),patch.object(c,'TASKS',{task:ARGS}),patch.object(subprocess,'call',selected):return c.worker(task)


def run_owned(destination,expected,protected,task=TASK):
    c.require(task in (TASK,DIRECT_ROOT,DIRECT_CRATE),'P150_CURRENT_TASK_SCOPE')
    original_pins=c.pins;dump=json.dump;captures=[];post_hash_revalidated=False
    minimum=15 if task==TASK else 10
    class Capture(capture.FullCapture):
        def __init__(self,*a,**kw):
            super().__init__(*a,**kw);self.closed_exception=None;captures.append(self)
        def communicate(self,timeout):
            try:return super().communicate(timeout)
            except subprocess.TimeoutExpired:raise
            except (ValueError,OSError,TypeError,KeyError,AttributeError) as error:
                import traceback
                self.closed_exception=dict(exception_type=type(error).__name__,
                    locations=[dict(file=t.filename.rsplit('/',1)[-1].rsplit('\\',1)[-1],line=t.lineno)
                        for t in traceback.extract_tb(error.__traceback__)[-3:]])
                raise ValueError('SIGNED_DURABLE_CAPTURE_OPERATION_NOT_ACCEPTED') from None
        def diagnostics(self):
            row=super().diagnostics()
            row['complete_result_accepted']=self.accepted
            row['closed_exception']=self.closed_exception
            with self.lock:
                output=bytes(self.buffers['stdout']).decode('utf-8',errors='replace')
                errors=bytes(self.buffers['stderr']).decode('utf-8',errors='replace')
            row['running_test_counts']=re.findall(r'(?m)^running ([0-9]+) tests\r?$',output)
            row['test_summary_numbers']=re.findall(r'test result: ok\. (\d+) passed; (\d+) failed; (\d+) ignored; (\d+) measured; (\d+) filtered out;',output)
            row['compile_only_completed']=errors.count('P150_COMPILE_ONLY_OK')==1
            row['compiled_test_artifact']=re.findall(r'(?m)^P150_COMPILED_TEST:(formula_issuer_product_postgres_probe-[0-9a-f]{16}\.exe):([0-9]+):([0-9a-f]{64})\r?$',output)
            row['closed_compiler_error_codes']=sorted(set(re.findall(r'(?m)^P150_COMPILER_ERROR:(E[0-9]{4})\r?$',errors)))
            names=set(re.findall(r'(?m)^    durable::tests::([a-z_]+)\r?$',output))
            row['failed_test_names']=sorted(names.intersection(TEST_NAMES))
            row['unclassified_failed_test_name_observed']=bool(names.difference(TEST_NAMES))
            row['closed_test_error_codes']=sorted(set(re.findall(r'(?m)^Error: (StorageFailure|AccessDenied|IntegrityMismatch|CryptoFailure|InvalidState)\r?$',errors+'\n'+output)))
            return row
    def pins(checkpoint=None):
        nonlocal post_hash_revalidated
        rows=original_pins(checkpoint);actual={p['path']:p for p in rows}
        c.require(all(actual.get(n)==p for n,p in expected.items()),'P150_CURRENT_INPUT_OR_PROTECTED_EXE_DRIFT');return rows
    def guarded_pins(checkpoint=None):
        nonlocal post_hash_revalidated
        rows=pins(checkpoint)
        if not post_hash_revalidated:
            # Admission before a long hash pass can be stale. Recheck BEFORE worker creation.
            r=SQLRuntimeResources();state={}
            try:
                r.admit();count=0;deadline=time.monotonic()+c.POLICY['admission_max_seconds']
                while time.monotonic()<deadline:
                    time.sleep(c.POLICY['sample_seconds']);sample=r.sample()
                    c.require(not r.stop.is_set(),r.reason or 'P150_POST_HASH_RESOURCE_STOP')
                    count=base.BASE_ADMITTED_COUNT(sample,count) if sample['available_ram_percent']>=minimum else 0
                    if count>=c.POLICY['start_consecutive_samples']:break
                c.require(count>=c.POLICY['start_consecutive_samples'],'P150_POST_HASH_STABLE_RESOURCE_WINDOW_REQUIRED')
                post_hash_revalidated=True
            finally:c.require(finish_watcher(r,state),'P150_POST_HASH_WATCHER_CLEANUP_FAILED')
        return rows
    def write(row,stream,**kw):
        observed=captures[-1] if captures else None
        accepted=bool(observed and observed.accepted and row['state']=='PASS_SCOPED_NOT_GATE' and row.get('tests_passed')==TOTAL_TEST_COUNT)
        if task==TASK and accepted:
            report=observed.diagnostics()
            accepted=report['compile_only_completed'] and len(report['compiled_test_artifact'])==1
        if row['state']=='PASS_SCOPED_NOT_GATE' and not accepted:row.update(state='STOPPED_NOT_ACCEPTED',stop_reason='P150_CURRENT_EXAMPLE_TEST_RESULT_MISSING')
        row.update(example_backend_tests_qualified=accepted,original_root_and_provider_whole_bodies_restored_exact=True,
            original_source_tests_retained=ORIGINAL_TEST_COUNT,new_backend_tests=len(TEST_NAMES),expected_example_test_count=TOTAL_TEST_COUNT,
            original_build_runtime_helpers_changed=False,whole_workspace_Rust_input_count=784,protected_executables=protected,
            protected_executables_exact_after=accepted,current_SQL_build_admission_qualified=False,
            actual_SQL_or_native_executed=False,durable_signed_SQL_consumer_qualified=False,
            same_process_backend_tests_only=True,independent_restart_or_key_custody_qualified=False,
            capture_diagnostics=observed.diagnostics() if observed else None,test_package_profile_config=list(base.CONFIG),
            compile_admission_RAM_percent=minimum,post_hash_stable_admission_revalidated=post_hash_revalidated,
            execution_kind='owned_compile_no_run_then_exact_test_binary_repository_CWD' if task==TASK else 'already_compiled_test_binary_CWD_diagnostic',
            diagnostic_working_directory='repository' if task==DIRECT_ROOT else ('package' if task==DIRECT_CRATE else None),
            source_variant='p150-original-root-source-body-preserved-owned-local-adapter',
            PC_freeze_resolved=False,product_complete=False,P09_gate='OPEN')
        return dump(row,stream,**kw)
    with patch.object(c,'__file__',str(c.ROOT/SELF)),patch.object(c,'TARGET',TARGET),patch.object(c,'TASKS',{task:ARGS}), \
            patch.object(c,'SOURCES',list(dict.fromkeys([*c.SOURCES,*expected]))),patch.object(c,'pins',guarded_pins), \
            patch.object(c,'admitted_count',lambda row,count:base.admission_count(base.INVENTORY if task==TASK else base.PROFILE,row,count)), \
            patch.object(capture,'validate_output',validate_output),patch.object(capture.bounded,'BoundedProcessCapture',Capture), \
            patch.object(json,'dump',write):return c.run(task,destination,600 if task==TASK else 60)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',type=int,choices=range(1,100),required=True)
    parser.add_argument('--diagnostic-cwd',choices=('root','crate'))
    args=parser.parse_args();c.require(c.Path.cwd().resolve()==c.ROOT,'P150_ROOT_SCOPE')
    target=scoped_path(TARGET.relative_to(c.ROOT).as_posix());target.mkdir(parents=True,exist_ok=True)
    destination=scoped_path(f'implementation/p09/evidence/p09-150-signed-durable-example.actual-run{args.run:02}.v1.json',fresh=True)
    expected,protected=load_binding();task=TASK
    if args.diagnostic_cwd:
        task=DIRECT_ROOT if args.diagnostic_cwd=='root' else DIRECT_CRATE
        r=SQLRuntimeResources();state={}
        try:
            r.admit();q=LiveSQLReader(r);expected[BINARY]=q.pin(BINARY);q.finish()
        finally:c.require(finish_watcher(r,state),'P150_BINARY_WATCHER_CLEANUP_FAILED')
    return run_owned(destination,expected,protected,task)


if __name__=='__main__':
    if len(sys.argv[1:])==3 and sys.argv[1:3]==['--owned-worker','--task']:raise SystemExit(worker(sys.argv[3]))
    try:raise SystemExit(main())
    except (ValueError,OSError,KeyError,TypeError,subprocess.SubprocessError) as error:
        code=str(error) if isinstance(error,ValueError) and re.fullmatch('[A-Z_]+',str(error)) else 'P150_OPERATION_NOT_ACCEPTED'
        print(json.dumps({'state':'FAILED_NOT_ACCEPTED','error_code':code}));raise SystemExit(2) from None
