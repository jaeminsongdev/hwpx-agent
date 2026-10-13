"""P305: 메타데이터의 원95 guard 안에 bounded90을 연결. hard/95/outer90/entry32 불변.
새 source/제품 실행 없음. 원102 준비 STOP 검토와 작은 실제 IO qualification만 수행.
"""
import io
import json
import sys
import unittest
from unittest.mock import patch
import leading_metadata_entry_pressure as previous
m=previous.m
SELF='tools/p09/leading_metadata_checkpoint_pressure.py'
TEST='tools/p09/tests/test_leading_metadata_checkpoint_pressure.py'
FAILURE={"path":"implementation/p09/evidence/locked-r07/p304-case-102-run002.v1.json","bytes":81902,"sha256":"a37eb691a8cb786f7b26d445267ecc550cdaf5b140e6a73f37f0b82d79249a5f"}
LIGHT={"path":"implementation/p09/evidence/locked-r07/p304-light-run001.v1.json","bytes":27993,"sha256":"f1dc5cd70aed230d3a01c9d18ff8ab3a476bd1a18367f82eeccf2e2d611a9e9b"}
PASS='PASS_INNER_HARD_GUARD90_REAL_READER_NOT_NEXT_RUNTIME_OR_GATE'
COUNT=30

def require(ok,code):m.require(ok,'INNER_METADATA_'+code)

class Binding:
    def __init__(self,q,owner,*,sleep=None):
        require(q.resources is owner and q.finished is False and q.reader.read_passes==0
            and not hasattr(q,'inner_metadata_binding'),'ONE_UNUSED_READER')
        self.q=q;self.owner=owner;self.pressure=q.pressure;self.original=self.pressure.base
        self.outer=q.early_metadata_binding.early;self.pacer=q.entry_binding.pacer
        require(self.pressure.resources is owner and callable(self.original)
            and q.reader.checkpoint is self.pacer.checkpoint is self.outer
            and self.outer.base is self.pressure and self.pacer.rate==32 and self.pacer.opens==0
            and self.pacer.previous is None and q.leading_entry_binding.active
            and q.leading_entry_binding.old95 is self.pressure,'EXACT_ORIGINAL_CALLBACK_GRAPH')
        kw={} if sleep is None else dict(sleep=sleep)
        self.early=m.early_review.EarlySourceCheckpoint(self.original,owner,**kw)
        self.calls=0;self.active=True
        def guarded():
            require(self.active and q.inner_metadata_binding is self
                and self.pressure.base is guarded,'EXACT_ACTIVE_INNER_GUARD')
            self.calls+=1;return self.early()
        self.guarded=guarded;self.pressure.base=guarded;q.inner_metadata_binding=self
    def close(self):
        if not self.active:return
        require(self.pressure.base is self.guarded,'RESTORE_EXACT_GUARD')
        self.pressure.base=self.original;self.active=False
    def summary(self):
        return dict(warning_CPU_percent=90,inner_guard_calls=self.calls,
            early_pressure=self.early.summary(),binding_active=self.active,
            original95_guard_callback_wrapped_only_while_bound=True,
            original_hard_CPU_RAM_IO600_callback_always_first=True,
            hard_callback_restored_after_close=not self.active and self.pressure.base is self.original,
            original95_object_and_outer90_and_entry32_callbacks_retained=
                self.q.pressure is self.pressure and self.outer.base is self.pressure
                and self.q.reader.checkpoint is self.pacer.checkpoint is self.outer and self.pacer.rate==32,
            original_reader_and_byte_pacer_and_counters_retained=True,
            new_sampler_or_thread_or_native_query_started=False,
            guards_or_deadline_or_source_coverage_relaxed=False,cleanup_not_guarded_or_paced=True,
            CPU_cause_or_PC_freeze_resolution_established=False)

class Reader(previous.Reader):
    def __init__(self,owner,context):
        super().__init__(owner,context)
        try:Binding(self,owner)
        except BaseException:super().close_entry();raise
    def close_entry(self):
        if hasattr(self,'inner_metadata_binding'):self.inner_metadata_binding.close()
        return super().close_entry()
    def summary(self):
        return dict(super().summary(),leading_metadata_checkpoint_pressure=self.inner_metadata_binding.summary())

def review_stop(d):
    require(d['schema_version']=='hwpx-agent.p09-completed101-anchor-runtime-pair/v1'
        and d['state']=='FAILED_NOT_ACCEPTED' and d['error_code']==d['resource_stop_reason']=='STOP_SUSTAINED_SYSTEM_CPU'
        and d['resource_watcher_cleanup_confirmed'] is True and d['failure_diagnostic']['stage']=='final_fresh_preparation'
        and d['selected_test_index']==102 and d['accepted_exact_product_body_count']==0
        and d['runtime_contract_executions']==132 and d['reused_retained_contract_executions']==1486,
        'EXACT_FAILED102_PREP_NOT_RUNTIME')
    require(d['prior_runtime_plan']['runtime_source_qualified_individual_cases']==95
        and d['prior_runtime_plan']['next_runtime_index']==102 and d['prior_runtime_plan']['runtime_remaining_individual_cases']==154
        and 'runtime_plan' not in d and 'terminal_source_frame' not in d and 'case_receipt_path' not in d
        and 'terminal_parent_failure_sidecar_pin' not in d
        and all(d[k] is False for k in ('actual_product_child_executed','early_source_guard_connected',
            'acquisition_phase_connection_selected','diagnostic_parent_connection_selected',
            'original_parent_capture_adapter_selected','aggregate_post_reader_connection_verified')),'NO_FRAME_JOB_BODY_OR_ADVANCE')
    row=d['preparation_IO'];x=row['leading_metadata_entry_pressure'];old=row['near_saturation_read_backpressure']
    require(row['read_passes']==154 and row['bytes_read']==9753235 and row['bound_inputs']==80
        and row['final_fresh_hashes']==44 and row['finished'] is False
        and x['calls']==155 and x['completed_original_reads']==154 and x['failed_calls']==1
        and x['early_pressure']['warning_entries']==0 and x['leading_binding_active'] is False
        and old['warning_entries']==1 and old['completed_pause_windows']==3
        and old['requested_pause_seconds']==1.5,'PREENTRY90_NO_WAIT_BUT_INNER95_WAIT_PARTIAL_FRESH')
    obs=d['metadata_observation'];tail=obs['samples'][-4:]
    require(obs['completed_sample_count']==len(obs['samples'])==25 and obs['system_cpu_max_percent']==100
        and obs['own_cpu_max_machine_percent']==5.753283 and obs['own_private_max_bytes']==47341568
        and all(r['system_cpu_percent']==100 and r['parent_cpu_machine_percent']==0
            and r['audited_logical_read_bytes_delta']==0 for r in tail),'LAST4_SATURATED_WITH_ZERO_OWN_WORK_NOT_CAUSE')
    require(d['P09_gate']==d['A12_gate']==d['A13_gate']=='OPEN'
        and all(d[k] is False for k in ('whole1470_current_fresh_qualified','historical67_current_fresh_qualified',
            'full249_current_qualified','signed16_current_qualified','product_complete','PC_freeze_resolved')),'NO_PROMOTION')
    return dict(original_failed102_preserved=True,failed_receipt_accepted=False,runtime_advance=False,
        prior_accepted_cases=95,next_index=102,remaining_cases=154,reviewed_stage='final_fresh_preparation',
        Native_Frame_or_Job_or_product_started=False,Native_counts_unmeasured_not_invented=True,
        original_metadata_read_passes=154,original_partial_fresh_hashes=44,original_metadata_bound_inputs=80,
        outside_preentry90_did_not_pause=True,original_inside95_paused_three_windows=True,
        live_hard_guard_inside95_callback_improvement_identified=True,
        last4_own_CPU_and_read_delta_zero=True,CPU_cause_or_PC_freeze_resolution_established=False)

def contracts(stop):
    sys.path.insert(0,str(m.p.c.ROOT/'tools/p09/tests'));import test_leading_metadata_checkpoint_pressure as t
    with patch.object(t,'STOP',stop),patch('subprocess.Popen',side_effect=AssertionError('NO_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('NO_CHILD')),patch('threading.Thread.start',side_effect=AssertionError('NO_NEW_THREAD')):
        r=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(t))
    require(r.wasSuccessful() and r.testsRun==COUNT and not r.skipped,'CONTRACT30')
    return COUNT

def main():
    require(m.p.c.Path.cwd().resolve()==m.p.c.ROOT,'CWD')
    dst=m.p.c.ROOT/(m.p.DIR+'/p305-inner-checkpoint90-qualification-run01.v1.json');require(not dst.exists(),'FRESH')
    ctx=m.g.observation.Context();o=m.g.observation.Resources(ctx);q=None;proposed=None
    out=dict(schema_version='hwpx-agent.p09-inner-metadata-checkpoint90-qualification/v1',state='FAILED_NOT_ACCEPTED',
        **m.p.r.flags(),original_failed102_pin=FAILURE,actual_full_source_or_product_executed=False)
    try:
        o.admit();q=Reader(o,ctx)
        failed=m.m.review.bound_json(q,FAILURE);out['review']=review_stop(failed)
        light=m.m.review.bound_json(q,LIGHT)
        require(light['state']=='PASS_COMPLETED101_ANCHOR_SELECTION_NOT_ACTUAL_OR_GATE'
            and light['runtime_contract_executions']==132 and light['resource_stop_reason'] is None
            and light['resource_watcher_cleanup_confirmed'] is True
            and light['selected_test_index']==102,'QUALIFIED_LIGHT_NOT_NATIVE_OR_PRODUCT')
        old=m.p.v.pins(light['scope_added_six_pins'])
        out['contract_tests_passed']=contracts(failed)
        out['qualified_code_pins']=[q.pin(n) for n in (SELF,TEST)]
        out['preserved_p304_source_test_pins']=[q.pin(n) for n in
            ('tools/p09/resume_completed101_compound_runtime.py','tools/p09/tests/test_completed101_compound_runtime.py')]
        require(all(old.get(pin['path'])==pin for pin in out['preserved_p304_source_test_pins']),'UNCHANGED_FAILED_P304_CODE')
        require(not (m.p.c.ROOT/(m.p.DIR+'/cases/p304-case-102-run002.json')).exists(),'NO_OLD_PRODUCT_BODY_FILE')
        q.finish();proposed=dict(state=PASS)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as e:
        out['error_code']=m.p.b.run.original.closed_error(e)
    finally:
        if q is not None:q.close_entry();out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        def valid(d):
            x=d['IO']['leading_metadata_checkpoint_pressure'];old=d['IO']['leading_metadata_entry_pressure']
            require(d['review']==review_stop(failed) and d['contract_tests_passed']==COUNT and d['IO']['finished'] is True
                and d['IO']['bound_inputs']==d['IO']['final_fresh_hashes']==6
                and x['inner_guard_calls']>=d['IO']['read_passes'] and x['binding_active'] is False
                and x['hard_callback_restored_after_close'] is True
                and x['original95_object_and_outer90_and_entry32_callbacks_retained'] is True
                and old['original_inner95_and90_callbacks_unmodified'] is True
                and old['completed_original_reads']==old['calls']==d['IO']['read_passes']
                and d['actual_full_source_or_product_executed'] is False,'REAL_CLOSED_INNER_GUARD30_NOT_NEXT_RUNTIME')
        m.g.complete(out,o,proposed,valid)
        obs=m.g.observation.summary(o);out['observation']={k:v for k,v in obs.items() if k!='samples'}
        with dst.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','error_code','resource_stop_reason','contract_tests_passed')}))
    return 0 if out['state']==PASS else 2
if __name__=='__main__':raise SystemExit(main())
