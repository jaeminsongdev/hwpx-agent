"""Actual32 renamed product reads and exact24 BMP pixels; no Native or old tests."""
import hashlib,json,subprocess,sys,time
import named_style_verification_runtime as r
import run_prepared_bookmark_native761 as e
import verify_prepared_bookmark636_graph as inventory
import verify_style_predicate_search as includes
import verify_source_field_semantics as dep
import resource_bundle714 as journal
import product_result_capture766 as capture
import renamed_bitmap767 as bitmap
from verify_prepared_bookmark631 import command
SELF='tools/p09/verify_renamed_readback766.py'
TEST='tools/p09/tests/test_renamed_bitmap767.py'
EXAMPLE='crates/product-cli/examples/p09_renamed_readback765.rs'
EXE='target/debug/examples/p09_renamed_readback765.exe'
DEP=EXE[:-4]+'.d'
PRIOR='implementation/p09/evidence/p09-361-renamed-bookmark763-readback001.v1.json'
MANIFEST='implementation/p09/evidence/p09-361-renamed-bookmark764-inputs.v1.json'
OUTPUT='implementation/p09/evidence/p09-361-renamed-bookmark766-product001.v1.json'

def require(ok,code):
    if not ok:raise ValueError('XREF_READBACK766_'+code)

def read_image(q,pin):
    require(54<=pin['bytes']<=16777216 and q.pin(pin['path'])==pin,'EXACT_BMP_INPUT')
    data=bytearray();start=time.monotonic()
    with(q.root/pin['path']).open('rb')as stream:
        while True:
            q.checkpoint();piece=stream.read(65536)
            if not piece:break
            data.extend(piece);require(len(data)<=pin['bytes'],'BOUNDED_BMP_READ')
            wait=len(data)/2097152.-(time.monotonic()-start)
            while wait>0:time.sleep(min(wait,.05));q.checkpoint();wait=len(data)/2097152.-(time.monotonic()-start)
    require(len(data)==pin['bytes']and hashlib.sha256(data).hexdigest()==pin['sha256'],'BMP_READ_IDENTITY')
    return bytes(data)

def main():
    require(sys.argv[1:]==['--actual-renamed-product-and-pixels-no-native']and not(r.c.ROOT/OUTPUT).exists(),'MODE_NEW_OUTPUT')
    r.tools.select_own_single_cpu();r.shared.host.configure_host_policy(r.c)
    guard=r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))()
    q=binary=observer=None;begin=time.monotonic();row=dict(state='FAILED766_RENAMED_PRODUCT_AND_PIXELS',steps=[],Native_started=False,old_tests_or_Native_replayed=False,Native_cursor_or_full_F11_qualified=False,P09_complete=False)
    try:
        observer=journal.Attached(guard);guard.acquire();observer.phase('input_binding');q=r.a.AcceptanceReader(r.c.ROOT,guard.check)
        prior=e.codec.unpack(q.json(PRIOR),guard.check)
        require(q.snapshots[PRIOR]['sha256']=='302c9eeb196cf0cdeb8669b2305782928c820b136acd453d51ac72de17f0393e'
            and prior['cleanup']is True and prior['fresh_inputs']==prior['final_fresh_hashes']==1378 and len(prior['cases'])==8
            and prior['semantic_product_or_render_qualified']is False,'EXACT763_OBSERVATIONS_NOT_PREVIOUS_ACCEPTANCE')
        for case in prior['cases']:
            require(all(case[k]is True for k in('all_source_ranges_preserved','all_commands_preserved','native_dirty_cleared','all_native_cache_matches_source_or_conditional_single_page','saved_reopened_parameters_equal')),'XML_OBSERVATIONS_WITHOUT_NEW_NATIVE')
        require(q.pin(MANIFEST)==prior['product_inputs'],'BOUND_NEW32_AND24_MANIFEST')
        old={p['path']:p for p in prior['source_pins']}
        names=inventory.inputs(guard.check)|includes.test_inputs((EXAMPLE,),guard)|{SELF,TEST,MANIFEST,'tools/p09/product_result_capture766.py','tools/p09/renamed_bitmap767.py'}
        row['current_execution_paths']=sorted(names)
        for name in sorted(names):
            pin=q.pin(name)
            if name in old:require(pin==old[name],'UNCHANGED_EXISTING_PRODUCT_CODE_NO_OLD_TEST_REPLAY')
        manifest=q.json(MANIFEST);require(len(manifest['cases'])==8 and len(manifest['snapshots'])==24,'ALL_INPUTS')
        for case in manifest['cases']:
            for stage in case['stages'].values():require(q.pin(stage['pin']['path'])==stage['pin'],'EXACT_CURRENT32')
        for snap in manifest['snapshots']:
            require(q.pin(snap['snapshot']['path'])==snap['snapshot']and q.pin(snap['trace']['path'])==snap['trace']
                and snap['previously_closed_native_producer_bound']is True and snap['page_count']==1 and snap['page_indices']==[0]
                and len(snap['page_images'])==1,'EXACT_CURRENT_PRODUCER_EXTENT')
            require(q.pin(snap['page_images'][0]['path'])==snap['page_images'][0],'BOUND_PAGE_IMAGE')
        native=e.runtime.base.session.startup;before=native.hwp_pids(guard.windows,guard.check);require(not before,'NO_HWP_BEFORE')
        observer.phase('model_checks');value=command(guard,[sys.executable,'-B',str(r.c.ROOT/TEST)],r.audit.environment(),row,'new_BMP_pixel_boundary_controls7')
        require({k:value[k]for k in('run','errors','failures','skipped')}==dict(run=7,errors=0,failures=0,skipped=0)and value['actual_native_started']is False,'PIXEL_CONTROLS')
        observer.phase('readback');pixel_rows=[]
        for snap in manifest['snapshots']:
            pin=snap['page_images'][0];description=bitmap.describe(read_image(q,pin),guard.check)
            require(description['file_sha256']==pin['sha256']and description['nonwhite_color_channels']>0
                and(description['width'],description['height'])==(794,1122),'COMPLETE_NONEMPTY_FIXED_PAGE_PIXELS')
            pixel_rows.append(dict(case_index=snap['case_index'],stage=snap['stage'],image=pin,description=description))
        for index in range(1,9):
            group=[v for v in pixel_rows if v['case_index']==index]
            require(len(group)==3 and {v['stage']for v in group}=={'initial','saved','reopened'}
                and len({v['description']['pixel_sha256']for v in group})==1,'EXACT_THREE_ROLE_VISIBLE_PIXEL_PARITY')
        row['producer_bound_page_pixel_observations']=pixel_rows
        binary=r.a.AcceptanceReader(r.c.ROOT,guard.check);env=r.audit.environment()
        common=['--offline','--locked','-j','1','--message-format=short','-p','hwpx-agent-cli','--features','p09-installed-format-fixture','--config','profile.dev.package.hwpx-agent-cli.codegen-units=2']
        observer.phase('build');r.harness.run_one('build_new_renamed_readback765_only',[r.harness.CARGO,'build',*common,'--example','p09_renamed_readback765'],set(),guard,env,row,observe_capture=r.snapshot)
        require(row['steps'][-1]['exit_code']==0 and not row['steps'][-1]['diagnostics'],'CLEAN_NEW_EXAMPLE_BUILD')
        observer.phase('binary_binding');row['compiled_example']=[binary.pin(EXE),binary.pin(DEP)]
        require(dep.dependencies(r.c.ROOT/DEP)<=set(q.snapshots),'ALL_COMPILER_DEPENDENCIES_BOUND')
        observer.phase('readback');actual=capture.command(guard,[str(r.c.ROOT/EXE),'--actual-renamed-thirty-two-no-native'],env,row,'actual32_current_renamed_meanings_results_source_navigation')
        row['product']=actual
        require(actual is not None and actual['all_conditions_passed']is True
            and actual['state']=='QUALIFIED765_RENAMED_NATIVE24_CANDIDATE8_CURRENT_PRODUCT_MEANINGS_RESULTS_NAVIGATION_NOT_NATIVE_CURSOR_OR_P09'
            and len(actual['observations'])==32 and(actual['source_text_matches'],actual['stale_candidate_names'],actual['needs_document_flow'],actual['producer_bound_conditional_single_page_matches'],actual['source_destinations'],actual['hyperlink_disabled'])==(14,2,16,12,16,16)
            and actual['common_block_meanings_per_source']==8 and actual['unsupported_per_source']==0 and actual['main_status']=='incomplete'
            and actual['Native_started']is False and actual['Native_cursor_or_general_flow_qualified']is False,'WHOLE32_CURRENT_PRODUCT_READBACK')
        for seen,(case,stage)in zip(actual['observations'],((c,s)for c in manifest['cases']for s in('candidate','initial','saved','reopened')),strict=True):
            require(seen['case_index']==case['case_index']and seen['stage']==stage and seen['source']==case['stages'][stage]['pin']and seen['source_unchanged']is True,'EXACT32_PRODUCT_IDENTITIES')
        require(native.hwp_pids(guard.windows,guard.check)==before,'NO_NATIVE_PROCESS_CHANGE')
        observer.phase('final_binary');binary.finish()
        observer.phase('final_source');q.finish()
        observer.phase('final_resource');guard.check(force=True)
        row.update(state='QUALIFIED766_RENAMED_NATIVE24_PRODUCT32_SAVED_EXTENT_AND24_PIXELS_NOT_NATIVE_CURSOR_OR_P09',Native_process_set_unchanged=True,all_eight_visible_three_role_pixel_groups_equal=True,original_BMP_files_not_rewritten=True)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError,KeyboardInterrupt)as error:row.update(**e.runtime.io.safe_failure(error))
    finally:
        guard.close();observer_cleanup=True if observer is None else observer.close()
        if observer is not None:row['phase_resources']=observer.packet()
        row.update(cleanup=guard.cleanup and observer_cleanup and all(s['cleanup']for s in row['steps']),source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,artifact_final_fresh_hashes=0 if binary is None else binary.final_fresh_hashes,resource_samples=len(guard.samples),elapsed_seconds=round(time.monotonic()-begin,3),system_CPU_max=max((s['system_cpu_percent']for s in guard.samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in guard.samples),default=None))
        value,_=e.publisher.retention.retain(r.c.ROOT,'implementation/p09/evidence/private/p09-361-renamed-bookmark766-product001-forensic',row);pin=e.publish(OUTPUT,value)
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','cleanup','fresh_inputs','final_fresh_hashes','artifact_final_fresh_hashes','resource_samples','system_CPU_max','available_RAM_min_percent','elapsed_seconds')},'steps':[{k:s.get(k)for k in('stage','exit_code','tests','result','safe_error_code','diagnostics')}for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('QUALIFIED766_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
