"""Keep sixteen accepted tests; only a unit marker Debug derive changes, then cargo check."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from types import SimpleNamespace as NS
import run_note_file_request_components as base
harness,shared,c,a=base.harness,base.shared,base.c,base.a
OUTPUT='implementation/p09/evidence/p09-361-note-file-request-debug-check033.v1.json'
MODULE='crates/product-cli/src/form_product_request/stored_note_file.rs'


def main():
    c.require(not (c.ROOT/OUTPUT).exists(),'NOTE_FILE_DEBUG_IMMUTABLE_RUN_ALREADY_EXISTS')
    shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic()
    row=dict(state='FAILED_NOTE_FILE_REQUEST_DEBUG_ONLY_CHECK',steps=[],actual_tests=False,actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        prior=q.json(base.OUTPUT)
        c.require(q.snapshots[base.OUTPUT]['sha256']=='16dd9eb4eedaf8a37c5be2e6127cf33e8ff4d0e645cd04f431a184adf2ba5d6d','EXACT_ORIGINAL_SIXTEEN_TEST_RESULT')
        c.require(prior['cleanup'] and prior['component_tests']==16 and len(prior['steps'])==1
            and prior['state']=='PASS_NOTE_FILE_PRODUCT_REQUEST_EIGHT_NEW_EIGHT_AFFECTED_STORED_NOT_NATIVE_OR_GATE','PRIOR_SIXTEEN_PASSES_PRESERVED')
        priorpins={p['path']:p for p in prior['source_pins']}
        names=base.inventory(guard.check)
        for name in sorted(names):q.pin(name)
        code=q.text(MODULE);mark='#[derive(Debug)]\npub struct StoredNoteFileProductRequest;'
        c.require(code.count(mark)==1,'EXACT_ONE_UNIT_MARKER_DEBUG_DERIVE')
        inverse=code.replace(mark,'pub struct StoredNoteFileProductRequest;')
        variants={hashlib.sha256(inverse.encode()).hexdigest(),hashlib.sha256(inverse.replace('\n','\r\n').encode()).hexdigest()}
        c.require(priorpins[MODULE]['sha256'] in variants,'EXACT_FULL_MODULE_INVERSE_NO_FUNCTION_CHANGES')
        for name,pin in priorpins.items():
            q.pin(name)
            if name!=MODULE:c.require(q.snapshots[name]==pin,'ALL_OTHER_TESTED_SOURCE_AND_INPUTS_UNCHANGED')
        c.require(names==set(priorpins)&names,'NO_NEW_SOURCE_INVENTORY_SINCE_SIXTEEN_PASSES')
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09') and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        env=dict(os.environ,CARGO_BUILD_JOBS='1',CARGO_TARGET_DIR=str(c.ROOT/'target'),
            CARGO_PROFILE_DEV_OPT_LEVEL='0',CARGO_PROFILE_TEST_OPT_LEVEL='0',CARGO_PROFILE_DEV_DEBUG='0',CARGO_PROFILE_TEST_DEBUG='0',
            CARGO_PROFILE_DEV_DEBUG_ASSERTIONS='true',CARGO_PROFILE_DEV_OVERFLOW_CHECKS='true',CARGO_PROFILE_TEST_DEBUG_ASSERTIONS='true',
            CARGO_PROFILE_TEST_OVERFLOW_CHECKS='true',CARGO_PROFILE_DEV_CODEGEN_UNITS='16',CARGO_PROFILE_TEST_CODEGEN_UNITS='16',
            CARGO_INCREMENTAL='0',RUST_TEST_THREADS='1',RUSTUP_AUTO_INSTALL='0')
        harness.run_one('unit_marker_debug_only_library_compile_no_tests',
            [harness.CARGO,'check','--offline','--locked','-j','1','-p','hwpx-agent-cli','--lib'],set(),guard,env,row)
        c.require(row['steps'][0]['diagnostics']==[],'NO_CURRENT_NOTE_FILE_REQUEST_COMPILE_DIAGNOSTICS')
        c.require(base.inventory(guard.check)==names,'FINAL_DEBUG_ONLY_INPUT_INVENTORY')
        q.finish();guard.check(force=True)
        row.update(state='PASS_NOTE_FILE_REQUEST_DEBUG_ONLY_LIBRARY_CHECK_SIXTEEN_PREVIOUS_PASSES_RETAINED_NOT_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,retained_component_tests=16,
            unit_marker_debug_derive_only=True,all_function_and_test_bodies_unchanged=True,tests_reexecuted=False,
            issuer_native_CAS_execution_publication_authority=False)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError) as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message) else 'NOTE_FILE_DEBUG_CHECK_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples
        row.update(cleanup=guard.cleanup and all(s['cleanup'] for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[] if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent'] for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent'] for s in samples),default=None))
        if samples and all(list(s)==list(samples[0]) for s in samples):
            keys=list(samples[0]);values=[[s[k] for k in keys] for s in samples]
            c.require([dict(zip(keys,v)) for v in values]==samples,'LOSSLESS_NOTE_FILE_DEBUG_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k) for k in ('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k) for k in ('stage','exit_code','diagnostics','locations','summaries','tests')} for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_') and row['cleanup'] else 2


if __name__=='__main__':raise SystemExit(main())
