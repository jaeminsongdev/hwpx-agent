"""Scoped style-code/evidence/document sync. Does not replay tests or history."""
import json
from pathlib import Path
import re
import sys
import time
from types import SimpleNamespace as NS
import run_source_note_style_recovery as recovery

base = recovery.base
shared, c, a = base.shared, base.c, base.a
OUTPUT = 'implementation/p09/evidence/p09-361-source-note-style-sync020.v1.json'
PRODUCTION = ('crates/hwpx-package/src/document_import/structure.rs',
    'crates/hwpx-package/src/document_import/structure/note_style.rs',
    'crates/hwpx-package/src/document_import/structure/note_style/catalog.rs',
    'crates/hwpx-package/src/document_import/structure/note_style/output.rs')
DOCS = ('CURRENT_STATE.md','implementation/p09/P09-03_NOTE_ENGINE_POLICY.md')


def main():
    c.require(not (c.ROOT / OUTPUT).exists(),'NOTE_STYLE_SYNC_IMMUTABLE_RUN_ALREADY_EXISTS')
    shared.host.configure_host_policy(c)
    guard = shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q = None; started = time.monotonic()
    row = dict(state='FAILED_SOURCE_NOTE_STYLE_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q = a.AcceptanceReader(c.ROOT,guard.check)
        first = q.json(base.OUTPUT); current = q.json(recovery.OUTPUT)
        c.require(q.snapshots[base.OUTPUT]['sha256'] == '323b3eae67654e28638e4b979d73f31c9a72f2aba7655ba912d99117e92e1a51','EXACT_ORIGINAL_STYLE_RESULT')
        c.require(q.snapshots[recovery.OUTPUT]['sha256'] == '2fb9827e81c5a2d1950c15e489317c784709346eda0703a1f95fa713aaf80679','EXACT_RECOVERY_STYLE_RESULT')
        c.require(first['state'] == 'FAILED_SOURCE_NOTE_STYLE_COMPONENTS' and first['cleanup'] is True,'PRESERVED_ORIGINAL_STYLE_FAILURE')
        c.require(current['state'] == 'PASS_SOURCE_NOTE_STYLE_TWO_FIXTURE_RECOVERIES_SEVEN_PRIOR_PASSES_PRESERVED_NOT_NATIVE_OR_GATE'
            and current['cleanup'] is True and current['fresh_inputs'] == current['final_fresh_hashes'] == 438,'STYLE_RECOVERY_FRESH_FINAL')
        for flag in ('original_production_and_inputs_unchanged','test_fixture_only_inverse_exact','original_seven_pass_bodies_unchanged'):
            c.require(current[flag] is True,'STYLE_RECOVERY_EXACT_INVERSE_FLAGS')
        original_tests = dict(first['steps'][0]['tests']); recovered_tests = dict(current['steps'][0]['tests'])
        c.require(len(original_tests) == 9 and sum(s == 'ok' for s in original_tests.values()) == 7
            and {n for n,s in original_tests.items() if s == 'FAILED'} == recovery.EXPECTED,'STYLE_ORIGINAL_EXACT_OUTCOMES')
        c.require(set(recovered_tests) == recovery.EXPECTED and set(recovered_tests.values()) == {'ok'},'STYLE_RECOVERED_EXACT_TWO_NO_REPLAY')
        for result in (first,current):
            job = result['steps'][0]['owned_job']
            c.require(job['cleanup_confirmed'] is True and job['owned_tree_empty'] is True and job['job_handle_closed'] is True
                and job['last_job_accounting']['active_processes'] == 0,'STYLE_OWNED_JOBS_TERMINAL')
            c.require(result['actual_Hangul_or_COM'] is False and result['Native011_executed'] is False
                and result['accepted_count_delta'] == 0 and result['P09_gate'] == 'OPEN','STYLE_NOT_NATIVE_OR_GATE')
        tested = {pin['path']:pin for pin in current['source_pins']}
        for name in PRODUCTION + (base.TEST,'tools/p09/run_source_note_style_components.py','tools/p09/run_source_note_style_recovery.py'):
            q.pin(name);c.require(q.snapshots[name] == tested[name],'STYLE_SCOPED_TESTED_SOURCE_UNCHANGED')
        for name in DOCS:q.pin(name)
        q.pin('implementation/p09/evidence/p09-03-note-engine-source-qualification.v1.json')
        q.pin(Path(__file__).relative_to(c.ROOT).as_posix())
        state = q.text(DOCS[0]).split('> 2026-10-19 P09 이전 source note API 연결',1)[0]
        policy = q.text(DOCS[1]).split('## Original typed model decision',1)[0]
        for marker in ('import_note_styles','lower_note_style_batch_candidate','16','22','18','438fresh/final438',
            '158/249','잔여91','next165','고정CROSSREF8종 NOT_RUN','Native011 미승인/미실행','REF-025'):
            c.require(marker in state,'CURRENT_STYLE_STATE_REQUIRED_BOUNDARY')
        for marker in ('16 known attributes','22/18/16','two fixture-setup failures','two passes','prior seven filtered out',
            'absence of a lock never qualifies complete protection','Stored-service/API selection integration','REF-025','158/249'):
            c.require(marker in policy,'STYLE_POLICY_REQUIRED_BOUNDARY')
        c.require(len(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(base.TEST))) == 9,'CURRENT_STYLE_NINE_TEST_INVENTORY')
        q.finish();guard.check(force=True)
        row.update(state='PASS_SOURCE_NOTE_STYLE_SCOPED_CODE_EVIDENCE_AND_DOCUMENT_SYNC_NOT_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            unchanged_tested_production_files=4,unique_component_passes=9,
            retained_prior_passes=7,recovered_passes=2,original_failures_preserved=2,
            entire_438_input_inventory_reaudited=False,scope='four_affected_production_files_test_runners_two_receipts_two_documents_and_contract',
            next_work='stored_service_original_authorization_and_operation_local_form_proof_then_source_api_style_selection',
            external_note_export_native_layout_and_gate_complete=False)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        message=str(error)
        row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message) else 'STYLE_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples
        row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[] if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent'] for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent'] for s in samples),default=None))
        if samples and all(list(s) == list(samples[0]) for s in samples):
            keys=list(samples[0]);values=[[s[k] for k in keys] for s in samples]
            c.require([dict(zip(keys,v)) for v in values] == samples,'LOSSLESS_STYLE_SYNC_RESOURCE_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k) for k in ('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_') and row['cleanup'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
