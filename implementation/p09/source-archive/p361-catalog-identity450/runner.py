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
    import native_postgres_catalog_storage as worker
    import run_native_postgres_runtime_qualification as postgres_runner
    c,a,shared=r.c,r.a,r.shared
    output=f'implementation/p09/evidence/p09-361-catalog-actual-sql-storage{args.run}.v1.json'
    c.require(not(c.ROOT/output).exists()and not worker.OWNED.exists()and not(c.ROOT/worker.OBSERVATION).exists(),'CATALOG_SQL_IMMUTABLE_RUN_AND_FRESH_OWNER')
    selection=r.tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=artifact=image=None;observation=None;final_attempted=False;started=time.monotonic()
    row=dict(state='FAILED_CATALOG_ACTUAL_SQL_STORAGE',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        official249_replayed=False,previous_test_bodies_replayed=False,Native_or_Hangul_COM_started=False,operational_database_accessed=False,
        fixture_route_and_scanner_not_trusted_product=True,full_manifest_reconciliation_qualified=False,parent_retained_ephemeral_fixture_keys=True)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        basepath='implementation/p09/evidence/p09-361-catalog-storage-commit-guard446.v1.json';base=layout.unpack(q.json(basepath))
        c.require(q.snapshots[basepath]['sha256']=='336712a2733a0659de4c45d8a2ef4825058dfda55c610a18a1afba40e0b2d22a'
            and base['cleanup']is True and base['fresh_inputs']==base['final_fresh_hashes']==879 and base['new_guard_cases']==15 and base['affected_legacy_cases']==5,
            'EXACT_CURRENT_COMMIT_GUARD20_ACCEPTED_NO_REPLAY')
        old={p['path']:p for p in base['source_pins']}
        oldsqlpath='implementation/p09/evidence/p09-361-registered-recovery-postgres298.v1.json';oldsql=r.closure.compact.unpack(q.json(oldsqlpath))
        c.require(q.snapshots[oldsqlpath]['sha256']=='5cb52bcd3daa26f9f3de0789ceb7ac28e298f56a29dae6d639eabc775ca10386'and oldsql['cleanup']is True,'CURRENT_REGISTERED_SQL_CAMPAIGN_SOURCE_NOT_REEXECUTION')
        sqlpins={p['path']:p for p in oldsql['source_pins']}
        common='crates/product-cli/examples/sql23_storage.rs';setup=common[:-3]+'/setup.rs';catalog=common[:-3]+'/catalog.rs'
        probe='crates/product-cli/examples/sql23_catalog_storage.rs'
        names=set(old)|shared.source_inventory(guard.check)|{DRIVER,common,setup,catalog,probe,common[:-3]+'/pipeline.rs',
            'crates/product-cli/tests/support/stored_commit_manifest.rs','tools/p09/fixtures/postgres_revision_adapter.sql',
            'tools/p09/fixtures/sql23_service_roles.sql','tools/p09/fixtures/native_postgres_hba.conf',worker.original.cluster.MANIFEST,
            'crates/hwpx-package/tests/support/search_definition_fixture.rs','crates/hwpx-package/tests/support/document_import_field_fixture.rs',
            'crates/hwpx-package/tests/support/document_import_catalog_fixture.rs','crates/hwpx-package/src/hancom_2020_minimal_header.xml'}
        names.update('migrations/postgres/'+p.name for p in(c.ROOT/'migrations/postgres').glob('*.up.sql')if re.fullmatch(r'00(?:0[1-9]|1[0-9]|2[0-3])_[a-z0-9_]+\.up\.sql',p.name))
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':names.add(path.relative_to(c.ROOT).as_posix())
        for path in sorted(names):
            if path.startswith('target/debug/'):continue
            pin=q.pin(path)
            if path in old and path!=DRIVER:c.require(pin==old[path],'UNCHANGED_ACCEPTED_COMMIT_GUARD_PRODUCTION_AND_TEST_INPUTS')
        text=q.text(common).replace('#[path="sql23_storage/catalog.rs"] mod catalog;\n','')
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
        runtime_manifest=q.json(worker.original.cluster.MANIFEST);row['runtime_file_count']=len(runtime_manifest['runtime_pins'])
        image=a.AcceptanceReader(prior.CONFIG.parent,guard.check);installed=image.pin(prior.CONFIG.name)
        c.require((installed['bytes'],installed['sha256'])==(17020,'fe3721e68a749c3d1ec843207d475249fa75e68f1de569fe45468c05b1022434'),'EXACT_CURRENT_INSTALLED_CATALOG_NOT_PRIVATE_CONFIG')
        completed=layout.unpack(q.json(COMPLETED));peak=max(s['owned_job']['last_job_accounting']['peak_job_private_percent']for s in completed['steps'])
        guard.check(force=True);row['memory_admission']=memory_headroom(guard.samples[-1]['available_ram_percent'],peak)
        c.require(row['memory_admission']['admitted'],'PREDICTED_WORKLOAD_WOULD_EXCEED_ORIGINAL_RAM95')
        scratch=c.ROOT/f'target/p09-catalog-sql-scratch-{args.run}';c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'CATALOG_SQL_UNIQUE_COMPILER_TEMP')
        scratch.mkdir();env=r.audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch),PYTHONPATH=str(c.ROOT/'tools/p09'),PYTHONDONTWRITEBYTECODE='1')
        print(json.dumps(dict(state='CATALOG_SQL_PREFLIGHT',inputs=len(q.snapshots),old_tests_replayed=0,existing_database_accessed=False)),flush=True)
        r.harness.run_one('compile_original_catalog_sql_storage_bridge',[r.harness.CARGO,'build','--offline','--locked','-j','1','-p','hwpx-agent-cli',
            '--example','sql23_catalog_storage','--message-format=short'],set(),guard,env,row,observe_capture=r.snapshot)
        c.require(not row['steps'][-1]['diagnostics'],'CATALOG_SQL_BUILD_NO_WARNINGS')
        artifact=a.AcceptanceReader(c.ROOT,guard.check);exe='target/debug/examples/sql23_catalog_storage.exe';env['P09_STORAGE_PROBE_SHA256']=artifact.pin(exe)['sha256']
        dep='target/debug/examples/sql23_catalog_storage.d';line=artifact.text(dep).splitlines()[0];c.require(': 'in line,'CATALOG_SQL_DEP_INFO_TARGET')
        paths=[]
        for item in line.split(': ',1)[1].split():
            item=item.replace('\\','/');path=Path(item)
            if path.is_absolute():c.require(path.is_relative_to(c.ROOT),'CATALOG_SQL_DEP_INFO_REPO_SCOPE');item=path.relative_to(c.ROOT).as_posix()
            item=posixpath.normpath(item);c.require(item.startswith(('crates/','migrations/','tools/p09/fixtures/'))and '..'not in item.split('/'),'CATALOG_SQL_DEP_INFO_INPUT_SCOPE');paths.append(item)
        c.require(0<len(paths)<=128 and set(paths)<=set(q.snapshots),'CATALOG_SQL_ALL_ACTUAL_RUST_INCLUDE_INPUTS_DECLARED')
        row['actual_compiled_dependency_paths']=sorted(set(paths))
        try:result=postgres_runner.run_owned('one_actual_catalog_SQL23_AEAD_guarded_job_and_restart',[sys.executable,str(c.ROOT/'tools/p09/native_postgres_catalog_storage.py'),'--owned-generated-hwpx-catalog-campaign'],guard,env,row,300)
        finally:
            if(c.ROOT/worker.OBSERVATION).is_file():observation=q.json(worker.OBSERVATION)
        c.require(result['observation_sha256']==q.snapshots[worker.OBSERVATION]['sha256']and result['observation_bytes']==q.snapshots[worker.OBSERVATION]['bytes'],'EXACT_SQL_OBSERVATION_BYTES')
        c.require(observation['state']=='PASS_GENERATED_CATALOG_HWPX_SQL23_GUARDED_JOB_AEAD_HEAD_RESTART_NOT_TRUSTED_PRODUCT_OR_GATE'
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


def main(argv=None):
    parser=argparse.ArgumentParser(description='One guarded, immutable read-only product verification; no Native or execution route.')
    parser.add_argument('--run',type=int,choices=range(432,451),required=True)
    parser.add_argument('--stage',choices=('product','manifest','storage','commit-guard','sql-storage'),default='product')
    parser.add_argument('--only-failed-from438',action='store_true')
    parser.add_argument('--after-storage-compile442',action='store_true');args=parser.parse_args(argv)
    if args.only_failed_from438 and args.stage!='manifest':parser.error('--only-failed-from438 requires --stage manifest')
    if args.after_storage_compile442 and args.stage!='storage':parser.error('--after-storage-compile442 requires --stage storage')
    if args.stage=='sql-storage':return run_sql_storage(args)
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
