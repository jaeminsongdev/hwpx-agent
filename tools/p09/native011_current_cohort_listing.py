"""List one pinned 805-source cohort binary; never execute test bodies or Cargo."""
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from types import SimpleNamespace as NS

SELF='tools/p09/native011_current_cohort_listing.py'
TEST='tools/p09/tests/test_native011_current_cohort_listing.py'
BUILD=dict(path='implementation/p09/evidence/p09-361-native011-current-cohort-build002.v1.json',
    bytes=167281,sha256='7e4aeb5ace1b81b36e6aa5b246c4b10171ec7446f6eef9f32edad68fe9ccba8d')
EXE=dict(path='target/p09-361-native011-current-source-g002/debug/deps/form_stored_provider-p361-native011-g002.exe',
    bytes=14174720,sha256='1e782c2551ff96c191b1ab2aa6c86650f1c43676cb8c0db2b0c27613095925d8')
OUTPUT='implementation/p09/evidence/p09-361-native011-current-cohort-listing001.v1.json'


def require(ok,code):
    if not ok:raise ValueError('COHORT_LISTING_'+code)


def build_contract(row):
    require(row['state']=='PASS_CURRENT805_BUILD_ONLY_NOT_LISTING_RUNTIME_OR_GATE'
        and type(row['build_generation']) is int and row['build_generation']==2
        and type(row['build_exit_code']) is int and row['build_exit_code']==0
        and type(row['stderr_bytes']) is int and row['stderr_bytes']==0
        and row['cleanup_confirmed'] is True and row['source_inventory_before_after'] is True
        and row['full805_current_source_bytes_verified'] is True
        and row['product_tests_executed'] is False and row['GO_authorized'] is False
        and type(row['accepted_count_delta']) is int and row['accepted_count_delta']==0
        and row['artifact_pin']==EXE and type(row['fresh_inputs']) is int
        and type(row['final_fresh_hashes']) is int and row['fresh_inputs']==row['final_fresh_hashes']==843,
        'EXACT_BUILD_ONLY_SOURCE_COHORT')
    require(row['build_proof']['catalog_profile']==dict(opt_level='1',debuginfo='line-tables-only',
        debug_assertions=True,overflow_checks=True,test=True)
        and row['build_proof']['validated_stream']['all_records_validated'] is True,
        'ORIGINAL_PROFILE_AND_ALL_RECORDS')


def list_arguments(root):
    return [str(root/EXE['path']),'--list','--format=terse']


def main():
    require(sys.argv[1:]==[],'NO_ARBITRARY_TARGET_OR_MODE')
    import accept_case112_current_epoch as a,conservative_maintenance as c
    import prepared_run_closure_v1 as host,owned_cpu_baseline_v1 as baseline
    import preparation_attributed_cpu_v1 as policy,distinct_final_sample_guard_v1 as final
    import current_stored_runtime_scope as scope,current_stored_listing_catalog as catalog
    import successor_preparation_workspace_v1 as publisher,native011_owned_preparation as cleanup
    import native011_source_generation_audit as audit
    from owned_sql_job import OwnedSQLJobProcess
    from bounded_process_progress import BoundedProcessCapture
    host.configure_host_policy(c)
    g=baseline.guard_type(policy.guard_type(final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;owned=capture=None;primary=None;started=time.monotonic()
    row=dict(schema_version='hwpx-agent.p09-native011-cohort-list-only/v1',
        state='FAILED_805_COHORT_LIST_ONLY_NOT_RUNTIME',official_accepted_count=158,accepted_count_delta=0,
        GO_authorized=False,runtime_tests_executed=False,product_test_bodies_executed=False,
        full249_current_qualified=False,current_whole805_freshness_qualified=False,
        owned=dict(constructor_entered=False,cleanup=False),automatic_retry=False)
    try:
        g.acquire();q=a.AcceptanceReader(c.ROOT,g.check)
        require(not (c.ROOT/OUTPUT).exists(),'ONE_EXCLUSIVE_LIST_RECEIPT')
        for name in (SELF,TEST,catalog.SELF,catalog.TEST,'tools/p09/native011_owned_preparation.py',
            'tools/p09/owned_sql_job.py','tools/p09/bounded_process_progress.py'):q.pin(name)
        build=a.read_exact(q,BUILD);build_contract(build)
        frozen=scope.pins(build['source_pins'],843)
        old=a.read_exact(q,scope.LIST_PIN);scope.listing_inputs(old)
        a.exact(q.pin(EXE['path']),EXE,'EXACT_NEW_BINARY_BEFORE_LIST')
        raw=q.text(catalog.PARSER_PIN['path'])
        a.exact(q.snapshots[catalog.PARSER_PIN['path']],catalog.PARSER_PIN,'ORIGINAL_WHOLE_PURE_PARSER_SOURCE')
        parser=catalog.Catalog(raw)
        def read_source(name):
            text=q.text(name);a.exact(q.snapshots[name],frozen[name],'CURRENT_CATALOG_MATCHES_COMPILED_SOURCE')
            return text
        names,modules=parser.names(read_source)
        require(names==old['source_test_names'],'SAME_EXACT249_NAMES_NOT_RUNTIME_REPLAY')
        row['owned']['constructor_entered']=True
        command=list_arguments(c.ROOT)
        owned=OwnedSQLJobProcess(command,windows=g.windows,allowed_executables=[command[0]],
            cwd=c.ROOT,checkpoint=g.check,env=dict(os.environ,RUST_TEST_THREADS='1'))
        capture=BoundedProcessCapture(owned,output_limit=32768,parse_markers=False)
        deadline=time.monotonic()+15
        while True:
            g.check();require(time.monotonic()<deadline,'LIST_ONLY15_NOT_NATIVE_READY_CLOCK')
            try:out,err=capture.communicate(timeout=.5)
            except subprocess.TimeoutExpired:capture.progress();owned.observe();continue
            owned.observe();require(owned.returncode==0 and not err,'CLEAN_LIST_ONLY_EXIT')
            parser.validate(out,names);break
        q.finish();g.check(force=True)
        require(q.final_fresh_hashes==len(q.snapshots),'CURRENT_CATALOG_AND_BINARY_CLOSING')
        row.update(state='PASS_CURRENT805_COHORT_BINARY_LIST_ONLY_NOT_CURRENT_RUNTIME_OR_GATE',
            compiled_cohort_Rust_count=805,compiled_test_executable_pin=EXE,build_only_pin=BUILD,
            current_catalog_byte_binding=True,current_catalog_names=names,current_module_instances=modules,
            listing_observation=dict(full_names_validated=True,test_count=len(names),
                stdout_bytes=len(out.encode()),stdout_sha256=hashlib.sha256(out.encode()).hexdigest(),
                stderr_bytes=0,raw_logs_included=False),actual_EXE_list_executed=True,
            original_parser_pin=catalog.PARSER_PIN,original_parser_functions=list(catalog.SELECTED),
            prior158_preserved_not_replayed=True,Native_Frame_or_dispatch_qualified=False,
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,IndexError,TypeError,AttributeError,subprocess.SubprocessError) as error:
        primary=error;row['first_failure']=cleanup.failure_record(error,g.samples)
    finally:
        try:cleanup.cleanup_owned(owned,capture,row['owned'],primary)
        except (ValueError,OSError,subprocess.SubprocessError) as error:
            row.update(state='FAILED_COHORT_LIST_CLEANUP',cleanup_failure=cleanup.failure_record(error,[]))
        finally:
            g.close();row.update(cleanup_confirmed=g.cleanup and row['owned'].get('cleanup',False),
                elapsed_seconds=time.monotonic()-started,source_pins=[] if q is None else list(q.snapshots.values()),
                resource_summary=audit.sample_summary(g.samples))
        receipt=publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=a.exact))
        print(json.dumps(dict(state=row['state'],failure=row.get('first_failure'),
            cleanup=row['cleanup_confirmed'],elapsed=row['elapsed_seconds'],
            fresh=row.get('fresh_inputs'),final=row.get('final_fresh_hashes'),
            count=row.get('listing_observation',{}).get('test_count'),receipt=receipt)),flush=True)
    return 0 if row['state'].startswith('PASS_') and row['cleanup_confirmed'] else 2


if __name__=='__main__':raise SystemExit(main())
