"""Recover only two invalid fixture setups; preserve the original seven passes."""
import hashlib
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
OUTPUT = 'implementation/p09/evidence/p09-361-source-note-style-recovery019.v1.json'
EXPECTED = {'same_local_styles_in_two_sections_are_distinct_and_one_transaction_preserves_both_parts',
    'source_values_are_observed_without_defaults_protection_grants_or_private_debug'}


def main():
    c.require(not (c.ROOT / OUTPUT).exists(), 'NOTE_STYLE_RECOVERY_IMMUTABLE_RUN_ALREADY_EXISTS')
    shared.host.configure_host_policy(c)
    guard = shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard), role='whole_metadata_preflight'))()
    q = None; started = time.monotonic()
    row = dict(state='FAILED_SOURCE_NOTE_STYLE_RECOVERY', steps=[], actual_Hangul_or_COM=False,
        Native011_executed=False, prior_Native_replayed=False, accepted_count_delta=0,
        P09_gate='OPEN', P10_started=False, output_ingest_commit_or_publication=False)
    try:
        guard.acquire(); q = a.AcceptanceReader(c.ROOT, guard.check)
        old = q.json(base.OUTPUT)
        c.require(q.snapshots[base.OUTPUT]['sha256'] == '323b3eae67654e28638e4b979d73f31c9a72f2aba7655ba912d99117e92e1a51', 'EXACT_ORIGINAL_NOTE_STYLE_FAILED_RECEIPT')
        c.require(old['state'] == 'FAILED_SOURCE_NOTE_STYLE_COMPONENTS' and old['cleanup'] is True, 'PRESERVE_NOTE_STYLE_ORIGINAL_FAILURE')
        tests = dict(old['steps'][0]['tests'])
        c.require(len(tests) == 9 and {n for n,s in tests.items() if s == 'FAILED'} == EXPECTED
            and sum(s == 'ok' for s in tests.values()) == 7, 'EXACT_ORIGINAL_SEVEN_PASS_TWO_FAILURE')
        names = base.inventory(guard.check)
        for name in sorted(names): q.pin(name)
        for pin in old['source_pins']:
            q.pin(pin['path'])
            if pin['path'] != base.TEST:
                c.require(q.snapshots[pin['path']] == pin, 'NOTE_STYLE_ORIGINAL_TESTED_PRODUCTION_AND_INPUTS_UNCHANGED')
        text = q.text(base.TEST)
        inverse = text.replace('#[allow(dead_code)]\n','').replace("<hp:p id='1'><hp:run><hp:t>NO STYLE", "<hp:p><hp:run><hp:t>NO STYLE")
        inverse = inverse.replace('    zip.start_file("mimetype",zip::write::SimpleFileOptions::default().compression_method(zip::CompressionMethod::Stored))?;\n'
            '    zip.write_all(entries.get("mimetype").ok_or("mimetype")?)?;\n'
            '    for (name,data) in entries.iter().filter(|(name,_)| name.as_str() != "mimetype")', '    for (name,data) in &entries')
        prior_test = next(pin for pin in old['source_pins'] if pin['path'] == base.TEST)
        c.require(hashlib.sha256(inverse.encode()).hexdigest() == prior_test['sha256'], 'EXACT_FIXTURE_ONLY_TEST_INVERSE_ORIGINAL_SEVEN_BODIES_UNCHANGED')
        for module in tuple(sys.modules.values()):
            value = getattr(module,'__file__',None)
            if value:
                path = Path(value).absolute()
                if path.is_relative_to(c.ROOT / 'tools/p09') and path.suffix == '.py': q.pin(path.relative_to(c.ROOT).as_posix())
        env = dict(os.environ, CARGO_BUILD_JOBS='1', CARGO_TARGET_DIR=str(c.ROOT/'target'),
            CARGO_PROFILE_TEST_OPT_LEVEL='0', CARGO_PROFILE_DEV_DEBUG='0', CARGO_PROFILE_TEST_DEBUG='0',
            CARGO_PROFILE_DEV_DEBUG_ASSERTIONS='true', CARGO_PROFILE_DEV_OVERFLOW_CHECKS='true',
            CARGO_PROFILE_TEST_DEBUG_ASSERTIONS='true', CARGO_PROFILE_TEST_OVERFLOW_CHECKS='true',
            CARGO_PROFILE_DEV_CODEGEN_UNITS='16', CARGO_PROFILE_TEST_CODEGEN_UNITS='16',
            CARGO_INCREMENTAL='0', RUST_TEST_THREADS='1', RUSTUP_AUTO_INSTALL='0')
        print(json.dumps(dict(state='RECOVERY_INPUTS_AND_INVERSE_CONFIRMED', inputs=len(q.snapshots))),flush=True)
        harness.run_one('two_fixture_setup_recoveries_only', [base.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package',
            '--test','document_import_note_style','--',*sorted(EXPECTED),'--exact','--test-threads=1'], EXPECTED,guard,env,row)
        c.require(base.inventory(guard.check) == names,'FINAL_NOTE_STYLE_RECOVERY_SOURCE_INVENTORY_DRIFT')
        q.finish(); guard.check(force=True)
        row.update(state='PASS_SOURCE_NOTE_STYLE_TWO_FIXTURE_RECOVERIES_SEVEN_PRIOR_PASSES_PRESERVED_NOT_NATIVE_OR_GATE',
            original_receipt=q.snapshots[base.OUTPUT], original_production_and_inputs_unchanged=True,
            test_fixture_only_inverse_exact=True, original_seven_pass_bodies_unchanged=True,
            retained_prior_passes=7, newly_executed_passes=2, original_failed_receipt_relabelled=False,
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,StopIteration,subprocess.SubprocessError) as error:
        message = str(error)
        row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message) else 'NOTE_STYLE_RECOVERY_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close()
        samples = guard.samples
        row.update(cleanup=guard.cleanup and all(s['cleanup'] for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[] if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent'] for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent'] for s in samples),default=None))
        if samples and all(list(s) == list(samples[0]) for s in samples):
            keys=list(samples[0]);values=[[s[k] for k in keys] for s in samples]
            c.require([dict(zip(keys,v)) for v in values] == samples,'LOSSLESS_NOTE_STYLE_RECOVERY_RESOURCE_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k) for k in ('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k) for k in ('stage','exit_code','diagnostics','locations','summaries','tests','panic_locations','safe_error_variants')} for s in row['steps']], 'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_') and row['cleanup'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
