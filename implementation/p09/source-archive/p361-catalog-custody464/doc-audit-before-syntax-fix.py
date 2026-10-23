"""Document-only close after accepted451. Never repeats Rust, SQL, Hancom or Native.

452's English-only wording assertion was narrower than the Korean plan's same
cold-lookup boundary. Preserve that failed receipt; accept either exact term.
"""
import argparse,ast,hashlib,importlib.util,json,re,time,unittest
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
import resource_sample_table as layout
DRIVER='tools/p09/verify_catalog_request_identity_docs.py'
def close_request_entry(args):
    c,a,shared=r.c,r.a,r.shared;output=f'implementation/p09/evidence/p09-361-catalog-request-entry-doc-sync{args.run}.v1.json'
    c.require(not(c.ROOT/output).exists(),'IMMUTABLE_REQUEST_ENTRY_DOCUMENT_CLOSE')
    shared.host.configure_host_policy(c);selection=r.tools.select_own_single_cpu()
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_REQUEST_ENTRY_DOCUMENT_CLOSE',Cargo_or_Native_or_DB_started=False,product_tests_replayed=False,P09_gate='OPEN',P10_started=False,accepted_count_delta=0,own_cpu_selection=selection)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);q.pin(DRIVER)
        path='implementation/p09/evidence/p09-361-catalog-request-entry459.v1.json';base=layout.unpack(q.json(path))
        c.require(q.snapshots[path]['sha256']=='7486639abe057028c1ec4611ae76c3958154623b1a565d4f23c976eb4916793b'
            and base['cleanup']is True and base['fresh_inputs']==base['final_fresh_hashes']==977 and base['new_product_cases']==8
            and base['steps'][0]['exit_code']==0 and not base['steps'][0]['diagnostics']and len(base['steps'][0]['tests'])==8,'EXACT_ACCEPTED_ENTRY8_NO_REPLAY')
        path='implementation/p09/evidence/p09-361-catalog-cold-request-lookup457.v1.json';sql=layout.unpack(q.json(path))
        c.require(q.snapshots[path]['sha256']=='b0e07567a76974e6d6d15b2aabd4f709f1ef4f1a79577f8d02e4cfee759a380e'
            and sql['cleanup']is True and sql['fresh_inputs']==sql['final_fresh_hashes']==968 and sql['actual_current_project_and_source_acl_denials']is True,'EXACT_ACCEPTED_SQL_LOOKUP457_NO_REPLAY')
        frozen={p['path']:p for p in base['source_pins']}
        paths=['crates/product-cli/src/form_product_request/stored_operations/compiled_search/catalog_mask.rs',
            'crates/product-cli/src/form_product_request/stored_operations/compiled_search/catalog_mask/entry.rs',
            'crates/product-cli/src/form_product_request/stored_operations/compiled_search/p02_registry.rs',
            'crates/product-cli/src/form_product_request/stored_literal_replacement/personal_info/catalog/request_lookup.rs',
            'crates/product-cli/src/form_stored_provider/actual_import/source_search.rs',
            'crates/revision-service/src/postgres/source_formula_policy/issuer_registry/stored_revision_jobs/request_lookup.rs',
            'crates/artifact-service/src/store/postgres_repository/schema24.rs',
            'crates/product-cli/tests/support/personal_info_catalog_request_entry.rs',
            'crates/product-cli/tests/support/personal_info_catalog_request_lookup.rs',
            'migrations/postgres/0024_p09_stored_request_lookup.up.sql','migrations/postgres/0024_p09_stored_request_lookup.down.sql',
            'tools/p09/run_personal_info_catalog_mask_product_recovery.py']
        for path in paths:c.require(q.pin(path)==frozen[path],'ACCEPTED_DIRECT_ENTRY_LOOKUP_MIGRATION_AND_ROUTE_BYTES_UNCHANGED')
        links=0
        for path in ['implementation/p09/P09_COMPLETION_EXECUTION.md','implementation/p09/P09_PERSONAL_INFO_CATALOG_MASK_PROGRESS.md','protocol/migrations/p09-personal-info-catalog-mask-product-v1.md','CURRENT_STATE.md']:
            text=q.text(path);c.require('459'in text and '조회'in text,'CURRENT_ENTRY_ACCEPTANCE_DOCUMENTED')
            if path=='CURRENT_STATE.md':
                raw=(c.ROOT/path).read_bytes();c.require(hashlib.sha256(raw[-1714653:]).hexdigest()=='ed1b4a3abe49e8df252989ca75937d75f7002502bb30f0f24faab5523a577b18','ALL_PRIOR_STATE_BYTES_PRESERVED');continue
            for link in re.findall(r'\]\(([^)]+)\)',text):
                if link.startswith(('http:','https:','#')):continue
                c.require(((c.ROOT/path).parent/link.split('#')[0]).is_file(),'DOCUMENT_LOCAL_LINK_RESOLVES');links+=1
        test='tools/p09/tests/test_finalize_catalog_mask_product.py';q.pin(test)
        spec=importlib.util.spec_from_file_location('entry_doc_close',str(c.ROOT/test));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);result=unittest.TestResult()
        for name in ('test_original_runner_exit_contract_refuses_prior_premature_pass','test_original_runner_installs_pass_only_after_mandatory_finish'):module.Tests(name).run(result)
        c.require(result.testsRun==2 and not result.errors and not result.failures,'TWO_AFFECTED_RUNNER_CLOSING_CONTRACTS')
        ast.parse(q.text(DRIVER));ast.parse(q.text('tools/p09/run_personal_info_catalog_mask_product_recovery.py'))
        q.finish();guard.check(force=True);row.update(state='PASS_CATALOG_LOOKUP_AND_COMMON_ENTRY_DOCUMENTS_NOT_GATE',unchanged_direct_code_inputs=len(paths),affected_runner_contracts=2,local_links=links,original_current_state_preserved_bytes=1714653)
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        code=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'DOC_CLOSE_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup,source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
            elapsed_seconds=round(time.monotonic()-started,3),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,output,layout.pack(row),NS(require=c.require,exact=a.exact));print(json.dumps({**{k:v for k,v in row.items()if k not in ('source_pins','resource_samples')},'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


def close_artifact_custody_docs(args,sql=False):
    c,a,shared=r.c,r.a,r.shared;kind='catalog-windows-custody-sql'if sql else'artifact-key-custody'
    output=f'implementation/p09/evidence/p09-361-{kind}-doc-sync{args.run}.v1.json'
    c.require(not(c.ROOT/output).exists(),'IMMUTABLE_ARTIFACT_CUSTODY_DOCUMENT_CLOSE')
    shared.host.configure_host_policy(c);selection=r.tools.select_own_single_cpu()
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_ARTIFACT_CUSTODY_DOCUMENT_CLOSE',Cargo_or_Native_or_DB_started=False,credentials_read_or_written=False,
        product_tests_replayed=False,P09_gate='OPEN',P10_started=False,accepted_count_delta=0,own_cpu_selection=selection)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);q.pin(DRIVER)
        path='implementation/p09/evidence/p09-361-catalog-windows-custody-sql464.v1.json'if sql else'implementation/p09/evidence/p09-361-artifact-windows-key-custody462.v1.json'
        base=layout.unpack(q.json(path))
        if sql:
            c.require(q.snapshots[path]['sha256']=='42775f11829e9ae7972dc78832cf58b78dbea7dc55b6ea137bfa1364dcaca6a7'
                and base['cleanup']is True and base['owned_credential_cleanup']is True and base['owned_credentials_removed']==3
                and base['fresh_inputs']==base['final_fresh_hashes']==900 and base['new_key_environment_models']==4
                and base['actual_SQL24_artifact_OS_key_path']is True and base['artifact_AES_HMAC_environment_used']is False
                and base['key_installer_exited_before_seed_and_execution']is True and all(step['exit_code']==0 and step['cleanup']is True for step in base['steps']),
                'EXACT_OS_KEY_SQL24_STORAGE_AND_RESTART464_WITH_ALL_CLEANUP')
        else:c.require(q.snapshots[path]['sha256']=='4c3c719b43b989bf9b28ec9ecd61b375dda90628bed905db4442216800c97024'
            and base['cleanup']is True and base['owned_credential_cleanup']is True and base['fresh_inputs']==base['final_fresh_hashes']==235
            and base['retained_new_models']==8 and base['new_model_bodies_executed']==0 and base['independent_child_body_completion_marker_and_exact_one_pass_verified']is True
            and len(base['steps'])==1 and len(base['steps'][0]['tests'])==1 and base['steps'][0]['exit_code']==0 and not base['steps'][0]['diagnostics'],'EXACT_CUSTODY_MODELS8_RETAINED_AND_ONE_NATIVE_BODY462')
        frozen={p['path']:p for p in base['source_pins']}
        paths=['Cargo.lock','crates/artifact-service/Cargo.toml','crates/artifact-service/src/lib.rs','crates/artifact-service/src/crypto.rs',
            'crates/artifact-service/src/signed_url.rs','crates/artifact-service/src/service.rs','crates/artifact-service/src/key_custody.rs',
            'crates/artifact-service/src/key_custody/windows.rs','crates/artifact-service/src/key_custody/tests.rs',
            'crates/artifact-service/src/key_custody/tests/windows.rs','tools/p09/run_personal_info_catalog_mask_product_recovery.py']
        if sql:paths+=['crates/product-cli/Cargo.toml','crates/product-cli/examples/sql23_storage.rs','crates/product-cli/examples/sql23_storage/catalog.rs',
            'crates/product-cli/examples/sql23_storage/windows_custody.rs','crates/product-cli/examples/sql24_catalog_windows_custody.rs',
            'tools/p09/native_postgres_storage.py','tools/p09/native_postgres_catalog_windows_custody.py','tools/p09/tests/test_windows_custody_sql_scope.py',
            'crates/product-cli/src/stored_revision_commit/intent.rs','migrations/postgres/0024_p09_stored_request_lookup.up.sql']
        for path in paths:c.require(q.pin(path)==frozen[path],'ACCEPTED_KEY_CUSTODY_AND_ORIGINAL_CRYPTO_BYTES_UNCHANGED')
        production=q.text('crates/artifact-service/src/key_custody/windows.rs')
        c.require(all(term not in production for term in('.set_secret(','.search(','.delete_credential(','env::','fs::')),'READ_ONLY_ADAPTER_WITHOUT_ENUMERATION_OR_FALLBACK')
        links=0
        docs=['protocol/migrations/p09-artifact-windows-key-custody-v1.md','implementation/p09/P09_COMPLETION_EXECUTION.md',
            'implementation/p09/P09_PERSONAL_INFO_CATALOG_MASK_PROGRESS.md','protocol/migrations/p09-personal-info-catalog-mask-product-v1.md','CURRENT_STATE.md']
        if sql:docs.append('implementation/p09/P09_REGISTERED_RECOVERY_PROGRESS.md')
        preserved=1717285 if sql else1715883
        for path in docs:
            text=q.text(path);c.require(('464'if sql else'462')in text,'CURRENT_CUSTODY_SCOPE_DOCUMENTED')
            if path=='CURRENT_STATE.md':
                expected='19901144b820fbd0887ef94c26293dd2c36aeed898b3937d1536f60a36475da0'if sql else'bfb13ea936b786383dd28db0bbf8034b9b99990ed46f6fbef3cbd8af55eeaed5'
                raw=(c.ROOT/path).read_bytes();c.require(hashlib.sha256(raw[-preserved:]).hexdigest()==expected,'ALL_PRIOR_STATE_BYTES_PRESERVED');continue
            for link in re.findall(r'\]\(([^)]+)\)',text):
                if link.startswith(('http:','https:','#')):continue
                c.require(((c.ROOT/path).parent/link.split('#')[0]).is_file(),'DOCUMENT_LOCAL_LINK_RESOLVES');links+=1
        test='tools/p09/tests/test_finalize_catalog_mask_product.py';q.pin(test)
        spec=importlib.util.spec_from_file_location('custody_doc_close',str(c.ROOT/test));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);result=unittest.TestResult()
        for name in ('test_original_runner_exit_contract_refuses_prior_premature_pass','test_original_runner_installs_pass_only_after_mandatory_finish'):module.Tests(name).run(result)
        c.require(result.testsRun==2 and not result.errors and not result.failures,'TWO_AFFECTED_RUNNER_CLOSING_CONTRACTS')
        ast.parse(q.text(DRIVER));ast.parse(q.text('tools/p09/run_personal_info_catalog_mask_product_recovery.py'))
        q.finish();guard.check(force=True);row.update(state='PASS_SQL24_OS_KEY_ARTIFACT_DOCUMENTS_AND_EXACT_ACCEPTED_SOURCE_PRESERVATION_NOT_GATE'if sql else'PASS_ARTIFACT_CUSTODY_DOCUMENTS_AND_ORIGINAL_CRYPTO_PRESERVATION_NOT_GATE',unchanged_direct_code_inputs=len(paths),affected_runner_contracts=2,local_links=links,original_current_state_preserved_bytes=preserved)
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        code=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'DOC_CLOSE_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup,source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
            elapsed_seconds=round(time.monotonic()-started,3),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,output,layout.pack(row),NS(require=c.require,exact=a.exact));print(json.dumps({**{k:v for k,v in row.items()if k not in ('source_pins','resource_samples')},'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',type=int,choices=range(453,471),required=True);mode=parser.add_mutually_exclusive_group()
    mode.add_argument('--request-entry',action='store_true');mode.add_argument('--artifact-custody',action='store_true');mode.add_argument('--custody-sql',action='store_true');args=parser.parse_args()
    if args.custody_sql:return close_artifact_custody_docs(args,sql=True)
    if args.artifact_custody:return close_artifact_custody_docs(args)
    if args.request_entry:return close_request_entry(args)
    c,a,shared=r.c,r.a,r.shared;output=f'implementation/p09/evidence/p09-361-catalog-request-identity-doc-sync{args.run}.v1.json'
    c.require(not(c.ROOT/output).exists(),'IMMUTABLE_IDENTITY_DOCUMENT_CLOSE')
    shared.host.configure_host_policy(c);selection=r.tools.select_own_single_cpu()
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_IDENTITY_DOCUMENT_CLOSE',Cargo_or_Native_or_DB_started=False,product_tests_replayed=False,P09_gate='OPEN',P10_started=False,accepted_count_delta=0,own_cpu_selection=selection)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);q.pin(DRIVER)
        base_path='implementation/p09/evidence/p09-361-catalog-request-identity451.v1.json';base=layout.unpack(q.json(base_path))
        c.require(q.snapshots[base_path]['sha256']=='5c193df9d54210e3372c018a8e42b5ca4557964f7d29fcc9b8fecff0fd1c3ee8'and base['cleanup']is True
            and base['fresh_inputs']==base['final_fresh_hashes']==935 and base['retained_product9_accepted']is True and base['new_identity_cases']==12 and base['affected_legacy_cases']==3,'EXACT_ACCEPTED_IDENTITY15_SQL451')
        failed_path='implementation/p09/evidence/p09-361-catalog-request-identity-doc-sync452.v1.json';failed=layout.unpack(q.json(failed_path))
        c.require(q.snapshots[failed_path]['sha256']=='89d3e32b19e73dfabf5bcb887fbcd0c5fdb88b1aaf6cebcf21eade88ccaabb5f'and failed['cleanup']is True
            and failed['error_code']=='CURRENT_ACCEPTANCE_AND_COLD_LOOKUP_BOUNDARY_DOCUMENTED'and failed['Cargo_or_Native_or_DB_started']is False,'ORIGINAL452_WORDING_AUDIT_FAILURE_PRESERVED')
        frozen={p['path']:p for p in base['source_pins']};code=[p['path']for p in failed['source_pins']if p['path'].startswith(('crates/','tools/','implementation/p04/trust/'))]
        c.require(len(code)==20,'EXACT_TWENTY_DIRECT_CODE_AND_TRUST_INPUTS')
        for path in code:c.require(q.pin(path)==frozen[path],'ACCEPTED_CODE_AND_TRUST_BYTES_UNCHANGED')
        failure_path='implementation/p09/evidence/p09-361-catalog-request-identity450.v1.json';original=layout.unpack(q.json(failure_path))
        c.require(q.snapshots[failure_path]['sha256']=='a023835133624feedd97c914bb065cc06cf16df258870a06b46dd63df418d125'and original['steps'][1]['exit_code']==0,'ORIGINAL450_PRODUCT_BODY_PASS_RETAINED')
        before=next(p for p in original['source_pins']if p['path']=='tools/p09/run_personal_info_catalog_mask_product_recovery.py')
        archive=q.pin('implementation/p09/source-archive/p361-catalog-identity450/failed-runner.py')
        c.require((archive['bytes'],archive['sha256'])==(before['bytes'],before['sha256']),'ORIGINAL450_RUNNER_BYTES_PRESERVED')
        links=0
        for path in ['implementation/p09/P09_COMPLETION_EXECUTION.md','implementation/p09/P09_PERSONAL_INFO_CATALOG_MASK_PROGRESS.md','protocol/migrations/p09-personal-info-catalog-mask-product-v1.md','CURRENT_STATE.md']:
            text=q.text(path)
            if path=='CURRENT_STATE.md':
                raw=(c.ROOT/path).read_bytes();c.require(hashlib.sha256(raw[-1712425:]).hexdigest()=='d9a20cdd0557436141cb1d9abbbcb7198992f18e82d0bd80b1fffce40ff4b287','ALL_PRIOR_CURRENT_STATE_BYTES_PRESERVED');continue
            c.require('451'in text and ('cold lookup'in text or '기존 작업 조회'in text),'ACCEPTANCE_AND_COLD_LOOKUP_BOUNDARY_PRESENT')
            for link in re.findall(r'\]\(([^)]+)\)',text):
                if link.startswith(('http:','https:','#')):continue
                c.require(((c.ROOT/path).parent/link.split('#')[0]).is_file(),'DOCUMENT_LOCAL_LINK_RESOLVES');links+=1
        test='tools/p09/tests/test_finalize_catalog_mask_product.py';q.pin(test)
        spec=importlib.util.spec_from_file_location('identity_doc_close',str(c.ROOT/test));module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);result=unittest.TestResult()
        for name in ('test_original_runner_exit_contract_refuses_prior_premature_pass','test_original_runner_installs_pass_only_after_mandatory_finish'):module.Tests(name).run(result)
        c.require(result.testsRun==2 and not result.errors and not result.failures,'TWO_AFFECTED_RUNNER_CLOSING_CONTRACTS')
        for path in [DRIVER,'tools/p09/run_personal_info_catalog_mask_product_recovery.py','tools/p09/native_postgres_catalog_storage.py','tools/p09/native_postgres_catalog_identity_storage.py']:ast.parse(q.text(path))
        q.finish();guard.check(force=True);row.update(state='PASS_CATALOG_IDENTITY_DOCUMENTS_AND_SOURCE_PRESERVATION_NOT_GATE',unchanged_direct_code_and_trust_inputs=len(code),affected_runner_contracts=2,local_links=links,original_current_state_preserved_bytes=1712425)
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        code=error.args[0]if error.args else None;row.update(error_type=type(error).__name__,error_code=code if type(code)is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}',code)else'DOC_CLOSE_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup,source_pins=[]if q is None else list(q.snapshots.values()),fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
            elapsed_seconds=round(time.monotonic()-started,3),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        pin=shared.publisher.publish(c.ROOT,output,layout.pack(row),NS(require=c.require,exact=a.exact))
        print(json.dumps({**{k:v for k,v in row.items()if k not in ('source_pins','resource_samples')},'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
