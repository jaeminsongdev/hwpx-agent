"""Actual product block-bookmark reader on retained Native670; no Native replay."""
import hashlib,json,re,subprocess,sys,time
from pathlib import Path
import named_style_verification_runtime as r
import verify_prepared_bookmark636_graph as inventory
import verify_style_predicate_search as includes
import verify_source_field_semantics as dep
import run_prepared_bookmark_native631 as p
SELF='tools/p09/verify_block_bookmark_import675.py'
TEST='crates/hwpx-package/tests/document_import_block_bookmarks.rs'
READBACK='implementation/p09/evidence/p09-361-block-bookmark-source673-readback001.v1.json'
OUTPUT='implementation/p09/evidence/p09-361-block-bookmark-import675-product004.v1.json'
PRIOR='implementation/p09/evidence/p09-361-block-bookmark-import675-product001.v1.json'
ARCHIVE='implementation/p09/source-archive/p361-block-bookmark-import675-product001/'
PARTIAL='implementation/p09/evidence/p09-361-block-bookmark-import675-product003.v1.json'
ARCHIVE003='implementation/p09/source-archive/p361-block-bookmark-import675-product003/'

def require(ok,code):
    if not ok:raise ValueError('BLOCK675_'+code)

def main():
    require(sys.argv[1:]==['--changed-product-reader-only']and not(r.c.ROOT/OUTPUT).exists(),'MODE_OR_IMMUTABLE_OUTPUT')
    r.tools.select_own_single_cpu();r.shared.host.configure_host_policy(r.c)
    guard=r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))()
    q=binary=None;start=time.monotonic();row=dict(state='FAILED675_PRODUCT_BLOCK_BOOKMARK_IMPORT',steps=[],Native_started=False,
        previous_Native_trials_replayed=False,unrelated_test_suites_replayed=False,block_authoring_or_Content_positive_qualified=False,P09_complete=False)
    try:
        guard.acquire();q=r.a.AcceptanceReader(r.c.ROOT,guard.check)
        readback=p.codec.unpack(q.json(READBACK))
        require(q.snapshots[READBACK]['sha256']=='cc9022ab8a90d50152ca5926c7494b6e2de8faf7af3f18ec6f197ade6b23b8ad'
            and readback['state']=='QUALIFIED673_FIXED_EIGHT_BLOCK_SOURCE_XML_NOT_PRODUCT_CONTENT_OR_F11'
            and readback['cleanup']is True and readback['documents']==2 and readback['block_ranges_per_document']==8,
            'RETAINED_TWO_CLOSED_BLOCK_SOURCES')
        failure=p.codec.unpack(q.json(PRIOR))
        require(q.snapshots[PRIOR]['sha256']=='f46c0a4d1972b1b995e3c0c76f44eca6e590ac8ab45c8d7f84190e4c10107a0b'
            and failure['cleanup']is True and len(failure['steps'])==1 and failure['steps'][0]['exit_code']==101
            and failure['steps'][0]['tests']==[]and failure['steps'][0]['bounded_output_observation']['rust_error_codes']==['E0599'],
            'ORIGINAL_TEST_COMPILE_FAILURE_NO_TEST_EXECUTED')
        for pin in failure['source_pins']:
            if pin['path']in(SELF,TEST):
                saved_path=ARCHIVE+Path(pin['path']).name;saved=q.pin(saved_path)
                raw=(r.c.ROOT/saved_path).read_bytes()
                # Preserve the archive's single extra LF separately. Original
                # length plus SHA binds every original byte without rewriting it.
                require(saved['bytes']==pin['bytes']+1 and raw[-1:]==b'\n'
                    and hashlib.sha256(raw[:-1]).hexdigest()==pin['sha256'],'ALL_FAILED_CODE_BYTES_PRESERVED_WITH_ONE_SEPARATOR_LF')
            else:require(q.pin(pin['path'])==pin,'UNCHANGED_PRODUCT_LIBRARY_AND_OTHER_INPUTS')
        archive_failure=p.codec.unpack(q.json('implementation/p09/evidence/p09-361-block-bookmark-import675-product002.v1.json'))
        require(q.snapshots['implementation/p09/evidence/p09-361-block-bookmark-import675-product002.v1.json']['sha256']=='15e314ea2ae4aebb71853e57daf4cbc2fbfc9a20f934969eb7d410e1c23aaf98'
            and archive_failure['cleanup']is True and archive_failure['steps']==[]
            and archive_failure['error_code']=='BLOCK675_EXACT_FAILED_CODE_ARCHIVED','PRESERVED_ARCHIVE_CHECK_FAILURE_NO_COMPILE_OR_TEST')
        q.pin('implementation/p09/source-archive/p361-block-bookmark-import675-product002/verify_block_bookmark_import675.py')
        before=q.text(ARCHIVE+Path(TEST).name)[:-1]
        intermediate=q.text(ARCHIVE003+Path(TEST).name)
        require(intermediate==before.replace('ReferenceAuxiliaryLimits::default()',
            'ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig::default()).expect("bounded limits")',1),
            'ONLY_TEST_LIMIT_CONSTRUCTOR_CORRECTED')
        old='''        let bytes=package(&raw)?;let forms=fixture::forms(&bytes,"parameter-drift")?;
        match ImportedDocumentFields::import(&forms) {
            Err(_)=>{},Ok(fields)=>assert!(ImportedBlockBookmarks::import(&fields,limits()).is_err()),
        }'''
        new='''        let bytes=package(&raw)?;
        if let Ok(forms)=fixture::forms(&bytes,"parameter-drift") {
            match ImportedDocumentFields::import(&forms) {
                Err(_)=>{},Ok(fields)=>assert!(ImportedBlockBookmarks::import(&fields,limits()).is_err()),
            }
        }'''
        require(intermediate.count(old)==1 and q.text(TEST)==intermediate.replace(old,new,1),
            'ONLY_FAILED_FIXTURE_ACCEPTS_ORIGINAL_EARLIER_ADMISSION_DENIAL')
        partial=p.codec.unpack(q.json(PARTIAL))
        require(q.snapshots[PARTIAL]['sha256']=='396c12a1abf77f2805234b514049c62a4b8a84c98240ffce1d2a8292906d29b2'
            and partial['cleanup']is True and len(partial['steps'])==1 and partial['steps'][0]['exit_code']==101,
            'ORIGINAL_PARTIAL_PRODUCT_RESULT')
        statuses=dict(partial['steps'][0]['tests']);failed='malformed_or_missing_parameter_envelope_does_not_invent_a_block'
        require(len(statuses)==11 and statuses[failed]=='FAILED'
            and all(state=='ok'for name,state in statuses.items()if name!=failed),'TEN_RETAINED_PASSES_ONE_FAILURE')
        for pin in partial['source_pins']:
            if pin['path']in(SELF,TEST):
                saved=q.pin(ARCHIVE003+Path(pin['path']).name)
                require((saved['bytes'],saved['sha256'])==(pin['bytes'],pin['sha256']),'EXACT_PARTIAL_RUN_CODE_ARCHIVED')
            else:require(q.pin(pin['path'])==pin,'PARTIAL_RUN_PRODUCT_AND_OTHER_INPUTS_UNCHANGED')
        names=inventory.inputs(guard.check)|includes.test_inputs((TEST,),guard)|{SELF,TEST,READBACK,PRIOR,PARTIAL}
        for stage in readback['stages'].values():
            pin=stage['source'];require(q.pin(pin['path'])==pin,'ORIGINAL_NATIVE_BYTES')
        for name in sorted(names):q.pin(name)
        tests=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(TEST)))
        require(len(tests)==11 and '#[ignore]'not in q.text(TEST),'ELEVEN_CHANGED_PRODUCT_TESTS')
        require(set(statuses)==tests,'SAME_UNIQUE_ELEVEN_TESTS')
        row.update(retained_pass_tests=sorted(name for name,state in statuses.items()if state=='ok'),
            retained_pass_conditions=10,executed_changed_tests=1,total_unique_product_conditions=11,
            prior_partial_receipt=q.snapshots[PARTIAL])
        tests={failed}
        before=p.runtime.base.session.startup.hwp_pids(guard.windows,guard.check)
        args=[r.harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package','--test','document_import_block_bookmarks',
            '--message-format=short','--',*sorted(tests),'--exact','--test-threads=1']
        begin=time.time_ns();r.harness.run_one('corrected_failed_fixture_only1_retained10_no_Native',args,tests,guard,r.audit.environment(),row,observe_capture=r.snapshot)
        require(row['steps'][-1]['exit_code']==0 and not row['steps'][-1]['diagnostics'],'CHANGED_PRODUCT_TESTS_CLEAN')
        binary=r.a.AcceptanceReader(r.c.ROOT,guard.check);compiled=[]
        for path in(r.c.ROOT/'target/debug/deps').glob('document_import_block_bookmarks-*.d'):
            if path.stat().st_mtime_ns<begin:continue
            actual=dep.dependencies(path)
            require({TEST,'crates/hwpx-package/tests/support/document_import_field_fixture.rs'}<=actual
                and actual<=set(q.snapshots),'COMPILED_TEST_INPUTS_PREBOUND')
            compiled.append(dict(dep_info=binary.pin(path.relative_to(q.root).as_posix()),
                binary=binary.pin(path.with_suffix('.exe').relative_to(q.root).as_posix()),dependency_count=len(actual)))
        require(len(compiled)==1,'ONE_CURRENT_TEST_EXECUTABLE')
        require(p.runtime.base.session.startup.hwp_pids(guard.windows,guard.check)==before,'NO_HWP_PROCESS_CHANGE')
        binary.finish();q.finish();guard.check(force=True)
        row.update(state='QUALIFIED675_PRODUCT_BLOCK_BOOKMARK_SOURCE_IMPORT_NOT_AUTHORING_CONTENT_OR_F11',
            compiled_inputs=compiled,new_product_tests=11,actual_Native_source_documents=2,actual_block_ranges_per_document=8,
            product_block_source_inventory_qualified=True,Native_process_set_unchanged=True,
            existing_point_authoring_admission_unchanged=True,source_names_and_selected_content_redacted=True)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError,KeyboardInterrupt)as error:
        row.update(**p.runtime.io.safe_failure(error))
        if isinstance(error,ValueError)and re.fullmatch(r'BLOCK675_[A-Z0-9_]{1,100}',str(error)):row['error_code']=str(error)
    finally:
        guard.close();row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),
            source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),
            final_fresh_hashes=0 if q is None else q.final_fresh_hashes,compiled_final_fresh_hashes=0 if binary is None else binary.final_fresh_hashes,
            elapsed_seconds=round(time.monotonic()-start,3),system_CPU_max=max((s['system_cpu_percent']for s in guard.samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in guard.samples),default=None))
        value,_=p.retention.retain(r.c.ROOT,'implementation/p09/evidence/private/p09-361-block-bookmark-import675-product004-forensic',row)
        pin=p.publish(OUTPUT,value)
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','cleanup','new_product_tests','fresh_inputs','final_fresh_hashes',
            'elapsed_seconds','system_CPU_max','available_RAM_min_percent')},'steps':[{k:s.get(k)for k in('stage','exit_code','diagnostics','panic_locations','safe_error_variants','tests')}for s in row['steps']],
            'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('QUALIFIED675_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
