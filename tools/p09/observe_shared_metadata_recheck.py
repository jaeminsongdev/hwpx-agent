"""P193: observe one unchanged P192 metadata verification, never a product run.

기존 수동 표본에 내 프로세스 메모리/구간/논리 읽기량만 덧붙인다.
새 감시 스레드, 외부 PID 조회, 보호 기준 완화, 통과 항목 재실행은 없다.
"""
import argparse
import contextlib
import ctypes
import io
import json
import math
import sys
import unittest
from unittest.mock import patch

import sync_shared_resumable_r07_progress as old

c=old.c; observation=old.run.pressure.observation
SELF='tools/p09/observe_shared_metadata_recheck.py'
TEST='tools/p09/tests/test_observed_shared_metadata.py'
PRIOR_STOP=dict(path='implementation/p09/evidence/p09-192-shared-resumable-progress-sync-run02.v1.json',
    bytes=7701,sha256='4437a16e7ea3ced1434b5bcca82a6407f4c87582562fb5c0d0c4d4ea340ff9bb')
PHASES=('admission','metadata_hash','metadata_read_parse','document_read','contract_tests','final_fresh_hash','idle')
RAW_WINDOWS=observation.observer.RAW_PARENT
RAW_RESOURCES=observation.OriginalResources
RAW_READER=old.run.pressure.PressureReader
RAW_CONTRACTS=old.batch.contracts
RAW_DUMP=json.dump
FIELDS=('time_utc','system_cpu_percent','available_ram_percent','commit_used_percent',
    'parent_cpu_machine_percent','parent_cpu_delta_100ns','raw_system_cpu_delta_100ns',
    'parent_affinity_mask','parent_priority_readback','parent_process_only','foreign_Process_query_executed',
    'own_private_bytes','own_working_set_bytes','own_private_percent_total_ram','own_working_set_percent_total_ram',
    'phase_at_sample','phases_since_previous_sample','audited_logical_read_bytes','audited_logical_read_passes',
    'audited_logical_read_bytes_delta','reader_counters_observed')


def require(ok,code):c.require(ok,'P193_'+code)


def own_memory(kernel,total):
    require(type(total) is int and total>0,'TOTAL_RAM')
    memory=c.ProcessMemory();memory.size=ctypes.sizeof(memory)
    # 현재 프로세스 pseudo handle만 사용한다. 실패를 0 사용량으로 바꾸지 않는다.
    require(kernel.K32GetProcessMemoryInfo(kernel.GetCurrentProcess(),ctypes.byref(memory),memory.size),
        'OWN_MEMORY_QUERY_FAILED')
    return dict(own_private_bytes=memory.private,own_working_set_bytes=memory.ws,
        own_private_percent_total_ram=100*memory.private/total,
        own_working_set_percent_total_ram=100*memory.ws/total)


class Context:
    def __init__(self):
        self.phase='admission';self.seen={'admission'};self.reader=None;self.previous=None
    @contextlib.contextmanager
    def scope(self,phase):
        require(phase in PHASES,'CLOSED_PHASE');prior=self.phase
        self.phase=phase;self.seen.add(phase)
        try:yield
        finally:self.phase=prior;self.seen.add(prior)
    def snapshot(self):
        row=dict(phase_at_sample=self.phase,phases_since_previous_sample=sorted(self.seen),
            reader_counters_observed=self.reader is not None,
            audited_logical_read_bytes=None,audited_logical_read_passes=None,audited_logical_read_bytes_delta=None)
        if self.reader is not None:
            count=self.reader.bytes_read;passes=self.reader.read_passes
            require(type(count) is int and count>=0 and type(passes) is int and passes>=0,'READ_COUNTERS')
            require(self.previous is None or count>=self.previous,'READ_COUNTER_RESET')
            row.update(audited_logical_read_bytes=count,audited_logical_read_passes=passes,
                audited_logical_read_bytes_delta=None if self.previous is None else count-self.previous)
            self.previous=count
        self.seen={self.phase};return row


class ObservedWindows(RAW_WINDOWS):
    def __init__(self,context):self.context=context;super().__init__()
    def sample(self):
        row=super().sample()  # 원 CPU/RAM/commit 표본과 구간 분모를 변경하지 않는다.
        row.update(own_memory(self.k,self.total_ram));row.update(self.context.snapshot());return row


class Resources(RAW_RESOURCES):
    def __init__(self,context):super().__init__(windows=ObservedWindows(context))


class Reader(RAW_READER):
    def __init__(self,resources,context):
        self.context=context;super().__init__(resources);context.reader=self.reader
        for name in (SELF,TEST):self.pin(name)
        require(self.pin(PRIOR_STOP['path'])==PRIOR_STOP,'PRIOR_STOP_PIN')
    def pin(self,name):
        with self.context.scope('metadata_hash'):return super().pin(name)
    def json(self,name):
        with self.context.scope('metadata_read_parse'):return super().json(name)
    def text(self,name):
        with self.context.scope('document_read'):return super().text(name)
    def finish(self):
        with self.context.scope('final_fresh_hash'):return super().finish()


def summary(resources):
    require(resources.thread.ident is None,'NO_NEW_WATCHER')
    with resources.lock:rows=[{k:r[k] for k in FIELDS if k in r} for r in resources.samples]
    require(len(rows)<=1440,'BOUNDED_SAMPLES')
    def extreme(key,fn):
        values=[r[key] for r in rows if type(r.get(key)) in (int,float) and math.isfinite(r[key])]
        return fn(values) if values else None
    return dict(completed_sample_count=len(rows),samples=rows,
        system_cpu_max_percent=extreme('system_cpu_percent',max),
        own_cpu_max_machine_percent=extreme('parent_cpu_machine_percent',max),
        own_private_max_bytes=extreme('own_private_bytes',max),
        own_working_set_max_bytes=extreme('own_working_set_bytes',max),
        available_ram_min_percent=extreme('available_ram_percent',min),
        own_process_only=True,foreign_PID_query_executed=False,new_sampler_thread_started=False,
        extra_own_memory_query_per_existing_sample=1,original_guard_and_CPU_denominator_unchanged=True,
        read_counters_are_logical_not_physical_disk_IO=True,
        samples_can_span_multiple_phases=True,CPU_cause_or_PC_freeze_resolution_established=False)


def new_contracts():
    sys.path.insert(0,str(c.ROOT/'tools/p09/tests'))
    suite=unittest.defaultTestLoader.loadTestsFromName('test_observed_shared_metadata')
    with patch('subprocess.Popen',side_effect=AssertionError('P193_NO_CHILD')), \
            patch('subprocess.run',side_effect=AssertionError('P193_NO_CHILD')), \
            patch('threading.Thread.start',side_effect=AssertionError('P193_NO_THREAD')):
        checked=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    require(checked.wasSuccessful() and checked.testsRun==10 and not checked.skipped,'CONTRACT10')
    return dict(observation_contract_tests_passed=10)


def combined_contracts(context):
    with context.scope('contract_tests'):
        result=RAW_CONTRACTS();result.update(new_contracts());return result


def reader_for_owner(owner,context,registry,*args,**kw):
    # 기존 synthetic reader 계약은 기존 구현으로 검증한다. 실제 소유자만 관측한다.
    if registry and owner is registry[0]:
        require(not args and not kw,'ACTUAL_READER_ARGUMENTS');return Reader(owner,context)
    return RAW_READER(owner,*args,**kw)


def observe(destination):
    context=Context();registry=[]
    def resources():
        require(not registry,'ONE_RESOURCE_OWNER');owner=Resources(context);registry.append(owner);return owner
    def dump(out,stream,**kw):
        if 'further_product_test_or_Cargo_SQL_Hangul_child_executed' in out:
            require(out['further_product_test_or_Cargo_SQL_Hangul_child_executed'] is False,'METADATA_ONLY')
            require(len(registry)==1,'ONE_OBSERVED_OWNER')
            out.update(metadata_observation=summary(registry[0]),original_CPU_stop_receipt_pin=PRIOR_STOP,
                observation_controller_sources=[SELF,TEST],original_document_verifier_body_unmodified=True)
        return RAW_DUMP(out,stream,**kw)
    with patch.object(old,'DEST',destination),patch.object(sys,'argv',[old.SELF,'--mode','verify']), \
            patch.object(observation,'ObservedResources',resources), \
            patch.object(old.run.pressure,'PressureReader',lambda owner,*a,**kw:reader_for_owner(owner,context,registry,*a,**kw)), \
            patch.object(old.batch,'contracts',lambda:combined_contracts(context)),patch.object(json,'dump',dump):
        return old.main()


def light(destination):
    owner=observation.ObservedResources();reader=None
    out=dict(state='FAILED_NOT_ACCEPTED',further_product_test_or_Cargo_SQL_Hangul_child_executed=False,
        actual_observed_document_recheck_executed=False,**old.core.flags())
    try:
        owner.admit();reader=RAW_READER(owner);out.update(combined_contracts(Context()))
        for name in (SELF,TEST,old.SELF):reader.pin(name)
        require(reader.pin(PRIOR_STOP['path'])==PRIOR_STOP,'PRIOR_STOP_PIN');reader.finish()
        out['state']='PASS_METADATA_OBSERVATION_CONTRACTS_ONLY_NOT_PRODUCT_OR_CAUSE'
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        out['error_code']=old.run.original.closed_error(error)
    finally:
        old.s.finish_watcher(owner,out);out['resource_stop_reason']=owner.reason
        if owner.reason or not out.get('resource_watcher_cleanup_confirmed'):out['state']='FAILED_NOT_ACCEPTED'
        if reader is not None:out.update(IO=reader.summary(),bound_input_pins=list(reader.reader.snapshots.values()))
        with old.s.scoped_path(destination,fresh=True).open('x',encoding='utf-8') as stream:RAW_DUMP(out,stream,indent=2)
        print(json.dumps({k:out.get(k) for k in ('state','contract_tests_passed','observation_contract_tests_passed',
            'error_code','resource_stop_reason')}))
    return 0 if out['state'].startswith('PASS_') else 2


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=('light','observe'),required=True)
    ap.add_argument('--run',type=int,required=True);args=ap.parse_args()
    require(c.Path.cwd().resolve()==c.ROOT,'CWD');require(1<=args.run<=99,'RUN_ID')
    destination=f'implementation/p09/evidence/p09-193-metadata-observation.{args.mode}-run{args.run:02d}.v1.json'
    old.s.scoped_path(destination,fresh=True)
    return light(destination) if args.mode=='light' else observe(destination)


if __name__=='__main__':raise SystemExit(main())
