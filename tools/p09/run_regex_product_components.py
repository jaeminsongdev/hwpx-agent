"""Thirteen regex candidate products plus16 affected original v4/v6 products, one CPU2 bounded binary."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_regex_replacement_focused as prior
harness,shared,c,a,audit=prior.base.harness,prior.shared,prior.c,prior.a,prior.audit
OUTPUT='implementation/p09/evidence/p09-361-regex-product-components116.v1.json'
SERVICE='crates/product-cli/src/form_stored_provider/actual_import/literal_search_output.rs';STORED=SERVICE[:-3]+'/regex.rs'
PARENT='crates/product-cli/src/form_product_request/stored_literal_replacement.rs';PRODUCT=PARENT[:-3]+'/regex.rs';SELECTOR=PARENT[:-3]+'/selector.rs'
TARGET='crates/product-cli/tests/regex_replacement_product.rs';WRAPPER='crates/product-cli/tests/regex_replacement_product/actual_import.rs'
TEST='crates/product-cli/tests/form_stored_provider/actual_import/regex_replacement_product.rs'
OLD='crates/product-cli/tests/form_stored_provider/actual_import/review_selector_product.rs'
NEW={STORED,PRODUCT,TARGET,WRAPPER,TEST};CHANGED={SERVICE,PARENT,SELECTOR}
HELPER=('pub(super) fn parse_selector_object(raw:&[u8])->Result<serde_json::Value,E> {\n'
    '    if raw.is_empty()||raw.len()>LITERAL_REPLACEMENT_PRODUCT_MAX_REQUEST_BYTES{return Err(E::Limit);}\n'
    '    let mut parser=serde_json::Deserializer::from_slice(raw);let _=UniqueJson::deserialize(&mut parser).map_err(|_|E::Request)?;parser.end().map_err(|_|E::Request)?;\n'
    '    let value:serde_json::Value=serde_json::from_slice(raw).map_err(|_|E::Request)?;\n'
    '    if !value.is_object()||!["selector","operation"].iter().all(|key|value.get(key).is_some_and(serde_json::Value::is_object)){return Err(E::Request);}\n'
    '    Ok(value)\n}\n')
ORIGINAL=('        if raw.is_empty()||raw.len()>LITERAL_REPLACEMENT_PRODUCT_MAX_REQUEST_BYTES{return Err(E::Limit);}\n'
    '        let mut parser=serde_json::Deserializer::from_slice(raw);let _=UniqueJson::deserialize(&mut parser).map_err(|_|E::Request)?;parser.end().map_err(|_|E::Request)?;\n'
    '        let mut value:serde_json::Value=serde_json::from_slice(raw).map_err(|_|E::Request)?;\n'
    '        if !value.is_object()||!["selector","operation"].iter().all(|key|value.get(key).is_some_and(serde_json::Value::is_object)){return Err(E::Request);}\n')


def inventory(check):return prior.inventory(check)|{TARGET,WRAPPER}


def inverse(q,old):
    for name in(SERVICE,PARENT):
        text=q.text(name);c.require(text.count('pub mod regex;\n')==1,'ONLY_ADDITIVE_REGEX_MODULE_IN_OLD_LITERAL_ROOT')
        audit.inverse(text.replace('pub mod regex;\n',''),old[name],'WHOLE_ORIGINAL_LITERAL_STORED_OWNERSHIP_ACCESS_AND_PRODUCT_SCHEMAS_UNCHANGED')
    text=q.text(SELECTOR);c.require(text.count(HELPER)==1 and text.count('        let mut value=parse_selector_object(raw)?;\n')==1,'ONE_EXACT_ORIGINAL_STRICT_SELECTOR_OBJECT_HELPER')
    audit.inverse(text.replace(HELPER,'').replace('        let mut value=parse_selector_object(raw)?;\n',ORIGINAL),old[SELECTOR],
        'WHOLE_ORIGINAL_V4_SELECTOR_POLICY_CANONICAL_HASH_AND_AUTHORIZATION_BODY_EXACT_INVERSE')
    stored=q.text(STORED);c.require(stored.count('self.fresh_source_reconstructed(provider,now)?')==1 and stored.count('proof.lower_review_selector_regex_candidate(&self.imported,query,selector,policy,replacement,run_policy,limits,writer)?')==1
        and stored.count('source:LiteralSource::Owned(Box::new(self))')==1 and stored.count('let fresh=self.source.fresh_source(provider,now)?;')==1,
        'ONE_ORIGINAL_PROOF_LOWERING_AND_SOURCE_OWNERSHIP_TRANSFER_NO_REIMPORT_OR_REPLAY')
    product=q.text(PRODUCT);c.require(product.count('super::selector::parse_selector_object(raw)')==1 and product.count('validate_regex_replacement_template(&request.operation.replacement)')==1,
        'EXACT_EXISTING_STRICT_OBJECT_PARSER_AND_PURE_TEMPLATE_PREFLIGHT_SHARED')


def expected(q):
    groups=[]
    for path,module in((TEST,'regex_replacement_product'),(OLD,'review_selector_product')):
        groups.append({'actual_import::'+module+'::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(path))})
    c.require(tuple(map(len,groups))==(13,16),'EXACT_THIRTEEN_NEW_SIXTEEN_AFFECTED_PRODUCT_IDENTITIES');return set().union(*groups)


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'REGEX_PRODUCT_IMMUTABLE_RUN_EXISTS');selection=prior.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_REGEX_PRODUCT_COMPONENTS',steps=[],actual_Hangul_or_COM=False,own_cpu_selection=selection,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False,zero_width_native_or_full_product_qualification_added=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        previous=q.json(prior.OUTPUT)
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='478e21869b593aeefd331fc7d115a6d214151e6fdac901a39bec968751ca86eb'
            and previous['state'].startswith('PASS_')and previous['total_distinct_core_cases']==89 and previous['actual_current_cases']==17 and previous['cleanup'],'EXACT_PREVIOUS_REGEX_CORE_RESULTS_AND_CLEANUP_RETAINED')
        old={p['path']:p for p in previous['source_pins']};old_names={n for n in old if n.startswith(('crates/','fixtures/'))or n in{'Cargo.toml','Cargo.lock','rust-toolchain.toml',prior.base.prior.prior.base.CAPTURE}}
        c.require(names==old_names|NEW,'EXACT_FIVE_NEW_REGEX_STORED_PRODUCT_AND_TEST_FILES')
        for name in names-NEW-CHANGED:c.require(q.snapshots[name]==old[name],'NO_REGEX_CORE_WORK_GUARD_CAPTURE_LITERAL_WRITER_EXISTING_TEST_OR_FIXTURE_INPUT_CHANGE')
        inverse(q,old);cases=expected(q)
        print(json.dumps(dict(state='REGEX_PRODUCT_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),new_cases=13,affected_cases=16,test_binaries=1,one_cpu_mask=4)),flush=True)
        harness.run_one('thirteen_regex_and_sixteen_original_selector_products',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli',
            '--test','regex_replacement_product','--','--test-threads=1'],cases,guard,audit.environment(),row,observe_capture=prior.base.prior.snapshot)
        limits=row['steps'][0]['owned_job']['limits_readback'];c.require(limits['verified']and limits['affinity_mask']==4 and limits['cpu_hard_cap_machine_percent']==6.25 and limits['priority_class']==16384,
            'ONE_CPU2_AND_ORIGINAL_HARD_CPU_CAP_PRIORITY_VERIFIED')
        c.require(inventory(guard.check)==names,'FINAL_REGEX_PRODUCT_SOURCE_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_REGEX_PRODUCT_THIRTEEN_NEW_SIXTEEN_AFFECTED_NOT_ZERO_WIDTH_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_product_cases=13,affected_cases=16,total_executed_cases=29,previous_eighty_nine_core_and_unaffected_suites_reexecuted=False,
            original_literal_root_and_strict_v4_selector_inverse_verified=True,one_call_local_whole_proof_capture_compiler_and_owned_transfer_without_reimport=True,
            current_output_does_not_repeat_query_capture_or_lowering=True,template_and_expansion_bindings_kept_distinct=True,
            next_work='Exact_zero_width_source_insertions_then_remaining_style_control_conversion_and_full_transaction_native_contract')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'REGEX_PRODUCT_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_REGEX_PRODUCT_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','diagnostics','locations','summaries','tests','panic_locations','safe_error_variants')}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
