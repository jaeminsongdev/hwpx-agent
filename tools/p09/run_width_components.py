"""24 width-source cases and complete226/28 table audit; no194-product/64-source replay."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_case_product_components as prior
from run_regex_replacement_focused import select_own_single_cpu
from run_style_replacement_sync import good_step
harness,shared,c,a,audit,snapshot=prior.harness,prior.shared,prior.c,prior.a,prior.audit,prior.snapshot
OUTPUT='implementation/p09/evidence/p09-361-width-components175.v1.json'
PARENT='crates/hwpx-package/src/document_import/search/replacement/atoms.rs'
CORE=PARENT[:-3]+'/width.rs';MAPPING=PARENT[:-3]+'/width/mapping.rs';TABLE=PARENT[:-3]+'/width/table.rs'
LICENSE=PARENT[:-3]+'/width/UNICODE_LICENSE.txt';TEST='crates/hwpx-package/tests/document_import_width_conversion.rs'
FIXTURE='crates/hwpx-package/tests/support/unicode17_width_pairs.tsv'
NEW={CORE,MAPPING,TABLE,LICENSE,TEST,FIXTURE};CHANGED={PARENT}
UCD_SHA='2e1efc1dcb59c575eedf5ccae60f95229f706ee6d031835247d843c11d96470c'


def inventory(check):return prior.inventory(check)|NEW


def tables(q):
    fixture=q.text(FIXTURE);rows=[r.split('\t')for r in fixture.splitlines()if r and not r.startswith('#')]
    c.require(len(rows)==254 and sum(r[0]=='wide'for r in rows)==104 and sum(r[0]=='narrow'for r in rows)==122 and sum(r[0]=='kana'for r in rows)==28,
        'EXACT104_WIDE122_NARROW28_REPRESENTABLE_KANA_FIXTURE_ROWS')
    c.require(UCD_SHA in fixture and '2198209'in fixture and 'https://www.unicode.org/Public/17.0.0/ucd/UnicodeData.txt'in fixture,'EXPLICIT_ORIGINAL_UCD17_SOURCE_IDENTITY_AND_EXTRACTION_SCOPE')
    pairs=sorted((int(r[1],16),int(r[2],16))if r[0]=='wide'else(int(r[2],16),int(r[1],16))for r in rows if r[0]!='kana')
    kana=[tuple(int(cp,16)for cp in r[1:])for r in rows if r[0]=='kana'];c.require(kana==sorted(kana),'CANONICAL_KANA_SORTED_BY_COMPOSITE')
    c.require(len({p[0]for p in pairs})==len({p[1]for p in pairs})==226,'ALL_WIDTH_PAIRS_BIJECTIVE_WITH_NO_INVENTED_OR_DUPLICATE_TARGETS')
    source=q.text(TABLE);point=lambda text:[int(v,16)for v in re.findall(r"'\\u\{([0-9A-F]+)\}'",text)]
    pair_points=point(source.split('const PAIRS:',1)[1].split('];',1)[0]);actual_pairs=list(zip(pair_points[::2],pair_points[1::2]))
    kana_points=point(source.split('const KANA:',1)[1].split('];',1)[0]);actual_kana=list(zip(kana_points[::3],kana_points[1::3],kana_points[2::3]))
    c.require(actual_pairs==pairs and actual_kana==kana,'EVERY_GENERATED_RUNTIME_PAIR_AND_KANA_EQUALS_THE_EXTRACTED_SOURCE_FIXTURE')
    index=lambda name:[int(n)for n in re.findall(r'\d+',source.split('const '+name+':',1)[1].split('=[',1)[1].split('];',1)[0])]
    c.require(index('HALF_INDEX')==sorted(range(226),key=lambda i:pairs[i][1])and index('COMPOSE_INDEX')==sorted(range(28),key=lambda i:kana[i][1:]),
        'BOTH_INDIRECTION_INDEXES_COMPLETE_UNIQUE_AND_SORTED_FOR_BINARY_SEARCH')
    c.require('UNICODE LICENSE V3'in q.text(LICENSE)and 'Copyright © 1991-2026 Unicode, Inc.'in q.text(LICENSE)and UCD_SHA in source,
        'GENERATED_UCD_DATA_SOURCE_DIGEST_AND_LICENSE_PRESERVED')


def inverse(q,old):
    text=q.text(PARENT);marker='pub mod width;\n';c.require(text.count(marker)==1,'ONE_ADDITIVE_WIDTH_MODULE')
    audit.inverse(text.replace(marker,''),old[PARENT],'ENTIRE_EXISTING_LITERAL_REGEX_STYLE_UNICODE_CASE_ROOT_UNCHANGED')
    source=q.text(CORE)
    for marker in('ImportedDocumentFields::import(original)','ImportedDocumentReviewBodies::import_bound_fields(original,&fields)',
        'SourceReviewScopeIndex::from_review(original,&review,limits)','unicode::plan::compile_mapped(',
        'styles::text::output::build(','readback::verify_artifact('):c.require(source.count(marker)==1,'ONE_WIDTH_SOURCE_PROOF_FIELDS_REVIEW_INDEX_PLAN_WRITER_READBACK')
    mapping=q.text(MAPPING);table=q.text(TABLE)
    c.require('pending:Option<Unit>'in mapping and 'first.segment==last.segment&&first.atom==last.atom'in mapping
        and 'before.changed||unit.changed'in mapping and 'binary_search_by_key'in table and '.nfkc('not in mapping and '.nfc('not in mapping,
        'BOUNDED_PENDING_KANA_FUSION_ONLY_WHEN_WIDTH_CHANGED_AND_SAME_ATOM_COALESCING_WITH_BINARY_TABLES_NOT_GENERAL_NORMALIZATION')
    tables(q)


def expected(q):
    names=re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(TEST));c.require(len(names)==len(set(names))==24,'EXACT24_NEW_WIDTH_SOURCE_IDENTITIES');return set(names)


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'WIDTH_COMPONENTS_IMMUTABLE_RUN_EXISTS');selection=select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_WIDTH_COMPONENTS',steps=[],own_cpu_selection=selection,actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False,width_stored_product_or_native_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        baseline=q.json(prior.OUTPUT)
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='51fdcd507529732e6916085630859511c9fa93541988356d2cd67cbba9744a00'
            and baseline['state']=='PASS_CASE_TWENTY_TWO_PRODUCTS_NOT_FULL_TRANSACTION_NATIVE_OR_GATE'and baseline['cleanup']
            and baseline['fresh_inputs']==baseline['final_fresh_hashes']==676 and baseline['new_product_cases']==22,'EXACT_PRIOR_CASE_PRODUCTS_AND_ORIGINAL_SOURCE_BASELINE')
        old={p['path']:p for p in baseline['source_pins']};c.require(NEW.isdisjoint(old),'NEW_WIDTH_FILES_ARE_ADDITIVE')
        for name in names-NEW-CHANGED:c.require(q.snapshots[name]==old[name],'ALL_SHARED_PLANS_PROTECTION_WRITERS_OLD_PRODUCTS_SOURCE_TESTS_AND_FIXTURES_UNCHANGED')
        inverse(q,old);cases=expected(q)
        print(json.dumps(dict(state='WIDTH_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),new_cases=24,width_pairs=226,kana_pairs=28,one_cpu_mask=4)),flush=True)
        harness.run_one('twenty_four_original_width_pair_and_kana_source_cases',[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package',
            '--test','document_import_width_conversion','--message-format=short','--','--test-threads=1'],cases,guard,audit.environment(),row,observe_capture=snapshot)
        good_step(row['steps'][0],cases);c.require(inventory(guard.check)==names,'FINAL_WIDTH_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_WIDTH24_ALL226_PAIRS28_KANA_NOT_STORED_PRODUCT_NATIVE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            new_source_cases=24,width_pairs=226,kana_pairs=28,original_ucd17_bytes=2198209,original_ucd17_sha256=UCD_SHA,
            old194_products_and64_source_reexecuted=False,all_shared_plan_guard_and_writer_bodies_unchanged=True,
            width_only_mapping_not_general_normalization_or_display_width=True,same_atom_changes_coalesced_and_cross_run_first_contributor_explicit=True,
            next_work='Current_stored_and_strict_product_binding_of_explicit_width_conversion_then_remaining_P09_contract_and_native_gates')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'WIDTH_COMPONENTS_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_WIDTH_COMPONENT_SAMPLES')
            row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations','safe_error_variants')},
                'observation':{k:s.get('bounded_output_observation',{}).get(k)for k in('safe_warning_locations','short_error_locations','rust_error_codes')},
                'pass_count':sum(status=='ok'for _,status in s.get('tests',[])),'failures':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
