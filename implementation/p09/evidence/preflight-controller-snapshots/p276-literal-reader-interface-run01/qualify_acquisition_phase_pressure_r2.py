"""P276: support 전용 literal 기록 검토+작은 Native14/s. 제품/fullscope 대체 아님.

P275 실패52MiB metadata replay 불변. 수용된94/실패95/old32계약만 검토하여
support의 불필요한 과거 전체 ancestry 반복을 제거. 전체 실행은 별도 연결/검증 필요.
"""
import argparse
import io
import json
import sys
import unittest
from unittest.mock import patch
import qualify_acquisition_phase_pressure as original

runtime=original.runtime;p=original.p;g=original.g
SELF='tools/p09/qualify_acquisition_phase_pressure_r2.py'
TEST='tools/p09/tests/test_acquisition_phase_pressure_r2.py'
SCHEMA='hwpx-agent.p09-literal-acquisition-phase-pressure-qualification/v1'
PASS='PASS_LITERAL95_STOP_REVIEW_AND_SMALL_NATIVE14_NOT_FULL_RUNTIME_OR_GATE'
COUNT=38
FAILED_SUPPORT=dict(path=p.DIR+'/p275-acquisition-phase-pressure-run01.v1.json',bytes=112398,
    sha256='0d84b558fb3c5785d66105bfd9ff95bb94e129c926176a18fc2bccca667695f1')
FROZEN_CODE=(dict(path=original.SELF,bytes=17050,sha256='b9fd030f1b4d1526b5d7bd21bf095ebf906e2cce0d4cd4e11919a147fd3b2813'),
    dict(path=original.TEST,bytes=8666,sha256='c5db68b6e5aae547da1536e0c4bd758435cbc091c81b5a0ca2c9246ea0ee5912'))


def require(ok,code):original.require(ok,'LITERAL_SUPPORT_'+code)


def accepted(root,body):
    runtime.closed_attempt(root)
    require(root['state']==runtime.PASS and root['selected_test_index']==94
        and root['selected_test_name']==runtime.a.NAME and root['runtime_contract_executions']==650
        and root['resource_stop_reason'] is None and root['resource_watcher_cleanup_confirmed'] is True
        and root['accepted_exact_product_body_count']==1 and root['actual_product_child_executed'] is True,
        'LITERAL94_COMPLETE_NOT_CALLER_DECLARATION')
    f=root['closing_component']['source_frame'];rows=f['actual_byte_boundaries']
    require(f['frame_state']=='COMMITTED' and f['registered_live_frame'] is False
        and f['input_count']==1579 and f['input_bytes']==119639255
        and [x['role'] for x in rows]==['before','after'] and rows[0]['actual_byte_pins']==rows[1]['actual_byte_pins'],
        'HISTORICAL94_TWO_WHOLE_BYTE_PROOF_NOT_CURRENT_FRESH')
    required=p.v.pins(rows[0]['actual_byte_pins']);extras=p.v.pins(root['extra_frame_controller_pins'])
    runtime.native_pair(root['closing_component'],body,root['case_receipt_pin'],required,root['binding'],extras)
    p.validate_parent(body,root['selected_test_name'],root['binding'],required);runtime.job_contract(body)
    require(body['state']=='PASS_SCOPED_NOT_GATE' and body['task']=='p204-r07-case-094-tests'
        and body['job_final']['active_processes']==0 and body['owned_tree_empty'] is True
        and root['P09_gate']==root['A12_gate']==root['A13_gate']=='OPEN'
        and all(root[k] is False for k in ('whole1470_current_fresh_qualified','historical67_current_fresh_qualified',
            'full249_current_qualified','signed16_current_qualified','product_complete','PC_freeze_resolved')),
        'OLD_ACCEPTANCE_NOT_NEW_BODY_SOURCE_OR_GATE')
    plan=root['runtime_plan'];require(plan['runtime_source_qualified_individual_cases']==88
        and plan['next_runtime_index']==95 and plan['runtime_remaining_individual_cases']==161
        and plan['runtime_remaining_regular_cases']==155 and plan['runtime_remaining_corpus_cases']==6,
        'LITERAL88_NOT_RUNTIME_ADVANCE')
    return plan,required


def support_failure(doc):
    require(doc['schema_version']==original.SCHEMA and doc['state']=='FAILED_NOT_ACCEPTED'
        and doc['error_code']==doc['resource_stop_reason']==original.STOP
        and doc['resource_watcher_cleanup_confirmed'] is True and doc['phase_contract_tests_passed']==32
        and doc['IO']['read_passes']==368 and doc['IO']['bytes_read']==52539972
        and doc['IO']['bound_inputs']==201 and doc['IO']['final_fresh_hashes']==135
        and doc['IO']['finished'] is False and 'small_native_probe' not in doc
        and doc['actual_full_runtime_connection_qualified'] is False
        and doc['actual_product_body_reexecuted'] is False and doc['actual_current95_reexecuted'] is False,
        'ORIGINAL_SUPPORT_STOP_NOT_NATIVE_PASS')
    return dict(original_metadata_read_bytes=52539972,original_fresh_inputs=135,original_bound_inputs=201,
        original_support_CPU_STOP_preserved=True,original_small_native_executed=False,original_support_accepted=False)


def future_budget():
    row=original.budget(1583,p.m.EXE['bytes'],119639255-p.m.EXE['bytes']+1048576)
    row.update(full_scope_upper_inputs=1585,nominal_seconds=row['nominal_seconds']+2/14+4/20,
        future_original1579_plus_six_controller_upper=True)
    require(row['nominal_seconds']<600 and row['original_IO_scope_seconds']==600
        and row['original_shared_metadata_read_limit']==720,'FUTURE1585_ORIGINAL600_NO_SCOPE_DROP')
    return row


def read_budget(io):
    require(io['bound_inputs']<=32 and io['read_passes']<=72 and io['bytes_read']<=8*1048576
        and io['finished'] is True and io['bound_inputs']==io['final_fresh_hashes'],
        'SUPPORT_ONLY_LITERAL32_INPUT_8MIB_NOT_FULL_RUNTIME')


def contracts(root,body,failed,plan,prototype):
    require(original.contracts(failed,plan)==32,'ORIGINAL32_RETAINED')
    sys.path.insert(0,str(p.c.ROOT/'tools/p09/tests'));import test_acquisition_phase_pressure_r2 as tests
    with patch.object(tests,'FIXTURES',(root,body,prototype)), \
            patch('subprocess.Popen',side_effect=AssertionError('NO_LITERAL_SUPPORT_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('NO_LITERAL_SUPPORT_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('NO_LITERAL_SUPPORT_THREAD')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
    require(result.wasSuccessful() and result.testsRun==6 and not result.skipped,'NEW6_EXACT')
    return 38


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=int,required=True);args=ap.parse_args()
    require(p.c.Path.cwd().resolve()==p.c.ROOT and 1<=args.run<=99,'CWD_RUN')
    destination=p.c.ROOT/f'{p.DIR}/p276-literal-phase-pressure-run{args.run:02}.v1.json'
    require(not destination.exists(),'NO_OVERWRITE')
    context=g.observation.Context();owner=g.observation.Resources(context);q=frame=early=None;proposed=None;stage='admission'
    out=dict(schema_version=SCHEMA,state='FAILED_NOT_ACCEPTED',**p.r.flags(),accepted94_pin=original.SUCCESS,
        original95_failure_pin=original.FAILURE,failed_support_pin=FAILED_SUPPORT,
        actual_product_body_reexecuted=False,actual_full_source_executed=False,actual_current95_reexecuted=False,
        actual_full_runtime_connection_qualified=False,CPU_or_PC_freeze_improvement_established=False,
        current_full1579_source_fresh_qualification_claimed=False,support_only_literal_scope_selected=True)
    try:
        owner.admit();stage='reader_constructor';q=runtime.Reader(owner,context);stage='literal_review'
        root=runtime.m.review.bound_json(q,original.SUCCESS)
        body=runtime.m.review.bound_json(q,root['case_receipt_pin']);plan,required=accepted(root,body)
        failed=runtime.m.review.bound_json(q,original.FAILURE);checked=original.review(failed,plan)
        prototype=runtime.m.review.bound_json(q,FAILED_SUPPORT);prototype_review=support_failure(prototype)
        for name in runtime.NEW:require(q.pin(name)==required[name],'FROZEN_RUNTIME16')
        for pin in FROZEN_CODE:require(q.pin(pin['path'])==pin,'FROZEN_FAILED_SUPPORT_CODE')
        folder=p.c.ROOT/p.DIR
        require(sorted(x.name for x in folder.glob('p273-*.v1.json'))==
            sorted(pin['path'].split('/')[-1] for pin in (original.LIGHT,original.SUCCESS,original.FAILURE))
            and sorted(x.name for x in (folder/'cases').glob('p273-*.json'))==[root['case_receipt_pin']['path'].split('/')[-1]],
            'ONLY_REVIEWED_ATTEMPTS_NO95_BODY')
        require(sorted(x.name for x in folder.glob('p275-*.v1.json'))==[FAILED_SUPPORT['path'].split('/')[-1]],
            'ONLY_REVIEWED_SUPPORT_STOP')
        small={name:q.pin(name) for name in (SELF,TEST,original.SELF)}
        stage='contract_tests'
        with context.scope('contract_tests'):count=contracts(root,body,failed,plan,prototype)
        out.update(runtime_plan=plan,original95_review=checked,failed_support_review=prototype_review,
            phase_contract_tests_passed=count,future_full_scope_budget=future_budget(),small_required_pins=list(small.values()))
        stage='metadata_final_fresh';q.finish();read_budget(q.summary());stage='small_native'
        early=runtime.early_review.EarlySourceCheckpoint(owner.checkpoint_io,owner)
        held=original.InputLocks(p.c.ROOT,early,owner,context)
        frame=p.frames.Frame(p.frames.Registry(),small,early,held=held)
        context.reader=p.frames.Counters(q.reader,frame.readers)
        held.mark('before_acquire')
        with context.scope('metadata_hash'):frame.acquire()
        held.mark('after_acquire')
        def factory(guard):
            reader=original.observed.TraceReader(p.c.ROOT,original.pressure.PressureCheckpoint(guard,owner))
            p.qualification.lower_read_rate(reader);return reader
        for label in ('metadata_hash','final_fresh_hash'):
            with context.scope(label):frame.read_boundary(factory,owner.checkpoint_io)
        held.verify_two_byte_passes(small);held.verify_held_identities();require(frame.close(),'SMALL_CLOSE')
        original.validate_probe(frame.summary(),small);proposed=dict(state=PASS)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,IndexError,KeyboardInterrupt) as error:
        out.update(error_code=p.b.run.original.closed_error(error),failure_diagnostic=runtime.diagnostic(error,stage))
    finally:
        if frame is not None:
            try:
                if not frame.close():out['error_code']='LITERAL_PHASE_FRAME_CLEANUP_FAILED';proposed=None
            except (ValueError,OSError):out['error_code']='LITERAL_PHASE_FRAME_CLEANUP_FAILED';proposed=None
            out['small_native_probe']=frame.summary()
        if q is not None:q.close_entry();out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        if early is not None:out['early_source_checkpoint']=early.summary()
        out['metadata_observation']=g.observation.summary(owner)
        def validate(doc):
            original.validate_probe(doc['small_native_probe'],small);read_budget(doc['IO'])
            require(doc['phase_contract_tests_passed']==COUNT and doc['runtime_plan']==plan
                and doc['actual_full_runtime_connection_qualified'] is False
                and doc['current_full1579_source_fresh_qualification_claimed'] is False,'CLOSED_SUPPORT_NOT_RUNTIME')
        g.complete(out,owner,proposed,validate)
        with destination.open('x',encoding='utf-8') as stream:
            runtime.r.compact.dump(out,stream,checkpoint=lambda:require(owner.done.is_set(),'TERMINAL_ONLY'),indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','phase_contract_tests_passed','error_code','resource_stop_reason')}))
    return 0 if out['state']==PASS else 2


if __name__=='__main__':
    sys.modules.setdefault('qualify_acquisition_phase_pressure_r2',sys.modules[__name__])
    raise SystemExit(main())
