"""Definition-search scoped source/result/docs closure, never Cargo or Native replay."""
import hashlib,json,re,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_search_definition_components as base
shared,c,a=base.shared,base.c,base.a
ROOT='implementation/p09/evidence/p09-361-'
OUTPUT=ROOT+'search-definition-sync055.v1.json'
PASSED=ROOT+'search-definition-recovery054.v1.json'
FAILED=ROOT+'search-definition-components051.v1.json'
OLD=ROOT+'search-inspection-components048.v1.json'
NEW={'crates/hwpx-package/src/document_import/search/inspection/definitions.rs',base.TEST,
    'crates/hwpx-package/tests/support/search_definition_fixture.rs'}
CHANGED={base.CATALOG,'crates/hwpx-package/src/document_import/search.rs','crates/hwpx-package/src/document_import/search/inspection.rs',
    'crates/product-cli/src/form_stored_provider/actual_import/source_search.rs','crates/product-cli/src/form_product_request/stored_source_search.rs',base.PRODUCT}
DOCS=('CURRENT_STATE.md','implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md',
    'protocol/migrations/p09-source-search-inspection-v2.md','protocol/migrations/p09-source-definition-style-search-v3.md')


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'DEFINITION_SYNC_IMMUTABLE_RUN_EXISTS');shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_SEARCH_DEFINITION_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check)
        passed,failed,old=q.json(PASSED),q.json(FAILED),q.json(OLD)
        for name,sha in ((PASSED,'5045862a5e3285136f8e3fdb9e9f2fd84139258e46cf31abe78207588a579766'),
            (FAILED,'d26c35187ecbea3e9a63e307decb6ed15b0b2d65057ae25ade5cf84af787adda'),
            (OLD,'25f6409f12938e9706e53adb2f9a518d3e1213102287a03f3fdd42e4c673b5c9')):
            c.require(q.snapshots[name]['sha256']==sha,'EXACT_DEFINITION_RESULT_AND_PRESERVED_BASELINES')
        c.require(passed['state']=='PASS_TYPED_STYLE_DEFINITIONS_NINE_CORE_ONE_INDEPENDENT_RETAINED_TWENTY_PRODUCT_PRIOR_THIRTY_NINE_PRESERVED_NOT_CASCADE_OR_GATE'
            and passed['fresh_inputs']==passed['final_fresh_hashes']==449 and passed['cleanup']and passed['independent_filter_pass_preserved']==1
            and not passed['retained_core_thirty_nine_reexecuted'],'EXACT_FRESH_TWENTY_NINE_AND_RETAINED_CASE_BOUNDARIES')
        tested={p['path']:p for p in passed['source_pins']};prior={p['path']:p for p in old['source_pins']};initial={p['path']:p for p in failed['source_pins']}
        sources={n for n in tested if n.startswith('crates/')and n.endswith('.rs')or n in {'Cargo.toml','Cargo.lock','rust-toolchain.toml'}}
        c.require(sources-set(prior)==NEW,'ONLY_THREE_NEW_DEFINITION_SOURCE_TEST_AND_FIXTURE_FILES')
        for name in sources-NEW-CHANGED:c.require(tested[name]==prior[name],'ORIGINAL_OTHER_SOURCE_PINS_RETAINED_IN_PASS')
        retained={'crates/hwpx-package/src/character_style.rs','crates/hwpx-package/src/paragraph_style.rs',
            'crates/hwpx-package/src/document_import/search/scope.rs','crates/hwpx-package/src/document_import/search/extract.rs',
            'crates/product-cli/src/form_stored_provider.rs','crates/hwpx-package/src/document_import/forms.rs'}
        retained|={'crates/hwpx-package/tests/'+n+'.rs'for n in base.RETAINED}
        for name in sorted(NEW|CHANGED|retained|{base.HEADER}):q.pin(name);c.require(q.snapshots[name]==tested[name],'CURRENT_DEFINITION_AND_RETAINED_SHARED_INPUTS_MATCH_PASS')
        for path,addition in (('crates/hwpx-package/src/document_import/search.rs','    #[error("SOURCE_SEARCH_STYLE_DEFINITION_REJECTED")] Definition,\n'),
            ('crates/hwpx-package/src/document_import/search/inspection.rs','pub mod definitions;\n')):
            text=q.text(path);c.require(text.count(addition)==1,'ONLY_ADDITIVE_DEFINITION_DECLARATIONS');base.inverse(text.replace(addition,''),prior[path],'RETAINED_MATCHER_AND_INSPECTION_EXACT_INVERSE')
        helper=('pub(in crate::document_import) fn source_style_catalogs_for_search(\n    source: &ImportedSourcePackage,\n'
            ') -> Result<(Vec<ImportedCatalogDefinition>, CharacterStyleCatalog, ParagraphStyleCatalog), CatalogImportError> {\n'
            '    let header = read_header(source)?;\n    Ok((header.definitions, header.characters, header.paragraphs))\n}\n\n')
        catalog=q.text(base.CATALOG);c.require(catalog.count(helper)==1,'ONE_PRIVATE_TYPED_HEADER_BRIDGE');base.inverse(catalog.replace(helper,''),prior[base.CATALOG],'UNCHANGED_ORIGINAL_HEADER_AND_CATALOG_BODY')
        core=q.text(base.TEST);prefix=core.split('struct FixtureDiagnostic',1)[0]
        c.require(prefix.endswith('\n\n'),'ONLY_ADDED_DIAGNOSTIC_SEPARATOR');base.inverse(prefix[:-1],initial[base.TEST],'ORIGINAL_NINE_CORE_BODIES_PRESERVE_INDEPENDENT_PASS')
        product=q.text(base.PRODUCT);prefix=product.split('// Additive v3 definition cases;',1)[0]
        c.require(prefix.endswith('\n\n'),'ONLY_APPENDED_V3_PRODUCT_SEPARATOR');base.inverse(prefix[:-1],prior[base.PRODUCT],'ORIGINAL_FOURTEEN_PRODUCT_BODIES_UNCHANGED')
        fixture='crates/hwpx-package/tests/support/search_definition_fixture.rs';text=q.text(fixture)
        repaired=('            let mut child=node.first_child();let mut offset=xml.tokens()[node.end_token().ok_or("char end")?].span().start();\n'
            '            while let Some(i)=child {let element=&xml.elements()[i];child=element.next_sibling();\n'
            '                if !matches!(element.name().local_name(),"fontRef"|"ratio"|"spacing"|"relSz"|"offset") {\n'
            '                    offset=xml.tokens()[element.start_token()].span().start();break;\n                }\n            }\n'
            '            edits.push((offset..offset,"<hh:italic/><hh:bold/>".to_owned()));\n')
        original=('            let offset=xml.tokens()[node.end_token().ok_or("char end")?].span().start();\n'
            '            edits.push((offset..offset,"<hh:bold/><hh:italic/>".to_owned()));\n')
        c.require(text.count(repaired)==1,'ONE_FIXTURE_EFFECT_PLACEMENT_AND_ORDER_REPAIR');base.inverse(text.replace(repaired,original),initial[fixture],'FIXTURE_REPAIR_EXACT_INVERSE_NO_READER_CHANGE')
        independent='definition_style_conditions_need_explicit_used_axes_and_reject_empty_filters'
        declared=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',core));products={'actual_import::source_search::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',product)}
        c.require(len(declared)==10 and len(products)==20 and dict(failed['steps'][0]['tests'])[independent]=='ok','EXACT_THIRTY_DEFINITION_PATH_CASES')
        for step,expected in zip(passed['steps'],(declared-{independent},products),strict=True):
            c.require(len(step['tests'])==len(expected)and{n for n,s in step['tests']}==expected and all(s=='ok'for n,s in step['tests'])and step['diagnostics']==[],
                'ALL_TWENTY_NINE_CURRENT_CASES_PASS_WITHOUT_DIAGNOSTICS')
            job=step['owned_job'];c.require(step['cleanup']and job['cleanup_confirmed']and job['owned_tree_empty']and job['job_handle_closed']
                and job['last_job_accounting']['active_processes']==0,'BOTH_DEFINITION_JOBS_TERMINAL_EMPTY_CLOSED')
        c.require(failed['state']=='FAILED_SEARCH_DEFINITION_COMPONENTS'and failed['cleanup']and sum(s=='FAILED'for n,s in failed['steps'][0]['tests'])==6,'ORIGINAL_DEFINITION_FAILURES_PRESERVED')
        for suffix,sha in (('052','75a127ce5acae0c6f9cccf00afc5725731d2181c0a59ea16ad636fa3031be261'),('053','8262bf6114d9cf6b83c22da41143188396b3d35fa0bd7fc7c8dd17c1cca1c039')):
            path=ROOT+'search-definition-header-diagnostic'+suffix+'.v1.json';record=q.json(path)
            c.require(q.snapshots[path]['sha256']==sha and record['state']=='FAILED_DEFINITION_HEADER_DIAGNOSTIC'and record['cleanup'],'ORIGINAL_HEADER_DIAGNOSTIC_FAILURES_PRESERVED')
            if suffix=='053':c.require('character_style_unsupported_shape'in record['steps'][0]['safe_error_variants'],'INDEPENDENT_CLOSED_CHARACTER_READER_FAILURE')
        for name in DOCS:q.pin(name)
        progress=q.text(DOCS[1]);c.require(len(re.findall(r'^\| SEARCH-[0-9]{3} \|',progress,re.M))==19,'RETAINED_NINETEEN_SEARCH_COMPLETION_ROWS')
        for marker in ('총29개','독립 필터1개','449 fresh/final449','핵심39개','italic→bold','캐스케이드','v3'):
            c.require(marker in progress,'DEFINITION_PROGRESS_PASS_REUSE_AND_LIMIT_BOUNDARIES')
        profile=q.text(DOCS[3])
        for marker in ('V1/v2 reject','Missing references stay missing','all_present_indexed_references_resolved=true','implicit_cascade_or_hidden_visibility_qualified=false',
            'All29 pass','449 fresh/final449','P09/A12/A13 OPEN','Native011 unapproved/unexecuted'):
            c.require(marker in profile,'V3_DEFINITION_REQUEST_SOURCE_AND_GATE_BOUNDARIES')
        c.require('p09-source-definition-style-search-v3.md'in q.text(DOCS[2]),'V2_AND_V3_PROFILES_LINKED')
        state=q.text(DOCS[0]).split('> 2026-10-19 P09 이전 원본 참조와 구조 태그 검색',1)[0]
        for marker in ('2026-10-20','29pass','449fresh/final449','55.09%','23.2508%','4.9804%','잔여91','고정CROSSREF8종 NOT_RUN','Native011 미승인/미실행','P10미시작'):
            c.require(marker in state,'CURRENT_DEFINITION_RESULT_AND_UNCHANGED_GATE')
        q.pin('tools/p09/run_search_definition_components.py');c.require(q.snapshots['tools/p09/run_search_definition_components.py']==tested['tools/p09/run_search_definition_components.py'],'SUCCESSFUL_DEFINITION_RUNNER_UNCHANGED')
        q.pin(Path(__file__).relative_to(c.ROOT).as_posix());q.finish();guard.check(force=True)
        row.update(state='PASS_SOURCE_DEFINITION_STYLE_CODE_DOCUMENT_SYNC_THIRTY_CASES_NOT_CASCADE_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            current_executed_cases=29,retained_independent_filter_case=1,original_core_thirty_nine_not_reexecuted=True,
            original_readers_matcher_and_test_bodies_inverse_verified=True,fixture_only_order_repair_verified=True,
            embedded_header_input_explicitly_pinned=True,entire_449_inputs_reaudited=False,
            implicit_cascade_hidden_visibility_native_or_full_search_qualified=False,next_work='Source_cascade_and_hidden_effective_style_policy_and_search_coverage')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'DEFINITION_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_DEFINITION_SYNC_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
