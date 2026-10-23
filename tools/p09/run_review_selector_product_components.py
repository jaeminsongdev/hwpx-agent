"""Sixteen strict review-selector products plus20 original v5/v3 cases, one bounded binary."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_stored_review_selector_components as prior
harness,shared,c,a,audit=prior.harness,prior.shared,prior.c,prior.a,prior.audit
OUTPUT='implementation/p09/evidence/p09-361-review-selector-product-components099.v1.json'
SELECTOR='crates/product-cli/src/form_product_request/stored_source_search/selector.rs'
SEARCH=SELECTOR[:-3]+'/review.rs'
PARENT='crates/product-cli/src/form_product_request/stored_literal_replacement.rs'
LITERAL=PARENT[:-3]+'/selector.rs'
TARGET='crates/product-cli/tests/review_selector_product.rs'
WRAPPER='crates/product-cli/tests/review_selector_product/actual_import.rs'
TEST='crates/product-cli/tests/form_stored_provider/actual_import/review_selector_product.rs'
OLD_LITERAL='crates/product-cli/tests/form_stored_provider/actual_import/review_literal_product.rs'
OLD_SCOPE='crates/product-cli/tests/form_stored_provider/actual_import/source_scope_product.rs'
NEW={SEARCH,LITERAL,TARGET,WRAPPER,TEST};CHANGED={SELECTOR,PARENT}
PARSE_BRIDGE=('        Self::parse_value(Self::parse_object(raw)?,SOURCE_SCOPE_PRODUCT_REQUEST_SCHEMA)\n    }\n'
    '    fn parse_object(raw:&[u8])->Result<serde_json::Value,E> {\n')
VALUE_BRIDGE=('        Ok(value)\n    }\n    fn parse_value(value:serde_json::Value,schema:&str)->Result<Self,E> {\n')
SHAPE_HEADER='    pub(crate) fn shape(selector:&serde_json::Value)->Result<(bool,bool),E> {\n'
VALIDATE_HEADER='    pub(crate) fn validate_shape(&self,has_sections:bool,has_range:bool)->Result<(),E> {\n'


def inventory(check):return prior.inventory(check)|{TARGET,WRAPPER}


def inverse(q,old):
    text=q.text(SELECTOR)
    for current,previous in(('pub mod review;\n',''),('pub(crate) struct Scope {pub(crate) revision_id:','struct Scope {revision_id:'),
        ('    pub(crate) fn native(','    fn native('),('pub(crate) fn valid_sha(','fn valid_sha('),(PARSE_BRIDGE,''),(VALUE_BRIDGE,''),
        ('request.schema_version!=schema','request.schema_version!=SOURCE_SCOPE_PRODUCT_REQUEST_SCHEMA')):
        c.require(text.count(current)==1,'ONLY_INTERNAL_SELECTOR_REUSE_AND_PARSE_OBJECT_VALUE_EXTRACTION');text=text.replace(current,previous)
    start=text.index(SHAPE_HEADER);split=text.index(VALIDATE_HEADER,start);end=text.index('\n}\n#[derive(Deserialize,Serialize)]',split)
    shape=text[start+len(SHAPE_HEADER):split];validate=text[split+len(VALIDATE_HEADER):end]
    c.require(shape.endswith('    }\n')and validate.endswith('    }'),'EXACT_SHARED_SCOPE_METHOD_BOUNDARIES')
    shape=shape[:-len('    }\n')]
    c.require(shape.endswith('Ok((has_sections,has_range))\n'),'SCOPE_SHAPE_HAS_ORIGINAL_PRESENCE_RESULT_ONLY')
    shape=shape[:-len('Ok((has_sections,has_range))\n')]+'\n'
    shape=shape.replace('        let has_sections=','        let selector=value.get("selector").ok_or(E::Request)?;let has_sections=',1)
    validate=validate[:-len('    }')]
    c.require(validate.endswith('Ok(())\n'),'SHARED_SCOPE_VALIDATOR_ONLY_RETURNS_ORIGINAL_RESULT')
    validate=validate[:-len('Ok(())\n')]+'\n';validate=validate.replace('self.scope','request.selector.scope').replace('self.section_ids','request.selector.section_ids').replace('self.range','request.selector.range')
    text=text[:start]+text[end+1:]
    call='        let(has_sections,has_range)=Scope::shape(value.get("selector").ok_or(E::Request)?)?;\n'
    c.require(text.count(call)==1 and text.count('        request.selector.validate_shape(has_sections,has_range)?;\n')==1,'ONE_SHARED_SCOPE_CALL_AT_ORIGINAL_VALIDATION_POSITION')
    text=text.replace(call,shape).replace('        request.selector.validate_shape(has_sections,has_range)?;\n',validate)
    audit.inverse(text,old[SELECTOR],'WHOLE_V5_PARSE_SHAPES_VALUES_CANONICAL_PROFILE_AND_AUTH_BODY_EXACT_INVERSE')
    text=q.text(PARENT);c.require(text.count('pub mod selector;\n')==1,'ONE_NEW_LITERAL_SELECTOR_PROFILE_MODULE')
    audit.inverse(text.replace('pub mod selector;\n',''),old[PARENT],'WHOLE_V1_V2_V3_LITERAL_PARSER_VALUES_AND_AUTH_BODY_UNCHANGED')


def expected(q):
    groups=[]
    for path,module in((TEST,'review_selector_product'),(OLD_SCOPE,'source_scope_product'),(OLD_LITERAL,'review_literal_product')):
        groups.append({'actual_import::'+module+'::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(path))})
    c.require(tuple(map(len,groups))==(16,10,10),'EXACT_SIXTEEN_NEW_AND_TWENTY_V5_V3_ORIGINAL_IDENTITIES')
    return set().union(*groups)


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'REVIEW_SELECTOR_PRODUCT_IMMUTABLE_RUN_EXISTS');shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_REVIEW_SELECTOR_PRODUCT_COMPONENTS',steps=[],actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False,full_selector_or_native_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        previous=q.json(prior.OUTPUT)
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='7bfd4197c6ddab3ce115fc208da5fca5063a8762f9401e8ee3a8d6ede1f11740'
            and previous['state'].startswith('PASS_')and previous['total_executed_cases']==61 and previous['cleanup'],'EXACT_PREVIOUS_SIXTY_ONE_STORED_PASSES_RETAINED')
        old={p['path']:p for p in previous['source_pins']}
        old_names={n for n in old if n.startswith(('crates/','fixtures/'))or n in{'Cargo.toml','Cargo.lock','rust-toolchain.toml',prior.prior.base.prior.base.prior.prior.base.prior.prior.CAPTURE}}
        c.require(names==old_names|NEW,'EXACT_FIVE_NEW_PRODUCT_AND_FOCUSED_TEST_FILES')
        for name in names-NEW-CHANGED:c.require(q.snapshots[name]==old[name],'NO_CORE_STORED_SOURCE_HEAD_PROTECTION_OLD_PRODUCT_OR_TEST_CHANGE')
        inverse(q,old);cases=expected(q)
        print(json.dumps(dict(state='REVIEW_SELECTOR_PRODUCT_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),new_cases=16,affected_cases=20,retained_stored_cases=61,test_binaries=1)),flush=True)
        harness.run_one('sixteen_review_selector_products_and_twenty_original_v5_v3_cases',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli',
            '--test','review_selector_product','--','--test-threads=1'],cases,guard,audit.environment(),row,observe_capture=prior.prior.base.base.prior.prior.snapshot)
        c.require(inventory(guard.check)==names,'FINAL_REVIEW_SELECTOR_PRODUCT_SOURCE_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_REVIEW_SELECTOR_STRICT_SEARCH_V6_LITERAL_V4_SIXTEEN_NEW_TWENTY_AFFECTED_NOT_FULL_SELECTOR_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,new_product_cases=16,affected_cases=20,total_executed_cases=36,
            previous_fifty_two_core_and_sixty_one_stored_cases_reexecuted=False,original_selector_shape_value_and_legacy_parser_bodies_inverse_verified=True,
            current_write_source_acl_aead_head_and_final_consumer_shared=True,query_lowering_or_inventory_not_replayed_on_retained_delivery=True,
            new_strict_product_search_schema='hwpx-agent.product-source-search-request/v6',new_strict_product_literal_schema='hwpx-agent.product-literal-replacement-request/v4',
            next_work='Selector_result_navigation_and_style_control_filter_contract_completion')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'REVIEW_SELECTOR_PRODUCT_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_REVIEW_SELECTOR_PRODUCT_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','diagnostics','locations','summaries','tests','panic_locations','safe_error_variants')}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
