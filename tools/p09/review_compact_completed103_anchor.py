"""P318: 이미 독립 수용된96을 literal 체크포인트로 사용해103만 닫는다.
역사 본문 재실행/역사 전체 체인 재읽기 없음. 현재 code81은 모두 live/final-fresh.
원103 전체1644두byte/Native/Job/600/720을 기존 typed classifier로 검증한다.
새 review/test2는 metadata qualification이며103 Native 범위에 포함됐다고 주장하지 않는다.
"""
import copy
import io
import json
import sys
import unittest
from unittest.mock import patch
import resume_completed102_guarded_contract_runtime as m
SELF='tools/p09/review_compact_completed103_anchor.py'
TEST='tools/p09/tests/test_compact_completed103_anchor.py'
PRIOR={'path':m.p.DIR+'/p313-actual102-accepted-status-doc-r0124-run01.v1.json','bytes':79488,'sha256':'7b4aa8fa08c9ee5257875ef0d664875508ff866bf78a4c106db5e02f2482e589'}
ROOT={'path':m.p.DIR+'/p317-case-103-run002.v1.json','bytes':646652,'sha256':'57e2ac01febecd9f718a4b71578722fcf51534d4c5a07c5fd3a8d2e4fa0b13cd'}
BODY={'path':m.p.DIR+'/cases/p317-case-103-run002.json','bytes':190979,'sha256':'64a8caed8fa915304f264136f324f50faa11e696f509cd246441553a871aef2c'}
RAW={'path':m.p.DIR+'/p317-actual103-perfproc-before-after-raw-run03.v1.json','bytes':253747,'sha256':'78375fa9a4d1b79f60d89e5d88889c8855258224b50eedede85d32be1d0142fd'}
REVIEW_STOP={'path':m.p.DIR+'/p317-actual103-independent-review-stop-run04.v1.json','bytes':8266,'sha256':'4ccbcd692eff9823d93eca7d79b84440d1a0af8c37f9e176dede2b4725f50544'}
FROZEN81=m.FROZEN77+m.GUARDED_CODE+[
 {'path':m.SELF,'bytes':32161,'sha256':'d5d61ac6dbd3ce48440a1bdbde6399ebfe075e15c36beb8c9ad25b1ae2510416'},
 {'path':m.TEST,'bytes':17635,'sha256':'d0dccf2443da200b42c51cbbaaea064d83c637c2c4609781372fee5e473e1ebc'}]
PASS='PASS_COMPACT_ACCEPTED96_CHECKPOINT_AND_EXACT103_NOT_WHOLE_OR_GATE'
COUNT=26
FIXTURES=None

def require(ok,code):m.require(ok,'COMPACT103_'+code)

def policy():
 return dict(accepted_checkpoint_pin=PRIOR,qualified_checkpoint_is_not_failed_or_declared_plan=True,
  frozen_checkpoint_instead_of_historical_body_replay=True,current81_code_live_and_final_fresh_required=True,
  original_103_full1644_two_byte_native_and_job_required=True,
  original_guards_and_reader_and_rates_preserved=True,missing_pin_or_changed_code_denies=True,
  new_review2_not_claimed_as_prior_Native_coverage=True,whole_or_gate_acceptance=False)

def validate(prior,root,body,names,expected,legacy,current,prior_body):
 require(type(prior) is dict and prior['state']=='PASS_EXACT_ACTUAL102_ACCEPTED_AND_R124_DOCUMENTS_NOT_WHOLE_OR_GATE'
  and prior['document_revision']==124 and prior['actual102_root_pin']==m.COMPLETED102
  and prior['actual102_typed_compound_recomputed'] is True and prior['all77_currently_Native_covered'] is True
  and prior['current77_Native_source_covered_code_pins']==m.FROZEN77
  and prior['resource_stop_reason'] is None and prior['resource_watcher_cleanup_confirmed'] is True
  and prior['IO']['finished'] is True and prior['IO']['bound_inputs']==prior['IO']['final_fresh_hashes']==106
  and prior['full_source_count']==1640 and prior['full_source_bytes']==120455622
  and prior['actual_product_or_Native_replayed_during_review'] is False,'QUALIFIED96_BOUNDARY_NOT_DECLARED_FAILED_OR_PARTIAL')
 base=prior['runtime_plan']
 require(base['runtime_source_qualified_individual_cases']==96 and base['next_runtime_index']==103
  and base['runtime_remaining_individual_cases']==153 and base['runtime_remaining_regular_cases']==147
  and base['runtime_remaining_corpus_cases']==6,'EXACT96_CHECKPOINT_SCOPE')
 require(list(current.values())==FROZEN81 and len(current)==81,'ALL81_CURRENT_DISTINCT_CODE')
 required=m.p.v.pins(body['source_freeze']);added=m.p.v.pins(root['scope_added_nineteen_pins'])
 extras=m.p.v.pins(root['extra_frame_controller_pins']);baseline={n:p for n,p in required.items() if n not in added}
 previous_required=m.p.v.pins(prior_body['source_freeze'])
 new4={n:current[n] for n in (m.guarded.SELF,m.guarded.TEST,m.SELF,m.TEST)}
 # 원 개별 runtime source와 whole1470 manifest는 같은 목록이 아니다.
 # 미닫힘 historical67을 현재 개별수용으로 승격하지 않고 원 범위를 그대로 비교한다.
 require(len(previous_required)==1640 and sum(p['bytes'] for p in previous_required.values())==120455622
  and prior['actual102_body_pin']['sha256']=='e912207e3038a70103d40e4f2785b9e9c6070899e5dd68bf140307a445dd235f'
  and required=={**previous_required,**new4} and not set(previous_required)&set(new4)
  and set(expected)-set(required)==set(expected)-set(previous_required)
  and len(set(expected)-set(required))==67,'EXACT_ACCEPTED1640_PLUS4_NOT_WHOLE1470_OR_HISTORICAL67')
 require(root['case_receipt_pin']==BODY and root['selected_test_index']==103
  and len(required)==1644 and sum(p['bytes'] for p in required.values())==120516712
  and len(extras)==177 and list(added)==list(m.NEW)
  and len(names)==249 and len(expected)==1470 and all(required[p['path']]==p for p in FROZEN81),
  'EXACT_103_BODY_AND_ALL_SOURCE_CODE_NOT_SUBSET')
 binding=m.p.v.identity(names,expected,m.p.m.EXE)
 require(root['binding']==binding and root['prior_runtime_plan']==base,'SAME_COMPILED_SCOPE_AND_EXACT_PRIOR96')
 plan=m.record(root,body,BODY,required,binding,extras,names,legacy,base,baseline,added)
 require(plan['runtime_source_qualified_individual_cases']==97 and plan['next_runtime_index']==104
  and plan['runtime_remaining_individual_cases']==152 and plan['runtime_remaining_regular_cases']==146
  and plan['runtime_remaining_corpus_cases']==6
  and plan['all_successful_bodies_pending_whole_reconciliation']==94
  and plan['runtime_successful_candidates_requiring_closing']==0,'EXACT_SINGLE_ADVANCE_NOT_WHOLE')
 return plan,required,extras,baseline,added

def load(q):
 bound=m.m.m.review.bound_json
 prior=bound(q,PRIOR);root=bound(q,ROOT);body=bound(q,BODY);prior_body=bound(q,prior['actual102_body_pin'])
 inventory=bound(q,root['binding']['compiled_inventory_pin'])
 prep=bound(q,m.p.b.BASE_PREP);legacy=bound(q,m.g.old.PRIOR)['legacy_plan']
 names=inventory['source_test_names'];expected=m.p.v.pins(prep['whole_inputs'])
 current={p['path']:q.pin(p['path']) for p in FROZEN81}
 require(list(current.values())==FROZEN81,'FROZEN81_DRIFT_DENIES')
 fixtures=(prior,root,body,names,expected,legacy,current,prior_body)
 validate(*fixtures)
 return fixtures

def main():
 sys.path.insert(0,str(m.p.c.ROOT/'tools/p09/tests'))
 import test_compact_completed103_anchor as tests
 c=m.g.observation.Context();o=m.g.observation.Resources(c);q=None;out=dict(
  schema_version='hwpx-agent.p09-compact-accepted103-checkpoint-review/v1',state='FAILED_NOT_ACCEPTED',
  **m.p.r.flags(),policy=policy(),product_or_Native_reexecuted=False,
  historical_chain_reconstructed_or_original_bodies_reexecuted=False,new_review_code_Native_qualified=False)
 stage='admission'
 try:
  o.admit();q=m.Reader(o,c);stage='compact_load'
  fixtures=load(q);prior,root,body,names,expected,legacy,current,prior_body=fixtures
  stopped=m.m.m.review.bound_json(q,REVIEW_STOP)
  require(stopped['state']=='FAILED_NOT_ACCEPTED' and stopped['resource_stop_reason']==stopped['error']=='STOP_SUSTAINED_SYSTEM_CPU'
   and stopped['resource_watcher_cleanup_confirmed'] is True
   and stopped['IO']['read_passes']==85 and stopped['IO']['bound_inputs']==85 and stopped['IO']['final_fresh_hashes']==0
   and stopped['IO']['finished'] is False and stopped['original_actual103_PASS_preserved'] is True,'PRESERVED_REVIEW_FAILURE_NOT_ANCHOR')
  code=[q.pin(SELF),q.pin(TEST)];stage='contracts'
  with c.scope('contract_tests'),m.guarded.bind(q.reader.checkpoint) as statistics, \
   patch.object(tests,'FIXTURES',fixtures), \
   patch('subprocess.Popen',side_effect=AssertionError('NO_CHILD')), \
   patch('subprocess.run',side_effect=AssertionError('NO_CHILD')), \
   patch('threading.Thread.start',side_effect=AssertionError('NO_THREAD')):
   rr=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
  require(rr.wasSuccessful() and rr.testsRun==COUNT and not rr.skipped,'ALL26_MUTATION_CONTRACTS')
  s=statistics.summary()
  require(s['started_tests']==s['stopped_tests']==s['successful_before_test_checks']==s['successful_after_test_checks']==26
   and s['runner_calls']==s['returned_runner_calls']==1,'EVERY26_CHECKPOINT')
  stage='counter_link'
  packet=m.m.m.review.bound_json(q,RAW)
  require(packet['actual_exit_code']==0 and packet['capture_stage']=='completed' and packet['counter_error'] is None
   and packet['role']=='SUPPLEMENTARY_DIAGNOSTIC_NOT_GUARD_OR_PRODUCT_ACCEPTANCE','COUNTER_NOT_GUARD')
  window=m.counter.window(packet['before'],packet['after'],packet['processors'])
  plan,required,extras,baseline,added=validate(*fixtures)
  f=root['closing_component']['source_frame'];h=f['handles']
  frame_summary=dict(frame_state=f['frame_state'],registered_live_frame=f['registered_live_frame'],
   input_count=f['input_count'],input_bytes=f['input_bytes'],
   locks_opened=h['input_lock_handles_opened'],locks_closed=h['input_lock_handles_closed'],locks_remaining=h['input_lock_handles_remaining'],
   duplicate_summary=h['borrowed_byte_streams'],metadata_checks=h['handle_metadata_checks'],
   native_reservations=h['native_open_pacing']['open_reservations'],
   timing=h['lock_timing_diagnostic'],acquisition=h['acquisition_phase_pressure'],
   whole_source_boundaries=[dict(role=b['role'],count=len(b['actual_byte_pins']),
     reads=b['reader_diagnostics']['read_passes'],bytes=b['reader_diagnostics']['bytes_read']) for b in f['actual_byte_boundaries']],
   complete_original_frame_preserved_in_pinned_root=ROOT)
  out.update(runtime_plan=plan,root_pin=ROOT,body_pin=BODY,accepted_checkpoint_pin=PRIOR,
   preserved_review_STOP_pin=REVIEW_STOP,actually_executed_mutation_contracts=26,contract_statistics=s,
   actual103_original254_contracts_reused_not_reexecuted=True,
   original_scope_count=1644,original_scope_bytes=120516712,original_controller_count=177,
   current81_Native_covered_code_pins=list(current.values()),new2_metadata_only_code_pins=code,
   counter_raw_pin=RAW,counter_window=window,source_frame_summary=frame_summary,
   original_product_terminal=body['terminal_summary'],original_product_exit=body['exit_code'],
   original_product_job=body['job_final'],original_product_capture=body['capture'],
   original_source_readers=[{k:r[k] for k in ('read_passes','bytes_read')} for r in body['owned_source_reader_passes']],
   original_runtime_observation={k:v for k,v in root['metadata_observation'].items() if k!='samples'},
   original_runtime_preparation={k:root['preparation_IO'][k] for k in ('read_passes','bytes_read','bound_inputs','final_fresh_hashes','finished')},
   original_early_source=root['early_source_checkpoint'],original_root_cleanup=root['resource_watcher_cleanup_confirmed'],
   original_root_STOP=root['resource_stop_reason'])
  stage='final_fresh';q.finish();out['state']=PASS
 except (ValueError,OSError,KeyError,TypeError,AttributeError,IndexError,KeyboardInterrupt) as e:
  out['error']=m.p.b.run.original.closed_error(e);out['diagnostic']=m.m.diagnostic(e,stage)
 finally:
  if q is not None:q.close_entry();out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
  out['review_observation']={k:v for k,v in m.g.observation.summary(o).items() if k!='samples'}
  m.g.complete(out,o,None,None)
  if out.get('resource_stop_reason') or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
  print(json.dumps(out))
 return 0 if out['state']==PASS else 2

if __name__=='__main__':raise SystemExit(main())
