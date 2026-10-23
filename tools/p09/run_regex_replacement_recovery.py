"""Retain72 unchanged cases; qualify17 regex cases after fixture corrections and bounded expansion work."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_regex_replacement_components as base
shared,c,a,audit=base.shared,base.c,base.a,base.audit
OUTPUT='implementation/p09/evidence/p09-361-regex-replacement-recovery113.v1.json'
FAILED={
    'regex_replacement::regex_replacement_cross_run_captures_use_first_original_run_and_retain_all_styles_and_runs',
    'regex_replacement::regex_replacement_zero_width_is_not_silently_skipped_and_no_matches_are_not_success'}


def budget_inverse(q,old):
    text=q.text(base.REGEX)
    for current,previous in(
        ('    pub expansion_work_units:usize,pub expansion_work_limit:usize,\n',''),
        ('let(work,work_limit)=collector.work_counters();let expanded=collector.expansions();','let expanded=collector.expansions();'),
        ('            expansion_work_units:work,expansion_work_limit:work_limit,\n','')):
        text=base.one(text,current,previous,'ONLY_EXPLICIT_EXPANSION_WORK_RECEIPT_COUNTERS_ADDED')
    audit.inverse(text,old[base.REGEX],'WHOLE_ORIGINAL_REGEX_FIELD_REVIEW_INDEX_ONE_PASS_COMPILER_AND_OUTPUT_BODY_UNCHANGED')
    text=q.text(base.TEMPLATE)
    text=base.one(text,',work:usize,max_work:usize','', 'ONLY_TOKEN_WORK_COUNTER_FIELDS')
    begin=text.index('    pub(super) fn new(');end=text.index('    pub(super) fn error(',begin)
    text=text[:begin]+('    pub(super) fn new(value:&\'a str,limits:SourceSearchLimits)->Result<Self,R> {Ok(Self {tokens:parse(value)?,resolved:Vec::new(),values:Vec::new(),bytes:0,maximum:limits.0.result_bytes,error:None})}\n')+text[end:]
    addition=('        // Empty optional captures consume work even when their output consumes zero bytes.\n'
        '        let Some(work)=self.work.checked_add(self.resolved.len()).filter(|n|*n<=self.max_work) else{return self.reject(R::Limit)};self.work=work;\n')
    text=base.one(text,addition,'','AGGREGATE_WORK_GUARD_BEFORE_EACH_EXPANSION_LOOP')
    audit.inverse(text,old[base.TEMPLATE],'ORIGINAL_TEMPLATE_GRAMMAR_BINDING_EXPANSION_VALUES_AND_BYTE_BOUNDS_EXACT_INVERSE')


def test_inverse(q,old):
    text=q.text(base.TEST);text=base.one(text,'#[allow(dead_code)] #[path="support/search_definition_fixture.rs"] mod definition;\n','','ONLY_EXISTING_TYPED_HEADER_FIXTURE_IMPORT')
    current=('    let stub=fixture::with_body(old)?;let f=forms(&stub)?;assert!(replace(&f,&stub,r"A([0-9]+)(B)",Scope::Document,all(),"[$2/$1]").is_err());\n'
        '    let raw=definition::package(old)?;let f=forms(&raw)?;let out=replace(&f,&raw,r"A([0-9]+)(B)",Scope::Document,all(),"[$2/$1]")?;\n')
    previous='    let raw=fixture::with_body(old)?;let f=forms(&raw)?;let out=replace(&f,&raw,r"A([0-9]+)(B)",Scope::Document,all(),"[$2/$1]")?;\n'
    text=base.one(text,current,previous,'PRESERVE_STUB_HEADER_NEGATIVE_AND_USE_ACTUAL_DECLARATIONS_FOR_STYLED_POSITIVE')
    current=('    // An empty match immediately after a nonempty match is suppressed by the original engine.\n'
        '    // Keep that behavior, then use a nonmatching gap to ensure the terminal empty match exists.\n'
        '    let raw=package("AA")?;let f=forms(&raw)?;let out=replace(&f,&raw,"A|$",Scope::Document,all(),"X")?;exact(&raw,&out,section(&raw)?.replace(">AA<",">XX<"))?;\n'
        '    let raw=package("AA Z")?;let f=forms(&raw)?;let original=Sha256::digest(&raw);\n'
        '    for q in["^","A|$"]{let index=f.source_review_scope_index(&raw,Default::default())?;assert!(index.find(query(q),Scope::Document,all())?.result().matches().iter().any(|m|m.zero_width));\n'
        '        assert!(matches!(replace(&f,&raw,q,Scope::Document,all(),"X"),Err(E::Compile(Compile::Selection))));}\n')
    previous=('    let raw=package("AA")?;let f=forms(&raw)?;let original=Sha256::digest(&raw);\n'
        '    for q in["^","A|$"]{assert!(matches!(replace(&f,&raw,q,Scope::Document,all(),"X"),Err(E::Compile(Compile::Selection))));}\n')
    text=base.one(text,current,previous,'ORIGINAL_REGEX_EMPTY_ADJACENCY_SEMANTICS_PRESERVED_AND_ACTUAL_EMPTY_MATCH_PROVEN')
    marker='#[test]\nfn regex_replacement_empty_optional_capture_work_is_bounded_even_without_output_growth()'
    c.require(text.count(marker)==1,'ONE_NEW_INDEPENDENT_EMPTY_CAPTURE_WORK_BOUNDARY_CASE');text=text[:text.index(marker)]
    audit.inverse(text,old[base.TEST],'ENTIRE_PREVIOUS_SIXTEEN_CASE_FILE_RESTORED_EXCEPT_TWO_EXPLICIT_FAILED_FIXTURE_CORRECTIONS')


def expected(q):
    cases={'regex_replacement::'+n for n in re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(base.TEST))}
    c.require(len(cases)==17,'SEVENTEEN_CURRENT_REGEX_CANDIDATE_IDENTITIES');return cases


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'REGEX_REPLACEMENT_RECOVERY_IMMUTABLE_RUN_EXISTS');shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_REGEX_REPLACEMENT_RECOVERY',steps=[],actual_Hangul_or_COM=False,
        Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        output_ingest_commit_or_publication=False,compiled_queue_reexecuted=False,stored_product_zero_width_or_native_qualification_added=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);names=base.inventory(guard.check)
        for name in sorted(names):q.pin(name)
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        failed=q.json(base.OUTPUT);previous=q.json(base.prior.OUTPUT)
        c.require(q.snapshots[base.OUTPUT]['sha256']=='f53fd16a7e66e637f3bdfb9cf9c303ae757f118a1b86280bc6222207fc28459b'
            and failed['state']=='FAILED_REGEX_REPLACEMENT_COMPONENTS'and failed['cleanup']and len(failed['steps'])==1,'ORIGINAL_FAILED_REGEX_RUN_AND_CLEANUP_RETAINED')
        old={p['path']:p for p in failed['source_pins']};original={p['path']:p for p in previous['source_pins']}
        c.require(names=={n for n in old if n.startswith(('crates/','fixtures/'))or n in{'Cargo.toml','Cargo.lock','rust-toolchain.toml',base.prior.prior.base.CAPTURE}},'SAME_REGEX_SOURCE_INVENTORY')
        for name in names-{base.REGEX,base.TEMPLATE,base.TEST}:c.require(q.snapshots[name]==old[name],'NO_ORIGINAL_MATCHER_LITERAL_COMPILER_STORED_PRODUCT_OR_BASELINE_CASE_INPUT_CHANGE')
        base.inverse(q,original);budget_inverse(q,old);test_inverse(q,old);cases=expected(q);step=failed['steps'][0]
        c.require(step['exit_code']==101 and len(step['tests'])==88 and {n for n,s in step['tests']if s!='ok'}==FAILED
            and all(s in{'ok','FAILED'}for n,s in step['tests'])and len([n for n,s in step['tests']if s=='ok'and not n.startswith('regex_replacement::')])==72
            and step['cleanup']and step['owned_job']['owned_tree_empty']and step['owned_job']['job_handle_closed'],
            'SEVENTY_TWO_ORIGINAL_PASSES_AND_TWO_NEW_FAILURES_RETAINED_NOT_A_RESOURCE_STOP')
        print(json.dumps(dict(state='REGEX_REPLACEMENT_RECOVERY_PREFLIGHT_COMPLETE',inputs=len(q.snapshots),retained_original_cases=72,affected_regex_cases=16,new_work_boundary_cases=1)),flush=True)
        base.harness.run_one('seventeen_regex_candidates_with_bounded_empty_capture_work',[base.harness.CARGO,'test','--offline','--locked','-j','1','-p','hwpx-package',
            '--test','regex_replacement_bundle','--','regex_replacement::','--test-threads=1'],cases,guard,audit.environment(),row,observe_capture=base.prior.snapshot)
        c.require(base.inventory(guard.check)==names,'FINAL_REGEX_RECOVERY_SOURCE_INVENTORY_DRIFT');q.finish();guard.check(force=True)
        row.update(state='PASS_REGEX_REPLACEMENT_SEVENTY_TWO_RETAINED_SEVENTEEN_CURRENT_NOT_STORED_PRODUCT_ZERO_WIDTH_NATIVE_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,new_core_cases=17,retained_original_cases=72,total_distinct_core_cases=89,
            actual_reexecuted_or_new_cases=17,previous_failed_run_preserved=True,original_matcher_literal_compiler_and_review_context_inverse_verified=True,
            capture_expansion_work_bounded_independently_of_output_bytes=True,one_regex_pass_and_one_original_protected_writer_for_variable_capture_expansions=True,
            next_work='Current_stored_and_strict_product_binding_of_regex_capture_candidates_then_remaining_full_contract_and_zero_width_insertions')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'REGEX_REPLACEMENT_RECOVERY_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),
            source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_REGEX_RECOVERY_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{k:s.get(k)for k in('stage','exit_code','diagnostics','locations','summaries','tests','panic_locations','safe_error_variants')}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
