"""Resource-aware read-only recovery. Immutable run IDs; no original/Native attempt replay."""
import argparse,json,math,re,subprocess,time
from types import SimpleNamespace as NS
import run_personal_info_catalog_mask_product as prior
r,layout=prior.r,prior.layout
DRIVER='tools/p09/run_personal_info_catalog_mask_product_recovery.py'
COMPLETED='implementation/p09/evidence/p09-361-personal-info-catalog-mask427.v1.json'


def memory_headroom(available,peak):
    for v in(available,peak):
        if type(v)not in(int,float)or not math.isfinite(v)or not 0<=v<=100:raise ValueError('CATALOG_PRODUCT_MEMORY_OBSERVATION_INVALID')
    # Workload-specific admission, not a lower global RAM ceiling. The original
    # global RAM/commit stop stays 95%, and observed allocations stay Job-bound.
    required=5+peak
    return dict(available_ram_percent=available,prior_completed_comparable_job_peak_percent=peak,
        original_global_ram_ceiling_percent=95,required_available_percent=required,admitted=available>required,
        prediction_not_memory_reservation=True,native_execution_authorized=False)


def admission_models():
    assert memory_headroom(12,6)['admitted']
    assert not memory_headroom(11,6)['admitted']
    assert not memory_headroom(6,6)['admitted']
    for value in(True,float('nan'),float('inf'),-1,101,'6'):
        try:memory_headroom(value,6)
        except ValueError:pass
        else:raise ValueError('CATALOG_PRODUCT_MEMORY_MODEL_FAILED')
    return dict(groups=4,errors=0,product_tests_executed=0)


def successful_exit(row):
    # A harness PASS is not final acceptance, even when cleanup succeeded.
    fresh=row.get('fresh_inputs');final=row.get('final_fresh_hashes')
    return (row.get('cleanup')is True and row.get('error_code')is None
        and row.get('error_type')is None and row.get('failed_final_fresh_check')is not True
        and type(fresh)is int and fresh>0 and type(final)is int and final==fresh
        and row.get('state','').startswith(('PASS_','DEFERRED_')))


def original_routing(text):
    wrapper="""    make_for_view(&compiled.candidate.compiler_view(),compiled.compiled(),compiled.receipt(),protection,context,catalog,transaction,now)
}
pub(super) fn make_for_view(v:&CompilationView<'_>,plan:&CompiledOperationPlan,receipt:&CompiledSearchReceipt,
    protection:&SourceProtectionObservation,context:&RouteContext,catalog:&CapabilityRouteCatalog,transaction:TransactionId,now:u64)
    ->Result<(Vec<RouteDecision>,ExecutionManifest,[u8;32]),SearchManifestError>{
"""
    r.c.require(text.count(wrapper)==1,'EXACT_SHARED_ROUTER_VIEW_EXTRACTION')
    return text.replace(wrapper,'').replace('protection.verify_binding(v.source.imported().source())?',
        'protection.verify_binding(compiled.candidate.compiler_view().source.imported().source())?').replace(
        '?.route_plan(plan,context,catalog)?','?.route_plan(compiled.compiled(),context,catalog)?').replace(
        '    let source=v.source.receipt();','    let v=compiled.candidate.compiler_view();let source=v.source.receipt();').replace(
        'transaction,artifact,receipt.source_package_sha256,source_size,plan,&routes',
        'transaction,artifact,compiled.receipt.source_package_sha256,source_size,compiled.compiled(),&routes')


def run_manifest(args):
    # Same bounded execution machinery/cache and output shape, a new stage rather
    # than a new historical-driver chain. Accepted45 never enter the filter set.
    c,a,shared=r.c,r.a,r.shared
    storage=args.stage=='storage'
    output=f'implementation/p09/evidence/p09-361-personal-info-catalog-mask-{"storage"if storage else"manifest"}{args.run}.v1.json'
    baseline='implementation/p09/evidence/p09-361-catalog-product-retained-final437.v1.json'
    routing='crates/product-cli/src/form_product_request/stored_operations/compiled_search/routing.rs'
    added=prior.COMPILER[:-3]+'/routing.rs'
    test='crates/product-cli/tests/support/personal_info_catalog_mask_routing.rs'
    dep='target/debug/deps/personal_info_mask_product-d9995c0aff1b1d2e.d'
    changed={DRIVER,routing,prior.COMPILER,prior.TEST}
    source_owner='crates/product-cli/src/form_stored_provider/actual_import.rs'
    parent_test=test;parent_routing=added
    if storage:
        baseline='implementation/p09/evidence/p09-361-personal-info-catalog-mask-manifest439.v1.json'
        added=parent_routing[:-3]+'/storage.rs'
        test='crates/product-cli/tests/support/personal_info_catalog_mask_storage.rs'
        changed={DRIVER,parent_test,parent_routing,source_owner,'implementation/p09/P09_COMPLETION_EXECUTION.md'}
    c.require(not(c.ROOT/output).exists(),'CATALOG_MANIFEST_IMMUTABLE_RESULT')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=artifact=None;final_attempted=False;started=time.monotonic()
    row=dict(state='FAILED_CATALOG_MASK_MANIFEST',steps=[],own_cpu_selection=selection,accepted_count_delta=0,
        P09_gate='OPEN',P10_started=False,original436_CPU_stop_preserved=True,accepted45_replayed=False,
        actual_DB_Hangul_COM_or_Native_started=False,official249_replayed=False,source_document_mutation=False,
        ingest_commit_or_publication=False,synthetic_routing_not_registry_or_execution_authority=True)
    if storage:row.update(ingest_commit_or_publication=True,only_in_memory_fixture_ingest_and_revision_CAS=True,
        operational_ingest_commit_or_publication=False,accepted_manifest14_replayed=False,
        current_catalog_and_route_recheck_at_final_mutation_boundary_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);base=layout.unpack(q.json(baseline))
        if storage:
            c.require(q.snapshots[baseline]['sha256']=='a96f0a05ed858c5cc6bce7c1af33fad5ff2ca7eaf1720c511ce641d001710f1d'
                and base['state']=='PASS_CATALOG_MASK_SHARED_MANIFEST_NEW13_LEGACY1_NOT_EXECUTION_OR_GATE'
                and base['fresh_inputs']==base['final_fresh_hashes']==862 and base['cleanup']is True
                and base['current_distinct_manifest_cases']==14,'EXACT_ACCEPTED_MANIFEST14_NO_REPLAY')
        else:
            c.require(q.snapshots[baseline]['sha256']=='2eff38200cfcd1f971d1787cd6b352b5e48229bb2942c955847c6f68a51f29a6'
                and base['state']=='PASS_RETAINED_CATALOG_PRODUCT42_AFFECTED3_FINAL_FRESH_NOT_NATIVE_QUEUE_OR_GATE'
                and base['fresh_inputs']==base['final_fresh_hashes']==857 and base['cleanup']is True
                and base['retained_product_cases_accepted']==45,'EXACT_ACCEPTED45_NO_REPLAY_BASELINE')
        old={p['path']:p for p in base['source_pins']}
        for name in sorted(set(old)|shared.source_inventory(guard.check)|{DRIVER,added,test}):
            if name==dep:continue # Cargo owns this generated artifact; source and historical evidence remain immutable.
            pin=q.pin(name)
            if name in old and name not in changed:c.require(pin==old[name],'UNCHANGED_PREVIOUS_PRODUCT_TEST_AND_GUARD_INPUTS')
        if storage:
            r.audit.inverse(q.text(parent_routing).replace('pub mod storage;\n',''),old[parent_routing],'ORIGINAL_ACCEPTED_MANIFEST_ROUTING_BODY_UNCHANGED')
            r.audit.inverse(q.text(parent_test).replace('mod storage{include!("personal_info_catalog_mask_storage.rs");}\n',''),old[parent_test],'ALL_PREVIOUS14_TEST_BODIES_UNCHANGED')
            helper="""    // Operation-local source borrowing for the storage bridge. No second copy,
    // retained reconstruction, caller artifact selector or service authority.
    pub(crate) fn with_verified_compiler_source<R,B,S,V,T>(&self,provider:&StoredFormProvider<'_,R,B,S,V>,now:u64,
        consume:impl FnOnce(&[u8],revision_service::ProjectId,revision_service::BranchId,RevisionHead)->T)
        ->Result<T,StoredActualFormImportError>
    where R:ArtifactMetadataRepository,B:EncryptedBlobStore,S:ArtifactScanner,V:RevisionRepository{
        let fresh=self.fresh_source(provider,now)?;self.check_compiler_head(provider)?;
        Ok(consume(&fresh.bytes,fresh.scope.project,fresh.scope.branch,fresh.head))
    }
"""
            text=q.text(source_owner);c.require(text.count(helper)==1,'ONE_SCOPED_SOURCE_BORROW_HELPER')
            r.audit.inverse(text.replace(helper,''),old[source_owner],'ORIGINAL_SOURCE_READ_AEAD_ACL_RECONSTRUCTION_AND_FINAL_HEAD_BODIES_UNCHANGED')
            docsync='implementation/p09/evidence/p09-361-catalog-product-plan-doc-sync441.v1.json'
            docs=layout.unpack(q.json(docsync));c.require(q.snapshots[docsync]['sha256']=='452c5c7e0c94bb5a7a01b262835275d0b618c57d3d650b010de80a4e97ab58c4'
                and docs['fresh_inputs']==docs['final_fresh_hashes']==16 and docs['cleanup']is True,'EXACT_DOCUMENT_ONLY_PLAN_UPDATE_AFTER439')
            plan='implementation/p09/P09_COMPLETION_EXECUTION.md';c.require(q.snapshots[plan]==next(p for p in docs['source_pins']if p['path']==plan),'CURRENT_PLAN_NOT_OLD_EXECUTION_INPUT')
        else:
            r.audit.inverse(original_routing(q.text(routing)),old[routing],'ORIGINAL_ROUTER_PROTECTION_TIME_BACKEND_MANIFEST_BODY_UNCHANGED')
            r.audit.inverse(q.text(prior.COMPILER).replace('pub mod routing;\n',''),old[prior.COMPILER],'ORIGINAL_CATALOG_COMPILER_BODY_UNCHANGED')
            r.audit.inverse(q.text(prior.TEST).replace('mod routing{include!("personal_info_catalog_mask_routing.rs");}\n',''),
                old[prior.TEST],'ORIGINAL_ACCEPTED42_TEST_BODIES_UNCHANGED')
        names=re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(test))
        cases={prior.PREFIX+('routing::storage::'if storage else'routing::')+name for name in names}
        c.require(len(names)==len(cases)==14 and '#[ignore]'not in q.text(test),'EXACT_NEW13_AND_SHARED_LEGACY_ROUTE1')
        if not storage:c.require('original_selected_mask_adapter_still_uses_same_shared_manifest_builder'in names,
            'ACTUAL_LEGACY_ADAPTER_REGRESSION_INCLUDED')
        all_cases=set(cases);retained=set()
        if storage and args.after_storage_compile442:
            failure='implementation/p09/evidence/p09-361-personal-info-catalog-mask-storage442.v1.json'
            failed=layout.unpack(q.json(failure))
            c.require(q.snapshots[failure]['sha256']=='dadf7d7f4d17b2b24850ffbc1cf5aa2798f38f006d664613bfba045166472b44'
                and failed['cleanup']is True and failed['error_code']=='SOURCE_NOTE_API_COMMAND_FAILED'
                and len(failed['steps'])==1 and failed['steps'][0]['exit_code']==101
                and failed['steps'][0]['tests']==[]and not failed['steps'][0]['bounded_output_observation']['observed_harness_started'],
                'EXACT442_COMPILE_FAILURE_ZERO_TEST_BODIES')
            frozen={p['path']:p for p in failed['source_pins']}
            for path,pin in frozen.items():
                if path not in(DRIVER,test):c.require(q.pin(path)==pin,'UNCHANGED442_PRODUCTION_AND_OTHER_TEST_INPUTS')
            text=q.text(test);typed='&mut |_:&operation_engine::RevisionCommitRequest|{called.set(true);'
            c.require(text.count(typed)==1,'ONE_TEST_CALLBACK_TYPE_ANNOTATION')
            r.audit.inverse(text.replace(typed,'&mut |_|{called.set(true);'),frozen[test],'ONLY_CALLBACK_LIFETIME_TYPE_INFERENCE_FIX_NO_TEST_REMOVAL')
            row['prior_compile442_preserved']=q.snapshots[failure]
        if args.only_failed_from438:
            failed_path='implementation/p09/evidence/p09-361-personal-info-catalog-mask-manifest438.v1.json'
            failed=layout.unpack(q.json(failed_path))
            c.require(q.snapshots[failed_path]['sha256']=='e755d8da0803b24ee5eb08d5755cf1b0b870394bd442c238fcc3806c524f7384'
                and failed['state']=='FAILED_CATALOG_MASK_MANIFEST' and failed['cleanup']is True
                and failed['error_code']=='SOURCE_NOTE_API_COMMAND_FAILED' and len(failed['steps'])==1,
                'EXACT438_TEST_FAILURE_NOT_RESOURCE_STOP')
            step=failed['steps'][0];pairs=step['tests']
            c.require(len(pairs)==14 and {n for n,_ in pairs}==all_cases and step['exit_code']==101
                and step['owned_job']['owned_tree_empty']is True and step['owned_job']['job_handle_closed']is True
                and step['owned_job']['last_job_accounting']['active_processes']==0,'EXACT438_BODIES_AND_CLEANUP')
            retained={n for n,status in pairs if status=='ok'};cases={n for n,status in pairs if status=='FAILED'}
            c.require(len(retained)==13 and cases=={prior.PREFIX+'routing::actual_document_protection_is_not_overridden_by_synthetic_unprotected_context'},
                'EXACT_ONE_CHANGED_PROTECTION_TEST_ONLY')
            archive='implementation/p09/source-archive/p361-catalog-manifest438/'
            frozen={p['path']:p for p in failed['source_pins']}
            for path,pin in frozen.items():
                if path in(DRIVER,test):
                    actual=q.pin(archive+('runner.py'if path==DRIVER else'routing-test.rs'))
                    c.require(actual['bytes']==pin['bytes']and actual['sha256']==pin['sha256'],'ORIGINAL438_DRIVER_AND_TEST_PRESERVED')
                else:c.require(q.pin(path)==pin,'ALL_UNCHANGED438_EXECUTION_AND_PRODUCT_INPUTS')
            before=q.text(archive+'routing-test.rs');after=q.text(test)
            marker='#[test]\nfn actual_document_protection_is_not_overridden_by_synthetic_unprotected_context'
            def remove_one(text):
                c.require(text.count(marker)==1,'ONE_PROTECTION_CASE')
                start=text.index(marker);end=text.index('\n#[test]',start+len(marker));return text[:start]+text[end:]
            c.require(remove_one(before)==remove_one(after),'ALL13_PASSED_BODIES_AND_FIXTURE_HELPERS_IDENTICAL')
            row.update(retained_manifest_cases_pending_final_fresh=13,retained_failed438_pin=q.snapshots[failed_path])
        # One new shared fixture is a real rustc input, not an omitted post-build dependency.
        fixture='crates/hwpx-package/tests/support/source_protection_fixture.rs';q.pin(fixture)
        completed=layout.unpack(q.json(COMPLETED));peak=max(s['owned_job']['last_job_accounting']['peak_job_private_percent']for s in completed['steps'])
        guard.check(force=True);row['memory_admission']=memory_headroom(guard.samples[-1]['available_ram_percent'],peak)
        if not row['memory_admission']['admitted']:
            row.update(state='DEFERRED_CATALOG_MANIFEST_PREDICTED_RAM95_HEADROOM',Cargo_started=False,product_cases_executed=0)
        else:
            previous_deps,dep_pin=prior.prior.dependencies(dep,guard)
            if storage:
                if not args.after_storage_compile442:c.require(dep_pin==base['actual_compiled_test_inputs'][0]['dep_info'],'EXACT_MANIFEST14_DEP_INFO_BEFORE_REBUILD')
            elif not args.only_failed_from438:c.require(dep_pin==old[dep],'EXACT_ACCEPTED45_DEP_INFO_BEFORE_REBUILD')
            row['previous_generated_dep_info']=dict(pin=dep_pin,role='rebuildable_Cargo_output_not_immutable_source')
            if storage:expected=set(base['actual_compiled_test_inputs'][0]['dependency_paths'])|{test}
            else:
                observed436=layout.unpack(q.json('implementation/p09/evidence/p09-361-personal-info-catalog-mask-product-recovery436.v1.json'))
                expected=set(observed436['actual_compiled_test_inputs'][0]['dependency_paths'])|{test,fixture}
            c.require(set(previous_deps)==(expected if storage and args.after_storage_compile442 else expected-{test}if storage else expected if args.only_failed_from438 else expected-{test,fixture}),
                'EXACT_BEFORE_BUILD_GENERATED_DEPENDENCIES')
            c.require(expected<=set(q.snapshots),'COMPLETE_DECLARED_MANIFEST_TEST_INPUTS')
            scratch=c.ROOT/f'target/p09-catalog-mask-manifest-scratch-{args.run}'
            c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()
                and not scratch.parent.is_junction(),'MANIFEST_UNIQUE_COMPILER_TEMP')
            scratch.mkdir();env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch))
            command=[r.harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli','--test','personal_info_mask_product',
                '--features','p09-installed-format-fixture','--message-format=short','--',*sorted(cases),'--test-threads=1']
            row['Cargo_started']=True;print(json.dumps(dict(state='CATALOG_MANIFEST_PREFLIGHT',inputs=len(q.snapshots),cases=len(cases),retained=len(retained),accepted45_replays=0)),flush=True)
            label='catalog_storage_bridge_and_actual_readback14'if storage else'catalog_manifest_failed_protection1_retained13'if args.only_failed_from438 else'catalog_shared_manifest_new13_legacy1'
            r.harness.run_one(label,command,cases,guard,env,row,observe_capture=r.snapshot)
            r.tools.good_step(row['steps'][-1],cases);c.require(not row['steps'][-1]['diagnostics'],'MANIFEST14_NO_WARNINGS')
            # Rebuilding legitimately changes dep-info. Bind its actual bytes in a
            # separate reader; never leave an old artifact pin in the source close.
            row['actual_compiled_test_inputs']=prior.prior.compiled_inputs(prior.prior.CONFIGS[1],expected,guard)
            artifact=a.AcceptanceReader(c.ROOT,guard.check)
            for value in row['actual_compiled_test_inputs']:
                c.require(artifact.pin(value['dep_info']['path'])==value['dep_info'],'ACTUAL_DEP_INFO_BOUND_AFTER_REBUILD')
            c.require(not any(scratch.iterdir()),'MANIFEST_COMPILER_TEMP_EMPTY')
            row.update(state='OBSERVED_CATALOG_MASK_MANIFEST14_PENDING_FINAL_FRESH',product_cases_executed=len(cases))
        final_attempted=True
        if artifact is not None:artifact.finish();row['compiled_artifact_final_fresh_hashes']=artifact.final_fresh_hashes
        q.finish();guard.check(force=True)
        if row['state']=='OBSERVED_CATALOG_MASK_MANIFEST14_PENDING_FINAL_FRESH':
            if storage:row.update(state='PASS_CATALOG_STORAGE_BRIDGE_REAL_HWPX_READBACK14_NOT_TRUSTED_ROUTE_SQL_NATIVE_OR_GATE',current_distinct_storage_cases=14)
            else:row.update(state='PASS_CATALOG_MASK_SHARED_MANIFEST_NEW13_LEGACY1_NOT_EXECUTION_OR_GATE',
                current_distinct_manifest_cases=14,retained_manifest_cases_accepted=len(retained),newly_executed_manifest_cases=len(cases))
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        code=error.args[0]if error.args else None
        row.update(state='FAILED_CATALOG_MASK_MANIFEST',error_type=type(error).__name__,
            error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'CATALOG_MANIFEST_FAILURE_NO_RAW_VALUES')
        if final_attempted:row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples
        row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,output,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','memory_admission','product_cases_executed',
            'fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('exit_code','diagnostics','cleanup','panic_locations')},'cases':len(s.get('tests',[])),
                'failed_cases':[n for n,status in s.get('tests',[])if status!='ok'],
                'compiler_locations':s.get('bounded_output_observation',{}).get('short_error_locations',[]),
                'compiler_codes':s.get('bounded_output_observation',{}).get('rust_error_codes',[])}for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if successful_exit(row)else 2


def run_commit_guard(args):
    # Current storage owner + original shared CAS/job. Never replay the earlier
    # 45/14/14 or official queue just to build a new receipt ancestry.
    c,a,shared=r.c,r.a,r.shared
    output=f'implementation/p09/evidence/p09-361-catalog-storage-commit-guard{args.run}.v1.json'
    c.require(not(c.ROOT/output).exists(),'CATALOG_COMMIT_GUARD_IMMUTABLE')
    root='crates/product-cli/'
    storage=root+'src/form_product_request/stored_operations/compiled_search/catalog_mask/routing/storage.rs'
    factory=storage[:-3]+'/guard.rs'
    catalog_parent=root+'tests/support/personal_info_catalog_mask_storage.rs'
    catalog_test=root+'tests/support/personal_info_catalog_mask_commit_guard.rs'
    job_parent=root+'tests/support/stored_job_coordinator.rs';job_test=root+'tests/support/stored_job_commit_guard.rs'
    cas=root+'src/stored_revision_commit.rs';job=root+'src/stored_revision_commit/job.rs'
    plan='implementation/p09/P09_COMPLETION_EXECUTION.md'
    changed={DRIVER,storage,catalog_parent,job_parent,cas,job,plan}
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=artifact=None;final_attempted=False;started=time.monotonic()
    row=dict(state='FAILED_CATALOG_STORAGE_COMMIT_GUARD',steps=[],own_cpu_selection=selection,accepted_count_delta=0,
        P09_gate='OPEN',P10_started=False,official249_replayed=False,Native_or_Hangul_COM_started=False,
        prior45_manifest14_storage14_replayed=False,affected_legacy_cases_only=True,
        fixture_ingest_and_revision_CAS=True,actual_SQL_or_trusted_product_route=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        basepath='implementation/p09/evidence/p09-361-personal-info-catalog-mask-storage444.v1.json'
        base=layout.unpack(q.json(basepath))
        c.require(q.snapshots[basepath]['sha256']=='aa47756345e45d63bec3685f9d91d27dd102472b1660220acb8dbeed9c4e54a8'
            and base['cleanup']is True and base['fresh_inputs']==base['final_fresh_hashes']==867
            and base['current_distinct_storage_cases']==14,'EXACT_STORAGE14_ACCEPTED_BASELINE')
        old={p['path']:p for p in base['source_pins']}
        docpath='implementation/p09/evidence/p09-361-catalog-storage-doc-sync445.v1.json'
        docs=layout.unpack(q.json(docpath));c.require(q.snapshots[docpath]['sha256']=='2317b3592170407cefb4aebfa1707f5c098c3e9b87942e5a9e511c7c94aa71ee'
            and docs['cleanup']is True and docs['fresh_inputs']==docs['final_fresh_hashes']==21,'EXACT_DOCUMENT_ONLY_UPDATE445')
        catalog_deps,cat_dep=prior.prior.dependencies('target/debug/deps/personal_info_mask_product-d9995c0aff1b1d2e.d',guard)
        c.require(cat_dep==base['actual_compiled_test_inputs'][0]['dep_info'],'EXACT444_GENERATED_DEPENDENCIES')
        job_deps,job_dep=prior.prior.dependencies('target/debug/deps/stored_revision_commit-962ed23df77566c2.d',guard)
        configs=[dict(test='personal_info_mask_product',source=catalog_test,prefix=prior.PREFIX+'routing::storage::guard::',
            wanted=set(catalog_deps)|{catalog_test},legacy={prior.PREFIX+'routing::storage::'+n for n in(
                'whole_encrypted_artifact_ingest_and_revision_cas_use_actual_hwpx_validator','scanner_unverified_output_prevents_actual_revision_commit')}),
            dict(test='stored_revision_commit',source=job_test,prefix='job_v1::guard::',wanted=set(job_deps)|{job_test},legacy={'job_v1::'+n for n in(
                'actual_pipeline_claims_leases_validates_registers_commits_and_completes_in_order',
                'replay_and_unknown_claim_never_lease_or_create_workspace',
                'cas_ack_loss_retains_original_receipts_and_marks_unknown_without_completing_or_reexecuting')})]
        generated={cat_dep['path'],job_dep['path']}
        names=set(old)|shared.source_inventory(guard.check)|{DRIVER,factory,catalog_test,job_test,job_parent}
        names.update(set.union(*(config['wanted']for config in configs)))
        for path in sorted(names-generated):
            pin=q.pin(path)
            if path in old and path not in changed:c.require(pin==old[path],'UNCHANGED_PREVIOUS_PRODUCT_INPUTS')
        c.require(q.pin(plan)==next(p for p in docs['source_pins']if p['path']==plan),'PLAN_DOCUMENT_UPDATE_NOT_EXECUTION_DRIFT')
        for path,addition in[(storage,'pub mod guard;\n'),(catalog_parent,'mod guard{include!("personal_info_catalog_mask_commit_guard.rs");}\n'),
                              (job_parent,'mod guard{include!("stored_job_commit_guard.rs");}\n')]:
            text=q.text(path);c.require(text.count(addition)==1,'ONE_ADDITIVE_CURRENT_GUARD_MODULE')
            if path in old:r.audit.inverse(text.replace(addition,''),old[path],'ALL_PRIOR_STORAGE_AND_COORDINATOR_TEST_BODIES_UNCHANGED')
        # Shared primitive changes are additive restriction points; compare every
        # original byte after removing ONLY the declared insertions.
        text=q.text(cas)
        start=text.index('/// Additional current-state restriction,');end=text.index('/// Values retained by the authenticated server',start)
        text=text[:start]+text[end:]
        text=text.replace('    #[error("stored commit additional current-state guard rejected")]\n    CurrentGuard,\n','')
        text=text.replace("    precommit_guard:Option<Box<dyn StoredPrecommitGuard+'a>>,\n",'').replace('registration_response: None,precommit_guard:None,','registration_response: None,')
        start=text.index('    /// Adds a restriction once,');end=text.index('    #[must_use]',start);text=text[:start]+text[end:]
        text=text.replace('        self.check_precommit_guard()?;\n','')
        r.audit.inverse(text,old[cas],'ORIGINAL_CAS_SOURCE_INGEST_INTENT_REGISTER_COMMIT_AND_UNKNOWN_BODIES_UNCHANGED')
        text=q.text(job).replace(",\n    precommit_guard:Option<Box<dyn StoredPrecommitGuard+'a>>}",'}').replace('limits,precommit_guard:None})','limits})')
        start=text.index('    /// # Errors\n    /// Adds a server current-state restriction');end=text.index('    #[must_use]',start);text=text[:start]+text[end:]
        text=text.replace('pub fn run_once<R,B,S,V,F,Q>(mut self,','pub fn run_once<R,B,S,V,F,Q>(self,')
        for begin,end in [('        if let Some(guard)=self.precommit_guard.as_mut(){','        report.stage=StoredJobRunStage::Claim;'),
                          ('        if let Some(guard)=self.precommit_guard.take(){','        let mut barrier_error=None;')]:
            start=text.index(begin);stop=text.index(end,start);text=text[:start]+text[stop:]
        r.audit.inverse(text,old[job],'ORIGINAL_JOB_CLAIM_LEASE_BARRIERS_REPLAY_COMPLETION_AND_UNKNOWN_BODIES_UNCHANGED')
        for config,count in zip(configs,(10,5),strict=True):
            found=re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(config['source']))
            c.require(len(found)==len(set(found))==count and '#[ignore]'not in q.text(config['source']),'EXACT_DIRECT_GUARD_CASES_NO_SKIPS')
            config['cases']={config['prefix']+n for n in found}|config['legacy']
            c.require(config['wanted']<=set(q.snapshots),'COMPLETE_ACTUAL_TEST_INPUT_DECLARATION')
        completed=layout.unpack(q.json(COMPLETED));peak=max(s['owned_job']['last_job_accounting']['peak_job_private_percent']for s in completed['steps'])
        guard.check(force=True);row['memory_admission']=memory_headroom(guard.samples[-1]['available_ram_percent'],peak)
        c.require(row['memory_admission']['admitted'],'PREDICTED_WORKLOAD_WOULD_EXCEED_ORIGINAL_RAM95')
        scratch=c.ROOT/f'target/p09-catalog-commit-guard-scratch-{args.run}';c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'UNIQUE_COMPILER_TEMP')
        scratch.mkdir();env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch));row['actual_compiled_test_inputs']=[]
        artifact=a.AcceptanceReader(c.ROOT,guard.check)
        print(json.dumps(dict(state='CATALOG_COMMIT_GUARD_PREFLIGHT',inputs=len(q.snapshots),new_cases=15,affected_legacy_cases=5)),flush=True)
        for config in configs:
            command=[r.harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli','--test',config['test'],
                '--features','p09-installed-format-fixture','--message-format=short','--',*sorted(config['cases']),'--test-threads=1']
            r.harness.run_one('current_commit_guard_'+config['test'],command,config['cases'],guard,env,row,observe_capture=r.snapshot)
            r.tools.good_step(row['steps'][-1],config['cases']);c.require(not row['steps'][-1]['diagnostics'],'CURRENT_GUARD_NO_WARNINGS')
            observed=prior.prior.compiled_inputs(config,config['wanted'],guard);row['actual_compiled_test_inputs'].extend(observed)
            for value in observed:c.require(artifact.pin(value['dep_info']['path'])==value['dep_info'],'ACTUAL_DEP_INFO_BOUND')
        c.require(not any(scratch.iterdir()),'COMPILER_TEMP_EMPTY')
        row['product_cases_executed']=sum(len(config['cases'])for config in configs)
        final_attempted=True;artifact.finish();row['compiled_artifact_final_fresh_hashes']=artifact.final_fresh_hashes;q.finish();guard.check(force=True)
        row.update(state='PASS_CATALOG_CURRENT_COMMIT_GUARD15_AFFECTED5_NOT_SQL_TRUSTED_ROUTE_NATIVE_OR_GATE',new_guard_cases=15,affected_legacy_cases=5)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        code=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'CATALOG_COMMIT_GUARD_FAILURE_NO_RAW_VALUES')
        if final_attempted:row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples
        row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,output,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','product_cases_executed','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('exit_code','diagnostics','cleanup','panic_locations')},'cases':len(s.get('tests',[])),
                'failed_cases':[n for n,status in s.get('tests',[])if status!='ok'],
                'compiler_locations':s.get('bounded_output_observation',{}).get('short_error_locations',[]),
                'compiler_codes':s.get('bounded_output_observation',{}).get('rust_error_codes',[])}for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if successful_exit(row)else 2


def run_sql_storage(args):
    import os,sys,posixpath
    from pathlib import Path
    identity=args.stage=='identity-storage'
    if identity:import native_postgres_catalog_identity_storage as worker
    else:import native_postgres_catalog_storage as worker
    import run_native_postgres_runtime_qualification as postgres_runner
    c,a,shared=r.c,r.a,r.shared
    output=f'implementation/p09/evidence/p09-361-catalog-{"request-identity"if identity else"actual-sql-storage"}{args.run}.v1.json'
    c.require(not(c.ROOT/output).exists()and not worker.OWNED.exists()and not(c.ROOT/worker.OBSERVATION).exists(),'CATALOG_SQL_IMMUTABLE_RUN_AND_FRESH_OWNER')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=artifact=image=None;observation=None;final_attempted=False;started=time.monotonic()
    row=dict(state='FAILED_CATALOG_ACTUAL_SQL_STORAGE',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        official249_replayed=False,previous_test_bodies_replayed=False,Native_or_Hangul_COM_started=False,operational_database_accessed=False,
        fixture_route_and_scanner_not_trusted_product=True,full_manifest_reconciliation_qualified=False,parent_retained_ephemeral_fixture_keys=True)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        basepath='implementation/p09/evidence/p09-361-catalog-actual-sql-storage448.v1.json'if identity else'implementation/p09/evidence/p09-361-catalog-storage-commit-guard446.v1.json'
        base=layout.unpack(q.json(basepath))
        if identity:c.require(q.snapshots[basepath]['sha256']=='596497cafc72ca31f6c2fbba78e8cd3035cf76e5c8fd428a14a8f334202b9ab5'
            and base['cleanup']is True and base['fresh_inputs']==base['final_fresh_hashes']==919 and base['actual_owned_SQL23_and_AEAD']is True,'EXACT448_REAL_SQL_BASELINE_NO_REPLAY')
        else:c.require(q.snapshots[basepath]['sha256']=='336712a2733a0659de4c45d8a2ef4825058dfda55c610a18a1afba40e0b2d22a'
                and base['cleanup']is True and base['fresh_inputs']==base['final_fresh_hashes']==879 and base['new_guard_cases']==15 and base['affected_legacy_cases']==5,
                'EXACT_CURRENT_COMMIT_GUARD20_ACCEPTED_NO_REPLAY')
        old={p['path']:p for p in base['source_pins']}
        oldsqlpath='implementation/p09/evidence/p09-361-registered-recovery-postgres298.v1.json';oldsql=r.closure.compact.unpack(q.json(oldsqlpath))
        c.require(q.snapshots[oldsqlpath]['sha256']=='5cb52bcd3daa26f9f3de0789ceb7ac28e298f56a29dae6d639eabc775ca10386'and oldsql['cleanup']is True,'CURRENT_REGISTERED_SQL_CAMPAIGN_SOURCE_NOT_REEXECUTION')
        sqlpins={p['path']:p for p in oldsql['source_pins']}
        common='crates/product-cli/examples/sql23_storage.rs';setup=common[:-3]+'/setup.rs';catalog=common[:-3]+'/catalog.rs'
        probe='crates/product-cli/examples/sql23_catalog_identity_storage.rs'if identity else'crates/product-cli/examples/sql23_catalog_storage.rs'
        storage='crates/product-cli/src/form_product_request/stored_operations/compiled_search/catalog_mask/routing/storage.rs'
        product='crates/product-cli/src/form_product_request/stored_literal_replacement/personal_info/catalog.rs'
        source='crates/product-cli/src/form_stored_provider/actual_import/source_search.rs'
        job='crates/product-cli/src/stored_revision_commit/job.rs'
        test='crates/product-cli/tests/support/personal_info_catalog_mask_job_identity.rs'
        parent_test='crates/product-cli/tests/support/personal_info_catalog_mask_storage.rs'
        changed={DRIVER,common,catalog,source,product,job,storage,parent_test,'tools/p09/native_postgres_catalog_storage.py','implementation/p09/P09_COMPLETION_EXECUTION.md'}if identity else{DRIVER}
        names=set(old)|shared.source_inventory(guard.check)|{DRIVER,common,setup,catalog,probe,common[:-3]+'/pipeline.rs',
            'crates/product-cli/tests/support/stored_commit_manifest.rs','tools/p09/fixtures/postgres_revision_adapter.sql',
            'tools/p09/fixtures/sql23_service_roles.sql','tools/p09/fixtures/native_postgres_hba.conf',('target/p09-native-postgres-18.6-5-278/runtime-manifest.json'),
            'crates/hwpx-package/tests/support/search_definition_fixture.rs','crates/hwpx-package/tests/support/document_import_field_fixture.rs',
            'crates/hwpx-package/tests/support/document_import_catalog_fixture.rs','crates/hwpx-package/src/hancom_2020_minimal_header.xml'}
        if identity:
            paths,dep_pin=prior.prior.dependencies('target/debug/deps/personal_info_mask_product-d9995c0aff1b1d2e.d',guard)
            product_inputs=set(paths)|{test};names.update(product_inputs)
            names.update({test,'tools/p09/native_postgres_catalog_identity_storage.py'})
            names.update({'crates/product-cli/tests/support/pinned_p02_registry_fixture.rs','implementation/p04/trust/p04-direct-route-attestation.json','implementation/p04/trust/p04-direct-route-attestation.sig'})
        names.update('migrations/postgres/'+p.name for p in(c.ROOT/'migrations/postgres').glob('*.up.sql')if re.fullmatch(r'00(?:0[1-9]|1[0-9]|2[0-3])_[a-z0-9_]+\.up\.sql',p.name))
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':names.add(path.relative_to(c.ROOT).as_posix())
        for path in sorted(names):
            if path.startswith('target/debug/'):continue
            pin=q.pin(path)
            if path in old and path not in changed:c.require(pin==old[path],'UNCHANGED_ACCEPTED_COMMIT_GUARD_PRODUCTION_AND_TEST_INPUTS')
        if identity:
            sync='implementation/p09/evidence/p09-361-catalog-guard-sql-doc-sync449.v1.json';docs=layout.unpack(q.json(sync))
            c.require(q.snapshots[sync]['sha256']=='60090f49925e7455468a8ac3d4f3a1cc2849e401755b83a129d271a49398e6dd'and docs['cleanup']is True,'EXACT_DOCUMENT_ONLY_UPDATE449')
            plan='implementation/p09/P09_COMPLETION_EXECUTION.md';c.require(q.pin(plan)==next(p for p in docs['source_pins']if p['path']==plan),'CURRENT_PLAN_ROLE_NOT_EXECUTED_SOURCE_DRIFT')
            archive='implementation/p09/source-archive/p361-catalog-identity450/'
            for path,leaf in [(common,'sql-main.rs'),(catalog,'catalog.rs'),('tools/p09/native_postgres_catalog_storage.py','native-catalog.py'),(DRIVER,'runner.py')]:
                pin=q.pin(archive+leaf);c.require((pin['bytes'],pin['sha256'])==(old[path]['bytes'],old[path]['sha256']),'EXACT448_SHARED_SQL_SOURCES_PRESERVED')
            # New source/product helpers retain the original body outside one insertion.
            for path,begin,end in [(source,'    pub(crate) fn source_search_job_identity','    pub(crate) fn source_search_product_scope'),
                (product,'    pub(crate) fn server_job_identity','    #[must_use]pub const fn receipt')]:
                text=q.text(path);start=text.index(begin);stop=text.index(end,start);r.audit.inverse(text[:start]+text[stop:],old[path],'ORIGINAL_PROVIDER_AND_STRICT_REQUEST_BODIES_UNCHANGED')
            r.audit.inverse(q.text(job).replace('pub mod identity;\n',''),old[job],'ORIGINAL_JOB_EXECUTION_AND_GUARDS_UNCHANGED')
            r.audit.inverse(q.text(parent_test).replace('mod identity{include!("personal_info_catalog_mask_job_identity.rs");}\n',''),old[parent_test],'ALL_PREVIOUS_STORAGE_AND_GUARD_TESTS_UNCHANGED')
            if args.after_identity450:
                failure_path='implementation/p09/evidence/p09-361-catalog-request-identity450.v1.json';failed=layout.unpack(q.json(failure_path))
                c.require(q.snapshots[failure_path]['sha256']=='a023835133624feedd97c914bb065cc06cf16df258870a06b46dd63df418d125'
                    and failed['error_code']=='LIBRARY_UNIT_ALL_CURRENT_INPUTS_DECLARED'and failed['cleanup']is True and len(failed['steps'])==3
                    and all(s['exit_code']==0 and s['cleanup']is True and not s['diagnostics']for s in failed['steps'])and failed.get('database_stage')is None,
                    'EXACT450_BODY15_AND_COMPILE_PASS_NO_DATABASE_NOT_RESOURCE_STOP')
                frozen={p['path']:p for p in failed['source_pins']}
                for path,pin in frozen.items():
                    if path==DRIVER:
                        original=q.pin(archive+'failed-runner.py');c.require((original['bytes'],original['sha256'])==(pin['bytes'],pin['sha256']),'EXACT450_FAILED_RUNNER_PRESERVED')
                    else:c.require(q.pin(path)==pin,'ALL450_PRODUCT_UNIT_AND_OWNED_EXECUTION_INPUTS_UNCHANGED')
                row.update(retained_product9_pending_final_fresh=True,original_unit6_body_pass_not_accepted_due_to_missing_compile_inputs=True)
            # The old SQL mode remains an archived baseline; this stage exercises
            # the new closed identity mode in a NEW fixed owner, never the old DB.
        else:
            pass
        if not identity:
            original_common=q.text(common)
        else:
            original_common=q.text('implementation/p09/source-archive/p361-catalog-identity450/sql-main.rs')
        text=original_common.replace('#[path="sql23_storage/catalog.rs"] mod catalog;\n','')
        text=text.replace('const CATALOG_ROOT:&str="D:/devdata/hwpx-agent-p09-pg18-catalog-447";\nstatic CATALOG_MODE:std::sync::atomic::AtomicBool=std::sync::atomic::AtomicBool::new(false);\n','')
        text=text.replace('PathBuf::from(if CATALOG_MODE.load(std::sync::atomic::Ordering::Relaxed){CATALOG_ROOT}else{ROOT})','PathBuf::from(ROOT)')
        text=text.replace('fn main(){let mode=env::args().nth(1).unwrap_or_default();finish(run(&mode),&mode)}\npub fn catalog_main(){CATALOG_MODE.store(true,std::sync::atomic::Ordering::Relaxed);let mode=env::args().nth(1).unwrap_or_default();finish(catalog::run(&mode),&mode)}\nfn finish(result:Result<Value>,mode:&str){',
            'fn main(){let mode=env::args().nth(1).unwrap_or_default();let result=run(&mode);')
        r.audit.inverse(text,sqlpins[common],'ORIGINAL_SQL_ROOT_AND_LEGACY_SCANNER_CRYPTO_MODE_BODIES_PRESERVED')
        text=q.text(setup).replace('pub fn seed()->Result<Value>{seed_source(SOURCE)}\npub fn seed_source(source:&[u8])->Result<Value>{','pub fn seed()->Result<Value>{')
        text=text.replace('ingest(&a,source,ArtifactKind::Result','ingest(&a,SOURCE,ArtifactKind::Result').replace('original.artifact_id,11)?==source,','original.artifact_id,11)?==SOURCE,')
        r.audit.inverse(text,sqlpins[setup],'ORIGINAL_SQL_BOOTSTRAP_LEASE_CAS_COMPLETE_BODY_PRESERVED')
        c.require(q.pin(common[:-3]+'/pipeline.rs')==sqlpins[common[:-3]+'/pipeline.rs'],'ORIGINAL_SQL_STORAGE_AND_RECOVERY_PIPELINE_UNCHANGED')
        # Existing native worker verifies every selected runtime file before and
        # after the campaign. Parent guard accounts the entire single owned tree.
        runtime_manifest=q.json('target/p09-native-postgres-18.6-5-278/runtime-manifest.json');row['runtime_file_count']=len(runtime_manifest['runtime_pins'])
        image=a.AcceptanceReader(prior.CONFIG.parent,guard.check);installed=image.pin(prior.CONFIG.name)
        c.require((installed['bytes'],installed['sha256'])==(17020,'fe3721e68a749c3d1ec843207d475249fa75e68f1de569fe45468c05b1022434'),'EXACT_CURRENT_INSTALLED_CATALOG_NOT_PRIVATE_CONFIG')
        completed=layout.unpack(q.json(COMPLETED));peak=max(s['owned_job']['last_job_accounting']['peak_job_private_percent']for s in completed['steps'])
        guard.check(force=True);row['memory_admission']=memory_headroom(guard.samples[-1]['available_ram_percent'],peak)
        c.require(row['memory_admission']['admitted'],'PREDICTED_WORKLOAD_WOULD_EXCEED_ORIGINAL_RAM95')
        scratch=c.ROOT/f'target/p09-catalog-sql-scratch-{args.run}';c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'CATALOG_SQL_UNIQUE_COMPILER_TEMP')
        scratch.mkdir();env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch),PYTHONPATH=str(c.ROOT/'tools/p09'),PYTHONDONTWRITEBYTECODE='1')
        print(json.dumps(dict(state='CATALOG_SQL_PREFLIGHT',inputs=len(q.snapshots),old_tests_replayed=0,existing_database_accessed=False)),flush=True)
        if identity:
            names=re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(test));c.require(len(names)==len(set(names))==6,'EXACT_SIX_NEW_PRODUCT_IDENTITY_CASES')
            cases={prior.PREFIX+'routing::storage::identity::'+n for n in names}|{prior.PREFIX+'routing::storage::'+n for n in(
                'prepared_job_binds_original_source_head_output_canonical_request_and_routes','caller_request_route_digest_and_old_revision_cannot_rebind_job_preparation','storage_consumer_cannot_rebind_write_scope_or_five_provider_dimensions')}
            identity_source=job[:-3]+'/identity.rs';found=re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(identity_source));c.require(len(found)==6,'EXACT_SIX_COMMON_IDENTITY_CASES')
            unit={'stored_revision_commit::job::identity::tests::'+n for n in found}
            for label,target,selected in [('identity_unit6',['--lib'],unit),('identity_product6_affected3',['--test','personal_info_mask_product'],cases)]:
                if args.after_identity450 and target[0]=='--test':
                    c.require({n for n,status in failed['steps'][1]['tests']if status=='ok'}==cases and len(failed['steps'][1]['tests'])==9,'EXACT_RETAINED_PRODUCT9_BODIES_NO_REPLAY')
                    previous=failed['actual_compiled_test_inputs'];c.require(any(set(p['dependency_paths'])==product_inputs for p in previous),'RETAINED_PRODUCT9_ACTUAL_COMPILED_INPUTS_COMPLETE')
                    continue
                command=[r.harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli',*target,'--features','p09-installed-format-fixture','--message-format=short','--',*sorted(selected),'--test-threads=1']
                r.harness.run_one(label,command,selected,guard,env,row,observe_capture=r.snapshot);r.tools.good_step(row['steps'][-1],selected)
                c.require(not row['steps'][-1]['diagnostics'],'IDENTITY_CASES_NO_WARNINGS')
            row.update(new_identity_cases=12,affected_legacy_cases=3)
        r.harness.run_one('compile_original_catalog_sql_storage_bridge',[r.harness.CARGO,'build','--offline','--locked','-j','1','-p','hwpx-agent-cli',
            '--example','sql23_catalog_identity_storage'if identity else'sql23_catalog_storage','--features','p09-installed-format-fixture','--message-format=short'],set(),guard,env,row,observe_capture=r.snapshot)
        c.require(not row['steps'][-1]['diagnostics'],'CATALOG_SQL_BUILD_NO_WARNINGS')
        artifact=a.AcceptanceReader(c.ROOT,guard.check);name='sql23_catalog_identity_storage'if identity else'sql23_catalog_storage'
        exe=f'target/debug/examples/{name}.exe';env['P09_STORAGE_PROBE_SHA256']=artifact.pin(exe)['sha256']
        dep=f'target/debug/examples/{name}.d';line=artifact.text(dep).splitlines()[0];c.require(': 'in line,'CATALOG_SQL_DEP_INFO_TARGET')
        paths=[]
        for item in line.split(': ',1)[1].split():
            item=item.replace('\\','/');path=Path(item)
            if path.is_absolute():c.require(path.is_relative_to(c.ROOT),'CATALOG_SQL_DEP_INFO_REPO_SCOPE');item=path.relative_to(c.ROOT).as_posix()
            item=posixpath.normpath(item);c.require(item.startswith(('crates/','migrations/','tools/p09/fixtures/'))and '..'not in item.split('/'),'CATALOG_SQL_DEP_INFO_INPUT_SCOPE');paths.append(item)
        c.require(0<len(paths)<=128 and set(paths)<=set(q.snapshots),'CATALOG_SQL_ALL_ACTUAL_RUST_INCLUDE_INPUTS_DECLARED')
        row['actual_compiled_dependency_paths']=sorted(set(paths))
        if identity:
            row['actual_compiled_test_inputs']=prior.prior.compiled_inputs(dict(test='personal_info_mask_product'),product_inputs,guard)
            for item in row['actual_compiled_test_inputs']:c.require(artifact.pin(item['dep_info']['path'])==item['dep_info'],'ACTUAL_PRODUCT_TEST_DEP_INFO_FINAL')
            library=[]
            for item in(c.ROOT/'target/debug/deps').glob('hwpx_agent_cli-*.d'):
                data=item.read_text(encoding='utf-8');guard.check()
                if 'src/stored_revision_commit/job/identity.rs'in data.replace('\\','/')and '.exe:'in data:
                    first=data.splitlines()[0].split(': ',1)[1];deps={posixpath.normpath(p.replace('\\','/'))for p in first.split()}
                    c.require(deps<=set(q.snapshots),'LIBRARY_UNIT_ALL_CURRENT_INPUTS_DECLARED');library.append(artifact.pin(item.relative_to(c.ROOT).as_posix()))
            c.require(bool(library),'ACTUAL_CURRENT_IDENTITY_LIBRARY_UNIT_DEP_INFO');row['actual_library_unit_dep_info']=library
        worker_path='tools/p09/native_postgres_catalog_identity_storage.py'if identity else'tools/p09/native_postgres_catalog_storage.py'
        try:result=postgres_runner.run_owned('one_actual_catalog_SQL23_AEAD_guarded_job_and_restart',[sys.executable,str(c.ROOT/worker_path),'--owned-generated-hwpx-catalog-campaign'],guard,env,row,300)
        finally:
            if(c.ROOT/worker.OBSERVATION).is_file():observation=q.json(worker.OBSERVATION)
        c.require(result['observation_sha256']==q.snapshots[worker.OBSERVATION]['sha256']and result['observation_bytes']==q.snapshots[worker.OBSERVATION]['bytes'],'EXACT_SQL_OBSERVATION_BYTES')
        wanted='PASS_BOUND_CATALOG_REQUEST_KEY_SQL23_REPLAY_REJECTION_AEAD_RESTART_NOT_TRUSTED_PRODUCT_OR_GATE'if identity else'PASS_GENERATED_CATALOG_HWPX_SQL23_GUARDED_JOB_AEAD_HEAD_RESTART_NOT_TRUSTED_PRODUCT_OR_GATE'
        c.require(observation['state']==wanted
            and observation['all_owned_postmasters_normal_stop']is True and len(observation['probes'])==5
            and len(observation['snapshots'])==2 and observation['snapshots'][0]==observation['snapshots'][1]
            and len(observation['blob_snapshots'][0])==6 and observation['blob_snapshots'][0]==observation['blob_snapshots'][1],
            'ACTUAL_CATALOG_HWPX_SQL_GUARDS_AEAD_WRONG_KEY_RESTART_NO_REEXECUTION')
        c.require(not any(scratch.iterdir()),'CATALOG_SQL_COMPILER_TEMP_EMPTY')
        final_attempted=True;artifact.finish();row['compiled_artifact_final_fresh_hashes']=artifact.final_fresh_hashes
        image.finish();row['installed_config_final_fresh_hashes']=image.final_fresh_hashes;q.finish();guard.check(force=True)
        row.update(state='PASS_CATALOG_GENERATED_HWPX_SQL23_GUARDED_JOB_CAS_AEAD_RESTART_NOT_TRUSTED_PRODUCT_OR_GATE',actual_owned_SQL23_and_AEAD=True,
            actual_staged_hwpx_validator=True,actual_current_guard_checks=3,actual_wrong_key_denial=True,actual_restart_readback=True,
            actual_SQL_counts=observation['snapshots'][0],generated_hwpx_not_actual_Hancom_save_reopen=True)
        if identity:row.update(state='PASS_CATALOG_REQUEST_KEY_IDENTITY12_AFFECTED3_REAL_SQL_REPLAY_REJECTION_NOT_TRUSTED_PRODUCT_OR_GATE',
            actual_bound_request_key_and_retained_claim_observation=True,cold_public_request_lookup_qualified=False,
            retained_product9_accepted=args.after_identity450,product9_replayed=False if args.after_identity450 else None)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        code=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'CATALOG_SQL_FAILURE_NO_RAW_VALUES')
        if final_attempted:row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples
        if observation is not None:row.update(database_stage=observation['stage'],last_probe=None if not observation['probes']else observation['probes'][-1],database_error=observation.get('error_code'))
        row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),installed_config_pins=[]if image is None else list(image.snapshots.values()),
            resource_samples=samples,fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,output,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent','database_stage','last_probe','database_error')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','cleanup','panic_locations','result')},
                'compiler_locations':s.get('bounded_output_observation',{}).get('short_error_locations',[]),
                'compiler_codes':s.get('bounded_output_observation',{}).get('rust_error_codes',[])}for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if successful_exit(row)else 2


def run_cold_lookup(args):
    import sys,posixpath
    from pathlib import Path
    import native_postgres_catalog_request_lookup as worker
    import run_native_postgres_runtime_qualification as postgres_runner
    c,a,shared=r.c,r.a,r.shared;output=f'implementation/p09/evidence/p09-361-catalog-cold-request-lookup{args.run}.v1.json'
    c.require(not(c.ROOT/output).exists()and not worker.OWNED.exists()and not(c.ROOT/worker.OBSERVATION).exists(),'COLD_LOOKUP_IMMUTABLE_RUN_AND_FRESH_OWNER')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=artifact=image=None;observation=None;final_attempted=False;started=time.monotonic()
    row=dict(state='FAILED_COLD_REQUEST_LOOKUP',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        official249_replayed=False,Native_or_Hangul_COM_started=False,operational_database_accessed=False,fixture_route_scanner_and_ephemeral_keys=True,
        full_manifest_recovery_and_trusted_product_route_qualified=False)
    def deps(data):
        c.require(0<len(data.encode())<=524288 and ': 'in data.splitlines()[0],'BOUNDED_CURRENT_DEP_INFO')
        result=set()
        for name in data.splitlines()[0].split(': ',1)[1].split():
            path=Path(name.replace('\\','/'))
            if path.is_absolute():c.require(path.is_relative_to(c.ROOT),'DEP_INFO_REPOSITORY_SCOPE');name=path.relative_to(c.ROOT).as_posix()
            name=posixpath.normpath(name.replace('\\','/'));c.require(name.startswith(('crates/','migrations/','tools/p09/','implementation/'))and '..'not in name.split('/'),'DEP_INFO_DECLARED_INPUT_SCOPE');result.add(name)
        c.require(0<len(result)<=2048,'DEP_INFO_INPUT_COUNT_BOUND');return result
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        basepath='implementation/p09/evidence/p09-361-catalog-request-identity451.v1.json';base=layout.unpack(q.json(basepath))
        c.require(q.snapshots[basepath]['sha256']=='5c193df9d54210e3372c018a8e42b5ca4557964f7d29fcc9b8fecff0fd1c3ee8'
            and base['cleanup']is True and base['fresh_inputs']==base['final_fresh_hashes']==935 and base['retained_product9_accepted']is True,'EXACT451_KEY_SQL_BASELINE_NOT_REPLAYED')
        old={p['path']:p for p in base['source_pins']}
        rev='crates/revision-service/src/postgres/source_formula_policy/issuer_registry/stored_revision_jobs'
        meta='crates/artifact-service/src/store/postgres_repository'
        source='crates/product-cli/src/form_stored_provider/actual_import/source_search.rs'
        product='crates/product-cli/src/form_product_request/stored_literal_replacement/personal_info/catalog.rs'
        job='crates/product-cli/src/stored_revision_commit/job/identity.rs'
        parent='crates/product-cli/tests/support/personal_info_catalog_mask_storage.rs';test='crates/product-cli/tests/support/personal_info_catalog_request_lookup.rs'
        sql='crates/product-cli/examples/sql23_storage'
        changed={DRIVER,rev+'.rs',rev+'/admission.rs',rev+'/lifecycle.rs',rev+'/lifecycle/sql.rs',meta+'.rs',meta+'/schema23.rs',source,product,job,parent,
            sql+'.rs',sql+'/setup.rs',sql+'/catalog.rs','tools/p09/native_postgres_cluster.py','tools/p09/native_postgres_storage.py','implementation/p09/P09_COMPLETION_EXECUTION.md'}
        names=set(old)|shared.source_inventory(guard.check)|{DRIVER,test,rev+'/request_lookup.rs',meta+'/schema24.rs',product[:-3]+'/request_lookup.rs',
            'migrations/postgres/0024_p09_stored_request_lookup.up.sql','migrations/postgres/0024_p09_stored_request_lookup.down.sql',
            'crates/product-cli/examples/sql24_catalog_request_lookup.rs',sql+'/lookup24.rs','tools/p09/native_postgres_catalog_request_lookup.py',
            'tools/p09/tests/test_stored_request_lookup_scope.py','tools/p09/tests/test_native_postgres_cluster.py'}
        prod_paths,_=prior.prior.dependencies('target/debug/deps/personal_info_mask_product-d9995c0aff1b1d2e.d',guard);product_inputs=set(prod_paths)|{test};names.update(product_inputs)
        # Declare old unit-library include inputs BEFORE executing, not after a passing body.
        for lib in('artifact_service','revision_service','hwpx_agent_cli'):
            for item in(c.ROOT/'target/debug/deps').glob(lib+'-*.d'):
                text=item.read_text(encoding='utf-8');guard.check()
                if '.exe:'in text:names.update(deps(text))
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':names.add(path.relative_to(c.ROOT).as_posix())
        for path in sorted(names):
            if path.startswith('target/debug/'):continue
            pin=q.pin(path)
            if path in old and path not in changed:c.require(pin==old[path],'UNCHANGED_PREVIOUS_PRODUCT_GUARD_CRYPTO_SQL_INPUTS')
        docpath='implementation/p09/evidence/p09-361-catalog-request-identity-doc-sync453.v1.json';docs=layout.unpack(q.json(docpath))
        c.require(q.snapshots[docpath]['sha256']=='a5897b82fe9a066bf2313bcab9f828bb4ac667c2dbe415cca5f1ccb7aa33bb26'and docs['cleanup']is True,'EXACT_DOCUMENT_ONLY_UPDATE453')
        plan='implementation/p09/P09_COMPLETION_EXECUTION.md';c.require(q.pin(plan)==next(p for p in docs['source_pins']if p['path']==plan),'PLAN_DOCUMENT_ROLE_NOT_EXECUTED_CODE')
        archive='implementation/p09/source-archive/p361-catalog-lookup454/'
        for path,leaf in[(sql+'.rs','sql-main.rs'),(sql+'/setup.rs','setup.rs'),(sql+'/catalog.rs','catalog.rs'),('tools/p09/native_postgres_storage.py','native-storage.py'),('tools/p09/native_postgres_cluster.py','native-cluster.py'),(DRIVER,'runner.py')]:
            pin=q.pin(archive+leaf);c.require((pin['bytes'],pin['sha256'])==(old[path]['bytes'],old[path]['sha256']),'EXACT_PREVIOUS_OWNED_RUNTIME_AND_SQL_SOURCES_PRESERVED')
        r.audit.inverse(q.text(product).replace('pub mod request_lookup;\n',''),old[product],'STRICT_REQUEST_COMPILER_AND_CURRENT_CATALOG_BODIES_UNCHANGED')
        r.audit.inverse(q.text(parent).replace('mod lookup{include!("personal_info_catalog_request_lookup.rs");}\n',''),old[parent],'ALL_PRIOR_STORAGE_IDENTITY_AND_GUARD_TEST_BODIES_UNCHANGED')
        if args.after_lookup454:
            failed_path='implementation/p09/evidence/p09-361-catalog-cold-request-lookup454.v1.json';failed=layout.unpack(q.json(failed_path))
            c.require(q.snapshots[failed_path]['sha256']=='bb6f0d1984c91b912ae53fd444d71dbb562a8f6f026cf3b27c1c835ead4a44ef'and failed['cleanup']is True
                and failed['error_code']=='SOURCE_NOTE_API_COMMAND_FAILED'and len(failed['steps'])==4 and failed['steps'][3]['exit_code']==101 and failed['steps'][3]['tests']==[]
                and failed['steps'][3]['bounded_output_observation']['rust_error_codes']==['E0599']and failed.get('database_stage')is None,'EXACT454_TEST_SCOPE_COMPILE_FAILURE_ZERO_PRODUCT_OR_SQL')
            frozen={p['path']:p for p in failed['source_pins']}
            for path,pin in frozen.items():
                if path in(DRIVER,test):
                    before=q.pin(archive+('failed-runner.py'if path==DRIVER else'failed-test.rs'));c.require((before['bytes'],before['sha256'])==(pin['bytes'],pin['sha256']),'EXACT454_FAILED_SOURCES_PRESERVED')
                elif args.after_lookup456 and path==sql+'.rs':
                    r.audit.inverse(q.text(path).replace('hwpx-agent-p09-pg18-catalog-lookup-457','hwpx-agent-p09-pg18-catalog-lookup-454'),pin,'ONLY_FRESH_OWNED_FIXTURE_ROOT_CHANGED')
                elif args.after_lookup455 and path in(sql+'/lookup24.rs','tools/p09/native_postgres_catalog_request_lookup.py'):
                    before=q.pin(archive+('lookup-fixture455.rs'if path==sql+'/lookup24.rs'else'native-lookup455.py'))
                    c.require((before['bytes'],before['sha256'])==(pin['bytes'],pin['sha256']),'PRE_EXECUTION_FIXTURE_CREDENTIAL_ORDER_SOURCE_PRESERVED')
                    c.require(all(path not in p['dependency_paths']for p in failed['actual_compiled_test_inputs']),'FIXTURE_NOT_AN_INPUT_OF_RETAINED_BACKEND_MODELS')
                else:c.require(q.pin(path)==pin,'ALL454_PRODUCTION_AND_RETAINED_TEST_EXECUTION_INPUTS_UNCHANGED')
            after=q.text(test);c.require(after.count('rev::RevisionRepository::authorize_context(self,c)?;')==1,'EXACT_ONE_TEST_TRAIT_QUALIFICATION')
            if not args.after_lookup455:r.audit.inverse(after.replace('rev::RevisionRepository::authorize_context(self,c)?;','self.authorize_context(c)?;'),frozen[test],'ONLY_TEST_TRAIT_METHOD_QUALIFICATION_FIXED')
            else:
                last_path='implementation/p09/evidence/p09-361-catalog-cold-request-lookup455.v1.json';last=layout.unpack(q.json(last_path))
                c.require(q.snapshots[last_path]['sha256']=='f859c8bd23c6320509f161ae16c9a128e1a80b0fcec054216d7ca9ff1acf30d3'and last['cleanup']is True and len(last['steps'])==1
                    and last['steps'][0]['exit_code']==101 and len(last['steps'][0]['tests'])==6 and last.get('database_stage')is None,'EXACT455_PRODUCT5_PASS_SCOPE1_FAIL_NO_DATABASE')
                pins={p['path']:p for p in last['source_pins']}
                for path,leaf in[(test,'failed-test455.rs'),(DRIVER,'failed-runner455.py')]:
                    pin=q.pin(archive+leaf);c.require((pin['bytes'],pin['sha256'])==(pins[path]['bytes'],pins[path]['sha256']),'EXACT455_FAILED_SOURCES_PRESERVED')
                def without_scope_case(text):
                    marker='#[test]\nfn current_read_write_and_external_document_scope_remain_mandatory';c.require(text.count(marker)==1,'ONE_SCOPE_CASE')
                    begin=text.index(marker);end=text.index('#[test]',begin+len(marker));return text[:begin]+text[end:]
                c.require(without_scope_case(q.text(archive+'failed-test455.rs'))==without_scope_case(after),'ALL_FIVE_PASSED_BODIES_AND_SHARED_HELPERS_UNCHANGED')
                c.require(product_inputs<=set(pins),'ALL_ACTUAL_PRODUCT_TEST_INPUTS_WERE_FRESH_BEFORE455')
                for path in product_inputs-{test}:c.require(q.pin(path)==pins[path],'ALL_OTHER_PRODUCT_EXECUTION_INPUTS_UNCHANGED_SINCE455')
                row.update(retained_product5_pending_final_fresh=True,fixture_setup_password_order_repaired_before_any_SQL_execution=True)
                if args.after_lookup456:
                    completed_path='implementation/p09/evidence/p09-361-catalog-cold-request-lookup456.v1.json';completed_lookup=layout.unpack(q.json(completed_path))
                    c.require(q.snapshots[completed_path]['sha256']=='21c3ff523104fabf0bcc7db047c26d410f6531db1c6d083b81cb0c4d93fc8a98'and completed_lookup['cleanup']is True
                        and len(completed_lookup['steps'])==3 and completed_lookup['steps'][0]['exit_code']==0 and len(completed_lookup['steps'][0]['tests'])==1
                        and completed_lookup['steps'][0]['tests'][0][1]=='ok'and completed_lookup['steps'][1]['exit_code']==0
                        and completed_lookup['database_error']=='PG_CLUSTER_COMMAND_FAILED','EXACT456_SCOPE_PASS_COMPILE_AND_PARTIAL_OWNED_SQL_NOT_RESOURCE_STOP')
                    frozen456={p['path']:p for p in completed_lookup['source_pins']}
                    for path,pin in frozen456.items():
                        if path in(DRIVER,sql+'.rs','tools/p09/native_postgres_catalog_request_lookup.py'):
                            leaf='failed-runner456.py'if path==DRIVER else'sql-main456.rs'if path==sql+'.rs'else'native-lookup456.py'
                            saved=q.pin(archive+leaf);c.require((saved['bytes'],saved['sha256'])==(pin['bytes'],pin['sha256']),'EXACT456_FAILED_SOURCES_AND_FIXTURE_OWNER_PRESERVED')
                        else:c.require(q.pin(path)==pin,'ALL_PASSED456_LIBRARY_PRODUCT_AND_REAL_SQL_INPUTS_UNCHANGED')
                    original_observation='target/p09-catalog-cold-request-lookup-observations-454.json';observed=q.json(original_observation)
                    c.require(q.snapshots[original_observation]['sha256']=='81e5db7c1123130be1d764e8b0d8f485c19d05ec7f70e8ca4a4e3478c882e177'
                        and observed['postmasters'][0]['normal_stop']is True and len(observed['probes'])==5
                        and observed['probes'][2]['cold_request_lookup']['cold_lookup']is True
                        and any(s['stage']=='lookup_fixture_source_acl_revoke'and s['exit_code']==3 and s['sqlstates']==['23514']for s in observed['commands']),
                        'EXACT456_COLD_LOOKUP_CORE_PASS_THEN_FIXTURE_ACL_CONSTRAINT_FAILURE_NORMAL_STOP')
                    row.update(retained_product6_pending_final_fresh=True,old_SQL_fixture_preserved_and_not_restarted=True,
                        new_SQL_fixture_is_independent_not_a_retry_of_old_job=True)
            row.update(retained_models_pending_final_fresh=20,previous_product_bodies_executed=0)
        artifact=a.AcceptanceReader(c.ROOT,guard.check);image=a.AcceptanceReader(prior.CONFIG.parent,guard.check);fixed=image.pin(prior.CONFIG.name)
        c.require((fixed['bytes'],fixed['sha256'])==(17020,'fe3721e68a749c3d1ec843207d475249fa75e68f1de569fe45468c05b1022434'),'CURRENT_UNMODIFIED_INSTALLED_CATALOG')
        completed=layout.unpack(q.json(COMPLETED));peak=max(s['owned_job']['last_job_accounting']['peak_job_private_percent']for s in completed['steps']);guard.check(force=True)
        row['memory_admission']=memory_headroom(guard.samples[-1]['available_ram_percent'],peak);c.require(row['memory_admission']['admitted'],'PREDICTED_WORKLOAD_WOULD_EXCEED_RAM95')
        scratch=c.ROOT/f'target/p09-cold-lookup-scratch-{args.run}';c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'UNIQUE_COLD_LOOKUP_COMPILER_TEMP');scratch.mkdir()
        env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch),PYTHONPATH=str(c.ROOT/'tools/p09'),PYTHONDONTWRITEBYTECODE='1')
        print(json.dumps(dict(state='COLD_REQUEST_LOOKUP_PREFLIGHT',inputs=len(q.snapshots),accepted_identity15_replayed=False,actual_database_started=False)),flush=True)
        models=failed['steps'][0]['result']if args.after_lookup454 else postgres_runner.run_owned('migration_scope_models3_affected_legacy1',[sys.executable,str(c.ROOT/'tools/p09/tests/test_stored_request_lookup_scope.py')],guard,env,row,60)
        c.require(models['state']=='PASS_LOOKUP_MIGRATION_MODELS3_LEGACY1'and models['tests_run']==4,'SELECTED_MIGRATION_SCOPE_MODELS4')
        prefix='postgres::source_formula_policy::issuer_registry::stored_revision_jobs::'
        rev_names=re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(rev+'/request_lookup.rs'));c.require(len(rev_names)==6,'EXACT_SIX_NEW_LOOKUP_BACKEND_MODELS')
        rev_cases={prefix+'request_lookup::tests::'+n for n in rev_names}|{prefix+'admission::tests::'+n for n in('lookup24_is_explicit_and_preserves_all_original23_schema_checks','exact23_versions_names_and_all_source_hashes_are_required','function_rights_path_owner_public_and_exact_body_all_fail_closed','table_rls_owner_direct_privilege_policy_and_both_triggers_all_fail_closed')}|{prefix+'lifecycle::sql::tests::all_six_queries_have_closed_names_and_exact_parameter_casts'}
        meta_names=re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(meta+'/schema24.rs'));c.require(len(meta_names)==3,'EXACT_THREE_METADATA24_MODELS')
        meta_cases={'store::postgres_repository::schema24::tests::'+n for n in meta_names}|{'store::postgres_repository::schema23::tests::'+n for n in('old_prefix_missing_middle_and_future_schema_are_denied','all11_job_functions_are_closed_and_no_execution_is_granted')}
        prod_names=re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',q.text(test));c.require(len(prod_names)==6,'EXACT_SIX_NEW_COLD_PRODUCT_CASES')
        prod_cases={prior.PREFIX+'routing::storage::lookup::'+n for n in prod_names}
        configs=[('artifact-service',['--lib'],meta_cases,'artifact_service',meta+'/schema24.rs'),('revision-service',['--lib'],rev_cases,'revision_service',rev+'/request_lookup.rs'),
            ('hwpx-agent-cli',['--test','personal_info_mask_product'],prod_cases,'personal_info_mask_product',test)]
        row['actual_compiled_test_inputs']=[]
        for package,target,cases,binary,marker in configs:
            if args.after_lookup454 and package!='hwpx-agent-cli':
                step=failed['steps'][1 if package=='artifact-service'else 2]
                c.require(step['exit_code']==0 and step['cleanup']is True and not step['diagnostics']and {n for n,status in step['tests']if status=='ok'}==cases
                    and len(step['tests'])==len(cases),'EXACT_RETAINED_CURRENT_BACKEND_OR_ARTIFACT_MODELS')
                observed=[p for p in failed['actual_compiled_test_inputs']if p['dep_info']['path'].split('/')[-1].startswith(binary+'-')]
                c.require(bool(observed)and all(test not in p['dependency_paths']for p in observed),'CHANGED_CLI_TEST_NOT_AN_INPUT_OF_RETAINED_MODELS')
                for item in observed:c.require(artifact.pin(item['dep_info']['path'])==item['dep_info'],'RETAINED_MODEL_ACTUAL_DEP_INFO_UNCHANGED')
                row['actual_compiled_test_inputs'].extend(observed);continue
            if args.after_lookup456 and package=='hwpx-agent-cli':
                observed=[p for p in completed_lookup['actual_compiled_test_inputs']if p['dep_info']['path'].split('/')[-1].startswith(binary+'-')]
                c.require(bool(observed)and any(set(p['dependency_paths'])==product_inputs for p in observed),'COMPLETE_CURRENT_PRODUCT6_COMPILED_INPUTS')
                for item in observed:c.require(artifact.pin(item['dep_info']['path'])==item['dep_info'],'RETAINED_PRODUCT6_ACTUAL_DEP_INFO_UNCHANGED')
                row['actual_compiled_test_inputs'].extend(observed);continue
            feature=['--features','p09-installed-format-fixture']if package=='hwpx-agent-cli'else[]
            if args.after_lookup455 and package=='hwpx-agent-cli':
                body=last['steps'][0]['tests'];retained={n for n,status in body if status=='ok'};selected={n for n,status in body if status=='FAILED'}
                c.require(len(retained)==5 and len(selected)==1 and retained|selected==cases and selected=={prior.PREFIX+'routing::storage::lookup::current_read_write_and_external_document_scope_remain_mandatory'},'EXACT_ONLY_FAILED_SCOPE_CASE_REEXECUTED')
                cases=selected
            command=[r.harness.CARGO,'test','--offline','--locked','-j','1','-p',package,*target,*feature,'--message-format=short','--',*sorted(cases),'--test-threads=1']
            r.harness.run_one('cold_lookup_'+package,command,cases,guard,env,row,observe_capture=r.snapshot);r.tools.good_step(row['steps'][-1],cases);c.require(not row['steps'][-1]['diagnostics'],'COLD_LOOKUP_NO_WARNINGS')
            actual=[]
            for item in(c.ROOT/'target/debug/deps').glob(binary+'-*.d'):
                data=item.read_text(encoding='utf-8');guard.check()
                if marker in data.replace('\\','/')and '.exe:'in data:
                    declared=deps(data);c.require(declared<=set(q.snapshots),'ALL_CURRENT_UNIT_AND_PRODUCT_COMPILED_INPUTS_PREDECLARED')
                    if binary=='personal_info_mask_product':c.require(declared==product_inputs,'EXACT_COLD_PRODUCT_TEST_INPUTS')
                    actual.append(dict(dep_info=artifact.pin(item.relative_to(c.ROOT).as_posix()),dependency_paths=sorted(declared)))
            c.require(bool(actual),'ACTUAL_SELECTED_CURRENT_COMPILED_TEST_INPUTS');row['actual_compiled_test_inputs'].extend(actual)
        row.update(new_backend_models=7,new_artifact_models=3,new_product_cases=6,affected_legacy_cases=6,python_scope_models=4)
        name='sql24_catalog_request_lookup';r.harness.run_one('compile_one_schema24_cold_lookup_probe',[r.harness.CARGO,'build','--offline','--locked','-j','1','-p','hwpx-agent-cli','--example',name,'--features','p09-installed-format-fixture','--message-format=short'],set(),guard,env,row,observe_capture=r.snapshot)
        c.require(not row['steps'][-1]['diagnostics'],'SCHEMA24_PROBE_NO_WARNINGS');env['P09_STORAGE_PROBE_SHA256']=artifact.pin(f'target/debug/examples/{name}.exe')['sha256']
        declared=deps(artifact.text(f'target/debug/examples/{name}.d'));c.require(declared<=set(q.snapshots),'ALL_ACTUAL_SQL24_PROBE_INPUTS_PREDECLARED');row['actual_probe_dependencies']=sorted(declared)
        try:result=postgres_runner.run_owned('one_fresh_schema24_cold_request_lookup_acl_and_restart',[sys.executable,str(c.ROOT/'tools/p09/native_postgres_catalog_request_lookup.py'),'--owned-schema24-cold-lookup'],guard,env,row,300)
        finally:
            if(c.ROOT/worker.OBSERVATION).is_file():observation=q.json(worker.OBSERVATION)
        c.require(result['observation_sha256']==q.snapshots[worker.OBSERVATION]['sha256']and result['observation_bytes']==q.snapshots[worker.OBSERVATION]['bytes'],'EXACT_COLD_SQL24_OBSERVATION')
        c.require(observation['state']=='PASS_SCHEMA24_COLD_PUBLIC_REQUEST_LOOKUP_NO_RECOMPILE_ACL_CONFLICT_RESTART_NOT_PRODUCT_OR_GATE'
            and observation['all_owned_postmasters_normal_stop']is True and len(observation['probes'])==9
            and observation['snapshots'][0]==observation['snapshots'][1]and observation['blob_snapshots'][0]==observation['blob_snapshots'][1]
            and len(observation['blob_snapshots'][0])==6,'ACTUAL_COLD_LOOKUP_REQUEST_CONFLICT_ACL_READONLY_RESTART_AND_UNCHANGED_EFFECTS')
        c.require(not any(scratch.iterdir()),'COLD_LOOKUP_COMPILER_TEMP_EMPTY');final_attempted=True
        artifact.finish();row['compiled_artifact_final_fresh_hashes']=artifact.final_fresh_hashes;image.finish();row['installed_config_final_fresh_hashes']=image.final_fresh_hashes;q.finish();guard.check(force=True)
        row.update(state='PASS_COLD_REQUEST_LOOKUP_SCHEMA24_TYPED_CONFLICT_CURRENT_ACL_RESTART_NOT_TRUSTED_PRODUCT_OR_GATE',actual_schema24_cold_lookup=True,
            actual_legacy23_denies24=True,actual_current_project_and_source_acl_denials=True,lookup_does_not_import_compile_or_claim=True,actual_SQL_counts=observation['snapshots'][0])
        if args.after_lookup454:row.update(retained_models_pending_final_fresh=0,retained_models_accepted=20,retained_models_replayed=False)
        if args.after_lookup455:row.update(retained_product5_pending_final_fresh=False,retained_product5_accepted=True,retained_product5_replayed=False)
        if args.after_lookup456:row.update(retained_product6_pending_final_fresh=False,retained_product6_accepted=True,retained_product6_replayed=False)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        code=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'COLD_LOOKUP_FAILURE_NO_RAW_VALUES')
        if final_attempted:row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples
        if observation is not None:row.update(database_stage=observation['stage'],database_error=observation.get('error_code'),last_probe=None if not observation['probes']else observation['probes'][-1])
        row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,installed_config_pins=[]if image is None else list(image.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,output,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent','database_stage','database_error','last_probe')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','cleanup','result','panic_locations')},'cases':len(s.get('tests',[])),
                'compiler_locations':s.get('bounded_output_observation',{}).get('short_error_locations',[]),'compiler_codes':s.get('bounded_output_observation',{}).get('rust_error_codes',[])}for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if successful_exit(row)else 2


def run_request_entry(args):
    # One small product delta + its document close; no recursive historical audits or SQL replay.
    import ast,hashlib,importlib.util,sys,unittest
    from pathlib import Path
    c,a,shared=r.c,r.a,r.shared
    output=f'implementation/p09/evidence/p09-361-catalog-request-entry{args.run}.v1.json'
    compiler=prior.COMPILER;entry=compiler[:-3]+'/entry.rs'
    parent='crates/product-cli/tests/support/personal_info_catalog_request_lookup.rs'
    test='crates/product-cli/tests/support/personal_info_catalog_request_entry.rs'
    c.require(not(c.ROOT/output).exists(),'REQUEST_ENTRY_IMMUTABLE_RESULT')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=artifact=None;started=time.monotonic();final_attempted=False
    row=dict(state='FAILED_CATALOG_REQUEST_ENTRY',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        SQL_or_Hangul_or_Native_started=False,previous_product_bodies_replayed=False,operational_execution_or_publication=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);artifact=a.AcceptanceReader(c.ROOT,guard.check)
        basepath='implementation/p09/evidence/p09-361-catalog-cold-request-lookup457.v1.json';base=layout.unpack(q.json(basepath))
        c.require(q.snapshots[basepath]['sha256']=='b0e07567a76974e6d6d15b2aabd4f709f1ef4f1a79577f8d02e4cfee759a380e'
            and base['cleanup']is True and base['fresh_inputs']==base['final_fresh_hashes']==968
            and base['actual_schema24_cold_lookup']is True,'EXACT_ACCEPTED_LOOKUP457_NOT_REPLAYED')
        old={p['path']:p for p in base['source_pins']}
        expected=set(next(p['dependency_paths']for p in base['actual_compiled_test_inputs']if 'personal_info_mask_product-'in p['dep_info']['path']))|{test}
        names=shared.source_inventory(guard.check)|set(old)|expected|{DRIVER,entry,test}
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':names.add(path.relative_to(c.ROOT).as_posix())
        changed={DRIVER,compiler,parent,'implementation/p09/P09_COMPLETION_EXECUTION.md'}
        for path in sorted(names):
            pin=q.pin(path)
            if path in old and path not in changed:c.require(pin==old[path],'UNCHANGED_ACCEPTED_LOOKUP_SQL_GUARD_AND_TEST_INPUTS')
        r.audit.inverse(q.text(compiler).replace('pub mod entry;\n',''),old[compiler],'ORIGINAL_COMPILER_AND_ROUTE_DENIAL_UNCHANGED')
        r.audit.inverse(q.text(parent).replace('// Child tests must follow bound!\'s textual declaration; product code is unchanged.\n','').replace('mod entry{include!("personal_info_catalog_request_entry.rs");}\n',''),old[parent],'ALL_ACCEPTED_LOOKUP_TEST_BODIES_UNCHANGED')
        if args.run==459:
            failedpath='implementation/p09/evidence/p09-361-catalog-request-entry458.v1.json';failed=layout.unpack(q.json(failedpath))
            c.require(q.snapshots[failedpath]['sha256']=='6ab8e550ac812ff9c69229a0310616fcf043798e29d57366ffade11271798442'
                and failed['cleanup']is True and len(failed['steps'])==1 and failed['steps'][0]['tests']==[]
                and failed['steps'][0]['bounded_output_observation']['macro_not_in_scope_observed']is True,'ORIGINAL458_TEST_MODULE_SCOPE_FAILURE_ZERO_BODIES_PRESERVED')
            frozen={p['path']:p for p in failed['source_pins']}
            for path in [entry,test]:c.require(q.pin(path)==frozen[path],'PRODUCT_ENTRY_AND_EIGHT_TEST_BODIES_UNCHANGED_AFTER458')
            original=q.text('implementation/p09/source-archive/p361-catalog-entry458/lookup-tests458.rs')
            repaired=q.text(parent).replace('// Child tests must follow bound!\'s textual declaration; product code is unchanged.\n','')
            c.require(original.replace('mod entry{include!("personal_info_catalog_request_entry.rs");}\n','')==repaired.replace('mod entry{include!("personal_info_catalog_request_entry.rs");}\n',''),'ONLY_CHILD_MODULE_TEXTUAL_POSITION_REPAIRED')
        saved=q.pin('implementation/p09/source-archive/p361-catalog-entry458/runner.py')
        c.require((saved['bytes'],saved['sha256'])==(old[DRIVER]['bytes'],old[DRIVER]['sha256']),'ORIGINAL457_DRIVER_BYTES_PRESERVED')
        body=q.text(test);cases={prior.PREFIX+'routing::storage::lookup::entry::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',body)}
        c.require(len(cases)==8 and '#[ignore]'not in body,'EXACT_EIGHT_NEW_ENTRY_CASES_ONLY')
        links=0
        for path in ['implementation/p09/P09_COMPLETION_EXECUTION.md','implementation/p09/P09_PERSONAL_INFO_CATALOG_MASK_PROGRESS.md','protocol/migrations/p09-personal-info-catalog-mask-product-v1.md']:
            text=q.text(path);c.require('457'in text and '조회'in text,'CURRENT_LOOKUP_BOUNDARY_DOCUMENTED')
            for link in re.findall(r'\]\(([^)]+)\)',text):
                if link.startswith(('http:','https:','#')):continue
                c.require(((c.ROOT/path).parent/link.split('#')[0]).is_file(),'DOCUMENT_LOCAL_LINK_RESOLVES');links+=1
        q.pin('CURRENT_STATE.md');raw=(c.ROOT/'CURRENT_STATE.md').read_bytes()
        c.require(hashlib.sha256(raw[-1713561:]).hexdigest()=='f80c05a2dc546584d304b6371fe04d13137a49d8ec823b67dbcd8d44b3c48e33','ALL_PRIOR_CURRENT_STATE_BYTES_PRESERVED')
        contract='tools/p09/tests/test_finalize_catalog_mask_product.py';q.pin(contract)
        spec=importlib.util.spec_from_file_location('entry_close_contracts',str(c.ROOT/contract));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        result=unittest.TestResult()
        for name in ('test_original_runner_exit_contract_refuses_prior_premature_pass','test_original_runner_installs_pass_only_after_mandatory_finish'):module.Tests(name).run(result)
        c.require(result.testsRun==2 and not result.errors and not result.failures,'TWO_AFFECTED_RUNNER_CLOSING_CONTRACTS')
        ast.parse(q.text(DRIVER));row.update(affected_runner_contracts=2,local_document_links=links,original_current_state_preserved_bytes=1713561)
        guard.check(force=True);row['memory_admission']=memory_headroom(guard.samples[-1]['available_ram_percent'],6.036870455636344)
        c.require(row['memory_admission']['admitted'],'ENTRY_COMPILE_PREDICTED_RAM95_HEADROOM')
        scratch=c.ROOT/f'target/p09-catalog-entry-scratch-{args.run}'
        c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'ENTRY_UNIQUE_COMPILER_TEMP')
        scratch.mkdir();env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch))
        print(json.dumps(dict(state='CATALOG_ENTRY_PREFLIGHT',run=args.run,inputs=len(q.snapshots),new_cases=8,old_cases_replayed=0)),flush=True)
        command=[r.harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli','--test','personal_info_mask_product','--features','p09-installed-format-fixture','--message-format=short','--',*sorted(cases),'--test-threads=1']
        r.harness.run_one('common_entry_observe_before_compile8',command,cases,guard,env,row,observe_capture=r.snapshot)
        r.tools.good_step(row['steps'][-1],cases);c.require(not row['steps'][-1]['diagnostics'],'REQUEST_ENTRY_NO_WARNINGS')
        row['actual_compiled_test_inputs']=prior.prior.compiled_inputs(dict(test='personal_info_mask_product'),expected,guard)
        for item in row['actual_compiled_test_inputs']:c.require(artifact.pin(item['dep_info']['path'])==item['dep_info'],'ACTUAL_ENTRY_DEP_INFO_FINAL')
        c.require(not any(scratch.iterdir()),'ENTRY_COMPILER_TEMP_EMPTY')
        final_attempted=True;artifact.finish();q.finish();guard.check(force=True)
        row.update(state='PASS_COMMON_CATALOG_ENTRY8_OBSERVE_FIRST_NO_OLD_TEST_OR_SQL_REPLAY_NOT_EXECUTION_OR_GATE',new_product_cases=8,
            compiled_artifact_final_fresh_hashes=artifact.final_fresh_hashes)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        code=error.args[0]if error.args else None;row.update(state='FAILED_CATALOG_REQUEST_ENTRY',error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'ENTRY_FAILURE_NO_RAW_VALUES')
        if final_attempted:row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,output,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','cleanup')},'cases':len(s.get('tests',[])),
                'compiler_locations':s.get('bounded_output_observation',{}).get('short_error_locations',[]),'compiler_codes':s.get('bounded_output_observation',{}).get('rust_error_codes',[]),
                'failed_cases':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if successful_exit(row)else 2


def main(argv=None):
    parser=argparse.ArgumentParser(description='One guarded, immutable read-only product verification; no Native or execution route.')
    parser.add_argument('--run',type=int,choices=range(432,461),required=True)
    parser.add_argument('--stage',choices=('product','manifest','storage','commit-guard','sql-storage','identity-storage','cold-lookup','request-entry'),default='product')
    parser.add_argument('--only-failed-from438',action='store_true')
    parser.add_argument('--after-storage-compile442',action='store_true')
    parser.add_argument('--after-identity450',action='store_true')
    parser.add_argument('--after-lookup454',action='store_true')
    parser.add_argument('--after-lookup455',action='store_true')
    parser.add_argument('--after-lookup456',action='store_true');args=parser.parse_args(argv)
    if args.only_failed_from438 and args.stage!='manifest':parser.error('--only-failed-from438 requires --stage manifest')
    if args.after_storage_compile442 and args.stage!='storage':parser.error('--after-storage-compile442 requires --stage storage')
    if args.after_identity450 and args.stage!='identity-storage':parser.error('--after-identity450 requires --stage identity-storage')
    if args.after_lookup454 and args.stage!='cold-lookup':parser.error('--after-lookup454 requires --stage cold-lookup')
    if args.after_lookup456:args.after_lookup455=True
    if args.after_lookup455:
        if args.stage!='cold-lookup':parser.error('--after-lookup455 requires --stage cold-lookup')
        args.after_lookup454=True
    if args.stage=='request-entry':return run_request_entry(args)
    if args.stage=='cold-lookup':return run_cold_lookup(args)
    if args.stage in('sql-storage','identity-storage'):return run_sql_storage(args)
    if args.stage=='commit-guard':return run_commit_guard(args)
    if args.stage in('manifest','storage'):return run_manifest(args)
    output=f'implementation/p09/evidence/p09-361-personal-info-catalog-mask-product-recovery{args.run}.v1.json'
    c,a,shared=r.c,r.a,r.shared;c.require(not(c.ROOT/output).exists(),'CATALOG_PRODUCT_RECOVERY_IMMUTABLE_RESULT')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=image=None;final_attempted=False;started=time.monotonic();row=dict(state='FAILED_CATALOG_MASK_PRODUCT_RECOVERY',steps=[],own_cpu_selection=selection,
        actual_DB_Hangul_or_COM_started=False,Native011_executed=False,prior_Native_replayed=False,official249_replayed=False,
        prior_source30_or_stored20_replayed=False,private_user_catalog_accessed=False,installed_catalog_mutated=False,
        original431_resource_failure_preserved=True,loaders_share_one_borrowed_catalog_adapter=True,request_match_and_component_caps_are_separate=True,
        source_document_mutation=False,ingest_commit_or_publication=False,native_execution_authorized=False,
        accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);base=layout.unpack(q.json(prior.OUTPUT));completed=layout.unpack(q.json(COMPLETED))
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='48f0a103fd625bcbdbc54aaaf0daebab601e48e53d6da38a260e49225e30fd1e'
            and base['cleanup']is True and base['error_code']=='CURRENT_EPOCH_ACCEPT_ORIGINAL_RESOURCE_STOP'
            and len(base['steps'])==1 and not base['steps'][0]['bounded_output_observation']['observed_harness_started'],'EXACT431_RAM95_STOP_WITHOUT_ACCEPTED_CASES_RETAINED')
        c.require(q.snapshots[COMPLETED]['sha256']=='9b766f491502fb82b2c96726795339600d3286235ebe487cd0d5561dc2f5cf80'
            and completed['cleanup']is True and completed['fresh_inputs']==completed['final_fresh_hashes']==842,'EXACT_COMPLETED_COMPARABLE_COMPILER_RESOURCE_RECORD')
        peak=max(s['owned_job']['last_job_accounting']['peak_job_private_percent']for s in completed['steps'])
        row['admission_models']=admission_models()
        # Even a deferred run pins the changed implementation and model inputs.
        for path in(DRIVER,prior.DRIVER,prior.PRODUCT,prior.COMPILER,prior.TEST,prior.PARENT,prior.COMMON,prior.SERVICE,prior.LINK):q.pin(path)
        guard.check(force=True);row['memory_admission']=memory_headroom(guard.samples[-1]['available_ram_percent'],peak)
        if not row['memory_admission']['admitted']:
            row.update(state='DEFERRED_CARGO_PREDICTED_RAM95_HEADROOM_NOT_PRODUCT_OR_GATE',cargo_started=False,
                product_cases_executed=0,complete_compile_input_closure_checked=False)
        else:
            old={p['path']:p for p in base['source_pins']};changed={prior.PRODUCT,prior.COMPILER,prior.TEST}
            for path in sorted(set(old)|r.shared.source_inventory(guard.check)|{DRIVER}):
                pin=q.pin(path)
                if path in old and path not in changed:c.require(pin==old[path],'ALL_PRIOR_PASSED_SOURCE_STORED_LEGACY_COMPILER_TESTS_AND_GUARDS_PRESERVED')
            # Re-run the old-to-new structural preservation checks for the only
            # legacy changes. Failed 431 itself is never acceptance evidence.
            accepted=layout.unpack(q.json(prior.BASE));pins={p['path']:p for p in accepted['source_pins']}
            text=q.text(prior.PARENT);r.audit.inverse(text.replace('pub mod catalog;\n',''),pins[prior.PARENT],'ORIGINAL_SELECTED_MASK_PRODUCT_UNCHANGED')
            text=q.text(prior.LINK);r.audit.inverse(text.replace('mod product{include!("personal_info_catalog_mask_product.rs");}\n',''),pins[prior.LINK],'ORIGINAL_STORED20_TEST_BODIES_UNCHANGED')
            r.audit.inverse(prior.original_service(q.text(prior.SERVICE)),pins[prior.SERVICE],'ORIGINAL_SOURCE_STORED_CURRENT_ACCESS_AND_DELIVERY_ALGORITHMS_UNCHANGED')
            r.audit.inverse(prior.original_common(q.text(prior.COMMON)),pins[prior.COMMON],'ORIGINAL_SHARED_COMPILER_RECEIPT_BODY_UNCHANGED')
            text=q.text(prior.TEST);new={prior.PREFIX+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',text)}
            c.require(len(new)==42 and '#[ignore]'not in text,'EXACT41_SYNTHETIC_ONE_INSTALLED_NEW_CASES')
            cases=new|prior.AFFECTED;c.require(len(cases)==45,'NEW42_AND_DIRECTLY_AFFECTED3_ONLY')
            config=prior.CONFIG;image=a.AcceptanceReader(config.parent,guard.check);pin=image.pin(config.name)
            c.require((pin['bytes'],pin['sha256'])==(17020,'fe3721e68a749c3d1ec843207d475249fa75e68f1de569fe45468c05b1022434'),'EXACT_UNMODIFIED_FIXED_INSTALLED_CONFIG')
            expected=set(accepted['actual_stored_test_inputs'][0]['dependency_paths'])|{prior.TEST}
            c.require(expected<=set(q.snapshots),'COMPLETE_BEFORE_COMPILE_TEST_INPUTS_PINNED')
            guard.check(force=True);row['memory_admission_before_cargo']=memory_headroom(guard.samples[-1]['available_ram_percent'],peak)
            if not row['memory_admission_before_cargo']['admitted']:
                row.update(state='DEFERRED_CARGO_PREDICTED_RAM95_HEADROOM_NOT_PRODUCT_OR_GATE',cargo_started=False,
                    product_cases_executed=0,complete_compile_input_closure_checked=True)
            else:
                scratch=c.ROOT/f'target/p09-catalog-mask-product-scratch-{args.run}';c.require(not scratch.exists()and scratch.parent.is_dir()
                    and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'PRODUCT_RECOVERY_UNIQUE_COMPILER_TEMP')
                scratch.mkdir();env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch))
                command=[r.harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli','--test','personal_info_mask_product','--features','p09-installed-format-fixture','--message-format=short','--',*sorted(cases),'--test-threads=1']
                row['cargo_started']=True;print(json.dumps(dict(state='CATALOG_PRODUCT_RECOVERY_PREFLIGHT',run=args.run,inputs=len(q.snapshots),new=42,affected=3)),flush=True)
                r.harness.run_one('optimized_catalog_products_shared_compiler45',command,cases,guard,env,row,observe_capture=r.snapshot)
                r.tools.good_step(row['steps'][-1],cases);c.require(not row['steps'][-1]['diagnostics'],'CATALOG_PRODUCTS45_NO_WARNINGS')
                row['actual_compiled_test_inputs']=prior.prior.compiled_inputs(prior.prior.CONFIGS[1],expected,guard)
                c.require(not any(scratch.iterdir()),'PRODUCT_RECOVERY_COMPILER_TEMP_EMPTY')
                row.update(state='OBSERVED_CATALOG_MASK_PRODUCT42_AFFECTED3_PENDING_FINAL_FRESH',product_cases_executed=45,new_product_cases=42,affected_product_cases=3,
                    complete_compile_input_closure_checked=True)
        final_attempted=True
        if image is not None:image.finish();row['installed_config_final_fresh_hashes']=image.final_fresh_hashes
        q.finish();guard.check(force=True);row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
        if row['state']=='OBSERVED_CATALOG_MASK_PRODUCT42_AFFECTED3_PENDING_FINAL_FRESH':
            row['state']='PASS_CATALOG_MASK_PRODUCT42_AFFECTED3_NOT_NATIVE_OR_GATE'
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        value=error.args[0]if error.args else None;row.update(state='FAILED_CATALOG_MASK_PRODUCT_RECOVERY',error_type=type(error).__name__,error_code=value if type(value)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',value)else'CATALOG_PRODUCT_RECOVERY_FAILURE_NO_RAW_VALUES')
        if final_attempted:row['failed_final_fresh_check']=True
        if q is not None and not final_attempted:
            final_attempted=True
            try:
                if image is not None:image.finish();row['installed_config_final_fresh_hashes']=image.final_fresh_hashes
                q.finish();row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
            except(ValueError,OSError,KeyError,TypeError,AttributeError):row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),installed_config_pins=[]if image is None else list(image.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if q is not None:row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
        pin=shared.publisher.publish(c.ROOT,output,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','memory_admission','memory_admission_before_cargo','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','safe_error_variants','panic_locations','cleanup')},'cases':len(s.get('tests',[])),
                'compiler_codes':s.get('bounded_output_observation',{}).get('rust_error_codes',[]),'compiler_locations':s.get('bounded_output_observation',{}).get('short_error_locations',[]),
                'failed_cases':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'receipt':pin}),flush=True)
    return 0 if successful_exit(row)else 2


if __name__=='__main__':raise SystemExit(main())
