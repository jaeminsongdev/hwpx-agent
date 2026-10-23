"""Exact source-proof regressions + new stored-style joins, serial and non-Native."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from types import SimpleNamespace as NS
import run_source_note_style_components as base

shared, harness, c, a = base.shared, base.harness, base.c, base.a
OUTPUT = 'implementation/p09/evidence/p09-361-stored-note-style-components021.v1.json'
STORED_TEST = 'crates/product-cli/tests/form_stored_provider/actual_import/source_note_style.rs'
PREFIX = 'actual_import::source_note_style::'


def inventory(check):
    return shared.source_inventory(check) | {base.TEST}


def main():
    c.require(not (c.ROOT/OUTPUT).exists(),'STORED_NOTE_STYLE_IMMUTABLE_RUN_ALREADY_EXISTS')
    shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic()
    row=dict(state='FAILED_STORED_NOTE_STYLE_COMPONENTS',steps=[],actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,
        P09_gate='OPEN',P10_started=False,output_ingest_commit_or_publication=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09') and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        generated='fixtures/target-build/p09-note-id-allocation-20261019-r01/output/'
        old='fixtures/target-build/p09-24-note-target-20261002-03/output/'
        for name in ('fixture-manifest.json','p09-24-c01-footnote.hwpx','p09-24-c02-endnote.hwpx','p09-24-c03-footnote-endnote.hwpx'):
            q.pin(generated+name);q.pin(old+name)
        q.pin('implementation/p09/evidence/p09-26-note-native-batch-qualification.current-2020.v1.json')
        q.pin('implementation/p09/evidence/p09-03-note-engine-source-qualification.v1.json')
        for i in range(1,4):
            for lane in ('saved','reopened'):
                q.pin(f'implementation/p09/evidence/private/p09-17-field-auto-number-target-p09-24-20261002-c{i:02}-attempt01/{lane}.hwpx')
        core=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(base.TEST)))
        stored={PREFIX+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(STORED_TEST))}
        c.require(len(core)==11 and len(stored)==8,'EXACT_ELEVEN_CORE_EIGHT_STORED_STYLE_TESTS')
        env=dict(os.environ,CARGO_BUILD_JOBS='1',CARGO_TARGET_DIR=str(c.ROOT/'target'),
            CARGO_PROFILE_TEST_OPT_LEVEL='0',CARGO_PROFILE_DEV_DEBUG='0',CARGO_PROFILE_TEST_DEBUG='0',
            CARGO_PROFILE_DEV_DEBUG_ASSERTIONS='true',CARGO_PROFILE_DEV_OVERFLOW_CHECKS='true',
            CARGO_PROFILE_TEST_DEBUG_ASSERTIONS='true',CARGO_PROFILE_TEST_OVERFLOW_CHECKS='true',
            CARGO_PROFILE_DEV_CODEGEN_UNITS='16',CARGO_PROFILE_TEST_CODEGEN_UNITS='16',
            CARGO_INCREMENTAL='0',RUST_TEST_THREADS='1',RUSTUP_AUTO_INSTALL='0')
        print(json.dumps(dict(state='STORED_STYLE_SOURCE_INPUT_PREFLIGHT_COMPLETE',inputs=len(q.snapshots))),flush=True)
        common=[base.CARGO,'test','--offline','--locked','-j','1']
        harness.run_one('source_style_two_new_and_nine_affected_compiler_regressions',
            common+['-p','hwpx-package','--test','document_import_note_style','--','--test-threads=1'],core,guard,env,row)
        harness.run_one('new_stored_style_eight_only',common+['-p','hwpx-agent-cli','--test','form_stored_provider','--',PREFIX,'--test-threads=1'],stored,guard,env,row)
        c.require(inventory(guard.check)==names,'FINAL_STORED_NOTE_STYLE_SOURCE_INVENTORY_DRIFT')
        q.finish();guard.check(force=True)
        row.update(state='PASS_STORED_NOTE_STYLE_EIGHT_AND_SOURCE_PROOF_ELEVEN_NOT_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_source_proof_and_digest_tests=2,affected_source_compiler_regressions=9,new_stored_tests=8,
            unrelated_stored_or_source_api_tests_reexecuted=False,compiled_queue_reexecuted=False,
            input_form_reconstruction_reused_without_second_source_import=True,
            native_layout_numbering_complete_protection_issuer_CAS_or_product_route_qualified=False)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError) as error:
        message=str(error)
        row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message) else 'STORED_STYLE_COMPONENT_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples
        row.update(cleanup=guard.cleanup and all(s['cleanup'] for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[] if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent'] for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent'] for s in samples),default=None))
        if samples and all(list(s)==list(samples[0]) for s in samples):
            keys=list(samples[0]);values=[[s[k] for k in keys] for s in samples]
            c.require([dict(zip(keys,v)) for v in values]==samples,'LOSSLESS_STORED_STYLE_RESOURCE_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k) for k in ('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k) for k in ('stage','exit_code','diagnostics','locations','summaries','tests','panic_locations','safe_error_variants')} for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_') and row['cleanup'] else 2


if __name__=='__main__':raise SystemExit(main())
