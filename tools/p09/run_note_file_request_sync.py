"""Scoped product note-file code/receipt/contract closure; no accepted test replay."""
import hashlib
import json
from pathlib import Path
import re
import time
from types import SimpleNamespace as NS
import run_note_file_request_debug_check as previous
base=previous.base
shared,c,a=base.shared,base.c,base.a
OUTPUT='implementation/p09/evidence/p09-361-note-file-request-sync034.v1.json'
MODULE=previous.MODULE
STORED='crates/product-cli/src/form_stored_provider/actual_import/note_export_output.rs'
ROOT='crates/product-cli/src/form_product_request.rs'
TEST_ROOT='crates/product-cli/tests/form_stored_provider/actual_import.rs'
FILES=(MODULE,STORED,ROOT,TEST_ROOT,base.TEST,base.STORED,
    'crates/product-cli/src/form_stored_provider/actual_import.rs',
    'crates/hwpx-package/src/document_import/structure/note_export.rs',
    'crates/hwpx-package/src/document_import/structure/note_export/xml.rs',
    'crates/hwpx-package/src/document_import/structure/note_export/package.rs',
    'crates/hwpx-package/src/writer.rs','crates/hwpx-package/src/vs0.rs',
    'crates/hwpx-package/src/document_import/structure.rs',
    'tools/p09/run_note_file_request_components.py','tools/p09/run_note_file_request_debug_check.py')
DOCS=('CURRENT_STATE.md','implementation/p09/P09-03_NOTE_ENGINE_POLICY.md',
    'protocol/migrations/p09-note-file-export-profile-v1.md','protocol/migrations/p09-note-file-product-request-v1.md')


def inverse(text,pin,label):
    text=text.replace('\r\n','\n');variants={hashlib.sha256(text.encode()).hexdigest(),hashlib.sha256(text.replace('\n','\r\n').encode()).hexdigest()}
    c.require(pin['sha256'] in variants,label)


def terminal(result):
    c.require(result['cleanup'] is True,'NOTE_REQUEST_RECEIPT_CLEANUP')
    for step in result['steps']:
        job=step['owned_job'];c.require(step['exit_code']==0 and step['cleanup'] and job['cleanup_confirmed'] and job['owned_tree_empty']
            and job['job_handle_closed'] and job['last_job_accounting']['active_processes']==0,'NOTE_REQUEST_OWNED_JOB_TERMINAL')


def main():
    c.require(not (c.ROOT/OUTPUT).exists(),'NOTE_REQUEST_SYNC_IMMUTABLE_RUN_ALREADY_EXISTS')
    shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic()
    row=dict(state='FAILED_NOTE_FILE_PRODUCT_REQUEST_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        tested=q.json(base.OUTPUT);checked=q.json(previous.OUTPUT)
        c.require(q.snapshots[base.OUTPUT]['sha256']=='16dd9eb4eedaf8a37c5be2e6127cf33e8ff4d0e645cd04f431a184adf2ba5d6d'
            and q.snapshots[previous.OUTPUT]['sha256']=='3bbee80c0f90ad6d07c37e9a15c38704a8d517b13b9c721ab6ecc9b0e5d0710c','EXACT_REQUEST_TEST_AND_DEBUG_RECEIPTS')
        terminal(tested);terminal(checked)
        c.require(tested['state']=='PASS_NOTE_FILE_PRODUCT_REQUEST_EIGHT_NEW_EIGHT_AFFECTED_STORED_NOT_NATIVE_OR_GATE'
            and tested['fresh_inputs']==tested['final_fresh_hashes']==447,'SIXTEEN_ACCEPTED_REQUEST_TESTS')
        c.require(checked['state']=='PASS_NOTE_FILE_REQUEST_DEBUG_ONLY_LIBRARY_CHECK_SIXTEEN_PREVIOUS_PASSES_RETAINED_NOT_NATIVE_OR_GATE'
            and checked['fresh_inputs']==checked['final_fresh_hashes']==449 and checked['steps'][0]['diagnostics']==[]
            and checked['unit_marker_debug_derive_only'] and checked['all_function_and_test_bodies_unchanged'] and not checked['tests_reexecuted'],
            'DEBUG_ONLY_CHANGE_AND_WARNING_FREE_CHECK')
        currentpins={p['path']:p for p in checked['source_pins']}
        for name in FILES:q.pin(name);c.require(q.snapshots[name]==currentpins[name],'CURRENT_TESTED_AND_CHECKED_SOURCE_UNCHANGED')
        expected=set()
        for name,prefix in ((base.TEST,'actual_import::source_note_file_request::'),(base.STORED,'actual_import::source_note_export::')):
            found=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(name)));c.require(len(found)==8,'EXACT_EIGHT_REQUEST_AND_AFFECTED_TESTS')
            expected|={prefix+n for n in found}
        actual=tested['steps'][0]['tests']
        c.require(len(actual)==len(expected)==16 and {n for n,s in actual}==expected and all(s=='ok' for n,s in actual),'EXACT_SIXTEEN_NO_SKIP_PASSES')
        old_name='implementation/p09/evidence/p09-361-stored-note-export-components030.v1.json';old=q.json(old_name)
        c.require(q.snapshots[old_name]['sha256']=='314b05de1cfeded857c18631c6df8eabc94eff5688c0636e624b55bd8ea2ac6e','EXACT_PRE_REQUEST_BASELINE')
        oldpins={p['path']:p for p in old['source_pins']}
        inverse(q.text(ROOT).replace('pub mod stored_note_file;\n',''),oldpins[ROOT],'OLD_PRODUCT_REQUEST_ONLY_ADDITIVE_INCLUDE')
        inverse(q.text(TEST_ROOT).replace('#[path = "actual_import/source_note_file_request.rs"]\nmod source_note_file_request;\n',''),oldpins[TEST_ROOT],'OLD_TEST_ROOT_ONLY_ADDITIVE_INCLUDE')
        stored=q.text(STORED)
        stored=stored.replace("source:NoteFileSource<'a>,output:","source:&'a StoredImportedDocumentForms,output:")
        start=stored.index('enum NoteFileSource');end=stored.index('impl fmt::Debug for PreparedStoredNoteFileCandidate',start);stored=stored[:start]+stored[end:]
        stored=stored.replace('    #[error("stored note file document.write scope required")] Permission,\n','')
        start=stored.index('        let(output,receipt)=self.build_note_file_candidate(');end=stored.index('        let (fresh,proof)=self.fresh_source_reconstructed',start);stored=stored[:start]+stored[end:]
        stored=stored.replace('        Ok((output,receipt))','        Ok(PreparedStoredNoteFileCandidate {source:self,output,receipt})')
        start=stored.index('impl<R,B,S,V> StoredFormProvider');end=stored.index('impl PreparedStoredNoteFileCandidate',start);stored=stored[:start]+stored[end:]
        inverse(stored,oldpins[STORED],'ORIGINAL_STORED_COMPILER_AND_VERIFY_BODIES_PRESERVED')
        for name in (base.STORED,*FILES[6:13]):c.require(q.snapshots[name]==oldpins[name],'ORIGINAL_CORE_AND_AFFECTED_TEST_BODIES_UNCHANGED')
        for name in DOCS:q.pin(name)
        state=q.text(DOCS[0]).split('> 2026-10-19 P09 이전 주석 저장 서비스 연결',1)[0]
        policy=q.text(DOCS[1]).split('## Source API note style integration and original verification',1)[0]
        profile=q.text(DOCS[3])
        for marker in ('product-note-file-request/v1','document.write','16KiB','신규 제품 요청8개','447fresh/final447','449fresh/final449',
            '55.44%','19.9714%','개인정보 제거 도구가 아니다','158/249','next165','고정CROSSREF8종 NOT_RUN','Native011 미승인/미실행'):
            c.require(marker in state,'CURRENT_REQUEST_RESULT_AND_GATE_BOUNDARIES')
        for marker in ('8 new request and 8 affected','document.write','not claimed','449 fresh/final449','No CLI/server dispatcher','158/249'):
            c.require(marker in policy,'NOTE_ENGINE_REQUEST_AND_GATE_BOUNDARIES')
        for marker in ('16,384','duplicate keys','document.write','not privacy redaction','not an execution claim',
            '447 fresh/final447','449 fresh/final449','always denies execution','P09 Gate remain open'):
            c.require(marker in profile,'PRODUCT_REQUEST_PROFILE_REQUIRED_BOUNDARIES')
        c.require('p09-note-file-product-request-v1.md' in q.text(DOCS[2]),'EXPORT_PROFILE_LINKS_ADDITIVE_PRODUCT_REQUEST')
        q.pin(Path(__file__).relative_to(c.ROOT).as_posix());q.finish();guard.check(force=True)
        row.update(state='PASS_NOTE_FILE_PRODUCT_REQUEST_SCOPED_CODE_CONTRACT_AND_DOCUMENT_SYNC_NOT_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,new_request_tests=8,affected_stored_tests=8,
            original_core_compiler_verify_and_test_bodies_preserved=True,old_product_dispatch_only_additive_include=True,
            original_failed_or_warned_receipts_preserved=True,entire_449_input_inventory_reaudited=False,
            idempotency_claim_or_Native_or_full_product_or_gate_complete=False,next_work='source_note_container_subList_layout_and_inherited_context')
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message) else 'NOTE_REQUEST_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples
        row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[] if q is None else list(q.snapshots.values()),
            resource_samples=samples,system_CPU_max=max((s['system_cpu_percent'] for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent'] for s in samples),default=None))
        if samples and all(list(s)==list(samples[0]) for s in samples):
            keys=list(samples[0]);values=[[s[k] for k in keys] for s in samples]
            c.require([dict(zip(keys,v)) for v in values]==samples,'LOSSLESS_NOTE_REQUEST_SYNC_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k) for k in ('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_') and row['cleanup'] else 2


if __name__=='__main__':raise SystemExit(main())
