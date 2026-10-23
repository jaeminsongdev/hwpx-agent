"""v12 source API and two exact stored JSON joins; no Native or queue replay."""
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
OUTPUT='implementation/p09/evidence/p09-361-source-note-style-api-components023.v1.json'
SOURCES=(*harness.SOURCES,'crates/product-cli/tests/reference_source_product/note_style_selection.rs')
MIGRATION='protocol/migrations/p09-reference-source-assessment-v11-to-v12.md'
STORED_TESTS={
    'actual_import::source_note_style::stored_note_style_v12_api_json_alone_builds_requests_and_rejects_foreign_stale_tampered_or_revoked_access',
    'actual_import::source_note_conversion::stored_note_kind_reference_source_api_json_builds_requests_and_rejects_foreign_stale_or_revoked_access',
}


def inventory(check):return shared.source_inventory(check)|set(SOURCES)


def main():
    c.require(not (c.ROOT/OUTPUT).exists(),'NOTE_STYLE_API_IMMUTABLE_RUN_ALREADY_EXISTS')
    shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic()
    row=dict(state='FAILED_SOURCE_NOTE_STYLE_API_COMPONENTS',steps=[],actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,
        P09_gate='OPEN',P10_started=False,output_ingest_commit_or_publication=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09') and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        q.pin('implementation/p09/evidence/private/p09-14-hyperlink-discovery-20260912-attempt02/after.hwpx')
        q.pin(MIGRATION)
        expected=set()
        for name,prefix in zip(SOURCES,('','joined_caption_state::','source_note_selection::','source_note_style_selection::'),strict=True):
            expected.update(prefix+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(name)))
        c.require(len(expected)==57,'EXACT_CURRENT_FIFTY_SEVEN_SOURCE_API_TESTS')
        for name in STORED_TESTS:
            file='crates/product-cli/tests/form_stored_provider/actual_import/'+('source_note_style.rs' if '::source_note_style::' in name else 'source_note_conversion.rs')
            c.require('fn '+name.rsplit('::',1)[1]+'()' in q.text(file),'EXACT_CURRENT_STORED_API_JOIN_EXISTS')
        env=dict(os.environ,CARGO_BUILD_JOBS='1',CARGO_TARGET_DIR=str(c.ROOT/'target'),
            CARGO_PROFILE_TEST_OPT_LEVEL='0',CARGO_PROFILE_DEV_DEBUG='0',CARGO_PROFILE_TEST_DEBUG='0',
            CARGO_PROFILE_DEV_DEBUG_ASSERTIONS='true',CARGO_PROFILE_DEV_OVERFLOW_CHECKS='true',
            CARGO_PROFILE_TEST_DEBUG_ASSERTIONS='true',CARGO_PROFILE_TEST_OVERFLOW_CHECKS='true',
            CARGO_PROFILE_DEV_CODEGEN_UNITS='16',CARGO_PROFILE_TEST_CODEGEN_UNITS='16',
            CARGO_INCREMENTAL='0',RUST_TEST_THREADS='1',RUSTUP_AUTO_INSTALL='0')
        common=[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli']
        print(json.dumps(dict(state='V12_STYLE_API_SOURCE_PREFLIGHT_COMPLETE',inputs=len(q.snapshots))),flush=True)
        harness.run_one('v12_source_API_six_new_and_fifty_one_affected',common+['--test','reference_source_product','--','--test-threads=1'],expected,guard,env,row)
        harness.run_one('style_JSON_join_and_affected_kind_JSON_join_only',common+['--test','form_stored_provider','--',*sorted(STORED_TESTS),'--exact','--test-threads=1'],STORED_TESTS,guard,env,row)
        c.require(inventory(guard.check)==names,'FINAL_NOTE_STYLE_API_SOURCE_INVENTORY_DRIFT')
        q.finish();guard.check(force=True)
        row.update(state='PASS_SOURCE_NOTE_STYLE_API_V12_FIFTY_SEVEN_AND_TWO_STORED_JOINS_NOT_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_source_API_tests=6,affected_source_API_tests=51,new_stored_join_tests=1,affected_stored_join_tests=1,
            source_schema='hwpx-agent.product.reference-source-assessment/v12',style_selector_fields=['style_id','source_style_sha256','kind'],
            note_style_values_or_characters_exposed=False,caller_side_style_import_required_for_request=False,
            issuer_or_native_or_full_product_route_qualified=False,remaining_unresolved_stage_count=4,incomplete_exit_code=3,
            prior_core_or_stored_suites_reexecuted=False,compiled_queue_reexecuted=False)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError) as error:
        message=str(error)
        row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message) else 'NOTE_STYLE_API_COMPONENT_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples
        row.update(cleanup=guard.cleanup and all(s['cleanup'] for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[] if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent'] for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent'] for s in samples),default=None))
        if samples and all(list(s)==list(samples[0]) for s in samples):
            keys=list(samples[0]);values=[[s[k] for k in keys] for s in samples]
            c.require([dict(zip(keys,v)) for v in values]==samples,'LOSSLESS_NOTE_STYLE_API_RESOURCE_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k) for k in ('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k) for k in ('stage','exit_code','diagnostics','locations','summaries','tests','panic_locations','safe_error_variants')} for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_') and row['cleanup'] else 2


if __name__=='__main__':raise SystemExit(main())
