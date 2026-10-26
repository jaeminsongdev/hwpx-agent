"""Changed core writer, shared ID profile and stored candidate boundaries only."""
import json,re,subprocess,sys,time
from pathlib import Path
import named_style_verification_runtime as r
import verify_prepared_bookmark636_graph as inventory
import verify_style_predicate_search as includes
import verify_source_field_semantics as dep
import run_prepared_bookmark_native631 as p
SELF='tools/p09/verify_block_bookmark_authoring680.py'
CORE='crates/hwpx-package/tests/block_bookmark_authoring679.rs'
CONTEXT='crates/hwpx-package/tests/bookmark_authoring_targets676.rs'
HOST='crates/product-cli/tests/stored_bookmark_insertion628.rs'
PRODUCT='crates/product-cli/tests/support/block_bookmark_authoring679.rs'
ADMISSION='crates/product-cli/tests/support/bookmark_display_admission639.rs'
PRIOR='implementation/p09/evidence/p09-361-bookmark-authoring-targets678-product002.v1.json'
OUTPUT='implementation/p09/evidence/p09-361-block-bookmark-authoring680-product004.v1.json'
FAILED='implementation/p09/evidence/p09-361-block-bookmark-authoring680-product001.v1.json'
FAILED_ARCHIVE='implementation/p09/source-archive/p361-block-bookmark-authoring680-product001/'
FAILED002='implementation/p09/evidence/p09-361-block-bookmark-authoring680-product002.v1.json'
ARCHIVE002='implementation/p09/source-archive/p361-block-bookmark-authoring680-product002/'
HELPER='crates/hwpx-package/tests/support/block_bookmark679_fixture.rs'
FAILED003='implementation/p09/evidence/p09-361-block-bookmark-authoring680-product003.v1.json'
ARCHIVE003='implementation/p09/source-archive/p361-block-bookmark-authoring680-product003/'
ARCHIVE='implementation/p09/source-archive/p361-bookmark-block-authoring679/'
CHANGED={
    'crates/hwpx-package/src/document_import/fields/bookmark_authoring_targets.rs',
    'crates/hwpx-package/src/document_import/fields/bookmark_crossref.rs',
    'crates/hwpx-package/src/document_import/fields/bookmark_insertion.rs',
    'crates/hwpx-package/src/document_import/fields/semantics/source_index/bookmark_updates.rs',
    'crates/hwpx-package/src/id_index.rs',
    'crates/product-cli/src/reference_validation_product/source_crossref/bookmark_insertion.rs',
    'crates/product-cli/src/reference_validation_product/source_crossref/bookmark_updates.rs',
    'crates/product-cli/src/form_stored_provider/actual_import/bookmark_insertion_output.rs',
    'crates/product-cli/src/form_stored_provider/actual_import/bookmark_command_output.rs',HOST}

def require(ok,code):
    if not ok:raise ValueError('AUTHOR680_'+code)

def test_names(q,path,prefix=''):
    text=q.text(path);require('#[ignore]'not in text,'NO_IGNORED_CHANGED_TEST')
    return {prefix+name for name in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',text)}

def main():
    require(sys.argv[1:]==['--changed-core-and-stored-only']and not(r.c.ROOT/OUTPUT).exists(),'MODE_OR_IMMUTABLE_OUTPUT')
    r.tools.select_own_single_cpu();r.shared.host.configure_host_policy(r.c)
    guard=r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))()
    q=binary=None;start=time.monotonic();row=dict(state='FAILED680_BLOCK_BOOKMARK_AUTHORING',steps=[],Native_started=False,
        old249_or_consumed_Native_replayed=False,Native_Content_positive_qualified=False,P09_complete=False)
    try:
        guard.acquire();q=r.a.AcceptanceReader(r.c.ROOT,guard.check)
        prior=p.codec.unpack(q.json(PRIOR))
        require(q.snapshots[PRIOR]['sha256']=='a7cd630dfd8902775ece926b4a9fdd71f25fffba5885c2bb87157db3910cb94e'
            and prior['cleanup']is True and prior['new_target_conditions']==12,'EXACT_PRIOR_TARGET_SELECTION')
        for pin in prior['source_pins']:
            if pin['path'].startswith('crates/')and Path(pin['path']).suffix in('.rs','.toml'):
                path=ARCHIVE+pin['path']if pin['path']in CHANGED else pin['path']
                bound=q.pin(path);require((bound['bytes'],bound['sha256'])==(pin['bytes'],pin['sha256']),'PRESERVED_PRODUCT_AND_ARCHIVED_CHANGED_CODE')
        old=q.text(ARCHIVE+HOST);new=q.text(HOST)
        require(new==old.replace('mod admission639;\n','mod admission639;\n#[path="support/block_bookmark_authoring679.rs"]\nmod block679;\n',1),
            'ONLY_NEW_STORED_TEST_MODULE_NO_OLD_TEST_EDITS')
        failure=p.codec.unpack(q.json(FAILED))
        require(q.snapshots[FAILED]['sha256']=='0e7c8edd431f63d7eec0aaf088ab2747a71d5ce534ed12eee93892afecf451a1'
            and failure['cleanup']is True and len(failure['steps'])==1 and failure['steps'][0]['tests']==[]
            and failure['steps'][0]['bounded_output_observation']['rust_error_codes']==['E0599'],'PRESERVED_INITIAL_COMPILE_FAILURE')
        corrected='crates/hwpx-package/src/document_import/fields/semantics/source_index/bookmark_updates.rs'
        for pin in failure['source_pins']:
            path=FAILED_ARCHIVE+pin['path']if pin['path']in(SELF,corrected)else ARCHIVE002+pin['path']if pin['path']in(CORE,HELPER)else ARCHIVE003+pin['path']if pin['path']==PRODUCT else pin['path']
            bound=q.pin(path);require((bound['bytes'],bound['sha256'])==(pin['bytes'],pin['sha256']),'FAILED_CODE_AND_OTHER_CURRENT_INPUTS')
        require(q.text(corrected)==q.text(FAILED_ARCHIVE+corrected).replace('destination.source_logical_target_id_sha256()',
            'destination.receipt().logical_target_id_sha256',1),'ONLY_TYPED_TARGET_RECEIPT_ACCESSOR_CORRECTION')
        second=p.codec.unpack(q.json(FAILED002))
        require(q.snapshots[FAILED002]['sha256']=='00b1a632a6277825e2fef7ba45147bbe4ffdea4a305b479ed9fd28af272ba290'
            and second['cleanup']is True and len(second['steps'])==1 and second['steps'][0]['tests']==[]
            and set(second['steps'][0]['bounded_output_observation']['rust_error_codes'])=={'E0277','E0624'},
            'PRESERVED_TEST_HELPER_COMPILE_FAILURE_NO_TEST_EXECUTION')
        for pin in second['source_pins']:
            path=ARCHIVE002+pin['path']if pin['path']in(SELF,CORE,HELPER)else ARCHIVE003+pin['path']if pin['path']==PRODUCT else pin['path']
            bound=q.pin(path);require((bound['bytes'],bound['sha256'])==(pin['bytes'],pin['sha256']),'SECOND_FAILURE_CODE_AND_OTHER_INPUTS_UNCHANGED')
        old=q.text(ARCHIVE002+CORE)
        expected=old.replace('std::result::Result<IdIndex, IdIndexError>','std::result::Result<IdIndex, Box<dyn Error>>',1)
        expected=expected.replace('    IdIndex::build(&mut reader, &graph, profile, IdIndexLimits::default())',
            '    Ok(IdIndex::build(&mut reader, &graph, profile, IdIndexLimits::default())?)',1)
        expected=expected.replace('Err(IdIndexError::BlockBookmarkProfileRejected)',
            'Err(ref e) if matches!(e.downcast_ref::<IdIndexError>(),Some(IdIndexError::BlockBookmarkProfileRejected))')
        require(q.text(ARCHIVE003+CORE)==expected,'ONLY_TEST_ERROR_CONVERSION_AND_SAME_REJECTION_TYPE')
        require(q.text(ARCHIVE003+HELPER)==q.text(ARCHIVE002+HELPER).replace('xml.source_text(s).ok() == Some(DISPLAY)',
            'xml.with_source_bytes(|b|b.get(s.start()..s.end())==Some(DISPLAY.as_bytes()))',1),'PRESERVED_PRIVATE_BYTE_HELPER_ATTEMPT')
        third=p.codec.unpack(q.json(FAILED003))
        require(q.snapshots[FAILED003]['sha256']=='30fd5ec40ef1f5c40d3fab023b434f38064cd8a20b7fd7bcfcce0333a4cb6ba1'
            and third['cleanup']is True and third['steps'][0]['tests']==[]
            and third['steps'][0]['bounded_output_observation']['rust_error_codes']==['E0624'],'PRESERVED_SECOND_PRIVATE_API_COMPILE_FAILURE')
        for pin in third['source_pins']:
            path=ARCHIVE003+pin['path']if pin['path']in(SELF,CORE,HELPER,PRODUCT)else pin['path']
            bound=q.pin(path);require((bound['bytes'],bound['sha256'])==(pin['bytes'],pin['sha256']),'THIRD_FAILURE_CODE_AND_OTHER_INPUTS_UNCHANGED')
        require(q.text(CORE)==q.text(ARCHIVE003+CORE).replace('native::select(&forms)?','native::select(&forms,raw)?',1),
            'ONLY_PASS_ORIGINAL_INPUT_BYTES_TO_CORE_FIXTURE')
        require(q.text(PRODUCT)==q.text(ARCHIVE003+PRODUCT).replace('native::select(source.imported())?',
            'native::select(source.imported(),&bytes)?'),'ONLY_PASS_ORIGINAL_INPUT_BYTES_TO_STORED_FIXTURE')
        helper=q.text(HELPER)
        require('xml.source_text('not in helper and'xml.with_source_bytes('not in helper
            and 'xml.original_sha256()'in helper and 'FIXTURE679_EXACT_PART_BYTES'in helper,
            'PUBLIC_ZIP_BYTES_MATCH_PARSER_SOURCE_IDENTITY_NO_PRIVATE_API_OR_WEAKENED_TEXT_MATCH')
        names=inventory.inputs(guard.check)|includes.test_inputs((CORE,CONTEXT,HOST),guard)|{SELF,CORE,CONTEXT,HOST,PRODUCT,ADMISSION,PRIOR,FAILED,FAILED002,FAILED003}
        for path in CHANGED:names.add(ARCHIVE+path)
        raw='implementation/p09/evidence/private/p09-361-block-bookmark670-source-document001/created.hwpx'
        require(q.pin(raw)['sha256']=='aa0ae8f3042a0b3be43733deb0196488bdd1bac14e6025f7785915cca5660076','EXACT_NATIVE_SOURCE_NO_REPLAY')
        for path in sorted(names):q.pin(path)
        core=test_names(q,CORE);stored=test_names(q,PRODUCT,'block679::');affected=test_names(q,ADMISSION,'admission639::')
        require((len(core),len(stored),len(affected))==(10,3,10),'EXACT_CHANGED_CORE_STORED_AND_AFFECTED_POINT_TESTS')
        context={'actual_created_and_reopened_eight_blocks_bind_all_four_displays_and_link_options',
            'point_commands_and_target_state_match_the_original_source_context','cross_family_name_collision_rejects_both_selected_ids'}
        require(context<=test_names(q,CONTEXT),'ONLY_THREE_DIRECTLY_AFFECTED_CONTEXT_CASES')
        before=p.runtime.base.session.startup.hwp_pids(guard.windows,guard.check)
        binary=r.a.AcceptanceReader(r.c.ROOT,guard.check);compiled=[]
        groups=[('hwpx-package','block_bookmark_authoring679',core,'new_core_writer_and_ID_profile10'),
            ('hwpx-package','bookmark_authoring_targets676',context,'affected_context3_retained9'),
            ('hwpx-agent-cli','stored_bookmark_insertion628',stored|affected,'new_stored3_and_affected_point10')]
        for package,target,cases,label in groups:
            args=[r.harness.CARGO,'test','--offline','--locked','-j','1','-p',package]
            if package=='hwpx-agent-cli':args+=['--features','p09-installed-format-fixture','--config','profile.dev.package.hwpx-agent-cli.codegen-units=2','--config','profile.test.package.hwpx-agent-cli.codegen-units=2']
            args+=['--test',target,'--message-format=short','--',*sorted(cases),'--exact','--test-threads=1']
            begin=time.time_ns();r.harness.run_one(label,args,cases,guard,r.audit.environment(),row,observe_capture=r.snapshot)
            require(row['steps'][-1]['exit_code']==0 and not row['steps'][-1]['diagnostics'],'CHANGED_TESTS_CLEAN')
            files=[]
            for path in(r.c.ROOT/'target/debug/deps').glob(target+'-*.d'):
                if path.stat().st_mtime_ns<begin:continue
                actual=dep.dependencies(path);require(actual<=set(q.snapshots),'COMPILED_DEPENDENCIES_PREBOUND')
                files.append(dict(dep_info=binary.pin(path.relative_to(q.root).as_posix()),
                    binary=binary.pin(path.with_suffix('.exe').relative_to(q.root).as_posix()),dependency_count=len(actual)))
            require(len(files)==1,'ONE_CURRENT_TEST_EXECUTABLE_PER_GROUP');compiled+=files
        require(p.runtime.base.session.startup.hwp_pids(guard.windows,guard.check)==before,'NO_HWP_PROCESS_CHANGE')
        binary.finish();q.finish();guard.check(force=True)
        row.update(state='QUALIFIED680_BLOCK_SOURCE_BINDING_WRITER_AND_STORED_CANDIDATES_NOT_NATIVE_OR_P09',
            compiled_inputs=compiled,new_core_conditions=10,new_stored_conditions=3,directly_affected_point_conditions=10,
            directly_affected_context_conditions=3,retained_context_conditions_not_replayed=9,
            native_derived_source_with_separate_plain_run=True,shared_block_fieldid_profile_qualified=True,
            original_mixed_runs_and_point_Content_still_denied=True,stored_write_and_current_head_checks_preserved=True,
            Native_process_set_unchanged=True)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError,KeyboardInterrupt)as error:
        row.update(**p.runtime.io.safe_failure(error))
        if isinstance(error,ValueError)and re.fullmatch(r'AUTHOR680_[A-Z0-9_]{1,100}',str(error)):row['error_code']=str(error)
    finally:
        guard.close();row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),
            source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),
            final_fresh_hashes=0 if q is None else q.final_fresh_hashes,compiled_final_fresh_hashes=0 if binary is None else binary.final_fresh_hashes,
            elapsed_seconds=round(time.monotonic()-start,3),system_CPU_max=max((s['system_cpu_percent']for s in guard.samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in guard.samples),default=None))
        value,_=p.retention.retain(r.c.ROOT,'implementation/p09/evidence/private/p09-361-block-bookmark-authoring680-product004-forensic',row)
        pin=p.publish(OUTPUT,value)
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','cleanup','fresh_inputs','final_fresh_hashes','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','diagnostics','safe_error_variants','tests')}for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('QUALIFIED680_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
