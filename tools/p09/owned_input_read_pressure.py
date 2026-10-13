"""Lightweight input pacing; no legacy runner imports, sampler, thread or child.

P340의 동일75%/두 distinct cool 표본/8-window 원칙을 원 소유 callback으로 적용한다.
원 guard 우선, 모든 read/path 검사 유지, 원 checkpoint 복구와 제한 없는 cleanup.
"""
import math
import time


def require(ok,code):
    if not ok:raise ValueError("OWNED_INPUT_IO_"+code)


class QueryPacer:
    def __init__(self,checkpoint,clock=time.monotonic,sleep=time.sleep):
        self.checkpoint=checkpoint;self.clock=clock;self.sleep=sleep
        self.next=clock();self.requests=0;self.wait_seconds=0
    def reserve(self):
        self.checkpoint();attempts=0
        while True:
            now=self.clock()
            require(type(now) in (int,float) and math.isfinite(now),"QUERY_CLOCK")
            remaining=self.next-now
            if remaining<=0:break
            attempts+=1;require(attempts<=64,"QUERY_CLOCK_NOT_ADVANCING")
            delay=min(.05,remaining);self.sleep(delay);self.wait_seconds+=delay;self.checkpoint()
        self.next=self.clock()+.05;self.requests+=1
    def summary(self):
        return dict(request_limit_per_second=20,requests=self.requests,requested_wait_seconds=self.wait_seconds,
                    requests_skipped=False,cleanup_paced=False)


class PreSaturationReadCheckpoint:
    WARNING_PERCENT=75
    COOL_SAMPLES=2
    MAX_WINDOWS=8
    def __init__(self,reader,resources,sleep=time.sleep,sample_seconds=.5):
        require(callable(reader.checkpoint) and callable(getattr(resources,"checkpoint_io",None))
            and hasattr(resources,"lock") and hasattr(resources,"samples"),"ORIGINAL_OWNER")
        require(sample_seconds==.5,"ORIGINAL_SAMPLE_INTERVAL")
        self.reader=reader;self.resources=resources;self.original=reader.checkpoint
        self.hard=resources.checkpoint_io;self.sleep=sleep;self.sample_seconds=sample_seconds
        self.warning_entries=self.pause_windows=self.maximum_windows=0;self.active=True;self.restored=False
        reader.checkpoint=self
    def latest(self):
        with self.resources.lock:
            require(bool(self.resources.samples),"ORIGINAL_SAMPLE_MISSING")
            row=self.resources.samples[-1]
        value=row.get("system_cpu_percent")
        require(type(value) in (int,float) and math.isfinite(value) and 0<=value<=100,"ORIGINAL_CPU_SAMPLE")
        return row,value
    def __call__(self):
        require(self.active and self.reader.checkpoint is self,"EXACT_CHECKPOINT_BINDING")
        self.hard();row,value=self.latest()
        if value>=self.WARNING_PERCENT:
            self.warning_entries+=1;cool=windows=0
            while cool<self.COOL_SAMPLES:
                require(windows<self.MAX_WINDOWS,"STOP_EARLY_READ_PRESSURE_NOT_COOLING")
                previous=row;self.sleep(self.sample_seconds);windows+=1;self.pause_windows+=1
                self.maximum_windows=max(self.maximum_windows,windows)
                self.hard();row,value=self.latest()
                require(row is not previous,"ORIGINAL_SAMPLE_NOT_ADVANCED")
                cool=cool+1 if value<self.WARNING_PERCENT else 0
        self.original()
    def restore(self):
        if not self.active:return
        require(self.reader.checkpoint is self,"RESTORE_EXACT_CHECKPOINT_BINDING")
        self.reader.checkpoint=self.original;self.active=False
        self.restored=self.reader.checkpoint is self.original
        require(self.restored,"ORIGINAL_CHECKPOINT_RESTORE")
