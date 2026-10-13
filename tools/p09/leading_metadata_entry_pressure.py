"""P301: 원 entry32/95/byte90 callback 앞의 제한된 pre-entry90. 기존 callback 불변."""
import io
import json
import sys
import unittest
from unittest.mock import patch
import accept_completed101_compound_r5 as compound
m=compound.m
SELF='tools/p09/leading_metadata_entry_pressure.py'
TEST='tools/p09/tests/test_leading_metadata_entry_pressure.py'
COUNT=18

def require(ok,code):m.require(ok,'LEADING_ENTRY_'+code)

class Binding:
    def __init__(self,q,owner,*,sleep=None):
        require(q.resources is owner and q.finished is False and q.reader.read_passes==0
            and not hasattr(q,'leading_entry_binding'),'ONE_UNUSED_OWNER_READER')
        self.q=q;self.owner=owner;self.reader=q.reader;self.entry=q.entry_binding
        self.pacer=self.entry.pacer;self.original=self.reader._read
        self.old_callback=self.reader.checkpoint;self.old_pacer_callback=self.pacer.checkpoint
        self.old95=q.pressure;self.old90=q.early_metadata_binding.early
        require(self.entry.active and self.reader._p246_entry_binding is self.entry
            and self.pacer.rate==32 and self.pacer.opens==0 and self.pacer.previous is None
            and self.old_callback is self.old_pacer_callback is self.old90
            and self.old90.base is self.old95 and self.old95.resources is owner
            and callable(self.old95.base),'ORIGINAL_SHARED32_95_90_UNMODIFIED')
        kw={} if sleep is None else dict(sleep=sleep)
        # 원 hard CPU/RAM/IO600 callback. 원95/90 대기는 제거하지 않고 뒤에서 반드시 호출한다.
        self.early=m.early_review.EarlySourceCheckpoint(self.old95.base,owner,**kw)
        self.calls=self.completed=self.failed=0;self.active=True
        def read(name,parse=False):
            require(self.active and q.leading_entry_binding is self
                and self.reader._read is read,'EXACT_ACTIVE_BINDING')
            self.calls+=1
            try:
                self.early()
                result=self.original(name,parse=parse);self.completed+=1;return result
            except BaseException:self.failed+=1;raise
        self.read=read;self.reader._read=read;q.leading_entry_binding=self
    def close(self):
        # 중단 뒤 guard/sleep 없이 원 entry wrapper를 먼저 복원한다.
        if not self.active:return
        require(self.reader._read is self.read,'RESTORE_EXACT_WRAPPER')
        self.reader._read=self.original;self.active=False
    def summary(self):
        return dict(pre_entry_warning_CPU_percent=90,original_entry_rate=32,
            calls=self.calls,completed_original_reads=self.completed,failed_calls=self.failed,
            leading_binding_active=self.active,early_pressure=self.early.summary(),
            original_inner95_and90_callbacks_unmodified=self.reader.checkpoint is self.old_callback
                and self.pacer.checkpoint is self.old_pacer_callback and self.old90.base is self.old95,
            original_entry_pacer_and_reader_retained=self.entry.pacer is self.pacer and self.q.reader is self.reader,
            original_hard_CPU_RAM_IO600_720_and_all_reads_preserved=True,
            new_sampler_or_thread_started=False,original_clock_credit_or_counter_reset=False,
            source_or_case_or_read_exclusions_added=False,cleanup_not_guarded_or_paced=True,
            CPU_cause_or_PC_freeze_resolution_established=False)

class Reader(m.Reader):
    def __init__(self,owner,context):
        super().__init__(owner,context)
        try:Binding(self,owner)
        except BaseException:super().close_entry();raise
    def close_entry(self):
        if hasattr(self,'leading_entry_binding'):self.leading_entry_binding.close()
        return super().close_entry()
    def summary(self):
        return dict(super().summary(),leading_metadata_entry_pressure=self.leading_entry_binding.summary())

def contracts():
    sys.path.insert(0,str(m.p.c.ROOT/'tools/p09/tests'))
    with patch('subprocess.Popen',side_effect=AssertionError('NO_CHILD')),patch('subprocess.run',side_effect=AssertionError('NO_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('NO_NEW_THREAD')):
        result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(unittest.defaultTestLoader.loadTestsFromName('test_leading_metadata_entry_pressure'))
    require(result.wasSuccessful() and result.testsRun==COUNT and not result.skipped,'CONTRACT18')
    return COUNT

def main():
    require(m.p.c.Path.cwd().resolve()==m.p.c.ROOT,'CWD')
    dst=m.p.c.ROOT/(m.p.DIR+'/p301-leading-entry90-qualification-run01.v1.json');require(not dst.exists(),'FRESH')
    ctx=m.g.observation.Context();owner=m.g.observation.Resources(ctx);q=None;proposed=None
    out=dict(schema_version='hwpx-agent.p09-leading-entry90-qualification/v1',state='FAILED_NOT_ACCEPTED',
        **m.p.r.flags(),actual_full_source_frame_executed=False)
    try:
        owner.admit();out['contract_tests_passed']=contracts();q=Reader(owner,ctx)
        out['qualified_code_pins']=[q.pin(n) for n in (SELF,TEST)]
        q.finish();proposed=dict(state='PASS_LEADING_ENTRY90_REAL_READER_NOT_COMPOUND_RUNTIME_OR_GATE')
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as e:
        out['error_code']=m.p.b.run.original.closed_error(e)
    finally:
        if q is not None:q.close_entry();out.update(IO=q.summary(),bound_input_pins=list(q.reader.snapshots.values()))
        def valid(d):
            x=d['IO']['leading_metadata_entry_pressure']
            require(d['contract_tests_passed']==COUNT and d['IO']['finished'] is True
                and d['IO']['bound_inputs']==d['IO']['final_fresh_hashes']==2 and d['IO']['read_passes']==4
                and x['calls']==x['completed_original_reads']==4 and x['failed_calls']==0 and x['leading_binding_active'] is False
                and x['original_inner95_and90_callbacks_unmodified'] is True,'REAL_READER_CLOSED')
        m.g.complete(out,owner,proposed,valid)
        obs=m.g.observation.summary(owner);out['observation']={k:v for k,v in obs.items() if k!='samples'}
        with dst.open('x',encoding='utf-8') as stream:json.dump(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','error_code','resource_stop_reason','contract_tests_passed')}))
    return 0 if out['state'].startswith('PASS_') else 2
if __name__=='__main__':raise SystemExit(main())
