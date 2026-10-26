"""Actual product block-bookmark reader on retained Native670; no Native replay."""
import json,re,subprocess,sys,time
from pathlib import Path
import named_style_verification_runtime as r
import verify_prepared_bookmark636_graph as inventory
import verify_style_predicate_search as includes
import verify_source_field_semantics as dep
import run_prepared_bookmark_native631 as p
SELF='tools/p09/verify_block_bookmark_import675.py'
TEST='crates/hwpx-package/tests/document_import_block_bookmarks.rs'
READBACK='implementation/p09/evidence/p09-361-block-bookmark-source673-readback001.v1.json'
OUTPUT='implementation/p09/evidence/p09-361-block-bookmark-import675-product001.v1.json'

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
        names=inventory.inputs(guard.check)|includes.test_inputs((TEST,),guard)|{SELF,TEST,READBACK}
        for stage in readback['stages'].values():
            pin=stage['source'];require(q.pin(pin['path'])==pin,'ORIGINAL_NATIVE_BYTES')
        for name in sorted(names):q.pin(name)
        tests=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(TEST)))
        require(len(tests)==11 and '#[ignore]'not in q.text(TEST),'ELEVEN_CHANGED_PRODUCT_TESTS')
        before=p.runtime.base.session.startup.hwp_pids(guard.windows,guard.check)
        args=[r.harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package','--test','document_import_block_bookmarks',
            '--message-format=short','--',*sorted(tests),'--exact','--test-threads=1']
        begin=time.time_ns();r.harness.run_one('actual_block_source_reader11_no_Native',args,tests,guard,r.audit.environment(),row,observe_capture=r.snapshot)
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
        value,_=p.retention.retain(r.c.ROOT,'implementation/p09/evidence/private/p09-361-block-bookmark-import675-product001-forensic',row)
        pin=p.publish(OUTPUT,value)
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','cleanup','new_product_tests','fresh_inputs','final_fresh_hashes',
            'elapsed_seconds','system_CPU_max','available_RAM_min_percent')},'steps':[{k:s.get(k)for k in('stage','exit_code','diagnostics','panic_locations','safe_error_variants','tests')}for s in row['steps']],
            'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('QUALIFIED675_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())

