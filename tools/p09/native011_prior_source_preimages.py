"""Recover exact prior source bytes in memory, without modifying current Rust."""
import hashlib
import json
import re
import sys
import time
from types import SimpleNamespace as NS

SELF='tools/p09/native011_prior_source_preimages.py'
TEST='tools/p09/tests/test_native011_prior_source_preimages.py'
PREFIX='implementation/p09/evidence/p09-native011-prior-compiled-rust787-code/'
RECOVERY=dict(path='implementation/p09/evidence/p09-361-native011-recorded-source-drift-recovery001.v1.json',
    bytes=10984,sha256='a463e885413bbd1c9dd2f3724287b70003320ba991ded454811d8533443e3846')
BUILD=dict(path='implementation/p09/evidence/p09-361-native011-current-cohort-build002.v1.json',
    bytes=167281,sha256='7e4aeb5ace1b81b36e6aa5b246c4b10171ec7446f6eef9f32edad68fe9ccba8d')
ADDITIONS={
    'crates/hwpx-package/src/document_import.rs':b'pub mod reference_targets;\n',
    'crates/hwpx-package/src/document_import/fields.rs':b'pub mod cross_reference_observation;\n',
    'crates/hwpx-package/src/lib.rs':b'pub mod cross_reference_sdk;\n',
    'crates/product-cli/src/reference_validation_product.rs':b'pub mod source;\npub mod source_crossref;\n\n',
}
MAIN='crates/product-cli/src/main.rs'
BRANCH=(b'    if env::args_os().nth(1).as_deref() == Some(std::ffi::OsStr::new("reference-source")) {\n'
        b'        return reference_source();\n    }\n')
FUNCTION_START=b'fn reference_source() -> ExitCode {\n'
FUNCTION_END=b'fn run() -> Result<(), hwpx_agent_cli::Vs0Error> {\n'


def require(ok,code):
    if not ok:raise ValueError('PRIOR_SOURCE_PREIMAGE_'+code)


def restore(name,raw,expected):
    require(type(raw) is bytes and expected['path']==name,'EXACT_SOURCE_IDENTITY')
    if name in ADDITIONS:
        addition=ADDITIONS[name];require(raw.count(addition)==1,'ONE_EXACT_MODULE_ADDITION')
        restored=raw.replace(addition,b'',1)
    else:
        require(name==MAIN,'ONLY_FIVE_PRIOR_SOURCES')
        require(raw.count(BRANCH)==raw.count(FUNCTION_START)==raw.count(FUNCTION_END)==1,'ONE_EXACT_CLI_EXTENSION')
        first=raw.index(FUNCTION_START);last=raw.index(FUNCTION_END)
        require(first<last and first>raw.index(BRANCH),'EXACT_CLI_EXTENSION_ORDER')
        restored=(raw[:first]+raw[last:]).replace(BRANCH,b'',1)
    actual=dict(path=name,bytes=len(restored),sha256=hashlib.sha256(restored).hexdigest())
    require(actual==expected,'EXACT_PRIOR_BYTES_AND_SHA256')
    return restored


def main():
    denied=[]
    def deny(event,args):
        if event in ('subprocess.Popen','os.system','os.startfile','os.exec','os.posix_spawn','os.fork'):
            denied.append(event);raise ValueError('PREIMAGE_NO_PROCESS')
    sys.addaudithook(deny)
    import accept_case112_current_epoch as a,conservative_maintenance as c
    import current_stored_runtime_scope as scope,successor_preparation_workspace_v1 as publisher
    import prepared_run_closure_v1 as host,owned_cpu_baseline_v1 as baseline
    import preparation_attributed_cpu_v1 as policy,distinct_final_sample_guard_v1 as final
    import native011_source_generation_audit as audit
    host.configure_host_policy(c)
    g=baseline.guard_type(policy.guard_type(final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();rows=[]
    row=dict(state='FAILED_PRIOR_SOURCE_PREIMAGES_NOT_CURRENT_RUNTIME',accepted_count_delta=0,
        official_accepted_count=158,current_Rust_modified=False,product_executed=False,GO_authorized=False)
    try:
        g.acquire();q=a.AcceptanceReader(c.ROOT,g.check)
        for name in (SELF,TEST):q.pin(name)
        prior=a.read_exact(q,RECOVERY);build=a.read_exact(q,BUILD)
        require(prior['state']=='RECOVERED_RECORDED_FIRST_READ_SOURCE_DRIFT_NOT_CURRENT_OR_GATE'
            and build['state']=='PASS_CURRENT805_BUILD_ONLY_NOT_LISTING_RUNTIME_OR_GATE'
            and build['cleanup_confirmed'] and build['fresh_inputs']==build['final_fresh_hashes']==843,
            'EXACT_RECORDED_AND_COMPILED_COHORTS')
        compiled=scope.pins(build['source_pins'],843);changes=prior['comparison']['changed']
        require(len(changes)==5 and {r['path'] for r in changes}==set(ADDITIONS)|{MAIN},'CLOSED_FIVE_SOURCE_CHANGES')
        for change in changes:
            name=change['path'];actual,payload=q._read(name,parse=True);q._bind(name,actual)
            a.exact(actual,change['observed'],'UNCHANGED_CURRENT_SOURCE_FROM_DRIFT')
            a.exact(actual,compiled[name],'UNCHANGED_CURRENT_COMPILED_SOURCE')
            restored=restore(name,bytes(payload),change['declared'])
            archive=dict(change['declared'],path=PREFIX+name)
            require(not (c.ROOT/archive['path']).exists(),'FRESH_ARCHIVE_TARGET_NOT_WRITTEN')
            rows.append(dict(original_pin=dict(change['declared']),current_pin=actual,
                proposed_archive_pin=archive,restored_utf8=restored.decode('utf-8')))
        q.finish();g.check(force=True)
        require(q.final_fresh_hashes==len(q.snapshots) and not denied,'ALL_PREIMAGE_INPUTS_FRESH_CLOSING')
        row.update(state='PASS_EXACT_FIVE_PRIOR_SOURCE_PREIMAGES_NOT_ARCHIVE_OR_RUNTIME',
            preimages=rows,source_archive_created=False,original_binary_pin_or_hash_rebased=False,
            current_source5_freshly_bound_to_build002=True,fresh_inputs=len(q.snapshots),
            final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,UnicodeError) as error:
        value=error.args[0] if error.args else None
        row.update(error_type=type(error).__name__,error_code=value if type(value) is str
            and re.fullmatch('[A-Za-z0-9_]{1,160}',value) else 'CLOSED_PREIMAGE_FAILURE')
    finally:
        g.close();row.update(cleanup_confirmed=g.cleanup,elapsed_seconds=time.monotonic()-started,
            source_pins=[] if q is None else list(q.snapshots.values()),
            process_creation_attempts=len(denied),resource_summary=audit.sample_summary(g.samples))
        receipt=publisher.publish(c.ROOT,
            'implementation/p09/evidence/p09-361-native011-prior-source-preimages001.v1.json',
            row,NS(require=c.require,exact=a.exact))
        print(json.dumps(dict(state=row['state'],error_code=row.get('error_code'),
            count=len(row.get('preimages',[])),fresh=row.get('fresh_inputs'),final=row.get('final_fresh_hashes'),
            cleanup=g.cleanup,receipt=receipt)),flush=True)
    return 0 if row['state'].startswith('PASS_') and g.cleanup else 2


if __name__=='__main__':raise SystemExit(main())
