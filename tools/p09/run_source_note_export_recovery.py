"""Only two source-admission fixture recoveries; preserve six actual export passes."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from types import SimpleNamespace as NS
import run_source_note_export_components as base
shared,harness,c,a=base.shared,base.harness,base.c,base.a
OUTPUT='implementation/p09/evidence/p09-361-source-note-export-recovery027.v1.json'
MODULE='crates/hwpx-package/src/document_import/structure/note_export.rs'
EXPECTED={'namespace_shadowing_default_namespaces_and_nested_rich_body_are_closed_without_flattening',
    'empty_selection_drift_protection_and_native_security_do_not_produce_output'}


def main():
    c.require(not (c.ROOT/OUTPUT).exists(),'NOTE_EXPORT_RECOVERY_IMMUTABLE_RUN_ALREADY_EXISTS')
    shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic()
    row=dict(state='FAILED_SOURCE_NOTE_EXPORT_RECOVERY',steps=[],actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        old=q.json(base.OUTPUT)
        c.require(q.snapshots[base.OUTPUT]['sha256']=='7bc980029b82116b8244b81dc2921497c3c5d5a9637c7ff3266abcc6ad8c55d6','EXACT_FAILED_NOTE_EXPORT_ORIGINAL')
        tests=dict(old['steps'][0]['tests'])
        c.require(old['state']=='FAILED_SOURCE_NOTE_EXPORT_COMPONENTS' and old['cleanup'] is True and len(tests)==8
            and sum(s=='ok' for s in tests.values())==6 and {n for n,s in tests.items() if s=='FAILED'}==EXPECTED,'PRESERVE_SIX_NOTE_EXPORT_PASSES_TWO_FAILURES')
        names=base.inventory(guard.check)
        for name in sorted(names):q.pin(name)
        oldpins={p['path']:p for p in old['source_pins']}
        for name,pin in oldpins.items():
            q.pin(name)
            if name not in (base.TEST,MODULE):c.require(q.snapshots[name]==pin,'NOTE_EXPORT_ORIGINAL_CODE_AND_INPUTS_UNCHANGED')
        module=q.text(MODULE).replace('PackagePath,WriterLimits','PackagePath,PreservingXmlDocument,WriterLimits')
        test=q.text(base.TEST).replace("<x:p id='22'><x:run>","<x:p id='22' z:property='kept'><x:run>")\
            .replace("<z:future z:property='kept' z:value='opaque'>","<z:future z:value='opaque'>")\
            .replace("<hp:ctrl><hp:footNote instId='101'><hp:subList lock='1'>","<hp:ctrl lock='1'><hp:footNote instId='101'><hp:subList>")
        for name,text in ((MODULE,module),(base.TEST,test)):
            c.require(hashlib.sha256(text.encode()).hexdigest()==oldpins[name]['sha256'],'EXACT_UNUSED_IMPORT_AND_TWO_FIXTURE_ONLY_INVERSES')
        for imported in tuple(sys.modules.values()):
            value=getattr(imported,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09') and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        env=dict(os.environ,CARGO_BUILD_JOBS='1',CARGO_TARGET_DIR=str(c.ROOT/'target'),
            CARGO_PROFILE_TEST_OPT_LEVEL='0',CARGO_PROFILE_DEV_DEBUG='0',CARGO_PROFILE_TEST_DEBUG='0',
            CARGO_PROFILE_DEV_DEBUG_ASSERTIONS='true',CARGO_PROFILE_DEV_OVERFLOW_CHECKS='true',
            CARGO_PROFILE_TEST_DEBUG_ASSERTIONS='true',CARGO_PROFILE_TEST_OVERFLOW_CHECKS='true',
            CARGO_PROFILE_DEV_CODEGEN_UNITS='16',CARGO_PROFILE_TEST_CODEGEN_UNITS='16',
            CARGO_INCREMENTAL='0',RUST_TEST_THREADS='1',RUSTUP_AUTO_INSTALL='0')
        print(json.dumps(dict(state='NOTE_EXPORT_FIXTURE_ONLY_RECOVERY_PREFLIGHT_COMPLETE',inputs=len(q.snapshots))),flush=True)
        harness.run_one('two_fixture_admission_recoveries_only',
            [harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package','--test','document_import_note_export','--',*sorted(EXPECTED),'--exact','--test-threads=1'],EXPECTED,guard,env,row)
        c.require(base.inventory(guard.check)==names,'FINAL_NOTE_EXPORT_RECOVERY_INPUT_INVENTORY_DRIFT')
        q.finish();guard.check(force=True)
        row.update(state='PASS_SOURCE_NOTE_EXPORT_TWO_FIXTURE_RECOVERIES_SIX_PRIOR_EXPORT_PASSES_PRESERVED_NOT_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,original_failed_receipt=q.snapshots[base.OUTPUT],
            original_failure_relabelled=False,retained_actual_export_passes=6,reexecuted_fixture_tests=2,
            export_function_bodies_and_other_test_bodies_unchanged=True,unused_import_only_removed=True,
            actual_HWPX_file_export_unique_tests=8,compiled_queue_reexecuted=False)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError) as error:
        message=str(error)
        row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message) else 'NOTE_EXPORT_RECOVERY_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples
        row.update(cleanup=guard.cleanup and all(s['cleanup'] for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[] if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent'] for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent'] for s in samples),default=None))
        if samples and all(list(s)==list(samples[0]) for s in samples):
            keys=list(samples[0]);values=[[s[k] for k in keys] for s in samples]
            c.require([dict(zip(keys,v)) for v in values]==samples,'LOSSLESS_NOTE_EXPORT_RECOVERY_RESOURCE_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k) for k in ('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k) for k in ('stage','exit_code','diagnostics','locations','summaries','tests','panic_locations','safe_error_variants')} for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_') and row['cleanup'] else 2


if __name__=='__main__':raise SystemExit(main())
