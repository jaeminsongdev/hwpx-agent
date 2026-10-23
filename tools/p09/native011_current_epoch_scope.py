"""Lossless 805-source declaration composition; never a runtime/Frame admission."""
import hashlib
import json
import re
import sys
import time
from types import SimpleNamespace as NS

SELF='tools/p09/native011_current_epoch_scope.py'
TEST='tools/p09/tests/test_native011_current_epoch_scope.py'
BUILD=dict(path='implementation/p09/evidence/p09-361-native011-current-cohort-build002.v1.json',
    bytes=167281,sha256='7e4aeb5ace1b81b36e6aa5b246c4b10171ec7446f6eef9f32edad68fe9ccba8d')
LIST=dict(path='implementation/p09/evidence/p09-361-native011-current-cohort-listing001.v1.json',
    bytes=61233,sha256='6a7ef761910e267cfde57e7b2237104f9d28e588b8400cb4f1ca3d6b1adef633')
PREIMAGES=dict(path='implementation/p09/evidence/p09-361-native011-prior-source-preimages001.v1.json',
    bytes=92704,sha256='8bce0d752f5ff8a8f788a2cae6b79d92800e64052aeaeaeb5a1800fcb2f321a6')
BODY=dict(path='implementation/p09/evidence/locked-r07/cases/p340-failure-111-run083.json',
    bytes=565807,sha256='b8495d04c9444875cd500d2941c5b055fab1bab630325cbefb327f9f79ec1e72')
ARCHIVE_PREFIX='implementation/p09/evidence/p09-native011-prior-compiled-rust787-code/'
CHANGED=frozenset(('crates/hwpx-package/src/document_import.rs',
    'crates/hwpx-package/src/document_import/fields.rs','crates/hwpx-package/src/lib.rs',
    'crates/product-cli/src/main.rs','crates/product-cli/src/reference_validation_product.rs'))


def require(ok,code):
    if not ok:raise ValueError('CURRENT805_SCOPE_'+code)


def digest(rows):
    return hashlib.sha256(json.dumps([rows[n] for n in sorted(rows)],sort_keys=True,
        ensure_ascii=True,allow_nan=False,separators=(',',':')).encode()).hexdigest()


def archive_rows(rows,translations,scope):
    """Only exact declared preimages may move to distinct immutable archive paths."""
    original=scope.pins(list(rows.values()));result={n:dict(p) for n,p in original.items()}
    for before,after in translations:
        require(original.get(before['path'])==before and after['path'] not in result
            and before['bytes']==after['bytes'] and before['sha256']==after['sha256'],
            'LOSSLESS_DISJOINT_ARCHIVE_MAPPING')
        del result[before['path']];result[after['path']]=dict(after)
    require(len(result)==len(original) and sum(p['bytes'] for p in result.values())==sum(p['bytes'] for p in original.values()),
        'ARCHIVE_COUNT_AND_BYTES_PRESERVED')
    return scope.pins(list(result.values()))


def admit(build,listing,preimages,scope,build_contract):
    build_contract(build)
    require(listing['schema_version']=='hwpx-agent.p09-native011-cohort-list-only/v1'
        and listing['state']=='PASS_CURRENT805_COHORT_BINARY_LIST_ONLY_NOT_CURRENT_RUNTIME_OR_GATE'
        and listing['compiled_test_executable_pin']==build['artifact_pin']
        and listing['compiled_cohort_Rust_count']==805 and listing['cleanup_confirmed'] is True
        and listing['fresh_inputs']==listing['final_fresh_hashes']==70
        and listing['actual_EXE_list_executed'] is True and listing['current_catalog_byte_binding'] is True
        and listing['current_whole805_freshness_qualified'] is False
        and listing['runtime_tests_executed'] is False and listing['product_test_bodies_executed'] is False
        and listing['Native_Frame_or_dispatch_qualified'] is False and listing['GO_authorized'] is False
        and listing['accepted_count_delta']==0,'EXACT_LIST_ONLY_NOT_NATIVE')
    names=listing['current_catalog_names'];modules=listing['current_module_instances']
    observation=listing['listing_observation']
    require(type(names) is list and names==sorted(set(names)) and len(names)==249
        and names[111]==scope.CASE112 and type(modules) is list and len(modules)==59
        and observation['full_names_validated'] is True and observation['test_count']==249
        and observation['stderr_bytes']==0,'EXACT249_CATALOG_AND59_MODULES')
    require(preimages['state']=='PASS_EXACT_FIVE_PRIOR_SOURCE_PREIMAGES_NOT_ARCHIVE_OR_RUNTIME'
        and preimages['cleanup_confirmed'] is True and preimages['current_Rust_modified'] is False
        and preimages['product_executed'] is False and len(preimages['preimages'])==5,'FIVE_EXACT_PREIMAGES')
    compiled=scope.pins(build['source_pins'],843)
    rust={n:p for n,p in compiled.items() if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
        and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
    require(len(rust)==805,'EXACT_COMPILED805_NOT_OBSERVED_UNION')
    actual_catalog=scope.pins(listing['source_pins'],70)
    require(all(compiled.get(row['path'])==actual_catalog.get(row['path']) for row in modules),
        'EVERY_LISTED_MODULE_COMPILED_BYTE_BINDING')
    translations=[]
    for row in preimages['preimages']:
        before=row['original_pin'];after=row['proposed_archive_pin'];current=row['current_pin']
        require(before['path'] in CHANGED and current==rust[before['path']]
            and after==dict(before,path=ARCHIVE_PREFIX+before['path']),'EXACT_PRIOR_CURRENT_ARCHIVE_TRIPLE')
        payload=row['restored_utf8'].encode('utf-8')
        require(len(payload)==before['bytes'] and hashlib.sha256(payload).hexdigest()==before['sha256'],
            'ARCHIVED_PAYLOAD_EXACT_PRIOR_HASH')
        translations.append((before,after))
    require({p['path'] for p,_ in translations}==CHANGED,'FIVE_DISTINCT_PREIMAGES')
    return rust,translations


def compose(original,prior,rust,translations,controls,exe,scope):
    old=scope.pins(original,1658);previous=scope.pins(list(prior.values()),826)
    require(all(old.get(p['path'])==p for p in scope.FROZEN),'ORIGINAL_THREE_FROZEN_PREIMAGES')
    require(set(scope.FIXTURES)<=set(old),'ALL_HISTORICAL_FIXTURES_PRESERVED')
    require(len(rust)==805 and {p['path'] for p,_ in translations}==CHANGED,'CLOSED_COMPILED_SCOPE')
    require(set(controls)=={SELF,TEST,BUILD['path'],LIST['path'],PREIMAGES['path']},'ONLY_FIVE_NAMED_CONTROLS')
    for pin in (BUILD,LIST,PREIMAGES):require(controls[pin['path']]==pin,'EXACT_COMPILED_LINEAGE_DATA')
    original_translation=list(zip(scope.FROZEN,scope.ARCHIVES))
    original_translation.extend((before,after) for before,after in translations if before['path'] in old)
    require(len(original_translation)==7,'ORIGINAL_THREE_AND_FOUR_PRIOR_RUST_ARCHIVES')
    archived=archive_rows(old,original_translation,scope)
    previous=archive_rows(previous,translations,scope)
    current=scope.extend(previous,rust)
    current=scope.extend(current,scope.pins([exe]))
    current=scope.extend(current,controls)
    whole=scope.extend(archived,current)
    require(all(whole[n]==p for rows in (archived,current) for n,p in rows.items()),'COMPLETE_LOSSLESS_DECLARATIONS')
    require(whole[exe['path']]==exe and all(whole[n]==p for n,p in rust.items()),'ONLY_NEW805_PRODUCT_CANDIDATE')
    return NS(whole=whole,current=current,archived=archived,prior=previous,translations=original_translation)


def prepare(q,a,scope,build_contract):
    build=a.read_exact(q,BUILD);listing=a.read_exact(q,LIST);preimages=a.read_exact(q,PREIMAGES)
    old_listing=a.read_exact(q,scope.LIST_PIN);prior=scope.listing_inputs(old_listing)
    body=a.read_exact(q,BODY)
    rust,translations=admit(build,listing,preimages,scope,build_contract)
    require(listing['current_catalog_names']==old_listing['source_test_names'],'OLD_NAMES_UNCHANGED_NOT_REPLAYED')
    for _,pin in translations:a.exact(q.pin(pin['path']),pin,'ACTUAL_PRIOR_ARCHIVE_BYTES')
    controls=scope.pins([q.pin(SELF),q.pin(TEST),BUILD,LIST,PREIMAGES])
    declaration=compose(body['source_freeze'],prior,rust,translations,controls,build['artifact_pin'],scope)
    return declaration,listing,rust,translations


def main():
    denied=[]
    def deny(event,args):
        if event in ('subprocess.Popen','os.system','os.startfile','os.exec','os.posix_spawn','os.fork'):
            denied.append(event);raise ValueError('EPOCH_SCOPE_NO_PROCESS')
    sys.addaudithook(deny)
    import accept_case112_current_epoch as a,conservative_maintenance as c
    import current_stored_runtime_scope as scope,successor_preparation_workspace_v1 as publisher
    import native011_current_cohort_listing as listing_contract
    import prepared_run_closure_v1 as host,owned_cpu_baseline_v1 as baseline
    import preparation_attributed_cpu_v1 as policy,distinct_final_sample_guard_v1 as final
    import native011_source_generation_audit as audit
    host.configure_host_policy(c)
    g=baseline.guard_type(policy.guard_type(final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic()
    row=dict(state='FAILED_CURRENT805_DECLARATION_COMPOSITION_NOT_RUNTIME',official_accepted_count=158,
        accepted_count_delta=0,GO_authorized=False,runtime_partition_applied=False,
        actual_Native_Frame_or_product_qualified=False,current_Rust_modified=False)
    try:
        g.acquire();q=a.AcceptanceReader(c.ROOT,g.check)
        for name in (scope.SELF,'tools/p09/native011_current_cohort_listing.py'):q.pin(name)
        declaration,listing,rust,translations=prepare(q,a,scope,listing_contract.build_contract)
        q.finish();g.check(force=True)
        require(q.final_fresh_hashes==len(q.snapshots) and not denied,'DECLARATION_INPUTS_AND_ARCHIVES_CLOSING')
        row.update(state='PASS_LOSSLESS_CURRENT805_SCOPE_DECLARATION_NOT_NATIVE_OR_RUNTIME',
            declared_whole_inputs=len(declaration.whole),declared_whole_sha256=digest(declaration.whole),
            declared_current_inputs=list(declaration.current.values()),declared_current_sha256=digest(declaration.current),
            archived_original_count=len(declaration.archived),archived_original_sha256=digest(declaration.archived),
            original_body_pin=BODY,original_compiled_list_pin=scope.LIST_PIN,
            compiled805_build_pin=BUILD,compiled249_list_pin=LIST,preimages_pin=PREIMAGES,
            original_body_archive_translations=[dict(before=b,after=p) for b,p in declaration.translations],
            compiled787_archive_translations=[dict(before=b,after=p) for b,p in translations],
            actual_five_archive_files_qualified=True,full_declared_source_freshness_qualified=False,
            old_product_cases_replayed=False,current_compiled_Rust_count=len(rust),
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError,OSError,KeyError,TypeError,AttributeError) as error:
        value=error.args[0] if error.args else None
        row.update(error_type=type(error).__name__,error_code=value if type(value) is str
            and re.fullmatch('[A-Za-z0-9_]{1,160}',value) else 'CLOSED_CURRENT805_DECLARATION_FAILURE')
    finally:
        g.close();row.update(cleanup_confirmed=g.cleanup,elapsed_seconds=time.monotonic()-started,
            source_pins=[] if q is None else list(q.snapshots.values()),
            process_creation_attempts=len(denied),resource_summary=audit.sample_summary(g.samples))
        receipt=publisher.publish(c.ROOT,
            'implementation/p09/evidence/p09-361-native011-current805-scope-declaration001.v1.json',
            row,NS(require=c.require,exact=a.exact))
        print(json.dumps(dict(state=row['state'],error_code=row.get('error_code'),
            whole=row.get('declared_whole_inputs'),current=len(row.get('declared_current_inputs',[])),
            fresh=row.get('fresh_inputs'),final=row.get('final_fresh_hashes'),cleanup=g.cleanup,receipt=receipt)),flush=True)
    return 0 if row['state'].startswith('PASS_') and g.cleanup else 2


if __name__=='__main__':raise SystemExit(main())
