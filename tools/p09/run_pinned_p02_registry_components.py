"""Actual preserved P02 Ed25519 evidence consumer plus before-source search policy denial; no promotion."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_source_protection_manifest_recovery as prior
base=prior.base
harness,shared,c,a,audit,tools=base.harness,base.shared,base.c,base.a,base.audit,base.tools
OUTPUT='implementation/p09/evidence/p09-361-pinned-p02-registry-components225.v1.json'
DRIVER='tools/p09/run_pinned_p02_registry_components.py'
DOC_BASE='implementation/p09/evidence/p09-361-source-protection-manifest-sync224.v1.json'
ROOT=base.base.MODEL
MODEL=ROOT[:-3]+'/p02_registry.rs'
DECODER=MODEL[:-3]+'/base64.rs'
UNIT=MODEL[:-3]+'/tests.rs'
PARENT=base.prior.TEST
TEST='crates/product-cli/tests/form_stored_provider/actual_import/pinned_p02_registry_product.rs'
FIXTURE='crates/product-cli/tests/support/pinned_p02_registry_fixture.rs'
NEW={MODEL,DECODER,UNIT,TEST,FIXTURE,DRIVER}
CHANGED={ROOT,PARENT}
MATERIALS={
    'implementation/p02/evidence/signing-runs/7b63d0ede07ea116e64d084fa00015a0fefb4ec3/signed-registry.json':'97c86645a4bf0696474cb6815699a2e4b012f650ae09ef81c582b672580b85e4',
    'implementation/p02/trust/p02-current-pc-local-trust-policy.json':'c96c6f4d4eddecd62dfb4c95badc8f1693a3e4d05c3b3dbc96bf26850212054c',
    'implementation/p02/trust/p02-current-pc-local-ed25519-public.pem':'838f7ce354cb2e284ca8b1e108c4234481b66fdfc0c9d415de43dc7cd3da57f5'}
EXPLANATION={'tools/p02/schemas/signed-registry-envelope-v1.schema.json','tools/p02/schemas/registry-trust-policy-v1.schema.json',
    'tools/p02/registry_signing.py','implementation/p02/P02-09_REPORT.md','protocol/migrations/p02-signed-registry-to-p10-execution-bundle-v1.md'}
UNIT_PREFIX='form_product_request::stored_operations::compiled_search::p02_registry::tests::'
PREFIX=base.prior.PREFIX+'p02_registry_v1::'


def inventory(check):return prior.inventory(check)|NEW|set(MATERIALS)|EXPLANATION|{'tools/p09/run_source_protection_manifest_sync.py','protocol/migrations/p09-source-protection-signals-v1.md'}


def expected(q):
    units=re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(UNIT));products=re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(TEST))
    c.require(len(units)==len(set(units))==12 and len(products)==len(set(products))==6,'EXACT12_CRYPTO_EVIDENCE_AND6_ACTUAL_SEARCH_POLICY_CASES')
    return{UNIT_PREFIX+n for n in units},{PREFIX+n for n in products}


def inverse(q,old):
    text=q.text(ROOT);marker='pub mod p02_registry;\n';c.require(text.count(marker)==1,'ONE_P09_REGISTRY_CONSUMER_CHILD')
    audit.inverse(text.replace(marker,''),old[ROOT],'ENTIRE_ORIGINAL_SOURCE_COMPILER_SOURCE_OWNER_BINDINGS_LIMITS_BYTE_DELIVERY_AND_ROUTE_DENIAL_UNCHANGED')
    text=q.text(PARENT);marker='#[path="pinned_p02_registry_product.rs"]mod p02_registry_v1;\n'
    c.require(text.count(marker)==1 and text.endswith(marker),'ONE_APPENDED_REGISTRY_PRODUCT_TEST_CHILD')
    audit.inverse(text.replace(marker,''),old[PARENT],'ALL26_MANIFEST_AND8_PROTECTION_PRODUCTS_AND_FIXTURES_UNCHANGED')
    text=q.text(MODEL);uncommented=re.sub(r'//[^\n]*','',text)
    for marker in('pin(input.policy,64*1024,POLICY_SHA)?','pin(input.public_key,64*1024,KEY_SHA)?','pin(input.envelope,MAX_ENVELOPE,ENVELOPE_SHA)?',
        'UnparsedPublicKey::new(&ED25519,&der[12..]).verify(payload,signature)','let mut claims=BTreeMap::new()',
        'if claims.len()!=original.len()','registry.require_routing()?;Ok(Self::prepare_compiled_search_json',
        'signature_verified:true,routing_enabled:false,execution_authority:false,runtime_probe_reexecuted:false,current_installed_target_observed:false'):
        c.require(text.count(marker)==1,'ACTUAL_PINNED_KEY_SIGNATURE_EMBEDDED_REGISTRY_COVERAGE_AND_DISABLED_SCOPE_BEFORE_SOURCE')
    c.require(all(marker not in uncommented for marker in('SupportState::Verified','RegistryTrustState::SignatureVerified','RouteContext::new',
        'WorkspaceTransaction::create','commit_success(','Command::','std::fs::','std::process::')),'NO_ROUTE_PROMOTION_RAW_COMMAND_FILE_IO_NATIVE_OR_COMMIT_IN_CONSUMER')
    c.require('private_key'not in q.text(FIXTURE),'FIXED_FIXTURE_READER_NEVER_OPENS_PRIVATE_SIGNING_KEY')


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'PINNED_REGISTRY_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_PINNED_P02_REGISTRY_COMPONENTS',steps=[],own_cpu_selection=selection,
        actual_Hangul_or_COM=False,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        private_key_read=False,registry_or_runtime_support_promoted=False,output_ingest_commit_or_publication=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=q.json(prior.OUTPUT);docs=q.json(DOC_BASE)
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='a8ab120602e26510ce6e106761a89f79b4d1a12dd855b741886339c32eb42264'
            and passed['cleanup']and passed['fresh_inputs']==passed['final_fresh_hashes']==764,'EXACT223_CURRENT_SOURCE_PROTECTION44_AND_TERMINAL_CLOSURE')
        c.require(q.snapshots[DOC_BASE]['sha256']=='59bccb0cfdc08137ed9e73f030af798adea04a7a9f87b74c0033c439401e929b'
            and docs['cleanup']and docs['fresh_inputs']==docs['final_fresh_hashes']==26,'EXACT224_CURRENT_PROTECTION_DOCS')
        old={p['path']:p for p in passed['source_pins']};documented={p['path']:p for p in docs['source_pins']};names=inventory(guard.check)
        for name in sorted(names):
            q.pin(name)
            if name in MATERIALS:c.require(q.snapshots[name]['sha256']==MATERIALS[name],'EXACT_PRESERVED_P02_ORIGINAL_PUBLIC_TRUST_AND_SIGNED_EVIDENCE')
            elif name not in NEW|CHANGED|EXPLANATION:
                pin=documented.get(name,old.get(name));c.require(pin is not None and q.snapshots[name]==pin,'ALL_OTHER_SOURCE_CORE_PROTECTION_COMPILER_PRODUCTS_TESTS_FIXTURES_AND_DOCS_UNCHANGED')
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        inverse(q,old);units,products=expected(q)
        print(json.dumps(dict(state='PINNED_P02_REGISTRY_CRYPTO_AND_POLICY_PREFLIGHT',inputs=len(q.snapshots),new_crypto_cases=len(units),new_product_cases=len(products),
            actual_private_signed_original_bound=True,private_key_read=False,old44_compiler36_and_official249_reexecuted=False)),flush=True)
        harness.run_one('twelve_actual_pinned_p02_crypto_and_historical_claim_tests',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli',
            '--lib','--message-format=short','--',UNIT_PREFIX,'--test-threads=1'],units,guard,audit.environment(),row,observe_capture=base.base.snapshot)
        tools.good_step(row['steps'][-1],units)
        harness.run_one('six_actual_registry_bound_before_source_search_policy_tests',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli',
            '--test','regex_replacement_product','--message-format=short','--',PREFIX,'--test-threads=1'],products,guard,audit.environment(),row,observe_capture=base.base.snapshot)
        tools.good_step(row['steps'][-1],products);q.finish();guard.check(force=True)
        row.update(state='PASS_ACTUAL_PINNED_P02_CRYPTO12_SEARCH_POLICY6_NOT_CURRENT_NATIVE_ROUTE_TRANSACTION_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,total_executed_cases=18,
            actual_p02_signature_verified_by_ring=True,signed_historical_claims=536,execution_routes_enabled=0,
            source_work_denied_before_original_preparation=True,old44_compiler36_and_official249_reexecuted=False,
            next_work='actual_qualified_P09_target_registry_and_native_protection_not_P02_promotion_then_durable_ingest_commit_CAS_idempotency_and_remaining_P09_contracts')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'PINNED_P02_REGISTRY_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_PINNED_REGISTRY_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations','safe_error_variants')},
                'observation':{k:s.get('bounded_output_observation',{}).get(k)for k in('safe_warning_locations','short_error_locations','rust_error_codes','closed_nested_error_variants','closed_patch_codes')},
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
