"""Scoped tested-code and document closure; no test or historical inventory replay."""
import hashlib
import json
from pathlib import Path
import re
import time
from types import SimpleNamespace as NS
import run_stored_note_style_components as base
shared,c,a=base.shared,base.c,base.a
OUTPUT='implementation/p09/evidence/p09-361-stored-note-style-sync022.v1.json'
FILES=('crates/hwpx-package/src/document_import/structure/note_style.rs',
    'crates/hwpx-package/src/document_import/structure/note_style/output.rs',
    'crates/product-cli/src/form_stored_provider/actual_import.rs',
    'crates/product-cli/src/form_stored_provider/actual_import/note_style_output.rs',
    'crates/hwpx-package/tests/document_import_note_style.rs',
    'crates/product-cli/tests/form_stored_provider/actual_import.rs',
    base.STORED_TEST,'tools/p09/run_stored_note_style_components.py')
DOCS=('CURRENT_STATE.md','implementation/p09/P09-03_NOTE_ENGINE_POLICY.md')


def main():
    c.require(not (c.ROOT/OUTPUT).exists(),'STORED_STYLE_SYNC_IMMUTABLE_RUN_ALREADY_EXISTS')
    shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic()
    row=dict(state='FAILED_STORED_NOTE_STYLE_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        result=q.json(base.OUTPUT)
        c.require(q.snapshots[base.OUTPUT]['sha256']=='a860afde5b3456af941c301c87b91a1bef553a3d29ac8071cf9cf92a65758e81','EXACT_STORED_STYLE_COMPONENTS_RESULT')
        c.require(result['state']=='PASS_STORED_NOTE_STYLE_EIGHT_AND_SOURCE_PROOF_ELEVEN_NOT_NATIVE_OR_GATE'
            and result['cleanup'] is True and result['fresh_inputs']==result['final_fresh_hashes']==443,'STORED_STYLE_FRESH_COMPONENTS_CLOSURE')
        for step,expected in zip(result['steps'],(11,8),strict=True):
            c.require(step['exit_code']==0 and len(step['tests'])==expected and all(status=='ok' for name,status in step['tests'])
                and step['diagnostics']==[],'EXACT_STORED_STYLE_EXECUTED_TESTS')
            job=step['owned_job']
            c.require(job['cleanup_confirmed'] is True and job['owned_tree_empty'] is True and job['job_handle_closed'] is True
                and job['last_job_accounting']['active_processes']==0,'STORED_STYLE_OWNED_JOBS_TERMINAL')
        tested={p['path']:p for p in result['source_pins']}
        for name in FILES:
            q.pin(name);c.require(q.snapshots[name]==tested[name],'STORED_STYLE_TESTED_SOURCE_UNCHANGED')
        old_name='implementation/p09/evidence/p09-361-source-note-style-recovery019.v1.json'
        old=q.json(old_name)
        c.require(q.snapshots[old_name]['sha256']=='2fb9827e81c5a2d1950c15e489317c784709346eda0703a1f95fa713aaf80679','EXACT_BEFORE_SERVICE_STYLE_BASELINE')
        before={p['path']:p for p in old['source_pins']}
        inverses={
            FILES[2]:q.text(FILES[2]).replace('pub mod note_style_output;\n',''),
            FILES[5]:q.text(FILES[5]).replace('#[path = "actual_import/source_note_style.rs"]\nmod source_note_style;\n',''),
            FILES[0]:q.text(FILES[0]).replace(', note_style_request_sha256',''),
        }
        for name,text in inverses.items():
            variants={hashlib.sha256(text.encode()).hexdigest(),hashlib.sha256(text.replace('\r\n','\n').encode()).hexdigest(),
                hashlib.sha256(text.replace('\r\n','\n').replace('\n','\r\n').encode()).hexdigest()}
            c.require(before[name]['sha256'] in variants,'EXACT_SERVICE_COMMON_CODE_TEST_INCLUDE_AND_PARSER_REEXPORT_INVERSES')
        for name in DOCS:q.pin(name)
        q.pin(Path(__file__).relative_to(c.ROOT).as_posix())
        state=q.text(DOCS[0]).split('> 2026-10-19 P09 이전 source 모양 편집',1)[0]
        policy=q.text(DOCS[1]).split('## Source note style implementation and original verification',1)[0]
        for marker in ('prepare_note_style_candidate','operation-local proof','총19개','443fresh/final443','258개','70.16%',
            '1552.70MiB','schema migration','REF-025','158/249','잔여91','next165','고정CROSSREF8종 NOT_RUN','Native011 미승인/미실행'):
            c.require(marker in state,'CURRENT_STORED_STYLE_REQUIRED_BOUNDARIES')
        for marker in ('avoiding a second complete input import','16 length-framed values','19 passing executions','eight new',
            'nine affected','258 unrelated','six edits plus three original paragraph-ID rejections','not a workspace-wide strict-lint',
            'API is still v11/incomplete','remain NOT_RUN pending session qualification'):
            c.require(marker in policy,'STORED_STYLE_POLICY_REQUIRED_BOUNDARIES')
        q.finish();guard.check(force=True)
        row.update(state='PASS_STORED_NOTE_STYLE_SCOPED_TESTED_CODE_AND_DOCUMENT_SYNC_NOT_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,source_tests=11,stored_tests=8,
            common_service_code_and_existing_test_include_inverses=True,source_style_parser_reexport_inverse=True,
            inverse_line_endings_only_normalized_if_needed=True,entire_443_input_inventory_reaudited=False,
            scope='eight_tested_files_two_receipts_two_documents_and_this_verifier',
            next_work='explicit_source_API_style_selection_schema_migration_and_JSON_to_stored_style_request',
            full_product_or_native_or_gate_complete=False)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        message=str(error)
        row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message) else 'STORED_STYLE_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples
        row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[] if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent'] for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent'] for s in samples),default=None))
        if samples and all(list(s)==list(samples[0]) for s in samples):
            keys=list(samples[0]);values=[[s[k] for k in keys] for s in samples]
            c.require([dict(zip(keys,v)) for v in values]==samples,'LOSSLESS_STORED_STYLE_SYNC_RESOURCE_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k) for k in ('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_') and row['cleanup'] else 2


if __name__=='__main__':raise SystemExit(main())
