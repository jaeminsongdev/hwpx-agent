"""P279: 생성 때 보관된 entry95 callback도 기존 byte90 객체에 연결한다.

P278 수용 preflight/CPU STOP·원P270 Binding은 보존. 원95가 early의 base로
매번 먼저 실행된다. 새 sampler/guard 생략/정리 변경/전체 실행 수용 없음.
"""
import argparse
import io
import json
import sys
import unittest
from unittest.mock import patch
import resume_acquisition_phased_runtime as runtime

p=runtime.p;g=runtime.g;metadata=runtime.metadata
SELF='tools/p09/qualify_metadata_entry_early_pressure.py'
TEST='tools/p09/tests/test_metadata_entry_early_pressure.py'
SCHEMA='hwpx-agent.p09-metadata-entry-early-pressure-qualification/v1'
PASS='PASS_CACHED_ENTRY_AND_BYTE_SHARED90_REAL_READER_NOT_FULL_RUNTIME_OR_GATE'
COUNT=54
LIGHT=dict(path=p.DIR+'/p278-light-run001.v1.json',bytes=43566,
    sha256='f36a1b47e16f179e3420043901e2664658026f7843e22d88857008d88da235ea')
FAILURE=dict(path=p.DIR+'/p278-case-095-run002.v1.json',bytes=120336,
    sha256='677c1d0f02c456b6db4b1e577307a0d8055087d1b120b93e0d3bc13d303c6dc8')
CODE=(dict(path=runtime.SELF,bytes=32873,sha256='ccc4a5a37758aa6f258a556f141aa654d80cdad1e17865de5989d0d5eb0f8f86'),
    dict(path=runtime.TEST,bytes=8073,sha256='8fe6de5cea32d6a9ed5d9181f1356b6216471c2984386d181bb37516287f1488'))


def require(ok,code):runtime.require(ok,'ENTRY_EARLY_'+code)


class Binding:
    def __init__(self,q,owner):
        require(q.resources is owner and q.finished is False and q.reader.read_passes==q.reader.bytes_read==0
            and not hasattr(q,'entry_early_binding'),'ONE_UNUSED_LIVE_READER')
        entry=q.entry_binding;pacer=entry.pacer;early=q.early_metadata_binding.early
        require(entry.active is True and entry.reader is q.reader and q.reader._p246_entry_binding is entry
            and pacer.rate==32 and pacer.opens==0 and pacer.previous is None
            and q.reader.checkpoint is early and early.base is q.pressure and q.pressure.resources is owner
            and pacer.checkpoint is q.pressure,'EXACT_CACHED_ORIGINAL95_BEFORE_ENTRY')
        self.q=q;self.entry=entry;self.pacer=pacer;self.early=early;self.original95=q.pressure
        self.clock=pacer.clock;self.sleeper=pacer.sleeper;self.reader=q.reader
        # 원 byte callback과 동일한 객체. base의 원95·600/CPU/RAM 검사는 그대로 수행.
        pacer.checkpoint=early;q.entry_early_binding=self
    def summary(self):
        q=self.q;pacer=self.entry.pacer
        return dict(entry_and_byte_warning_CPU_percent=90,original_entry_rate_per_second=32,
            same_original_entry_pacer=pacer is self.pacer,entry_and_byte_share_existing_early_object=
                pacer.checkpoint is q.reader.checkpoint is self.early,
            original95_retained_as_first_base=self.early.base is q.pressure is self.original95,
            original_clock_sleeper_reader_retained=pacer.clock is self.clock and pacer.sleeper is self.sleeper
                and q.reader is self.reader,constructor_before_attachment_original95_preserved=True,
            clock_credit_or_read_counter_reset=False,original600_720_CPU_RAM_guards_preserved=True,
            extra_CPU_native_query_sampler_or_thread_started=False,cleanup_callback_wrapped=False,
            original_reads_source_byte_or_identity_checks_skipped=False,CPU_or_PC_freeze_improvement_established=False)


class Reader(runtime.Reader):
    def __init__(self,owner,context):
        super().__init__(owner,context)
        try:Binding(self,owner)
        except BaseException:self.close_entry();raise
    def summary(self):
        row=super().summary();row['metadata_entry_early_pressure_connection']=self.entry_early_binding.summary();return row


def connection_contract(row):
    require(row['entry_and_byte_warning_CPU_percent']==90 and row['original_entry_rate_per_second']==32
        and all(row[k] is True for k in ('same_original_entry_pacer','entry_and_byte_share_existing_early_object',
            'original95_retained_as_first_base','original_clock_sleeper_reader_retained',
            'constructor_before_attachment_original95_preserved','original600_720_CPU_RAM_guards_preserved'))
        and all(row[k] is False for k in ('clock_credit_or_read_counter_reset','extra_CPU_native_query_sampler_or_thread_started',
            'cleanup_callback_wrapped','original_reads_source_byte_or_identity_checks_skipped',
            'CPU_or_PC_freeze_improvement_established')),'SHARED90_ALL_ORIGINAL_GUARDS')


def review(doc,plan):
    require(doc['schema_version']==runtime.SCHEMA and doc['state']=='FAILED_NOT_ACCEPTED'
        and doc['error_code']==doc['resource_stop_reason']=='STOP_SUSTAINED_SYSTEM_CPU'
        and doc['resource_watcher_cleanup_confirmed'] is True and doc['runtime_contract_executions']==754
        and doc['failure_diagnostic']['stage']=='final_fresh_preparation'
        and doc['failure_diagnostic']['exception_class']=='ValueError'
        and doc['prior_runtime_plan']==plan and doc['selected_test_index']==95
        and doc['accepted_exact_product_body_count']==0 and doc['actual_product_child_executed'] is False
        and doc['acquisition_phase_connection_selected'] is False and 'terminal_source_frame' not in doc
        and 'case_receipt_path' not in doc and 'terminal_metadata_IO' not in doc,'ORIGINAL_STOP_BEFORE_FRAME_OR_JOB')
    row=doc['preparation_IO'];old=row['near_saturation_read_backpressure'];early=row['early_metadata_pressure']
    require(row['read_passes']==255 and row['bound_inputs']==212 and row['final_fresh_hashes']==13
        and row['bytes_read']==38495800 and row['finished'] is False
        and old['warning_entries']==1 and old['completed_pause_windows']==3
        and early['original_early_source_algorithm_statistics']['warning_entries']==0,
        'OBSERVED_ENTRY95_PAUSED_BEFORE_BYTE90_INCOMPLETE_FRESH')
    hot=doc['metadata_observation']['samples'][-4:]
    require(len(hot)==4 and all(x['system_cpu_percent']==100 and x['parent_cpu_machine_percent']==0
        and x['phase_at_sample']=='final_fresh_hash' for x in hot),'ORIGINAL4_CPU100_OWN0')
    require(plan['runtime_source_qualified_individual_cases']==88 and plan['next_runtime_index']==95
        and plan['runtime_remaining_individual_cases']==161,'NO_STOP_ADVANCE')
    return dict(original_STOP_preserved=True,original_partial_fresh_not_accepted=True,accepted_runtime_subset=88,next_index=95,
        acquisition_phase14_or_original_parent_or_product_body_invoked=False,
        observed_byte90_warning_entries=0,observed_original95_warning_entries=1,
        constructor_cached_entry_callback_gap_confirmed_by_code=True,CPU_cause_or_PC_freeze_resolution_established=False)


def contracts(failed,plan,warning):
    require(metadata.contracts(warning)==32,'ORIGINAL32_RETAINED')
    sys.path.insert(0,str(p.c.ROOT/'tools/p09/tests'));import test_metadata_entry_early_pressure as tests
    with patch.object(tests,'FIXTURES',(failed,plan)), \
            patch('subprocess.Popen',side_effect=AssertionError('NO_ENTRY_PRESSURE_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('NO_ENTRY_PRESSURE_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('NO_ENTRY_PRESSURE_THREAD')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
    require(result.wasSuccessful() and result.testsRun==22 and not result.skipped,'NEW22_SHARED_ENTRY_BYTE_AND_STOP')
    return 54


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--run',type=int,required=True);args=ap.parse_args()
    require(p.c.Path.cwd().resolve()==p.c.ROOT and 1<=args.run<=99,'CWD_RUN')
    destination=p.c.ROOT/f'{p.DIR}/p279-metadata-entry-early-pressure-run{args.run:02}.v1.json'
    require(not destination.exists(),'NO_OVERWRITE')
    context=g.observation.Context();owner=g.observation.Resources(context);q=None;proposed=None;stage='admission'
    out=dict(schema_version=SCHEMA,state='FAILED_NOT_ACCEPTED',**p.r.flags(),original_failure_pin=FAILURE,
        actual_current95_product_body_reexecuted=False,actual_full_source_or_native_frame_executed=False,
        actual_full_runtime_connection_qualified=False,CPU_or_PC_freeze_improvement_established=False)
    try:
        owner.admit();stage='reader_constructor';q=Reader(owner,context);stage='literal_review'
        light=runtime.m.review.bound_json(q,LIGHT);runtime.closed_attempt(light)
        require(light['state']==runtime.LIGHT and light['selected_test_index']==95,'LITERAL_PREFLIGHT_NOT_RUNTIME_PASS')
        plan=light['prior_runtime_plan'];failed=runtime.m.review.bound_json(q,FAILURE);checked=review(failed,plan)
        frozen=p.v.pins(light['bound_preparation_input_pins'])
        for name in runtime.NEW:require(q.pin(name)==frozen[name],'FROZEN_PREFLIGHT_ALL24_CODE')
        for pin in CODE:require(q.reader.snapshots[pin['path']]==pin,'ORIGINAL_EXECUTED_CONTROLLER_CODE')
        for name in (SELF,TEST):q.pin(name)
        warning=runtime.m.review.bound_json(q,metadata.ROOT)
        folder=p.c.ROOT/p.DIR
        require(sorted(x.name for x in folder.glob('p278-*.v1.json'))==
            sorted(pin['path'].split('/')[-1] for pin in (LIGHT,FAILURE))
            and not list((folder/'cases').glob('p278-*.json')),'ONLY_REVIEWED_P278_NO_BODY')
        stage='contract_tests'
        with context.scope('contract_tests'):count=contracts(failed,plan,warning)
        out.update(runtime_plan=plan,original_failure_review=checked,entry_pressure_contract_tests_passed=count,
            constructor_cached_entry_callback_now_shared=True)
        stage='metadata_final_fresh';q.finish();connection_contract(q.summary()['metadata_entry_early_pressure_connection'])
        require(q.summary()['bound_inputs']<=32 and q.summary()['bytes_read']<=8*1048576,'BOUNDED_SUPPORT_ONLY_NOT_FULL_INPUTS')
        proposed=dict(state=PASS)
    except (ValueError,OSError,KeyError,TypeError,AttributeError,IndexError,KeyboardInterrupt) as error:
        out.update(error_code=p.b.run.original.closed_error(error),failure_diagnostic=runtime.diagnostic(error,stage))
    finally:
        if q is not None:q.close_entry();out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        out['metadata_observation']=g.observation.summary(owner)
        def validate(doc):
            connection_contract(doc['IO']['metadata_entry_early_pressure_connection'])
            require(doc['IO']['finished'] is True and doc['IO']['bound_inputs']==doc['IO']['final_fresh_hashes']
                and doc['entry_pressure_contract_tests_passed']==COUNT
                and doc['actual_full_runtime_connection_qualified'] is False,'REAL_READER_CLOSED_NOT_PRODUCT')
        g.complete(out,owner,proposed,validate)
        with destination.open('x',encoding='utf-8') as stream:
            runtime.r.compact.dump(out,stream,checkpoint=lambda:require(owner.done.is_set(),'TERMINAL_ONLY'),indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','entry_pressure_contract_tests_passed','error_code','resource_stop_reason')}))
    return 0 if out['state']==PASS else 2


if __name__=='__main__':
    sys.modules.setdefault('qualify_metadata_entry_early_pressure',sys.modules[__name__])
    raise SystemExit(main())
