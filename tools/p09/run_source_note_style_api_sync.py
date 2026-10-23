"""Scoped v12 contract/code/evidence closure without replaying tests or history."""
import hashlib
import json
from pathlib import Path
import re
import time
from types import SimpleNamespace as NS
import run_source_note_style_api_recovery as recovery
base=recovery.base
shared,c,a=base.shared,base.c,base.a
OUTPUT='implementation/p09/evidence/p09-361-source-note-style-api-sync025.v1.json'
SOURCE='crates/product-cli/src/reference_validation_product/source.rs'
FILES=(SOURCE,*base.SOURCES,
    'crates/hwpx-package/src/document_import/structure/note_style.rs',
    'crates/hwpx-package/src/document_import/structure/note_style/output.rs',recovery.CORE,
    'crates/product-cli/tests/form_stored_provider/actual_import/source_note_conversion.rs',
    'crates/product-cli/tests/form_stored_provider/actual_import/source_note_style.rs',
    'crates/product-cli/src/form_stored_provider/actual_import/note_style_output.rs',
    'tools/p09/run_source_note_style_api_components.py','tools/p09/run_source_note_style_api_recovery.py')
DOCS=('CURRENT_STATE.md','implementation/p09/P09-03_NOTE_ENGINE_POLICY.md',base.MIGRATION)


def original_api(text):
    begin=text.index('/// Body-spine style selectors only');end=text.index('/// No raw bookmark names',begin)
    text=text[:begin]+text[end:]
    return text.replace('reference-source-assessment/v12','reference-source-assessment/v11')\
        .replace('    note_style_selections: Vec<ReferenceSourceNoteStyleSelection>,\n','')\
        .replace('    /// Actual body-spine style declarations in XML order, not effective style,\n'
            '    /// global/native identity, numbering/layout or complete protection authority.\n'
            '    #[must_use]\n    pub fn note_style_selections(&self) -> &[ReferenceSourceNoteStyleSelection] {\n'
            '        &self.note_style_selections\n    }\n','')\
        .replace('    #[error("REFERENCE_SOURCE_NOTE_STYLES_REJECTED")]\n    NoteStyles,\n','')\
        .replace('        let note_style_selections = ReferenceSourceNoteStyleSelection::from_source(structure, reference_limits)?;\n','')\
        .replace('            note_style_selections,\n','')


def main():
    c.require(not (c.ROOT/OUTPUT).exists(),'STYLE_API_SYNC_IMMUTABLE_RUN_ALREADY_EXISTS')
    shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic()
    row=dict(state='FAILED_SOURCE_NOTE_STYLE_API_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        first=q.json(base.OUTPUT);result=q.json(recovery.OUTPUT)
        c.require(q.snapshots[base.OUTPUT]['sha256']=='23a7099a6a59dedfb5a65ed52d2eaea043cea4c10fa76761448507869a244d03','EXACT_ORIGINAL_V12_FAILURE')
        c.require(q.snapshots[recovery.OUTPUT]['sha256']=='ddf2f46206502a733dedf5495101ccf43a971c7be1090d62ab90003f004fa6af','EXACT_V12_RECOVERY')
        c.require(first['state']=='FAILED_SOURCE_NOTE_STYLE_API_COMPONENTS' and first['cleanup'] is True,'PRESERVE_ORIGINAL_V12_FAILURE')
        c.require(result['state']=='PASS_SOURCE_NOTE_STYLE_API_V12_UINT_ZERO_RECOVERY_TWENTY_THREE_TESTS_NOT_NATIVE_OR_GATE'
            and result['cleanup'] is True and result['fresh_inputs']==result['final_fresh_hashes']==435,'V12_RECOVERY_FRESH_CLOSURE')
        old=dict(first['steps'][0]['tests']);api=dict(result['steps'][1]['tests'])
        retained={name for name,status in old.items() if status=='ok' and not name.startswith(recovery.API_PREFIX)}
        c.require(len(retained)==49 and len(old)==57 and {n for n,s in old.items() if s=='FAILED'}==recovery.OLD_FAILURES
            and set(api)==set(old)-retained and set(api.values())=={'ok'},'FORTY_NINE_RETAINED_PLUS_EXACT_EIGHT_SOURCE_API')
        for step,count in zip(result['steps'],(12,8,3),strict=True):
            c.require(step['exit_code']==0 and len(step['tests'])==count and all(s=='ok' for n,s in step['tests'])
                and step['diagnostics']==[],'EXACT_V12_RECOVERY_TESTS')
            job=step['owned_job']
            c.require(job['cleanup_confirmed'] is True and job['owned_tree_empty'] is True and job['job_handle_closed'] is True
                and job['last_job_accounting']['active_processes']==0,'V12_RECOVERY_OWNED_JOBS_TERMINAL')
        tested={p['path']:p for p in result['source_pins']}
        for name in FILES:q.pin(name);c.require(q.snapshots[name]==tested[name],'SCOPED_V12_TESTED_CODE_UNCHANGED')
        old_name='implementation/p09/evidence/p09-361-source-note-api-components016.v1.json'
        baseline=q.json(old_name)
        c.require(q.snapshots[old_name]['sha256']=='a5d0ee2f4bd5c86b1e9d90c6fc5dfce14b9e854c6a183f7ec9ba4419fa3dd7e2','EXACT_BEFORE_V12_API_BASELINE')
        previous={p['path']:p for p in baseline['source_pins']}
        inverse={SOURCE:original_api(q.text(SOURCE))}
        for name in (*base.SOURCES[:3],FILES[8]):
            inverse[name]=q.text(name).replace('reference-source-assessment/v12','reference-source-assessment/v11')\
                .replace('source_note_selector_actual_cli_is_v12_','source_note_selector_actual_cli_is_v11_')\
                .replace('mod source_note_style_selection {include!("reference_source_product/note_style_selection.rs");}\n','')
        for name,text in inverse.items():
            variants={hashlib.sha256(text.encode()).hexdigest(),hashlib.sha256(text.replace('\r\n','\n').encode()).hexdigest(),
                hashlib.sha256(text.replace('\r\n','\n').replace('\n','\r\n').encode()).hexdigest()}
            c.require(previous[name]['sha256'] in variants,'EXACT_V11_API_AND_TEST_TEXT_INVERSES_OUTSIDE_INTENDED_ADDITIONS')
        for name in DOCS:q.pin(name)
        q.pin(Path(__file__).relative_to(c.ROOT).as_posix())
        state=q.text(DOCS[0]).split('> 2026-10-19 P09 이전 저장 모양 후보 연결',1)[0]
        policy=q.text(DOCS[1]).split('## Stored note style service integration and original verification',1)[0]
        migration=q.text(base.MIGRATION)
        for marker in ('note_style_selections','style_id','source_style_sha256','API57개는49유지+8재검증','core12·API8·저장3=23개',
            '435fresh/final435','72.66%','1555.57MiB','REF-025','v12 incomplete/미해결4/report없음/exit3',
            '158/249','잔여91','next165','고정CROSSREF8종 NOT_RUN','Native011 미승인/미실행'):
            c.require(marker in state,'CURRENT_V12_SOURCE_API_BOUNDARIES')
        for marker in ('57 unique verified cases','49 unaffected','23 passing recovery','newNum="0"','positive-start validation',
            '265 unrelated tests','REF-025','NOT_RUN pending their authorized session qualification'):
            c.require(marker in policy,'V12_NOTE_STYLE_POLICY_BOUNDARIES')
        for marker in ('reference-source-assessment/v12','exactly three fields','REFERENCE_SOURCE_NOTE_STYLES_REJECTED',
            'UINT','no stored-document','49 unaffected positive API passes','12 core tests and three','not Native or the P09 Gate'):
            c.require(marker in migration,'V12_MIGRATION_REQUIRED_CONTRACT')
        q.finish();guard.check(force=True)
        row.update(state='PASS_SOURCE_NOTE_STYLE_API_V12_SCOPED_CODE_MIGRATION_AND_DOCUMENT_SYNC_NOT_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,source_API_unique_cases=57,
            retained_API_cases=49,reexecuted_API_cases=8,source_core_tests=12,stored_tests=3,
            production_API_and_four_test_file_inverses=True,inverse_line_endings_only_normalized_if_needed=True,
            entire_435_input_inventory_reaudited=False,next_work='REF025_actual_note_file_export_contract_and_artifact_not_digest_manifest',
            full_product_or_native_or_gate_complete=False)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        message=str(error)
        row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message) else 'V12_API_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples
        row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[] if q is None else list(q.snapshots.values()),
            resource_samples=samples,system_CPU_max=max((s['system_cpu_percent'] for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent'] for s in samples),default=None))
        if samples and all(list(s)==list(samples[0]) for s in samples):
            keys=list(samples[0]);values=[[s[k] for k in keys] for s in samples]
            c.require([dict(zip(keys,v)) for v in values]==samples,'LOSSLESS_V12_API_SYNC_RESOURCE_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k) for k in ('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_') and row['cleanup'] else 2


if __name__=='__main__':raise SystemExit(main())
