"""383: retain382 zero-build inventory failure; complete11-section catalog with empty USERDEF, new27/affected6."""
import configparser,json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import named_style_verification_runtime as r
shared,c,a,tools,compact,harness,audit=r.shared,r.c,r.a,r.tools,r.compact,r.harness,r.audit
OUTPUT='implementation/p09/evidence/p09-361-personal-info-catalog-recovery383.v1.json';DRIVER='tools/p09/run_personal_info_catalog_recovery.py'
BASE='implementation/p09/evidence/p09-361-personal-info-detection-product378.v1.json'
DOCS='implementation/p09/evidence/p09-361-current-crossref-prerequisites-sync381.v1.json'
CORE_PARENT='crates/hwpx-package/src/document_import/search/personal_info.rs';CORE=CORE_PARENT[:-3]+'/catalog.rs'
SEARCH='crates/hwpx-package/src/document_import/search.rs';REVIEW='crates/hwpx-package/src/document_import/search/reviews/selector.rs'
ROOT_TEST='crates/hwpx-package/tests/personal_info_mask.rs';TEST='crates/hwpx-package/tests/support/personal_info_catalog.rs';REVIEW_TEST='crates/hwpx-package/tests/document_import_review_selector.rs'
EXTERNAL=Path(r'C:\Program Files (x86)\HNC\Office 2020\HOffice110\Bin\PrivateInfo.ini');CONFIG_SHA='fe3721e68a749c3d1ec843207d475249fa75e68f1de569fe45468c05b1022434'
LINK='#[path="support/personal_info_catalog.rs"]mod catalog;\n'
NEW={DRIVER,CORE,TEST,'tools/p09/run_personal_info_catalog.py','implementation/p09/evidence/p09-361-personal-info-catalog382.v1.json'};CHANGED={CORE_PARENT,SEARCH,REVIEW,ROOT_TEST}
AFFECTED={'detection::cross_run_regex_and_entities_return_original_text_anchors_without_values','detection::explicit_rule_order_resolves_equal_start_overlap_and_nonoverlapping_scan_is_stable',
    'detection::aggregate_matches_reported_points_query_and_regex_compilation_limits_are_not_silently_truncated'}
REVIEW_CASES={'review_selector_document_four_policies_exclude_before_caps_and_bind_request_without_widening_scope','review_selector_partial_hidden_and_memo_windows_apply_regex_before_caps_and_keep_global_positions',
    'review_selector_multi_block_and_collapsed_selection_do_not_concatenate_or_fabricate_editable_ranges'}
EXTRACT='''        self.scan_compiled_windowed(&expression,Sha256::digest(request).into(),query.max_results,selected,accept,windows,capture)
    }
    // Shared finite scanner. Only validated internal callers can supply compiled expressions.
    fn scan_compiled_windowed(&self,expression:&regex::Regex,query_sha256:[u8;32],max_results:usize,selected:Option<&BTreeSet<domain_ir::LogicalId>>,
        accept:Option<&dyn Fn(&BTreeSet<usize>)->bool>,windows:Option<&std::collections::BTreeMap<usize,(usize,usize)>>,
        mut capture:Option<&mut dyn captures::CaptureSink>)->Result<SourceSearchResult,E>{
        let limits=self.limits.0;if max_results==0||max_results>limits.matches{return Err(E::Limit);}
'''

def inverse(q,old):
    text=q.text(CORE_PARENT);c.require(text.count('pub mod catalog;\n')==1,'ONE_DISTINCT_CATALOG_EXPORT_NO_LEGACY_POLICY_WIDENING')
    audit.inverse(text.replace('pub mod catalog;\n',''),old[CORE_PARENT],'ALL_LEGACY16_RULE_4096_BYTE_DETECTION_POLICY_AND_ITS_MATCHING_UNCHANGED')
    text=q.text(SEARCH);c.require(text.count(EXTRACT)==1,'ONE_SHARED_SCANNER_EXTRACTION')
    text=text.replace(EXTRACT,'').replace('captures::scan(expression,window,capture.is_some())','captures::scan(&expression,window,capture.is_some())')
    text=text.replace('matches.len()>=max_results','matches.len()>=query.max_results').replace('index:self.receipt.clone(),query_sha256,matches,','index:self.receipt.clone(),query_sha256:Sha256::digest(request).into(),matches,')
    audit.inverse(text,old[SEARCH],'ALL_LEGACY_QUERY_COMPILATION_LIMITS_MATCH_LOOP_ORIGIN_MAPPING_RESULT_HASHES_AND_BYTES_PRESERVED')
    text=q.text(REVIEW);start=text.index('    pub(in crate::document_import::search) fn find_precompiled_catalog(');end=text.index('    fn finish_resolved(',start)
    audit.inverse(text[:start]+text[end:],old[REVIEW],'ALL_ORIGINAL_REVIEW_SCOPE_WINDOWS_POLICY_EXCLUSIONS_AND_RESULTS_UNCHANGED')
    text=q.text(ROOT_TEST);c.require(text.count(LINK)==1,'ONE_CATALOG_CHILD_LINK');audit.inverse(text.replace(LINK,''),old[ROOT_TEST],'ALL_ORIGINAL_MASK25_AND_DETECTION23_TEST_BODIES_UNCHANGED')

def main(scratch_relative='target/p09-personal-info-catalog-scratch-383'):
    c.require(not(c.ROOT/OUTPUT).exists(),'PERSONAL_INFO_CATALOG_IMMUTABLE')
    text=(c.ROOT/TEST).read_text(encoding='utf-8');c.require(len(text.encode())<=128*1024,'FINITE_CATALOG_TEST_SOURCE')
    cases={'catalog::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',text)};c.require(len(cases)==27,'EXACT_NEW27_CATALOG_IDENTITIES')
    c.require(REVIEW_CASES<=set(re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)',(c.ROOT/REVIEW_TEST).read_text(encoding='utf-8'))),'EXACT_THREE_ORIGINAL_REVIEW_NAMES_BEFORE_BUILD')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=image=None;started=time.monotonic();row=dict(state='FAILED_PERSONAL_INFO_CATALOG',steps=[],own_cpu_selection=selection,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        Native011_executed=False,prior_Native_replayed=False,actual_DB_or_Hangul_or_COM_started=False,official249_replayed=False,old_suites_replayed=False,
        original_installation_config_mutated=False,private_user_ini_accessed=False,source_document_mutation=False,output_ingest_commit_or_publication=False,
        installed_vendor_authenticity_or_native_semantics_qualified=False,whole_package_personal_data_removed=False)
    try:
        guard.acquire();scratch=c.ROOT/scratch_relative;c.require(not scratch.exists()and scratch.parent.is_dir()and not scratch.parent.is_symlink()and not scratch.parent.is_junction(),'CATALOG_UNIQUE_TEMP')
        q=a.AcceptanceReader(c.ROOT,guard.check);before=compact.unpack(q.json(BASE));docs=q.json(DOCS)
        c.require(q.snapshots[BASE]['sha256']=='878ffdb85abcc6fc57635c45a3a142b2bad2a8b4d5f4037f6b7f87359fd0e732'and before['cleanup']and before['fresh_inputs']==before['final_fresh_hashes']==881,'EXACT378_FULL_SOURCE_STORED_PRODUCT_FRONTIER')
        c.require(q.snapshots[DOCS]['sha256']=='7b674a483387b7a39a26a177e04c184f1109d83705bba74d146096556ac71b51'and docs['cleanup'],'EXACT381_NATIVE_GATE_NOT_BYPASSED_AND_EXTERNAL_QUESTION_PENDING')
        failed=compact.unpack(q.json('implementation/p09/evidence/p09-361-personal-info-catalog382.v1.json'))
        c.require(q.snapshots['implementation/p09/evidence/p09-361-personal-info-catalog382.v1.json']['sha256']=='0f75c8b3e9f57ec02fd6f49270cd129b3a8cd3722dc9ce7d004c7a9799ef68c4'
            and failed['cleanup']and failed['steps']==[]and failed['fresh_inputs']==failed['final_fresh_hashes']==887 and failed['external_final_fresh_hashes']==1
            and failed['error_code']=='INDEPENDENT_COMPLETE10_SECTION64_PATTERN_SOURCE_INVENTORY','EXACT382_ZERO_BUILD_OR_TEST_EMPTY_USERDEF_INVENTORY_FAILURE_PRESERVED')
        old={p['path']:p for p in before['source_pins']}
        for path in sorted(r.closure.inventory(guard.check)|set(old)|NEW|CHANGED|{REVIEW_TEST}):
            q.pin(path)
            if path in old and path not in CHANGED:c.require(q.snapshots[path]==old[path],'ALL_OTHER_PROTECTION_WRITERS_SERVICE_PRODUCT_COMPILER_TESTS_AND_GUARDS_UNCHANGED')
            elif path not in old:c.require(path in NEW|{REVIEW_TEST},'ONLY_CATALOG_SOURCE_TEST_DRIVER_AND_EXACT_REVIEW_REGRESSION_INPUT_ADDED')
        inverse(q,old)
        image=a.AcceptanceReader(EXTERNAL.parent,guard.check);pin=image.pin(EXTERNAL.name)
        c.require(pin['bytes']==17020 and pin['sha256']==CONFIG_SHA,'EXACT_READONLY_HANCOM2020_INSTALLATION_CONFIG_NOT_PRIVATE_USER_DATA_OR_VENDOR_ATTESTATION')
        with EXTERNAL.open('rb')as stream:raw=stream.read(65537)
        c.require(len(raw)==17020,'BOUNDED_EXTERNAL_FORMAT_CONFIG_READ')
        parsed=configparser.ConfigParser(interpolation=None,strict=True);parsed.optionxform=str;parsed.read_string(raw.decode('utf-16'))
        expected=dict(zip(['TELEPHONE','RESIDENT','FOREIGNER','EMAIL','ACCOUNT','LICENSE','PASSPORT','CREDIT','IPADDRESS','BIRTHDAY','USERDEF'],[8,1,1,6,35,1,2,1,1,8,0]))
        c.require(parsed.sections()==list(expected)and all(list(parsed[s])==[f'pattern{i}'for i in range(n)]and all(parsed[s][k]for k in parsed[s])for s,n in expected.items()),'INDEPENDENT_COMPLETE11_SECTION64_PATTERN_SOURCE_INVENTORY')
        row['observed_installation_catalog']=dict(bytes=17020,sha256=CONFIG_SHA,sections=11,nonempty_pattern_sections=10,patterns=64,patterns_per_section=list(expected.items()),vendor_authenticity_or_native_matching_attested=False)
        del raw,parsed
        for module in tuple(sys.modules.values()):
            f=getattr(module,'__file__',None)
            if f:
                p=Path(f).absolute()
                if p.is_relative_to(c.ROOT/'tools/p09')and p.suffix=='.py':q.pin(p.relative_to(c.ROOT).as_posix())
        scratch.mkdir();env=audit.environment();env.update(TEMP=str(scratch),TMP=str(scratch),P09_INSTALLED_FORMAT_CATALOG=str(EXTERNAL));print(json.dumps(dict(state='PERSONAL_INFO_CATALOG_PREFLIGHT',inputs=len(q.snapshots),external_configs=1,new_cases=27,affected_cases=6)),flush=True)
        for binary,label,selected in [('personal_info_mask','catalog27_affected_detection3',cases|AFFECTED),('document_import_review_selector','affected_original_review_selector3',REVIEW_CASES)]:
            harness.run_one(label,[harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package','--test',binary,'--message-format=short','--',*sorted(selected),'--test-threads=1'],selected,guard,env,row,observe_capture=r.snapshot)
            tools.good_step(row['steps'][-1],selected);c.require(row['steps'][-1]['diagnostics']==[],'COMPLETE_CATALOG_AND_UNCHANGED_SHARED_REGRESSIONS_NO_WARNINGS')
        c.require(not any(scratch.iterdir()),'CATALOG_TEMP_EMPTY');image.finish();q.finish();guard.check(force=True)
        row.update(state='PASS_COMPLETE_INSTALLATION_CATALOG64_SOURCE27_AFFECTED6_NOT_NATIVE_DEFAULT_MATCHING_VENDOR_TRUST_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            external_executable_pins=list(image.snapshots.values()),external_final_fresh_hashes=image.final_fresh_hashes,new_cases=27,affected_cases=6,all_selected_patterns_preserved=True,
            next_work='current_stored_catalog_provenance_and_strict_product_selection_then_native_matching_and_target_qualification')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,configparser.Error,subprocess.SubprocessError)as error:
        value=str(error);row.update(error_type=type(error).__name__,error_code=value if re.fullmatch('[A-Za-z0-9_]{1,160}',value)else'PERSONAL_INFO_CATALOG_FAILURE_NO_RAW_VALUES')
        if q is not None:
            try:
                if image is not None:image.finish();row['external_final_fresh_hashes']=image.final_fresh_hashes
                q.finish();row.update(fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes)
            except(ValueError,OSError,KeyError,TypeError,AttributeError):row['failed_final_fresh_check']=True
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),
            external_config_pins=[]if image is None else list(image.snapshots.values()),resource_samples=samples,system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'CATALOG_LOSSLESS_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_type','error_code','fresh_inputs','final_fresh_hashes','external_final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','safe_error_variants','panic_locations','bounded_output_observation','cleanup')},'case_count':len(s.get('tests',[])),
            'failed_cases':[n for n,status in s.get('tests',[])if status!='ok']}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2
if __name__=='__main__':raise SystemExit(main())
