"""Bounded per-logical-CPU observation, never affinity selection or mutation.

Uses the existing bounded PDH array reader/cleanup unchanged in an owned Job.
Only numeric processor instances are returned; no processes, paths or commands.
"""
import math
from types import FunctionType
import host_cpu_observer as original

SELF='tools/p09/native011_logical_cpu_observation.py'
TEST='tools/p09/tests/test_native011_logical_cpu_observation.py'
PATHS=(r'\Processor(*)\% Processor Time',)


def require(ok,label):
    if not ok:raise ValueError('LOGICAL_CPU_OBSERVATION_'+label)


def numeric_rows(rows,processors):
    require(type(processors) is int and 1<=processors<=64,'ONE_SUPPORTED_PROCESSOR_GROUP')
    require(type(rows) is dict and set(rows)=={*(str(i) for i in range(processors)),'_total'},
        'EXACT_NUMERIC_PROCESSOR_INSTANCES')
    require(all(type(value) in (int,float) and math.isfinite(value) and 0<=value<=100
        for value in rows.values()),'VALID_COMPLETE_BUSY_PERCENTAGES')
    return dict(total_busy_percent=rows['_total'],logical_cpus=[
        dict(logical_cpu=i,busy_percent=rows[str(i)]) for i in range(processors)])


def observer_type():
    init=original.Observer.__init__
    require(type(init) is FunctionType,'ORIGINAL_BOUNDED_PDH_CONSTRUCTOR')
    selected=FunctionType(init.__code__,dict(init.__globals__,PATHS=PATHS),
        argdefs=init.__defaults__,closure=init.__closure__)
    selected.__kwdefaults__=init.__kwdefaults__
    class Observer(original.Observer):
        primed=False
        def prime_core(self):
            require(not self.closed and self.query.value and not self.primed and len(self.handles)==1,
                'ONE_LIVE_PROCESSOR_QUERY')
            require(original.status(self.api.PdhCollectQueryData(self.query))==0,'PRIME_QUERY')
            self.primed=True
        def collect_core(self):
            require(not self.closed and self.query.value and self.primed and len(self.handles)==1,
                'PRIMED_LIVE_QUERY_ONLY')
            require(original.status(self.api.PdhCollectQueryData(self.query))==0,'COLLECT_QUERY')
            return numeric_rows(self.array(self.handles[0]),self.processors)
    Observer.__init__=selected
    require(Observer.array is original.Observer.array and Observer.close is original.Observer.close
        and Observer.__init__.__code__ is init.__code__,'ORIGINAL_BOUNDS_NATIVE_CALLS_AND_CLEANUP')
    return Observer
