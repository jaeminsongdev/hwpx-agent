"""Scoped note-file code/evidence/contract closure; never replays accepted tests."""
import hashlib
import json
from pathlib import Path
import re
import time
from types import SimpleNamespace as NS
import run_source_note_export_recovery as recovery
base=recovery.base
shared,c,a=base.shared,base.c,base.a
OUTPUT='implementation/p09/evidence/p09-361-source-note-export-sync029.v1.json'
FILES=(recovery.MODULE,'crates/hwpx-package/src/document_import/structure/note_export/xml.rs',
    'crates/hwpx-package/src/document_import/structure/note_export/package.rs',
    'crates/hwpx-package/src/writer.rs','crates/hwpx-package/src/vs0.rs',
    'crates/hwpx-package/src/document_import/structure.rs',base.TEST,
    'tools/p09/run_source_note_export_components.py','tools/p09/run_source_note_export_recovery.py')
DOCS=('CURRENT_STATE.md','implementation/p09/P09-03_NOTE_ENGINE_POLICY.md','protocol/migrations/p09-note-file-export-profile-v1.md')


def main():
    c.require(not (c.ROOT/OUTPUT).exists(),'NOTE_EXPORT_SYNC_IMMUTABLE_RUN_ALREADY_EXISTS')
    shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic()
    row=dict(state='FAILED_SOURCE_NOTE_EXPORT_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        first=q.json(base.OUTPUT);result=q.json(recovery.OUTPUT)
        c.require(q.snapshots[base.OUTPUT]['sha256']=='7bc980029b82116b8244b81dc2921497c3c5d5a9637c7ff3266abcc6ad8c55d6','EXACT_NOTE_FILE_ORIGINAL_FAILURE')
        c.require(q.snapshots[recovery.OUTPUT]['sha256']=='9dac12364f47a0deb6b5b8eb8f91004b0556e5f87e5f07ec9a4a09524dc9d6e0','EXACT_NOTE_FILE_RECOVERY')
        c.require(first['state']=='FAILED_SOURCE_NOTE_EXPORT_COMPONENTS' and first['cleanup'] is True,'PRESERVED_NOTE_EXPORT_FAILURE')
        c.require(result['state']=='PASS_SOURCE_NOTE_EXPORT_TWO_FIXTURE_RECOVERIES_SIX_PRIOR_EXPORT_PASSES_PRESERVED_NOT_NATIVE_OR_GATE'
            and result['cleanup'] is True and result['fresh_inputs']==result['final_fresh_hashes']==442,'NOTE_FILE_RECOVERY_FRESH_CLOSURE')
        before=dict(first['steps'][0]['tests']);current=dict(result['steps'][0]['tests'])
        c.require(len(before)==8 and sum(v=='ok' for v in before.values())==6 and {n for n,s in before.items() if s=='FAILED'}==recovery.EXPECTED
            and set(current)==recovery.EXPECTED and set(current.values())=={'ok'},'SIX_RETAINED_AND_EXACT_TWO_RECOVERED_NOTE_EXPORTS')
        for record in (first,result):
            job=record['steps'][0]['owned_job']
            c.require(job['cleanup_confirmed'] is True and job['owned_tree_empty'] is True and job['job_handle_closed'] is True
                and job['last_job_accounting']['active_processes']==0,'NOTE_EXPORT_OWNED_JOBS_TERMINAL')
        c.require(result['export_function_bodies_and_other_test_bodies_unchanged'] is True and result['unused_import_only_removed'] is True,'NOTE_EXPORT_FIXTURE_AND_IMPORT_ONLY_RECOVERY')
        tested={p['path']:p for p in result['source_pins']}
        for name in FILES:q.pin(name);c.require(q.snapshots[name]==tested[name],'NOTE_EXPORT_SCOPED_TESTED_CODE_UNCHANGED')
        old_name='implementation/p09/evidence/p09-361-source-note-style-api-recovery024.v1.json'
        old=q.json(old_name)
        c.require(q.snapshots[old_name]['sha256']=='ddf2f46206502a733dedf5495101ccf43a971c7be1090d62ab90003f004fa6af','BEFORE_EXPORT_SHARED_SOURCE_BASELINE')
        oldpins={p['path']:p for p in old['source_pins']}
        writer=q.text(FILES[3]);start=writer.index('/// Same original writer trust chain for a newly derived note-only package.');end=writer.index('fn validate_archive<R: Read + Seek>(',start)
        writer=(writer[:start]+writer[end:]).replace('pub(crate) struct BoundedArchiveBuffer','struct BoundedArchiveBuffer')\
            .replace('pub(crate) const fn new(limit: u64)','const fn new(limit: u64)')\
            .replace('pub(crate) fn into_inner(self) -> Result<Vec<u8>, WriterError>','fn into_inner(self) -> Result<Vec<u8>, WriterError>')
        vs0=q.text(FILES[4]).replace("/// Reuses the existing non-render preview asset for derived note documents.\npub(crate) fn neutral_preview_png() -> &'static [u8] { TRANSPARENT_PNG_1X1 }\n\n",'')
        structure=q.text(FILES[5]).replace('pub mod note_export;\n','')
        for name,text in ((FILES[3],writer),(FILES[4],vs0),(FILES[5],structure)):
            variants={hashlib.sha256(text.encode()).hexdigest(),hashlib.sha256(text.replace('\r\n','\n').encode()).hexdigest(),
                hashlib.sha256(text.replace('\r\n','\n').replace('\n','\r\n').encode()).hexdigest()}
            c.require(oldpins[name]['sha256'] in variants,'EXACT_SHARED_WRITER_VS0_AND_STRUCTURE_INVERSES')
        for name in DOCS:q.pin(name)
        q.pin(Path(__file__).relative_to(c.ROOT).as_posix())
        state=q.text(DOCS[0]).split('> 2026-10-19 P09 이전 source 모양 API 연결',1)[0]
        policy=q.text(DOCS[1]).split('## Source API note style integration and original verification',1)[0]
        migration=q.text(DOCS[2])
        for marker in ('export_note_file_candidate','Footnotes/Endnotes/Both','개인정보 제거 도구가 아니다','6pass','정확한2개','442fresh/final442',
            '67.83%','143.422초','parent run 전체','v12 incomplete/미해결4/report없음/exit3','158/249','고정CROSSREF8종 NOT_RUN','Native011 미승인/미실행'):
            c.require(marker in state,'NOTE_EXPORT_CURRENT_STATE_BOUNDARIES')
        for marker in ('actual note-only body','NOT a redaction','existing writer behavior','eight unique tests','six passes and two',
            'full parent-run copy','Native format/numbering','158/249'):
            c.require(marker in policy,'NOTE_EXPORT_POLICY_REQUIRED_BOUNDARIES')
        for marker in ('source-note-file-hwpx/v1','DigestManifestV1','not a privacy-redaction tool','Hancom 120 help','multi-version help',
            'not binary HWP','full parent-run copy','scope/head/ACL/quarantine/AEAD'):
            c.require(marker in migration,'NOTE_EXPORT_PROFILE_REQUIRED_BOUNDARIES')
        q.finish();guard.check(force=True)
        row.update(state='PASS_SOURCE_NOTE_EXPORT_SCOPED_CODE_PROFILE_AND_DOCUMENT_SYNC_NOT_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,unique_export_tests=8,retained_passes=6,recovered_passes=2,
            original_failed_receipt_preserved=True,shared_writer_vs0_and_structure_inverses=True,
            entire_442_input_inventory_reaudited=False,scope='nine_tested_files_three_receipts_three_documents_and_this_verifier',
            actual_HWPX_component_export=True,Native_format_equivalence_or_full_product_or_gate_complete=False,
            next_work='avoid_full_parent_run_copy_then_stored_source_proof_and_authorization_join')
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        message=str(error)
        row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message) else 'NOTE_EXPORT_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples
        row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[] if q is None else list(q.snapshots.values()),
            resource_samples=samples,system_CPU_max=max((s['system_cpu_percent'] for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent'] for s in samples),default=None))
        if samples and all(list(s)==list(samples[0]) for s in samples):
            keys=list(samples[0]);values=[[s[k] for k in keys] for s in samples]
            c.require([dict(zip(keys,v)) for v in values]==samples,'LOSSLESS_NOTE_EXPORT_SYNC_RESOURCE_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k) for k in ('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_') and row['cleanup'] else 2


if __name__=='__main__':raise SystemExit(main())
