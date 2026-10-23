"""Recover native UINT-zero source handling; retain unaffected positive API passes."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from types import SimpleNamespace as NS
import run_source_note_style_api_components as base
shared,harness,c,a=base.shared,base.harness,base.c,base.a
OUTPUT='implementation/p09/evidence/p09-361-source-note-style-api-recovery024.v1.json'
CORE='crates/hwpx-package/tests/document_import_note_style.rs'
API_PREFIX='source_note_style_selection::'
OLD_FAILURES={'actual_cli_exposes_historical_field_inventory_but_no_resolved_target_or_complete_pass',
    'historical_source_topology_is_original_body_data_not_complete_flow'}
ZERO_STORED='actual_import::source_note_style::stored_note_style_existing_zero_number_is_preserved_but_new_zero_or_restart_reinterpretation_is_denied'
CHANGED={'crates/hwpx-package/src/document_import/structure/note_style.rs',
    'crates/hwpx-package/src/document_import/structure/note_style/output.rs',
    'crates/product-cli/tests/form_stored_provider/actual_import/source_note_style.rs',base.MIGRATION}


def inventory(check):return base.inventory(check)|{CORE}


def main():
    c.require(not (c.ROOT/OUTPUT).exists(),'STYLE_API_RECOVERY_IMMUTABLE_RUN_ALREADY_EXISTS')
    shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic()
    row=dict(state='FAILED_SOURCE_NOTE_STYLE_API_RECOVERY',steps=[],actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        old=q.json(base.OUTPUT)
        c.require(q.snapshots[base.OUTPUT]['sha256']=='23a7099a6a59dedfb5a65ed52d2eaea043cea4c10fa76761448507869a244d03','EXACT_FAILED_STYLE_API_ORIGINAL')
        tests=dict(old['steps'][0]['tests'])
        c.require(old['state']=='FAILED_SOURCE_NOTE_STYLE_API_COMPONENTS' and old['cleanup'] is True
            and len(tests)==57 and sum(s=='ok' for s in tests.values())==55
            and {n for n,s in tests.items() if s=='FAILED'}==OLD_FAILURES,'PRESERVED_FIFTY_FIVE_PASS_TWO_FAILURE')
        names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for pin in old['source_pins']:
            if pin['path'] not in CHANGED:
                q.pin(pin['path']);c.require(q.snapshots[pin['path']]==pin,'UNCHANGED_STYLE_API_CODE_TESTS_AND_ORIGINAL_INPUTS')
        q.pin(base.MIGRATION)
        q.pin('implementation/p09/evidence/p09-03-note-engine-source-qualification.v1.json')
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09') and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        core=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(CORE)))
        api={n for n in tests if n.startswith(API_PREFIX)}|OLD_FAILURES
        stored=base.STORED_TESTS|{ZERO_STORED}
        c.require(len(core)==12 and len(api)==8 and len(stored)==3,'EXACT_TWELVE_CORE_EIGHT_API_THREE_STORED_RECOVERY_SCOPE')
        env=dict(os.environ,CARGO_BUILD_JOBS='1',CARGO_TARGET_DIR=str(c.ROOT/'target'),
            CARGO_PROFILE_TEST_OPT_LEVEL='0',CARGO_PROFILE_DEV_DEBUG='0',CARGO_PROFILE_TEST_DEBUG='0',
            CARGO_PROFILE_DEV_DEBUG_ASSERTIONS='true',CARGO_PROFILE_DEV_OVERFLOW_CHECKS='true',
            CARGO_PROFILE_TEST_DEBUG_ASSERTIONS='true',CARGO_PROFILE_TEST_OVERFLOW_CHECKS='true',
            CARGO_PROFILE_DEV_CODEGEN_UNITS='16',CARGO_PROFILE_TEST_CODEGEN_UNITS='16',
            CARGO_INCREMENTAL='0',RUST_TEST_THREADS='1',RUSTUP_AUTO_INSTALL='0')
        common=[harness.CARGO,'test','--offline','--locked','-j','1']
        print(json.dumps(dict(state='UINT_ZERO_RECOVERY_PREFLIGHT_COMPLETE',inputs=len(q.snapshots))),flush=True)
        harness.run_one('native_UINT_zero_preservation_plus_affected_core_eleven',common+['-p','hwpx-package','--test','document_import_note_style','--','--test-threads=1'],core,guard,env,row)
        harness.run_one('six_style_API_regressions_and_two_historical_failures_only',common+['-p','hwpx-agent-cli','--test','reference_source_product','--',*sorted(api),'--exact','--test-threads=1'],api,guard,env,row)
        harness.run_one('two_JSON_joins_and_stored_zero_preservation_only',common+['-p','hwpx-agent-cli','--test','form_stored_provider','--',*sorted(stored),'--exact','--test-threads=1'],stored,guard,env,row)
        c.require(inventory(guard.check)==names,'FINAL_STYLE_API_RECOVERY_SOURCE_INVENTORY_DRIFT')
        q.finish();guard.check(force=True)
        row.update(state='PASS_SOURCE_NOTE_STYLE_API_V12_UINT_ZERO_RECOVERY_TWENTY_THREE_TESTS_NOT_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,original_failed_receipt=q.snapshots[base.OUTPUT],
            original_failure_relabelled=False,retained_unaffected_positive_API_passes=49,reexecuted_API_passes=8,
            full_source_API_unique_passes=57,source_core_tests=12,stored_join_and_zero_tests=3,
            native_zero_source_value_preserved_without_meaning_or_default=True,new_zero_or_restart_reinterpretation_rejected=True,
            domain_positive_style_validation_unchanged=True,compiled_queue_reexecuted=False,
            source_schema='hwpx-agent.product.reference-source-assessment/v12',remaining_unresolved_stage_count=4,incomplete_exit_code=3)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError) as error:
        message=str(error)
        row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message) else 'STYLE_API_RECOVERY_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples
        row.update(cleanup=guard.cleanup and all(s['cleanup'] for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[] if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent'] for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent'] for s in samples),default=None))
        if samples and all(list(s)==list(samples[0]) for s in samples):
            keys=list(samples[0]);values=[[s[k] for k in keys] for s in samples]
            c.require([dict(zip(keys,v)) for v in values]==samples,'LOSSLESS_STYLE_API_RECOVERY_RESOURCE_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k) for k in ('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k) for k in ('stage','exit_code','diagnostics','locations','summaries','tests','panic_locations','safe_error_variants')} for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_') and row['cleanup'] else 2


if __name__=='__main__':raise SystemExit(main())
