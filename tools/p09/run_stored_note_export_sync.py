"""Scoped tested-code/document audit; does not repeat Cargo, Native or queue tests."""
import hashlib
import json
from pathlib import Path
import re
import time
from types import SimpleNamespace as NS
import run_stored_note_export_components as base
shared,c,a=base.shared,base.c,base.a
OUTPUT='implementation/p09/evidence/p09-361-stored-note-export-sync031.v1.json'
FILES=(
    'crates/hwpx-package/src/document_import/structure/note_export.rs',
    'crates/hwpx-package/src/document_import/structure/note_export/xml.rs',
    'crates/hwpx-package/src/document_import/structure/note_export/package.rs',
    'crates/product-cli/src/form_stored_provider/actual_import.rs',
    'crates/product-cli/src/form_stored_provider/actual_import/note_export_output.rs',
    base.TEST,base.STORED,'crates/product-cli/tests/form_stored_provider/actual_import.rs',
    'crates/hwpx-package/src/writer.rs','crates/hwpx-package/src/vs0.rs',
    'crates/hwpx-package/src/document_import/structure.rs',
    'tools/p09/run_stored_note_export_components.py')
DOCS=('CURRENT_STATE.md','implementation/p09/P09-03_NOTE_ENGINE_POLICY.md',
      'protocol/migrations/p09-note-file-export-profile-v1.md')


def restored(text,pin,label):
    text=text.replace('\r\n','\n')
    c.require(pin['sha256'] in {hashlib.sha256(text.encode()).hexdigest(),
        hashlib.sha256(text.replace('\n','\r\n').encode()).hexdigest()},label)


def main():
    c.require(not (c.ROOT/OUTPUT).exists(),'STORED_NOTE_EXPORT_SYNC_IMMUTABLE_RUN_ALREADY_EXISTS')
    shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic()
    row=dict(state='FAILED_STORED_NOTE_EXPORT_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        result=q.json(base.OUTPUT)
        c.require(q.snapshots[base.OUTPUT]['sha256']=='314b05de1cfeded857c18631c6df8eabc94eff5688c0636e624b55bd8ea2ac6e','EXACT_STORED_EXPORT_COMPONENT_RESULT')
        c.require(result['state']=='PASS_OPTIMIZED_NOTE_EXPORT_ELEVEN_CORE_EIGHT_STORED_COMPONENTS_NOT_NATIVE_OR_GATE'
            and result['cleanup'] is True and result['fresh_inputs']==result['final_fresh_hashes']==446,'STORED_EXPORT_FRESH_TEST_CLOSURE')
        tested={p['path']:p for p in result['source_pins']}
        for name in FILES:q.pin(name);c.require(q.snapshots[name]==tested[name],'STORED_EXPORT_TESTED_CODE_UNCHANGED')
        core=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(base.TEST)))
        stored={'actual_import::source_note_export::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(base.STORED))}
        c.require(len(core)==11 and len(stored)==8 and len(result['steps'])==2,'STORED_EXPORT_EXACT_NINETEEN_INVENTORY')
        for step,expected in zip(result['steps'],(core,stored),strict=True):
            c.require(step['exit_code']==0 and step['diagnostics']==[] and len(step['tests'])==len(expected)
                and {n for n,s in step['tests']}==expected and all(s=='ok' for n,s in step['tests']),'STORED_EXPORT_NINETEEN_NO_SKIP_PASSES')
            job=step['owned_job']
            c.require(step['cleanup'] and job['cleanup_confirmed'] and job['owned_tree_empty'] and job['job_handle_closed']
                and job['last_job_accounting']['active_processes']==0,'STORED_EXPORT_BOTH_OWNED_JOBS_TERMINAL')
        old=q.json('implementation/p09/evidence/p09-361-source-note-export-recovery027.v1.json')
        c.require(q.snapshots['implementation/p09/evidence/p09-361-source-note-export-recovery027.v1.json']['sha256']==
            '9dac12364f47a0deb6b5b8eb8f91004b0556e5f87e5f07ec9a4a09524dc9d6e0','EXACT_PREVIOUS_EXPORT_SOURCE_PINS')
        oldpins={p['path']:p for p in old['source_pins']}
        restored(q.text(base.TEST).split('#[test]\nfn large_unselected_main_run_',1)[0],oldpins[base.TEST],'ORIGINAL_EIGHT_CORE_TEST_BODIES_PRESERVED')
        restored(q.text(FILES[3]).replace('pub mod note_export_output;\n',''),oldpins[FILES[3]],'ORIGINAL_SERVICE_MODULE_ONLY_ADDITIVE_INCLUDE')
        restored(q.text(FILES[7]).replace('#[path = "actual_import/source_note_export.rs"]\nmod source_note_export;\n',''),oldpins[FILES[7]],'ORIGINAL_STORED_TEST_ROOT_ONLY_ADDITIVE_INCLUDE')
        for name in FILES[8:11]:c.require(q.snapshots[name]==oldpins[name],'ORIGINAL_SHARED_WRITER_VS0_STRUCTURE_UNCHANGED')
        xml=q.text(FILES[1]);package=q.text(FILES[2]);source=q.text(FILES[0]);service=q.text(FILES[4])
        span=xml.split('pub(super) fn section_properties_run(',1)[1]
        c.require('close(xml,run' not in span and 'close(xml,pr,max)?' in span
            and 'source.get(content.end()..outer.end())' in span and 'source.get(at..content.start())' in span,
            'ONLY_RUN_ENVELOPE_AND_SECPR_MATERIALIZED')
        c.require('s.bytes.as_slice()' in package and 'section.bytes.clone()' not in package
            and 'if sections.contains_key(path)||collection.omitted.contains(path){continue;}' in package,'SECTIONS_BORROWED_AND_BODY_ROLE_FIRST')
        c.require('validate_note_export_archive(fresh,zip)' in source and 'assess_active_content' in source
            and 'self.for_original(original)' in source and 'fresh!=rebuilt.source().original.as_ref()' in source,'ORIGINAL_SOURCE_TRUST_AND_EXACT_PROOF_BINDING')
        c.require('self.fresh_source_reconstructed(provider,now)?' in service and 'self.source.fresh_source(provider,now)?' in service
            and 'self.verify(provider,now)?;Err(E::RouteUnqualified)' in service,'FRESH_SERVICE_AUTHORIZATION_AND_ROUTE_DENIAL')
        for name in DOCS:q.pin(name)
        state=q.text(DOCS[0]).split('> 2026-10-19 P09 이전 주석 파일 구현',1)[0]
        policy=q.text(DOCS[1]).split('## Source API note style integration and original verification',1)[0]
        migration=q.text(DOCS[2])
        for marker in ('prepare_note_file_candidate','총19개','446fresh/final446','30.86%','19.2843%','1563.45MiB',
            '개인정보 제거 도구가 아니다','158/249','next165','고정CROSSREF8종 NOT_RUN','Native011 미승인/미실행'):
            c.require(marker in state,'CURRENT_STORED_EXPORT_SCOPE_AND_LIMITS')
        for marker in ('11 core and 8 stored','scope/head/ACL/quarantine/AEAD','not atomic CAS','NOT a redaction',
            '268 unrelated','Native format/numbering','158/249'):c.require(marker in policy,'POLICY_STORED_EXPORT_SCOPE_AND_LIMITS')
        for marker in ('source-note-file-hwpx/v1','DigestManifestV1','not a privacy-redaction tool','call-local VerifiedFormReconstruction',
            'scope/head/ACL/quarantine/AEAD','11 core and 8 stored','Next is product API request binding'):
            c.require(marker in migration,'PROFILE_STORED_EXPORT_SCOPE_AND_LIMITS')
        q.pin(Path(__file__).relative_to(c.ROOT).as_posix());q.finish();guard.check(force=True)
        row.update(state='PASS_OPTIMIZED_STORED_NOTE_EXPORT_SCOPED_CODE_AND_DOCUMENT_SYNC_NOT_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,core_tests=11,stored_tests=8,
            original_eight_core_tests_preserved=True,old_service_and_test_root_only_additive_includes=True,
            original_shared_writer_vs0_structure_unchanged=True,entire_446_input_inventory_reaudited=False,
            output_is_not_redaction_or_atomic_CAS=True,Native_format_equivalence_or_full_product_or_gate_complete=False,
            next_work='product_API_request_binding_for_fresh_stored_note_file_candidate')
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        message=str(error)
        row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message) else 'STORED_EXPORT_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples
        row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[] if q is None else list(q.snapshots.values()),
            resource_samples=samples,system_CPU_max=max((s['system_cpu_percent'] for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent'] for s in samples),default=None))
        if samples and all(list(s)==list(samples[0]) for s in samples):
            keys=list(samples[0]);values=[[s[k] for k in keys] for s in samples]
            c.require([dict(zip(keys,v)) for v in values]==samples,'LOSSLESS_STORED_EXPORT_SYNC_RESOURCE_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k) for k in ('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_') and row['cleanup'] else 2


if __name__=='__main__':raise SystemExit(main())
