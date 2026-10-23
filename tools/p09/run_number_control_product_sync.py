"""Selected number-control product/docs closure, no26-case/Cargo/727-input replay."""
import json,re,time
from types import SimpleNamespace as NS
import run_number_control_product_components as target
import run_number_control_review_sync as retained
shared,c,a,tools=target.shared,target.c,target.a,target.tools
OUTPUT='implementation/p09/evidence/p09-361-number-control-product-sync204.v1.json'
PROFILE='protocol/migrations/p09-number-control-product-request-v1.md'
DOCS=set(retained.DOCS)|{PROFILE}
RETAINED=retained.RETAINED|target.NEW|target.CHANGED|{'tools/p09/run_number_control_product_components.py'}


def norm(text):return ' '.join(text.split())


def main():
    c.require(not(c.ROOT/OUTPUT).exists(),'NUMBER_CONTROL_PRODUCT_SYNC_IMMUTABLE_RUN_EXISTS');selection=tools.select_own_single_cpu();shared.host.configure_host_policy(c)
    guard=shared.baseline.guard_type(shared.policy.guard_type(shared.final.guard_type(a.Guard),role='whole_metadata_preflight'))()
    q=None;started=time.monotonic();row=dict(state='FAILED_NUMBER_CONTROL_PRODUCT_DOC_SYNC',actual_Cargo_or_tests=False,actual_Hangul_or_COM=False,
        own_cpu_selection=selection,Native011_executed=False,prior_Native_replayed=False,accepted_count_delta=0,P09_gate='OPEN',P10_started=False,
        native_counter_full_control_transaction_or_gate_qualified=False)
    try:
        guard.acquire();q=a.AcceptanceReader(c.ROOT,guard.check);passed=q.json(target.OUTPUT);baseline=q.json(target.prior.OUTPUT)
        c.require(q.snapshots[target.OUTPUT]['sha256']=='9909a7cb2f031ffce55d1395b041cc15ce6cd0fef117472a009852b80efecad0'
            and passed['state']=='PASS_NUMBER_CONTROL_TWENTY_SIX_PRODUCTS_NOT_NATIVE_COUNTER_FULL_TRANSACTION_OR_GATE'and passed['cleanup']
            and passed['fresh_inputs']==passed['final_fresh_hashes']==727 and passed['new_product_cases']==26
            and not passed['source67_reexecuted']and not passed['old266_products_reexecuted'],'EXACT203_NUMBER_PRODUCT26_FRESH_CLOSURE_AND_RETAINED_SCOPE')
        c.require(q.snapshots[target.prior.OUTPUT]['sha256']=='a8a32399ec72474a03f8672dc6530e661b0108f1c09e941232460c2808250450'
            and baseline['state']=='PASS_REVIEW_BOUND_NUMBER_SOURCE30_DIAGNOSTIC1_AFFECTED36_NOT_STORE_PRODUCT_NATIVE_OR_GATE'
            and baseline['total_executed_cases']==67 and baseline['cleanup'],'ORIGINAL200_SOURCE67_RETAINED_NOT_REPLAYED')
        tested={p['path']:p for p in passed['source_pins']};c.require(RETAINED<=tested.keys(),'SELECTED_NUMBER_PRODUCT_INPUTS_DECLARED_BY203')
        for name in sorted(RETAINED):q.pin(name);c.require(q.snapshots[name]==tested[name],'SELECTED_SERVICE_PRODUCT_VALUES_SOURCE_GUARDS_READBACK_AND_TESTS_MATCH203')
        target.inverse(q,{p['path']:p for p in baseline['source_pins']});tools.good_step(passed['steps'][0],target.expected(q))
        for name in sorted(DOCS):q.pin(name)
        q.pin('tools/p09/run_number_control_product_sync.py');progress=q.text('implementation/p09/P09_SEARCH_SOURCE_INDEX_PROGRESS.md')
        rows=re.findall(r'^\| SEARCH-(\d{3}) \|',progress,re.M);c.require(len(rows)==len(set(rows))==19 and not set(rows)&{'011','012','015','016','017','018'},'EXACT19_P09_SEARCH_ROWS_EXCLUDE_P11')
        for text in(q.text(PROFILE),progress,q.text('CURRENT_STATE.md')[:12500]):
            c.require('product-number-control-replacement-request/v1'in text and '26pass'in text and '727fresh/final727'in text
                and 'ValidatedNumberControlValues'in text and '158/249'in text and '91'in text and 'Native011'in text and 'P10'in text,
                'DOCS_NUMBER_PRODUCT_PROFILE_PASSES_VALUES_AND_UNCHANGED_GATES')
        profile=norm(q.text(PROFILE))
        for marker in('replace_number_controls','auto_number 또는 new_number','1~4096','i32','preserve','replace','include_hidden_explanations/include_memo_bodies',
            '22종','16KiB','UnsupportedKind','RouteUnqualified','fresh source proof','Borrowed/Owned','forward iterator','canonical payload',
            '원본67·이전 제품266· 공식249는 반복하지 않았다','고유292개','현재292개 단일 실행','추가 control0개','실제 저장/commit/CAS/'):
            c.require(norm(marker)in profile,'STRICT_TYPED_NUMBER_PREPARATION_PROOF_COST_TEST_SCOPE_AND_UNFINISHED_REAL_TRANSACTION_NATIVE_BOUNDARIES')
        c.require('현재 저장/엄격한 제품26개 검증, 다른 제어·전체 계약/실제 실행 미완료'in progress,
            'SEARCH009_CURRENT_PRODUCT26_NOT_FULL_CONTROL_OR_EXECUTION')
        c.require(passed['original_source_compiler_search_and_old_product_bodies_inverse_verified']
            and passed['one_borrowed_validated_format_current_source_proof_compiler_owner_move_and_no_search_replay']
            and passed['forward_anchor_subset_and_bounded_number_node_aggregation']and passed['canonical_payload_serialized_once_per_binding_check'],
            'REAL_SOURCE_PROOF_OWNER_MOVE_BOUND_NODE_CHECKS_AND_NO_SEARCH_REPLAY_RETAINED')
        q.finish();guard.check(force=True);row.update(state='PASS_SELECTED_NUMBER_CONTROL_PRODUCT_DOC_SYNC_NOT_NATIVE_COUNTER_TRANSACTION_OR_GATE',
            fresh_inputs=len(q.snapshots),final_fresh_hashes=q.final_fresh_hashes,product_cases_retained=26,source67_and_old266_products_reexecuted=False,
            full727_inputs_replayed=False,next_work='SEARCH009_other_control_families_reference_ID_preservation_and_remaining_full_P09_contract_transaction_native_gates')
    except(ValueError,OSError,KeyError,TypeError,AttributeError)as error:
        message=str(error);row.update(error_type=type(error).__name__,error_code=message if re.fullmatch('[A-Za-z0-9_]{1,160}',message)else'NUMBER_CONTROL_PRODUCT_DOC_SYNC_FAILURE_NO_RAW_VALUES')
    finally:
        guard.close();row.update(cleanup=guard.cleanup,elapsed_seconds=round(time.monotonic()-started,3),source_pins=[]if q is None else list(q.snapshots.values()),resource_samples=guard.samples)
        pin=shared.publisher.publish(c.ROOT,OUTPUT,row,NS(require=c.require,exact=lambda x,y,label:c.require(x==y,label)))
        print(json.dumps({**{k:row.get(k)for k in('state','error_code','fresh_inputs','final_fresh_hashes','cleanup','elapsed_seconds')},'pin':pin}),flush=True)
    return 0 if row['state'].startswith('PASS_')and row['cleanup']else 2


if __name__=='__main__':raise SystemExit(main())
