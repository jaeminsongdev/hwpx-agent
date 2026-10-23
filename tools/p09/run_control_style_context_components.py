"""Control style uncertainty: new8 source/new6 product plus affected18/20, serial only."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_resolved_style_product_components as prior
harness,shared,c,a,audit,snapshot=prior.harness,prior.shared,prior.c,prior.a,prior.audit,prior.snapshot
OUTPUT='implementation/p09/evidence/p09-361-control-style-context-components154.v1.json'
CORE='crates/hwpx-package/src/document_import/search/inspection/definitions/resolved.rs'
SOURCE_PARENT='crates/hwpx-package/tests/document_import_resolved_style_search.rs'
SOURCE_TEST='crates/hwpx-package/tests/resolved_style_control_context.rs'
PRODUCT_PARENT=prior.TEST
PRODUCT_TEST='crates/product-cli/tests/form_stored_provider/actual_import/resolved_style_control_product.rs'
MODEL='fixtures/target-build/official-source-cache/hwpx-owpml-model-save-145338/OWPML/Class/Para/ctrl.cpp'
OBSERVATION='implementation/p09/evidence/p09-361-historical-style-observation153.v1.json'
NEW={SOURCE_TEST,PRODUCT_TEST};CHANGED={CORE,SOURCE_PARENT,PRODUCT_PARENT}


def inventory(check):return prior.inventory(check)|NEW|{MODEL}


def expected(q):
    source=prior.prior.expected(q)
    product=prior.expected(q)
    new_source=re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(SOURCE_TEST))
    new_product=re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(PRODUCT_TEST))
    c.require(len(source)==18 and len(product)==20 and len(new_source)==len(set(new_source))==8
        and len(new_product)==len(set(new_product))==6,'EXACT_EIGHT_SOURCE_SIX_PRODUCT_NEW_AND_38_AFFECTED_IDENTITIES')
    return source|{'control_context::'+n for n in new_source},product|{'actual_import::regex_replacement_product::resolved_style_v9::control_context::'+n for n in new_product}


def inverse(q,old):
    text=q.text(CORE);start=text.index('    fn unresolved_control_contexts(');end=text.index('    /// The caller supplies segments',start)
    helper=text[start:end]
    c.require('for (i,node) in xml.elements().iter().enumerate()'in helper and 'let parent=match node.parent()'in helper
        and 'selected.into_iter().peekable()'in helper and 'source_parts.get(path)'in helper
        and 'parts.entry(resolved.part().path().as_str())'in helper and 'semantic_value()'not in helper,
        'ONE_PART_CONTEXT_PASS_SORTED_SELECTION_AND_BORROWED_PATHS_NO_PRECEDENCE_OR_TARGET_DOMAIN_INFERENCE')
    text=text[:start]+text[end:]
    changes=(('filter.validate()?;let control_contexts=self.unresolved_control_contexts(segments)?;','filter.validate()?;'),
        ('            let uncertain=refs.text.is_some()||control_contexts.contains(&segment);\n            if uncertain{coverage.unresolved_text_style_segments+=1;}',
            '            if refs.text.is_some(){coverage.unresolved_text_style_segments+=1;}'),
        ('refs.run.is_some()&&!uncertain','refs.run.is_some()&&refs.text.is_none()'))
    for current,original in changes:
        c.require(text.count(current)==1,'ONE_CONTEXTUAL_RESOLUTION_CONDITION_CHANGE');text=text.replace(current,original)
    audit.inverse(text,old[CORE],'WHOLE_ORIGINAL_FILTER_COVERAGE_SHAPE_AND_DIRECT_DEFINITION_MEANING_PRESERVED_EXCEPT_CONTEXT_GUARD')
    for name,marker in[(SOURCE_PARENT,'#[path="resolved_style_control_context.rs"] mod control_context;\n'),
        (PRODUCT_PARENT,'#[path="resolved_style_control_product.rs"] mod control_context;\n')]:
        text=q.text(name);c.require(text.count(marker)==1 and text.endswith(marker),'ONE_APPENDED_CONTEXT_TEST_MODULE')
        audit.inverse(text.replace(marker,''),old[name],'ALL_ORIGINAL18_SOURCE_AND20_PRODUCT_TEST_BODIES_AND_ASSERTIONS_UNCHANGED')
    model=q.text(MODEL)
    c.require(q.snapshots[MODEL]['sha256']=='a928569df0b890d8a58470a70a1501520bfb4d8af121df58eeb1fd8b9e0eed1d'
        and 'CCtrl::CCtrl()'in model and 'L"charStyleIDRef"'in model,'REVIEWED_PRIMARY_CONTROL_ATTRIBUTE_STORAGE_NOT_CASCADE_RULE')


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'CONTROL_CONTEXT_IMMUTABLE_RUN_EXISTS')
    selection=prior.prior.prior.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_CONTROL_STYLE_CONTEXT_COMPONENTS',steps=[],actual_Hangul_or_COM=False,own_cpu_selection=selection,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False,full_effective_cascade_or_visibility_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        baseline=q.json(prior.OUTPUT)
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='5e421a1580b6b0b0830a685eb7cd0cdcf427d886762a6fe07964a6a4ec33a33d'
            and baseline['state']=='PASS_RESOLVED_STYLE_TWENTY_PRODUCTS_NOT_FULL_CASCADE_NATIVE_OR_GATE'and baseline['cleanup']
            and baseline['fresh_inputs']==baseline['final_fresh_hashes']==639 and baseline['new_product_cases']==20,
            'EXACT_V9_PRODUCT_BASELINE_WITH_PRIOR18_SOURCE_RETAINED')
        old={p['path']:p for p in baseline['source_pins']}
        old_names={n for n in old if n.startswith(('crates/','fixtures/'))or n in{'Cargo.toml','Cargo.lock','rust-toolchain.toml',prior.prior.prior.CAPTURE}}
        c.require(names==old_names|NEW|{MODEL},'EXACT_TWO_NEW_CONTEXT_TEST_FILES_AND_ONE_ADDED_REVIEWED_MODEL')
        for name in names-NEW-CHANGED-{MODEL}:c.require(q.snapshots[name]==old[name],'NO_OTHER_SOURCE_PRODUCT_SECURITY_WRITER_OR_PRIOR_SUITE_CHANGE')
        inverse(q,old);source,product=expected(q)
        print(json.dumps(dict(state='CONTROL_CONTEXT_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),source_cases=len(source),product_cases=len(product),retained_unrelated_products=104,one_cpu_mask=4)),flush=True)
        harness.run_one('eight_new_and_eighteen_affected_source_context_cases',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package',
            '--test','document_import_resolved_style_search','--message-format=short','--',*sorted(source),'--exact','--test-threads=1'],source,guard,audit.environment(),row,observe_capture=snapshot)
        harness.run_one('six_new_and_twenty_affected_v9_product_context_cases',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-agent-cli',
            '--test','regex_replacement_product','--message-format=short','--',*sorted(product),'--exact','--test-threads=1'],product,guard,audit.environment(),row,observe_capture=snapshot)
        for step in row['steps']:
            limits=step['owned_job']['limits_readback'];c.require(limits['verified']and limits['affinity_mask']==4 and limits['cpu_hard_cap_machine_percent']==6.25 and limits['priority_class']==16384,
                'ORIGINAL_ONE_CPU2_HARD_CAP_AND_PRIORITY_FOR_EACH_SERIAL_JOB')
        c.require(inventory(guard.check)==names,'FINAL_CONTROL_CONTEXT_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_CONTROL_CONTEXT_14_NEW_38_AFFECTED_NOT_CASCADE_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_source_cases=8,new_product_cases=6,affected_source_cases=18,affected_product_cases=20,total_executed_cases=52,
            unrelated104_products_reexecuted=False,source_filter_receipt_shape_and_previous_test_bodies_inverse_verified=True,
            control_contexts_share_one_part_map_not_per_match_ancestor_walk=True,native_inheritance_or_target_domain_inferred=False,
            next_work='Qualified_native_text_and_control_style_target_precedence_missing_axes_visibility_then_full_scope_transaction_contract')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'CONTROL_STYLE_CONTEXT_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_CONTROL_CONTEXT_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations','safe_error_variants')},
                'observation':{k:s.get('bounded_output_observation',{}).get(k)for k in('safe_warning_locations','short_error_locations','rust_error_codes')},
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
