"""Actual source literal replacement and current stored output, no Native or publication."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_search_scalar_patch_components as scalar
base,harness,shared,c,a=scalar.base,scalar.harness,scalar.shared,scalar.c,scalar.a
OUTPUT='implementation/p09/evidence/p09-361-literal-search-output-recovery068.v1.json'
FAILED='implementation/p09/evidence/p09-361-literal-search-output-components067.v1.json'
RECOVERED='literal_replacement_multiple_occurrences_share_leaf_delete_and_reject_unqualified_control_text'
OLD_FAILED='literal_replacement_multiple_occurrences_share_leaf_and_support_deletion_and_semantic_cr'
PRIOR='implementation/p09/evidence/p09-361-search-scalar-linear-recovery065.v1.json'
TEST='crates/hwpx-package/tests/document_import_search_replacement.rs'
PRODUCT='crates/product-cli/tests/form_stored_provider/actual_import/literal_search_output.rs'
SEARCH='crates/hwpx-package/src/document_import/search.rs'
PROTECTION='crates/hwpx-package/src/document_import/structure/caption_text_batch.rs'
STORED='crates/product-cli/src/form_stored_provider/actual_import.rs'
MODULE='crates/product-cli/tests/form_stored_provider/actual_import.rs'
NEW={TEST,PRODUCT,'crates/hwpx-package/src/document_import/search/replacement.rs',
    'crates/hwpx-package/src/document_import/search/replacement/output.rs',
    'crates/product-cli/src/form_stored_provider/actual_import/literal_search_output.rs'}
TEXT_FLOW='crates/hwpx-package/src/text_flow.rs'
CHANGED={SEARCH,PROTECTION,STORED,MODULE,TEXT_FLOW}


def inventory(check):return scalar.inventory(check)|{TEST}


def inverse(q,old):
    for path,addition in ((SEARCH,'pub mod replacement;\n'),(STORED,'pub mod literal_search_output;\n'),
        (MODULE,'#[path = "actual_import/literal_search_output.rs"]\nmod literal_search_output;\n')):
        text=q.text(path);c.require(text.count(addition)==1,'ONLY_ADDITIVE_LITERAL_SEARCH_MODULE');base.inverse(text.replace(addition,''),old[path],'ORIGINAL_SEARCH_PROVIDER_AND_TEST_MODULE_BODIES_UNCHANGED')
    text=q.text(PROTECTION);current='pub(in crate::document_import) fn observed_protection(';prior='pub(super) fn observed_protection('
    c.require(text.count(current)==1,'ONE_CRATE_INTERNAL_EXISTING_PROTECTION_BRIDGE');base.inverse(text.replace(current,prior),old[PROTECTION],'ORIGINAL_PROTECTION_AND_CAPTION_WRITER_BODY_UNCHANGED')
    text=q.text(TEXT_FLOW);current='pub(crate) fn validate_text(';prior='fn validate_text('
    c.require(text.count(current)==1,'ONE_CRATE_INTERNAL_ORIGINAL_PLAIN_TEXT_POLICY_BRIDGE');base.inverse(text.replace(current,prior),old[TEXT_FLOW],'ORIGINAL_TEXT_FLOW_READER_WRITER_AND_POLICY_BODY_UNCHANGED')


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'LITERAL_OUTPUT_IMMUTABLE_RUN_EXISTS');shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_LITERAL_SEARCH_OUTPUT_COMPONENTS',steps=[],actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False,full_literal_search_product_or_native_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        prior=q.json(PRIOR);c.require(q.snapshots[PRIOR]['sha256']=='e0ec9bcd90899043bd2fedc3fcef2466430f18d2dbf31027d9ed1168a45af715'
            and prior['state'].startswith('PASS_')and prior['cleanup'],'EXACT_PRIOR_SCALAR_PATCH_PASS')
        old={p['path']:p for p in prior['source_pins']};old_names={n for n in old if n.startswith(('crates/','fixtures/'))or n in {'Cargo.toml','Cargo.lock','rust-toolchain.toml',scalar.CAPTURE}}
        c.require(names==old_names|NEW,'EXACT_FIVE_NEW_LITERAL_LOWERING_AND_TEST_FILES')
        for name in names-NEW-CHANGED:c.require(q.snapshots[name]==old[name],'NO_UNRELATED_SOURCE_SEARCH_SCALAR_TEST_OR_HEADER_CHANGE')
        inverse(q,old)
        failed=q.json(FAILED);c.require(q.snapshots[FAILED]['sha256']=='d2c2cc523c2aca5bb33053068bd7c76bcb182aead3d9db61f7008ba9bae4a79d'
            and failed['state']=='FAILED_LITERAL_SEARCH_OUTPUT_COMPONENTS'and failed['cleanup']and len(failed['steps'])==1,'ORIGINAL_NINE_PASSES_ONE_UNADMITTED_CR_FIXTURE_FAILURE_PRESERVED')
        initial={p['path']:p for p in failed['source_pins']};lower='crates/hwpx-package/src/document_import/search/replacement.rs'
        for name in names-{TEST,TEXT_FLOW,lower}:c.require(q.snapshots[name]==initial[name],'NO_OTHER_LITERAL_OUTPUT_INPUT_CHANGE_DURING_POLICY_RECOVERY')
        text=q.text(lower);addition='        crate::text_flow::validate_text(replacement).map_err(|_|E::Value)?;\n'
        c.require(text.count(addition)==1,'ONLY_EXISTING_TYPED_PLAIN_TEXT_POLICY_ADDED');base.inverse(text.replace(addition,''),initial[lower],'ORIGINAL_LITERAL_COMPILER_BODY_UNCHANGED_AFTER_INPUT_FAILURE')
        tests=q.text(TEST);start=tests.index('fn '+RECOVERED+'(');end=tests.index('\n}\n',start)+len('\n}\n')
        original=('fn '+OLD_FAILED+'()->TestResult {\n'
            '    let b=fixture::package("<hp:p id=\'1\'><hp:run><hp:t>K&#38;K\\r\\nTAIL</hp:t></hp:run></hp:p>")?;let f=forms(&b,"multiple")?;\n'
            '    let out=replace(&f,&b,"K","X\\r")?;assert_eq!(out.receipt().matched_occurrences,2);assert_eq!(out.receipt().changes.len(),1);\n'
            '    assert!(out.with_verified_bytes(section)??.contains("X&#13;&#38;X&#13;\\r\\nTAIL"));\n'
            '    assert!(replace(&f,&b,"K","")?.with_verified_bytes(section)??.contains("<hp:t>&#38;\\r\\nTAIL</hp:t>"));Ok(())\n}\n')
        base.inverse(tests[:start]+original+tests[end:],initial[TEST],'ORIGINAL_NINE_PASSED_TEST_BODIES_AND_OTHER_ASSERTIONS_UNCHANGED')
        core=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(TEST)))
        product={'actual_import::literal_search_output::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(PRODUCT))}
        c.require(len(core)==10 and len(product)==6,'EXACT_TEN_CORE_AND_SIX_STORED_LITERAL_OUTPUT_CASES')
        statuses=dict(failed['steps'][0]['tests']);c.require(set(statuses)==(core-{RECOVERED})|{OLD_FAILED}
            and statuses[OLD_FAILED]=='FAILED'and all(s=='ok'for n,s in statuses.items()if n!=OLD_FAILED),'EXACT_NINE_ORIGINAL_PASSES_RETAINED')
        env=base.environment();common=[harness.CARGO,'test','--offline','--locked','-j','1']
        print(json.dumps(dict(state='LITERAL_OUTPUT_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),new_core_cases=10,new_stored_cases=6,original_search_and_writer_bodies_preserved=True)),flush=True)
        harness.run_one('one_admitted_multi_match_and_typed_control_rejection_case',common+['-p','hwpx-package','--test','document_import_search_replacement','--',RECOVERED,'--exact','--test-threads=1'],{RECOVERED},guard,env,row)
        harness.run_one('six_current_stored_literal_candidate_boundary_cases',common+['-p','hwpx-agent-cli','--test','form_stored_provider','--',*sorted(product),'--exact','--test-threads=1'],product,guard,env,row)
        c.require(inventory(guard.check)==names,'FINAL_LITERAL_OUTPUT_SOURCE_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_ACTUAL_LITERAL_SEARCH_OUTPUT_ONE_CORE_NINE_RETAINED_SIX_STORED_NOT_FULL_PROTECTION_PRODUCT_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,new_core_cases=1,prior_core_passes_preserved=9,new_stored_cases=6,total_executed_cases=7,distinct_validated_cases=16,
            original_search_provider_protection_and_writer_bodies_inverse_verified=True,field_cached_text_edits_qualified=False,
            mixed_atoms_or_ambiguous_NFC_edits_qualified=False,actual_candidate_output_semantic_readback=True,source_reconstruction_once_per_prepare=True,
            prior_search_and_patch_tests_reexecuted=False,idempotency_key_claimed=False,command_line_or_server_route_added=False)
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'LITERAL_OUTPUT_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_LITERAL_OUTPUT_RESOURCE_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','diagnostics','locations','summaries','tests','panic_locations','safe_error_variants')}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
