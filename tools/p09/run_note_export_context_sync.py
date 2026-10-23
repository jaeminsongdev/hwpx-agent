"""Source context code/failed-evidence/document closure, without Cargo or accepted test replay."""
import hashlib,json,re,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_note_export_context_product_recovery as base
shared,c,a=base.shared,base.c,base.a
OUTPUT='implementation/p09/evidence/p09-361-note-export-context-sync039.v1.json'
FILES=(
 'crates/hwpx-package/src/text_flow.rs','crates/hwpx-package/src/document_import/structure.rs',
 'crates/hwpx-package/src/document_import/structure/note_export.rs','crates/hwpx-package/src/document_import/structure/note_export/xml.rs',
 'crates/hwpx-package/src/document_import/structure/note_export/package.rs',
 'crates/hwpx-package/tests/document_import_note_export_context.rs','crates/hwpx-package/tests/document_import_note_export.rs',
 'crates/hwpx-package/tests/text_flow.rs','crates/hwpx-package/tests/document_import_notes.rs','crates/hwpx-package/tests/document_import_structure.rs',
 base.base.TEST,'crates/product-cli/src/form_stored_provider/actual_import/note_export_output.rs',
 'crates/product-cli/src/form_product_request/stored_note_file.rs','crates/product-cli/src/form_product_request.rs',
 'crates/product-cli/src/form_stored_provider/actual_import.rs','crates/hwpx-package/src/writer.rs','crates/hwpx-package/src/vs0.rs',
 'tools/p09/run_note_export_context_components.py','tools/p09/run_note_export_context_public_spans.py',
 'tools/p09/run_note_export_context_product_recovery.py')
DOCS=('CURRENT_STATE.md','implementation/p09/P09-03_NOTE_ENGINE_POLICY.md',
 'protocol/migrations/p09-note-file-export-profile-v1.md','protocol/migrations/p09-note-file-product-request-v1.md',
 'protocol/migrations/p09-note-export-xml-context.md')


def inverse(text,pin,label):
    text=text.replace('\r\n','\n');c.require(pin['sha256'] in {hashlib.sha256(text.encode()).hexdigest(),hashlib.sha256(text.replace('\n','\r\n').encode()).hexdigest()},label)


def main():
    c.require(not (c.ROOT/OUTPUT).exists(),'XML_CONTEXT_SYNC_IMMUTABLE_RUN_EXISTS');shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_NOTE_XML_CONTEXT_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=q.json(base.OUTPUT);prior=q.json(base.PRIOR)
        c.require(q.snapshots[base.OUTPUT]['sha256']=='e9b76870002e6475e5beb72f9d6023d6b9bd67aee9478c1982a3c0c3a84f5a90'
            and q.snapshots[base.PRIOR]['sha256']=='5b429d7bcc6a7b71409488471091d9985cb50946617255eca1b2716abdd15fe6','EXACT_CONTEXT_RESULT_AND_RECOVERY')
        c.require(passed['state']=='PASS_NOTE_EXPORT_XML_CONTEXT_TWO_PRODUCT_TESTS_FIFTY_TWO_PRIOR_PASSES_PRESERVED_NOT_NATIVE_OR_GATE'
            and passed['fresh_inputs']==passed['final_fresh_hashes']==459 and passed['production_and_core_tests_unchanged']
            and passed['only_product_test_assertion_syntax_changed'] and not passed['prior_fifty_two_tests_reexecuted'],'RETAINED_CORE_AND_FRESH_PRODUCT_CLOSURE')
        expected=set()
        for suite in base.base.CORE:
            names=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text('crates/hwpx-package/tests/'+suite+'.rs')))-base.base.EXCLUDE
            c.require(not expected&names,'CONTEXT_DISTINCT_CORE_CASES');expected|=names
        actual=prior['steps'][0]['tests'];c.require(len(actual)==len(expected)==52 and {n for n,s in actual}==expected and all(s=='ok'for n,s in actual),'EXACT_FIFTY_TWO_PASSES')
        actual=passed['steps'][0]['tests'];c.require(len(actual)==2 and {n for n,s in actual}==base.base.PRODUCT and all(s=='ok'for n,s in actual),'EXACT_TWO_PRODUCT_PASSES')
        for record in (prior,passed):
            c.require(record['cleanup'],'CONTEXT_RESULT_CLEANUP')
            for step in record['steps']:
                job=step['owned_job'];c.require(step['cleanup'] and job['cleanup_confirmed'] and job['owned_tree_empty'] and job['job_handle_closed']
                    and job['last_job_accounting']['active_processes']==0,'ALL_CONTEXT_JOBS_TERMINAL')
        tested={p['path']:p for p in passed['source_pins']}
        for name in FILES:q.pin(name);c.require(q.snapshots[name]==tested[name],'ALL_SCOPED_TESTED_CONTEXT_CODE_UNCHANGED')
        for suffix,sha in (('035','c168e0692f85e5f5a01025dd89d50a19636dc82dbc4a6d29825a78a947c656de'),('036','c57b197c58e7b4f6a50e7ff8bf6d04348cfa9ca1c2a4be270d64b1223e9d1a8e')):
            name='implementation/p09/evidence/p09-361-note-export-context-components'+suffix+'.v1.json';failed=q.json(name)
            c.require(q.snapshots[name]['sha256']==sha and failed['state']=='FAILED_NOTE_EXPORT_CONTEXT_COMPONENTS' and failed['cleanup']
                and failed['steps'][0]['tests']==[] and any('E0624' in s for s in failed['steps'][0]['diagnostics']),'PRIVATE_TEST_ACCESS_FAILURES_PRESERVED')
        old_name='implementation/p09/evidence/p09-361-note-file-request-debug-check033.v1.json';old=q.json(old_name)
        c.require(q.snapshots[old_name]['sha256']=='3bbee80c0f90ad6d07c37e9a15c38704a8d517b13b9c721ab6ecc9b0e5d0710c','EXACT_PRE_CONTEXT_BASELINE')
        oldpins={p['path']:p for p in old['source_pins']};flow=q.text(FILES[0])
        start=flow.index('    /// Source graph mapping only:');end=flow.index('    fn read_document_profile(',start);flow=flow[:start]+flow[end:]
        flow=flow.replace('validate_profile_attributes(\n            root,','validate_attributes(\n            root,').replace('            ],\n            profile,\n        )?;','            ],\n        )?;')
        flow=flow.replace('    SourceXmlContext,\n','').replace('validate_profile_attributes(run, &["charPrIDRef", "charTcId"], state.profile)','validate_attributes(run, &["charPrIDRef", "charTcId"])')
        flow=flow.replace('state.profile != ReadProfile::TypedParagraph && child.first_child().is_some()','state.profile == ReadProfile::SourcePreserving && child.first_child().is_some()')
        start=flow.index('fn validate_profile_attributes(');end=flow.index('fn validate_attributes(',start);flow=flow[:start]+flow[end:]
        inverse(flow,oldpins[FILES[0]],'ORIGINAL_TEXT_FLOW_READERS_AND_WRITER_EXACT_INVERSE')
        inverse(q.text(FILES[1]).replace('TextFlowReader::read_preserving_xml_context(xml, index, TextFlowLimits::default())',
            'TextFlowReader::read_preserving_source(xml, index, TextFlowLimits::default())'),oldpins[FILES[1]],'MAPPER_ONLY_EXPLICIT_SOURCE_PROFILE_SWITCH')
        inverse(q.text(FILES[2]).replace('    #[error("NOTE_FILE_INHERITED_XML_CONTEXT_UNQUALIFIED")] InheritedContext,\n',''),oldpins[FILES[2]],'ORIGINAL_EXPORT_COMPILER_BODY_UNCHANGED')
        inverse(q.text(base.base.TEST).split('#[test]\nfn note_file_product_inherited_xml_context_',1)[0],oldpins[base.base.TEST],'ORIGINAL_EIGHT_PRODUCT_TEST_BODIES_UNCHANGED')
        for name in FILES[11:17]:c.require(q.snapshots[name]==oldpins[name],'ORIGINAL_STORED_REQUEST_AND_SHARED_WRITER_UNCHANGED')
        for name in DOCS:q.pin(name)
        state=q.text(DOCS[0]).split('> 2026-10-19 P09 이전 주석 제품 준비 요청',1)[0]
        for marker in ('xml:lang','xml:space','InheritedContext','52개를 반복하지','459fresh/final459','78.91%','14.6709%',
            'REF46+SEARCH19=65','158/249','고정CROSSREF8종 NOT_RUN','Native011 미승인/미실행'):c.require(marker in state,'CURRENT_CONTEXT_RESULT_AND_SCOPE_BOUNDARIES')
        context=q.text(DOCS[4])
        for marker in ('SourceXmlContext','empty value','XML Base','459 fresh/final459','54 unique tests','no official queue acceptance',
            'container-to-body layout','P09 Gate remain open'):c.require(marker in context,'CONTEXT_PROFILE_REQUIRED_BOUNDARIES')
        for name in DOCS[1:4]:c.require('p09-note-export-xml-context.md' in q.text(name),'CONTEXT_CONTRACT_AND_POLICY_LINKS')
        q.pin(Path(__file__).relative_to(c.ROOT).as_posix());q.finish();guard.check(force=True)
        row.update(state='PASS_NOTE_EXPORT_XML_CONTEXT_SCOPED_CODE_AND_DOCUMENT_SYNC_NOT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),
            final_fresh_hashes=q.final_fresh_hashes,retained_core_passes=52,fresh_product_passes=2,original_typed_reader_writer_inverse=True,
            original_compiler_and_eight_product_tests_preserved=True,entire_459_input_inventory_reaudited=False,
            native_container_layout_and_intermediate_base_qualified=False,next_work='XML_Base_URI_binding_and_native_subList_semantics')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'CONTEXT_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_CONTEXT_SYNC_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2

if __name__=='__main__':raise SystemExit(main())
