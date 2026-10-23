"""Actual sixteen-family source/plan-to-original-router/manifest, no trusted execution claims."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_source_search_review_compiler_recovery as prior
base=prior.base
harness,shared,c,a,audit,tools=base.harness,base.shared,base.c,base.a,base.audit,base.tools
OUTPUT='implementation/p09/evidence/p09-361-source-search-manifest-components218.v1.json'
DRIVER='tools/p09/run_source_search_manifest_components.py'
SYNC='implementation/p09/evidence/p09-361-source-search-operation-compiler-sync217.v1.json'
SYNC_DRIVER='tools/p09/run_source_search_operation_compiler_sync.py'
PROFILE='protocol/migrations/p09-source-search-operation-compiler-v1.md'
ROUTER='crates/domain-ir/src/capability_router.rs'
ROUTING=base.MODEL[:-3]+'/routing.rs'
TEST='crates/product-cli/tests/form_stored_provider/actual_import/compiled_search_routing.rs'
PREFIX=base.PREFIX.replace('compiled_v1::','routing_v1::')
CHANGED={ROUTER,base.MODEL,base.PARENT}
NEW={ROUTING,TEST,DRIVER}
GETTERS='''
    #[must_use]
    pub const fn target_profile(&self) -> &ExactTargetProfile {
        &self.target_profile
    }

    #[must_use]
    pub const fn now_unix_ms(&self) -> u64 {
        self.now_unix_ms
    }
'''
BATCH='''
    /// Routes a whole immutable plan, sharing each capability's original routing decision.
    /// The original router depends only on capability and this exact context/catalog snapshot;
    /// operation IDs are projected separately and never reused across operations. This cache
    /// lives only in this call, so a later registry, health, policy or time snapshot is rechecked.
    /// # Errors
    /// Preserves every original routing failure; no partial route set is returned.
    pub fn route_plan(
        &self,
        plan: &crate::CompiledOperationPlan,
        context: &RouteContext,
        catalog: &CapabilityRouteCatalog,
    ) -> Result<Vec<RouteDecision>, CapabilityRouterError> {
        let mut by_capability = BTreeMap::<&CapabilityId, RouteDecision>::new();
        let mut routes = Vec::with_capacity(plan.operations().len());
        for operation in plan.operations() {
            let route = if let Some(previous) = by_capability.get(operation.capability_id()) {
                let mut route = previous.clone();
                route.operation_id = operation.operation_id().clone();
                route
            } else {
                let route = self.route(operation, context, catalog)?;
                by_capability.insert(operation.capability_id(), route.clone());
                route
            };
            routes.push(route);
        }
        Ok(routes)
    }
'''


def inventory(check):return prior.inventory(check)|NEW|{SYNC_DRIVER,PROFILE,ROUTER,'crates/operation-engine/src/manifest.rs'}


def expected(q):
    text=q.text(TEST);ordinary=re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',text)
    generated=re.findall(r'^manifest_case!\(([A-Za-z0-9_]+),',text,re.M)
    c.require(len(ordinary)==10 and len(generated)==16 and len(set(ordinary+generated))==26,'EXACT26_ROUTER_MANIFEST_CASES_ALL16_SOURCE_FAMILIES')
    return{PREFIX+n for n in ordinary+generated}


def inverse(q,tested):
    router=q.text(ROUTER)
    c.require(router.count(GETTERS)==router.count(BATCH)==1,'ONLY_ADDITIVE_READONLY_CLOCK_TARGET_AND_PER_CALL_CAPABILITY_CACHE')
    audit.inverse(router.replace(GETTERS,'').replace(BATCH,''),tested[ROUTER],'ENTIRE_ORIGINAL_SINGLE_ROUTER_CONTEXT_CONSTRUCTION_POLICY_HEALTH_PRESERVATION_AND_DECISION_BODIES_UNCHANGED')
    text=q.text(base.MODEL);c.require(text.count('pub mod routing;\n')==1,'ONE_ADDITIVE_ROUTING_CHILD')
    audit.inverse(text.replace('pub mod routing;\n',''),tested[base.MODEL],'ENTIRE_TESTED_SOURCE_COMPILER_CURRENT_VERIFICATION_AND_ROUTE_DENIAL_UNCHANGED')
    text=q.text(base.PARENT);marker='#[path="compiled_search_routing.rs"] mod routing_v1;\n'
    c.require(text.count(marker)==1 and text.endswith(marker),'ONE_APPENDED_ROUTER_MANIFEST_TEST_CHILD')
    audit.inverse(text.replace(marker,''),tested[base.PARENT],'ALL_ORIGINAL_DISPATCH_SPLICE_AND_COMPILER_TESTS_UNCHANGED')
    text=q.text(ROUTING)
    for marker in('now.checked_mul(1000)!=Some(context.now_unix_ms())','route_plan(compiled.compiled(),context,catalog)?',
        'ExecutionManifest::from_receipts(transaction,artifact,compiled.receipt.source_package_sha256,source_size,compiled.compiled(),&routes)?',
        'route.backend_kind()!=BackendKind::DirectHwpx','target!=self.target_profile_sha256',
        'self.compiled.require_current_product_route(provider,now)','self.compiled.candidate.compiler_view().source.check_compiler_head(provider)'):
        c.require(text.count(marker)==1,'REAL_ORIGINAL_ROUTER_MANIFEST_EXACT_SOURCE_CURRENT_CLOCK_TARGET_AND_FINAL_HEAD_NOT_PERMISSION')
    c.require(all(marker not in text for marker in('SupportState::Verified','RegistryTrustState::SignatureVerified','ImportedSourcePackage::import',
        'commit_success(','WorkspaceTransaction::create','Command::','unsafe','Deserialize')),'NO_FABRICATED_SUPPORT_TRUST_REIMPORT_NATIVE_OR_COMMIT')


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'SOURCE_MANIFEST_COMPONENTS_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SOURCE_SEARCH_MANIFEST_COMPONENTS',steps=[],own_cpu_selection=selection,
        actual_Hangul_or_COM=False,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        trusted_registry_or_native_evidence=False,output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=q.json(prior.OUTPUT);sync=q.json(SYNC)
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='1061ad23466f2c7d57bd056439620384f82eb36dfbecd3f3b17b87610092e89c'
            and passed['cleanup']and passed['fresh_inputs']==passed['final_fresh_hashes']==750,'EXACT216_COMPILER_SOURCE_AND_TERMINAL_CURRENT_CLOSURE')
        c.require(q.snapshots[SYNC]['sha256']=='926184ba203ca22646e267973766784b33e113aac048ec1cd44f618e44a949ed'
            and sync['cleanup']and sync['fresh_inputs']==sync['final_fresh_hashes']==63,'EXACT217_COMPILER_DOC_SYNC_NOT_PRODUCT_EXECUTION')
        tested={p['path']:p for p in passed['source_pins']};documented={p['path']:p for p in sync['source_pins']}
        names=inventory(guard.check)
        for name in sorted(names):
            q.pin(name)
            if name not in NEW|CHANGED:
                expected_pin=documented.get(name,tested.get(name));c.require(expected_pin is not None and q.snapshots[name]==expected_pin,'ALL_OTHER_CURRENT_SOURCE_TESTS_FIXTURES_PROTECTIONS_AND_DOCS_UNCHANGED')
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        inverse(q,tested);cases=expected(q)
        print(json.dumps(dict(state='SOURCE_SEARCH_MANIFEST_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),new_cases=len(cases),all16_source_families=True,
            prior36_or_official249_reexecuted=False,synthetic_routing_evidence_not_trusted_registry=True)),flush=True)
        harness.run_one('twentysix_actual_source_plan_router_manifest_and_current_boundaries',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli',
            '--test','regex_replacement_product','--message-format=short','--',PREFIX,'--test-threads=1'],cases,guard,audit.environment(),row,observe_capture=base.snapshot)
        tools.good_step(row['steps'][-1],cases);q.finish();guard.check(force=True)
        row.update(state='PASS_SIXTEEN_FAMILY_SOURCE_ROUTER_EXECUTION_MANIFEST26_NOT_TRUSTED_REGISTRY_NATIVE_TRANSACTION_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,total_executed_cases=26,
            per_call_per_capability_routing_not_per_edit_catalog_replay=True,original_single_router_and_compiler_and_security_bodies_inverse_verified=True,
            prior36_compiler_cases_reexecuted=False,
            next_work='trusted_current_registry_target_and_source_protection_binding_then_durable_ingest_commit_CAS_idempotency_and_remaining_P09_contracts')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'SOURCE_MANIFEST_COMPONENTS_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_SOURCE_MANIFEST_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations','safe_error_variants')},
                'observation':{k:s.get('bounded_output_observation',{}).get(k)for k in('safe_warning_locations','short_error_locations','rust_error_codes','closed_nested_error_variants','closed_patch_codes')},
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
