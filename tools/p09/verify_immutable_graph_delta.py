"""Whole inverse source delta + all parent inputs/protected EXEs + actual graph15.

Current product full249 EXE is STALE after this declared Rust edit; no restamp.
"""
import base64
import hashlib
import json
import re
import time
import prepare_current_stored_generation as s

SELF='tools/p09/verify_immutable_graph_delta.py'
ARCHIVE='implementation/p09/source-archive/p09-156-pre-immutable-graph-digest-r37/source-preimages.v1.json'
TYPECHECK='implementation/p09/evidence/p09-149-maintenance-run91.v1.json'
UNITS='implementation/p09/evidence/p09-156-immutable-graph.units-run01.v1.json'
NEW_TYPE='''#[derive(Clone, Serialize)]
#[serde(transparent)]
pub struct DocumentGraph(
    DocumentGraphDraft,
    #[serde(skip)] std::sync::OnceLock<[u8; 32]>,
);

// Memoized derived bytes are not document state. Warm/cold graphs must remain
// equal, and transparent serialization must remain exactly the original draft.
impl PartialEq for DocumentGraph {
    fn eq(&self, other: &Self) -> bool {
        self.0 == other.0
    }
}

impl Eq for DocumentGraph {}'''
OLD_TYPE='''#[derive(Clone, Eq, PartialEq, Serialize)]
#[serde(transparent)]
pub struct DocumentGraph(DocumentGraphDraft);'''
GETTER='''        // This graph is immutable after full from_draft validation. Cache ONLY
        // its 32-byte serialization digest, never source/ACL/head/policy/AEAD
        // verification. A newly admitted draft starts with a fresh empty cell.
        if let Some(digest) = self.1.get() {
            return Ok(*digest);
        }
'''
SETTER='''        let computed: [u8; 32] = digest.0.finalize().into();
        // Concurrent first readers may compute the same immutable byte stream;
        // no fallible serializer is run inside a reentrant cache initializer.
        let _ = self.1.set(computed);
        Ok(computed)'''
NEW_TESTS=('immutable_digest_memo_keeps_canonical_bytes_and_warm_cold_equality',
    'digest_memo_clone_and_reopened_graph_have_the_same_original_digest',
    'changed_draft_does_not_reuse_the_previous_immutable_digest',
    'digest_memo_does_not_bypass_new_draft_serialized_size_admission',
    'concurrent_immutable_digest_first_reads_return_identical_whole_bytes')


def require(ok,code):s.require(ok,'P156_DELTA_'+code)


def inverse(text):
    changes=((NEW_TYPE,OLD_TYPE),('Ok(Self(draft, std::sync::OnceLock::new()))','Ok(Self(draft))'),
        (GETTER,''),(SETTER,'        Ok(digest.0.finalize().into())'))
    for added,old in changes:
        require(text.count(added)==1,'DECLARED_WHOLE_DELTA');text=text.replace(added,old,1)
    return text.encode()


def main():
    require(s.c.Path.cwd().resolve()==s.c.ROOT,'CWD')
    destination=s.scoped_path('implementation/p09/evidence/p09-156-immutable-graph.source-closing-run02.v1.json',fresh=True)
    resources=s.SQLRuntimeResources();q=None;started=time.monotonic()
    out=dict(state='FAILED_NOT_ACCEPTED',source_closing_exact=False,full249_current_qualified=False,
        current_compiled249_qualified=False,signed16_current_qualified=False,product_complete=False,
        P09_gate='OPEN',PC_freeze_resolved=False,full_product_performance_improvement_measured=False,
        actual_audit_child_SQL_or_native_started=False,remaining_non_permission_work_units=76)
    try:
        resources.admit();q=s.LiveSQLReader(resources);q.pin(SELF);archive=q.json(ARCHIVE)
        basepin=archive['baseline_closing_pin'];require(q.pin(basepin['path'])==basepin,'BASELINE_CLOSING')
        parent=q.json(basepin['path']);require(parent['state']=='PASS_UNFILTERED_COST_DIAGNOSTIC_TERMINAL_ACCOUNTED_NOT_FULL249_OR_GATE'
            and parent['source_closing_exact'] and parent['contract_tests_passed']==75 and parent['protected_EXE_inputs_exact']==60,'BASELINE_SCOPE')
        expected=s.inputs.inventory(parent['bound_input_pins'],1239)
        require(len(archive['files'])==2,'EXACT_TWO_CHANGES');changed={};original_tests=None
        for item in archive['files']:
            n=item['path'];raw=base64.b64decode(item['base64'],validate=True);pin={k:item[k] for k in ('path','bytes','sha256')}
            require(expected.get(n)==pin and len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256'],'WHOLE_PREIMAGE')
            text=q.text(n);current=q.reader.snapshots[n];require(current!=pin,'REAL_SOURCE_CHANGE');changed[n]=current
            if n=='crates/domain-ir/src/document_graph.rs':require(inverse(text)==raw,'WHOLE_ORIGINAL_CORE_INVERSE_EXACT')
            elif n=='crates/domain-ir/tests/document_graph.rs':
                require(text.encode().startswith(raw),'ALL_ORIGINAL_TEST_BYTES_PRESERVED')
                added=text.encode()[len(raw):].decode();names=re.findall(r'(?m)^fn ([a-z0-9_]+)\(',added)
                require(tuple(names)==NEW_TESTS and added.count('#[test]')==5 and text.count('#[test]')==15,'NEW_FIVE_ONLY')
                original_tests=len(re.findall(r'(?m)^fn [a-z0-9_]+\(',raw.decode()))
            else:require(False,'CHANGED_SCOPE')
        require(set(changed)=={'crates/domain-ir/src/document_graph.rs','crates/domain-ir/tests/document_graph.rs'},'TWO_SOURCE_SCOPE')
        for n,pin in expected.items():
            if n not in changed:require(q.pin(n)==pin,'ALL_UNRELATED_INPUTS_EXACT')
        rust={n for n in expected if n.startswith(('crates/','protocol/generated/rust/','tools/xtask/'))
            and (n.endswith('.rs') or n.endswith('/Cargo.toml'))}
        require(len(rust)==785 and s.inputs.rust_inputs(s.c.ROOT,resources.checkpoint_io)==rust,'WHOLE_RUST785')
        check=q.json(TYPECHECK);units=q.json(UNITS)
        require(check['state']=='PASS_SCOPED_NOT_GATE' and check['task']=='domain-check' and check['stop_reason'] is None
            and check['cleanup_confirmed'] and check['owned_tree_empty'] and check['job_final']['active_processes']==0,'TYPE_CHECK_ONLY')
        require(units['state']=='PASS_CURRENT_IMMUTABLE_GRAPH_UNITS15_ONLY_NOT_FULL249_OR_GATE'
            and units['tests_passed']==15 and units['original_domain_cases']==10 and units['new_cache_regression_cases']==5
            and units['stop_reason'] is None and units['cleanup_confirmed'] and units['owned_tree_empty']
            and units['job_final']['active_processes']==0 and units['job_final']['owned_processes']==[]
            and units['isolated_target']==str(s.c.Path('target/p09-156-immutable-graph'))
            and units['policy']==s.c.POLICY,'ACTUAL15_NOT_PRODUCT')
        for row in (check,units):
            frozen={p['path']:p for p in row['source_freeze']}
            require(all(frozen.get(n)==p for n,p in changed.items()),'ACTUAL_CURRENT_CHANGED_SOURCE')
        for pin in units['source_freeze']:require(q.pin(pin['path'])==pin,'WHOLE_UNIT_INPUTS_CURRENT')
        exes=list((s.c.ROOT/'target/p09-156-immutable-graph/debug/deps').glob('document_graph-*.exe'))
        require(len(exes)==1,'EXACT_FRESH_DOMAIN_EXE');exe=q.pin(exes[0].relative_to(s.c.ROOT).as_posix())
        q.finish();out.update(state='PASS_CURRENT_IMMUTABLE_GRAPH_DELTA_AND_UNITS15_ONLY_NOT_FULL249_OR_GATE',
            source_closing_exact=True,whole_original_core_inverse_exact=True,all_original_domain_tests_preserved=True,
            declared_Rust_source_changes=list(changed.values()),protected_EXE_inputs_exact=sum(n.endswith('.exe') for n in expected),
            current_Rust_input_count=785,actual_unit_tests_passed=15,typecheck_accepted=True,fresh_domain_unit_executable_pin=exe,
            old_product_full_EXE_is_not_current_after_Rust_change=True,source_security_or_policy_checks_removed=False)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        code=str(error) if isinstance(error,ValueError) else 'P156_DELTA_REDACTED_FAILURE'
        out['error_code']=code if re.fullmatch('[A-Za-z0-9_]{1,160}',code) else 'P156_DELTA_REDACTED_FAILURE'
    finally:
        s.finish_watcher(resources,out);out['resource_stop_reason']=resources.reason
        if resources.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if q is not None:out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        out['wall_seconds']=round(time.monotonic()-started,4)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','actual_unit_tests_passed','whole_original_core_inverse_exact','protected_EXE_inputs_exact','error_code','wall_seconds','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2


if __name__=='__main__':raise SystemExit(main())
