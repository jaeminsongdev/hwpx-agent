"""Bounded isolated staged-output tamper probe before accepting a bytes-source transaction API."""
import json,re,subprocess,sys,time
from pathlib import Path
from types import SimpleNamespace as NS
import run_sort_groups_compiler_compact as prior
harness,shared,c,a,audit,tools=prior.harness,prior.shared,prior.c,prior.a,prior.audit,prior.tools
OUTPUT='implementation/p09/evidence/p09-361-transaction-bytes-probe251.v1.json'
DRIVER='tools/p09/run_transaction_bytes_probe.py'
DOC_BASE='implementation/p09/evidence/p09-361-sort-groups-compiler-sync250.v1.json'
MODEL='crates/operation-engine/src/transaction.rs'
SOURCE=MODEL[:-3]+'/source.rs'
PARENT='crates/operation-engine/tests/workspace_transaction.rs'
TEST='crates/operation-engine/tests/support/bytes_transaction.rs'
NEW={DRIVER,SOURCE,TEST};CHANGED={MODEL,PARENT}
CHILD='#[path="support/bytes_transaction.rs"]mod bytes_v1;\n'
CASE='bytes_v1::bytes_validator_cannot_publish_a_tampered_staged_output'


def inventory(check):return prior.inventory(check)|NEW|{'tools/p09/run_sort_groups_compiler_sync.py','protocol/migrations/p09-sort-groups-operation-compiler-v1.md'}


def expected(q):
    def names(path):return re.findall(r'#\[test\]\s*fn\s+([A-Za-z0-9_]+)\s*\(',q.text(path))
    old=names(PARENT);new=names(TEST);c.require(len(old)==len(set(old))==9 and len(new)==len(set(new))==12,'EXACT9_OLD12_NEW_BYTE_TRANSACTION_CASES')
    return set(old)|{'bytes_v1::'+name for name in new}


def inverse(q,old):
    text=q.text(PARENT);c.require(text.endswith(CHILD)and text.count(CHILD)==1,'ONE_NEW_TRANSACTION_TEST_CHILD')
    audit.inverse(text[:-len(CHILD)],old[PARENT],'ALL9_ORIGINAL_WORKSPACE_TRANSACTION_TEST_BODIES_UNCHANGED')
    text=q.text(MODEL);marker='mod source;\nuse source::TransactionSource;\n';c.require(text.count(marker)==1,'ONE_PRIVATE_SOURCE_INPUT_ADAPTER')
    text=text.replace(marker,'');start=text.index('    pub fn execute<V, C>(\n');header_end=text.index('    {\n',start)+len('    {\n')
    private=text.index('    fn execute_source<V, C>(\n',header_end);body=text.index('        let initial_source = source_input.observe(self);\n',private);stop=text.index('    fn run<V, C>(\n',body)
    text=text[:start]+text[start:header_end]+'        let source_path = source_path.as_ref();\n'+text[body:stop]+text[stop:]
    text=text.replace('source_input.observe(self)','self.observe_source(source_path)').replace('            source_input,\n','            source_path,\n')
    text=text.replace("        source_input: &TransactionSource<'_>,\n",'        source_path: &Path,\n')
    text=text.replace('source_input.read_verified(self)?','self.read_verified_source(source_path)?').replace('source_input.matches(self)','self.source_matches(source_path)')
    audit.inverse(text,old[MODEL],'ORIGINAL_STATE_PIPELINE_VALIDATOR_CAS_FAULT_RECOVERY_FILE_LINK_CONTAINMENT_AND_RECEIPT_LOGIC_RETAINED')
    adapter=q.text(SOURCE)
    for marker in('transaction.read_verified_source(path).map(Cow::Owned)','transaction.source_matches(path)','transaction.observe_source(path)',
        'Cow::Borrowed(bytes)','transaction.manifest.expected_source_size()','transaction.manifest.expected_source_sha256()',
        'transaction.limits.max_source_bytes'):
        c.require(marker in adapter,'UNCHANGED_FILE_GUARDS_AND_BORROWED_BOUNDED_BYTE_SOURCE_IDENTITY')
    c.require(all(x not in adapter for x in('std::fs::','std::process::','unsafe','SignatureVerified','ValidationOutcome::Valid')),'INPUT_ADAPTER_NEVER_ISSUES_TRUST_VALIDATION_OR_EXECUTION_AUTHORITY')


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'TRANSACTION_BYTES_PROBE_IMMUTABLE_RUN_EXISTS')
    selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_TRANSACTION_BYTES_PROBE',steps=[],own_cpu_selection=selection,
        actual_Hangul_or_COM=False,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        P09_product_execution_or_commit=False,bytes_source_API_accepted=False,expected_security_negative_case=True,real_filesystem_only_owned_test_scratch=True)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);packet=q.json(prior.OUTPUT);previous=prior.compact.unpack(packet);docs=q.json(DOC_BASE)
        c.require(q.snapshots[prior.OUTPUT]['sha256']=='0e118e7c6d12be8bb8792793e9eb4c4ed08974542f96a940bbd1b1911245e324'
            and previous['cleanup']and previous['fresh_inputs']==previous['final_fresh_hashes']==836,'EXACT249_SOURCE_AND_COMPONENT_LINEAGE')
        c.require(q.snapshots[DOC_BASE]['sha256']=='9383b9a082ba6eb65e7400e56f9d1228e8ea2611f890348e6c2326c4574ee5cb'and docs['cleanup'],'EXACT250_DOCUMENTED_PLAN_LINEAGE')
        old={p['path']:p for p in previous['source_pins']};documented={p['path']:p for p in docs['source_pins']}
        for name in sorted(inventory(guard.check)):
            q.pin(name)
            if name not in NEW|CHANGED:
                pin=documented.get(name,old.get(name));c.require(pin is not None and q.snapshots[name]==pin,'ALL_OTHER_SOURCE_SERVICES_ROUTER_NATIVE_GUARDS_AND_TESTS_UNCHANGED')
        for module in tuple(sys.modules.values()):
            value=getattr(module,'__file__',None)
            if value:
                path=Path(value).absolute()
                if path.is_relative_to(c.ROOT/'tools/p09')and path.suffix=='.py':q.pin(path.relative_to(c.ROOT).as_posix())
        inverse(q,old);expected(q)
        print(json.dumps(dict(state='BYTE_TRANSACTION_PROBE_PREFLIGHT',inputs=len(q.snapshots),one_negative_case=True,official249_reexecuted=False)),flush=True)
        snapshot=prior.base.base.prior.base.base.base.prior.prior.base.prior.base.prior.base.base.snapshot
        try:
            harness.run_one('one_staged_output_tamper_case_before_repair',[harness.CARGO,'test','--offline','--locked','-j','1','-p','operation-engine',
                '--test','workspace_transaction','--message-format=short','--',CASE,'--exact','--test-threads=1'],{CASE},guard,audit.environment(),row,observe_capture=snapshot)
        except ValueError:
            c.require(len(row['steps'])==1 and row['steps'][0]['exit_code']==101 and row['steps'][0]['tests']==[(CASE,'FAILED')],
                'ONLY_EXPECTED_NEGATIVE_CASE_FAILURE_NOT_COMPILATION_OR_RESOURCE_ERROR')
        else:raise ValueError('EXPECTED_TAMPER_FAILURE_NOT_REPRODUCED')
        q.finish();guard.check(force=True)
        row.update(state='REPRODUCED_STAGED_OUTPUT_TAMPER_TEST_FAILURE_NOT_ACCEPTANCE_OR_GATE',fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,
            security_negative_test_failed=True,total_accepted_cases=0,next_work='streaming_staged_and_published_result_identity_checks_then_12_new_and9_affected_file_regressions')
    except(ValueError,OSError,KeyError,TypeError,AttributeError,subprocess.SubprocessError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'TRANSACTION_BYTES_PROBE_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();samples=guard.samples;row.update(cleanup=guard.cleanup and all(s['cleanup']for s in row['steps']),elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=samples,
            system_CPU_max=max((s['system_cpu_percent']for s in samples),default=None),available_RAM_min_percent=min((s['available_ram_percent']for s in samples),default=None))
        if samples and all(list(s)==list(samples[0])for s in samples):
            keys=list(samples[0]);values=[[s[k]for k in keys]for s in samples];c.require([dict(zip(keys,v))for v in values]==samples,'LOSSLESS_BYTE_PROBE_SAMPLES');row['resource_samples']=dict(encoding='lossless_columns_v1',columns=keys,rows=values)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,prior.compact.pack(row),NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'steps':[{**{k:s.get(k)for k in('stage','exit_code','diagnostics','summaries','panic_locations')},'tests':s.get('tests',[])}for s in row['steps']],'pin':pin}),flush=True)
    return 0 if row['state'].startswith('REPRODUCED_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
