"""P270: metadata 최종읽기91→100 경고 검토/원90% 완화를 실제 reader에 연결.

기존95% pressure/98x4/RAM/600/720/모든읽기/표본/정리는 유지한다.
constructor 기존 경로는 유지하며 이후 owned metadata checkpoint만 감싼다.
"""
import argparse
import io
import json
import sys
import unittest
from unittest.mock import patch
import qualify_rejected_parent_connection_r2 as prior
import review_packed_cpu_peak_r2 as peak
a=prior.a;m=prior.m
SELF='tools/p09/qualify_early_metadata_pressure.py'
TEST='tools/p09/tests/test_early_metadata_pressure.py'
REPORT='implementation/p09/P09-270_EARLY_METADATA_PRESSURE_REPORT.md'
ROOT=dict(path=m.p.DIR+'/p269-rejected-parent-connection-run01.v1.json',bytes=163181,
    sha256='c9d9d95a434cb9b7c31dc80c460ad70eb175249c112e3dd1485baaeec669b1c5')
SCHEMA='hwpx-agent.p09-early-metadata-pressure-connection/v1'
PASS='PASS_EARLY_METADATA90_REVIEW_AND_REAL_READER_CONNECTION_NOT_RUNTIME_GATE_OR_CAUSE'
COUNT=32


def require(ok,code):a.require(ok,'EARLY_METADATA_'+code)


class Binding:
    def __init__(self,q,owner,*,sleep=m.early_review.m.entry.locks.time.sleep):
        require(q.resources is owner and q.finished is False and not hasattr(q,'early_metadata_binding'),
            'ONE_LIVE_EXACT_METADATA_OWNER')
        base=q.reader.checkpoint
        require(base is getattr(q,'pressure',None) and base.resources is owner,'ORIGINAL95_PRESSURE_NOT_REPLACED')
        self.original=base;self.early=m.early_review.EarlySourceCheckpoint(base,owner,sleep=sleep)
        # 원 Context/reader/counter/previous/entry binding/clock/deadline은 변경하지 않는다.
        q.reader.checkpoint=self.early;q.early_metadata_binding=self
    def summary(self):
        return dict(selected_metadata_warning_CPU_percent=90,constructor_original95_path_retained=True,
            original95_pressure_retained_as_base=True,original_guard_and_sampler_reused=True,
            reader_or_aggregate_counter_replaced=False,CPU_RAM600_or720_guard_extended=False,
            cleanup_callback_wrapped=False,new_sampler_or_thread_started=False,
            source_byte_or_identity_checks_skipped=False,CPU_or_PC_freeze_improvement_established=False,
            original_early_source_algorithm_statistics=self.early.summary())


class Reader(m.m.Reader):
    def __init__(self,owner,context):
        super().__init__(owner,context)
        try:Binding(self,owner)
        except BaseException:
            self.close_entry();raise
    def summary(self):
        return dict(super().summary(),early_metadata_pressure=self.early_metadata_binding.summary())


def review(root):
    require(root['schema_version']==prior.SCHEMA and root['state']==prior.PASS
        and root.get('error_code') is None and root.get('terminal_diagnostic_write_error') is None
        and root['resource_stop_reason'] is None and root['resource_watcher_cleanup_confirmed'] is True
        and root['IO']['finished'] is True and root['IO']['bound_inputs']==root['IO']['final_fresh_hashes']==179
        and root['connection_contract_tests_passed']==88 and root['actual_product_body_or_full_source_executed'] is False
        and root['actual_current_case94_reexecuted'] is False,'ORIGINAL_P269_CLOSED_SMALL_ONLY')
    prior.validate_probe(root['small_native_probe'],m.p.v.pins(root['small_required_pins']),root['lock_timing'])
    rows=root['metadata_observation']['samples'];summary=peak.summarize(rows)
    require(summary['sample_count']==79 and summary['system_peak_percent']==100
        and summary['samples_at_or_above95']==summary['samples_at_or_above98']==summary['maximum_consecutive98_samples']==1
        and summary['own_CPU_max_at_warning']==0 and summary['job_CPU_max_at_warning'] is None
        and summary['warning_phase_counts']=={'final_fresh_hash':1},'METADATA_WARNING_NOT_SMALL_NATIVE_OR_SUSTAINED_STOP')
    neighbors=summary['first_warning_numeric_neighbors']
    require(len(neighbors)==3 and [x['system_cpu_percent'] for x in neighbors]==[91.21,100,91.41]
        and [x['audited_logical_read_bytes_delta'] for x in neighbors]==[1011056,973048,0],
        'OBSERVED91_BEFORE100_AND_OLD_PAUSE_NOT_CAUSE')
    a.no_promotion(root)
    return dict(peak=summary,earlier90_metadata_warning_has_observed_pre95_window=True,
        reading_cause_or_external_PID_established=False,CPU_or_PC_freeze_improvement_established=False,
        original95_pause_did_not_prevent_single100_sample=True,runtime_acceptance_changed=False,
        original_parent94_reason_still_unavailable=True)


def contracts(root):
    sys.path.insert(0,str(m.p.c.ROOT/'tools/p09/tests'))
    import test_early_metadata_pressure as tests
    import test_checkpoint_queue_stop as retained
    with patch.object(tests,'FIXTURES',root),patch('subprocess.Popen',side_effect=AssertionError('NO_METADATA_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('NO_METADATA_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('NO_METADATA_THREAD')):
        suite=unittest.TestSuite((unittest.defaultTestLoader.loadTestsFromTestCase(retained.EarlySourceTests),
            unittest.defaultTestLoader.loadTestsFromModule(tests)))
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    require(result.wasSuccessful() and result.testsRun==COUNT and not result.skipped,'ORIGINAL12_NEW20_NO_SKIP')
    return COUNT


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=int,required=True);args=ap.parse_args()
    require(m.p.c.Path.cwd().resolve()==m.p.c.ROOT and 1<=args.run<=99,'CWD_RUN')
    destination=m.p.c.ROOT/f'{m.p.DIR}/p270-early-metadata-pressure-run{args.run:02}.v1.json'
    require(not destination.exists(),'FRESH_ONLY')
    context=m.g.observation.Context();owner=m.g.observation.Resources(context);q=proposed=None
    out=dict(schema_version=SCHEMA,state='FAILED_NOT_ACCEPTED',**m.p.r.flags(),original_warning_root_pin=ROOT,
        actual_product_body_or_full_source_executed=False,actual_current_case94_reexecuted=False,
        actual_full_runtime_connection_qualified=False,CPU_or_PC_freeze_improvement_established=False)
    try:
        owner.admit();q=Reader(owner,context)
        plan,required,binding=a.qualified_before_failure(q)
        failed=m.m.review.bound_json(q,a.FAILURE);require(q.pin(a.ZERO['path'])==a.ZERO,'ORIGINAL94_ZERO_PRESERVED')
        a.review(failed,a.ZERO,plan,required,binding)
        root=m.m.review.bound_json(q,ROOT);checked=review(root)
        require(root['runtime_plan']==plan,'SAME_87_NOT_RUNTIME_ADVANCE')
        sidecar=m.m.review.bound_json(q,root['small_terminal_diagnostic_pin'])
        require(sidecar['state']=='REJECTED_ORIGINAL_PARENT_DIAGNOSTIC_NOT_ACCEPTED'
            and sidecar['diagnostic_only'] is True and sidecar['runtime_accepted'] is False
            and sidecar['original_parent_document']['job_final'] is None
            and sidecar['original_frame_snapshot']==root['small_native_probe'],'ORIGINAL_DIAGNOSTIC_NOT_JOB_OR_RUNTIME')
        frozen=m.p.v.pins(root['bound_input_pins'])
        for name in (prior.SELF,prior.TEST,a.SELF,a.TEST):require(q.pin(name)==frozen[name],'FROZEN_CONNECTION_CODE')
        report=q.text(REPORT);require(ROOT['sha256'] in report and a.FAILURE['sha256'] in report
            and all(w in report for w in ('runtime 수용87/249','원600초·CPU/RAM 기준은 변경하지 않음',
                '실제 full runtime 연결 NOT_RUN','PC 프리즈 원인·해결 미확정')),'REPORT_BOUNDARY')
        for name in (SELF,TEST):q.pin(name)
        out.update(review=checked,runtime_plan=plan,metadata_contract_tests_passed=contracts(root))
        require(q.reader.checkpoint is q.early_metadata_binding.early
            and q.early_metadata_binding.original is q.pressure
            and q.early_metadata_binding.original.resources is owner,'REAL_READER_SAME_ORIGINAL95_OWNER')
        q.finish();out['required_bound_input_names']=sorted(q.reader.snapshots)
        proposed=dict(state=PASS)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out['error_code']=m.p.b.run.original.closed_error(error)
    finally:
        if q is not None:q.close_entry();out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        def validate(doc):
            require(doc['IO']['finished'] is True and doc['IO']['bound_inputs']==doc['IO']['final_fresh_hashes']
                and sorted(x['path'] for x in doc['bound_input_pins'])==doc['required_bound_input_names']
                and doc['metadata_contract_tests_passed']==COUNT,'ALL_BOUND_FRESH_AND32')
            m.m.metadata_contract(doc['IO'])
        m.g.complete(out,owner,proposed,validate);out['metadata_observation']=m.g.observation.summary(owner)
        with destination.open('x',encoding='utf-8') as stream:json.dump(out,stream,ensure_ascii=True,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','metadata_contract_tests_passed','error_code','resource_stop_reason')}))
    return 0 if out['state']==PASS else 2


if __name__=='__main__':raise SystemExit(main())
