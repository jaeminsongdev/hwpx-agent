"""Strict product note-file requests + eight affected stored cases; no Native/queue replay."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from types import SimpleNamespace as NS
import run_source_note_api_components as harness
shared,c,a=harness.shared,harness.c,harness.a
OUTPUT='implementation/p09/evidence/p09-361-note-file-request-components032.v1.json'
TEST='crates/product-cli/tests/form_stored_provider/actual_import/source_note_file_request.rs'
STORED='crates/product-cli/tests/form_stored_provider/actual_import/source_note_export.rs'


def inventory(check):return shared.source_inventory(check)|{TEST,STORED}


def main():
    c.require(not (c.ROOT/OUTPUT).exists(),'NOTE_EXPORT_IMMUTABLE_RUN_ALREADY_EXISTS')
    shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic()
    row=dict(state='FAILED_NOTE_FILE_PRODUCT_REQUEST_COMPONENTS',steps=[],actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09') and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        q.pin('fixtures/target-build/p09-24-note-target-20261002-03/output/fixture-manifest.json')
        q.pin('implementation/p09/evidence/p09-26-note-native-batch-qualification.current-2020.v1.json')
        for i,file in enumerate(('p09-24-c01-footnote.hwpx','p09-24-c02-endnote.hwpx','p09-24-c03-footnote-endnote.hwpx'),1):
            q.pin('fixtures/target-build/p09-24-note-target-20261002-03/output/'+file)
            for lane in ('saved','reopened'):
                q.pin(f'implementation/p09/evidence/private/p09-17-field-auto-number-target-p09-24-20261002-c{i:02}-attempt01/{lane}.hwpx')
        regenerated='fixtures/target-build/p09-note-id-allocation-20261019-r01/output/'
        q.pin(regenerated+'fixture-manifest.json')
        for file in ('p09-24-c01-footnote.hwpx','p09-24-c02-endnote.hwpx','p09-24-c03-footnote-endnote.hwpx'):q.pin(regenerated+file)
        stored_expected={'actual_import::source_note_export::'+name for name in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(STORED))}
        c.require(len(stored_expected)==8,'EXACT_EIGHT_STORED_NOTE_EXPORT_TESTS')
        expected={'actual_import::source_note_file_request::'+name for name in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(TEST))}
        c.require(len(expected)==8,'EXACT_EIGHT_NOTE_FILE_REQUEST_TESTS')
        env=dict(os.environ,CARGO_BUILD_JOBS='1',CARGO_TARGET_DIR=str(c.ROOT/'target'),
            CARGO_PROFILE_TEST_OPT_LEVEL='0',CARGO_PROFILE_DEV_DEBUG='0',CARGO_PROFILE_TEST_DEBUG='0',
            CARGO_PROFILE_DEV_DEBUG_ASSERTIONS='true',CARGO_PROFILE_DEV_OVERFLOW_CHECKS='true',
            CARGO_PROFILE_TEST_DEBUG_ASSERTIONS='true',CARGO_PROFILE_TEST_OVERFLOW_CHECKS='true',
            CARGO_PROFILE_DEV_CODEGEN_UNITS='16',CARGO_PROFILE_TEST_CODEGEN_UNITS='16',
            CARGO_INCREMENTAL='0',RUST_TEST_THREADS='1',RUSTUP_AUTO_INSTALL='0')
        print(json.dumps(dict(state='NOTE_FILE_EXPORT_PREFLIGHT_COMPLETE',inputs=len(q.snapshots))),flush=True)
        harness.run_one('eight_product_note_file_requests_and_eight_affected_stored_cases',
            [harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli','--test','form_stored_provider','--',*sorted(expected|stored_expected),'--exact','--test-threads=1'],expected|stored_expected,guard,env,row)
        c.require(inventory(guard.check)==names,'FINAL_NOTE_EXPORT_INPUT_INVENTORY_DRIFT')
        q.finish();guard.check(force=True)
        row.update(state='PASS_NOTE_FILE_PRODUCT_REQUEST_EIGHT_NEW_EIGHT_AFFECTED_STORED_NOT_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,component_tests=16,new_product_request_tests=8,affected_stored_tests=8,
            candidate_source_owned_without_clone=True,document_write_required=True,strict_duplicate_free_closed_request=True,
            idempotency_key_claimed=False,command_line_or_server_route_added=False,original_core_export_suite_reexecuted=False,
            actual_new_hwpx_file_write_and_reopen=True,original_source_preserved=True,legacy_native_failures_preserved=True,
            native_export_layout_numbering_or_format_equivalence_qualified=False,full_product_or_native_or_gate_complete=False,
            source_api_and_unaffected_stored_suites_reexecuted=False,compiled_queue_reexecuted=False)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError) as error:
        message=str(error)
        row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message) else 'NOTE_EXPORT_COMPONENT_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples
        row.update(cleanup=guard.cleanup and all(s['cleanup'] for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[] if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent'] for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent'] for s in samples),default=None))
        if samples and all(list(s)==list(samples[0]) for s in samples):
            keys=list(samples[0]);values=[[s[k] for k in keys] for s in samples]
            c.require([dict(zip(keys,v)) for v in values]==samples,'LOSSLESS_NOTE_EXPORT_RESOURCE_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k) for k in ('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k) for k in ('stage','exit_code','diagnostics','locations','summaries','tests','panic_locations','safe_error_variants')} for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_') and row['cleanup'] else 2


if __name__=='__main__':raise SystemExit(main())




