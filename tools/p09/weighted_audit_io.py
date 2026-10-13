"""P176 lower binary-read pressure; every original fresh read/guard stays intact."""
import math
import time
import audit_evidence_io as original
from live_sql_evidence_reader import LiveSQLReader

SELF='tools/p09/weighted_audit_io.py'
BINARY_RATE=5*1024*1024//2
OTHER_RATE=4*1024*1024

def require(ok,code):original.require(ok,'weighted_audit_'+code)

class WeightedPacer(original.AuditReadPacer):
    def __init__(self,clock=time.monotonic,sleeper=time.sleep):
        super().__init__(clock,sleeper);self.rate=OTHER_RATE
        self.bytes_by_kind={'binary':0,'other':0};self.kind='other'
    def select(self,name):
        require(isinstance(name,str),'name_type')
        self.kind='binary' if name.lower().endswith('.exe') else 'other'
        self.rate=BINARY_RATE if self.kind=='binary' else OTHER_RATE
    def reserve(self,checkpoint):
        # Original token algorithm, with a per-instance rate instead of a
        # mutable module global. One chunk only; no idle burst accumulation.
        require(type(self.rate) is int and 0<self.rate<=original.READ_BYTES_PER_SECOND,'rate_scope')
        attempts=0
        while True:
            now=self.clock()
            require(type(now) in (int,float) and math.isfinite(now) and now>=self.last,'clock_invalid')
            self.tokens=min(original.CHUNK_BYTES,self.tokens+(now-self.last)*self.rate)
            self.last=now
            if self.tokens>=original.CHUNK_BYTES:
                self.tokens-=original.CHUNK_BYTES;return
            attempts+=1;require(attempts<=64,'clock_not_advancing')
            delay=min(0.05,max(0.000001,(original.CHUNK_BYTES-self.tokens)/self.rate))
            checkpoint();self.sleeper(delay);self.requested_sleep_seconds+=delay;checkpoint()
    def refund(self,actual_bytes):
        super().refund(actual_bytes);self.bytes_by_kind[self.kind]+=actual_bytes

class WeightedReader(original.AuditEvidenceReader):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self.pacer=WeightedPacer()
    def _read(self,name,parse=False):
        self.pacer.select(name)
        return super()._read(name,parse= parse)

class WeightedLiveReader(LiveSQLReader):
    def __init__(self,resources,clock=time.monotonic):
        super().__init__(resources,clock)
        # Same root/checkpoint/parse budget/600-second scope. Only pacer changes.
        self.reader=WeightedReader(self.reader.root,self.checkpoint,self.reader.maximum_parse_bytes)
    def summary(self):
        row=super().summary()
        # The base summary imports a fixed global rate by value. Do not label
        # a mixed per-file policy as either that 8MiB/s default or one flat rate.
        row.update(read_bytes_per_second=None,read_rate_policy='P176_binary2p5_other4_MiB_per_second',
            read_rates_by_kind={'binary':BINARY_RATE,'other':OTHER_RATE},
            bytes_read_by_kind=dict(self.reader.pacer.bytes_by_kind),
            burst_bytes=original.CHUNK_BYTES,all_original_read_operations_preserved=True,
            pacer_bytes_read=self.reader.pacer.bytes_paced)
        require(sum(row['bytes_read_by_kind'].values())==row['bytes_read']==row['pacer_bytes_read'],'byte_accounting')
        return row

def resource_tail(resources):
    # Reuse completed original samples; no new native query, thread or sampler.
    with resources.lock:
        rows=list(resources.samples[-8:]);count=len(resources.samples)
    keys=('time_utc','system_cpu_percent','available_ram_mib','total_ram_mib',
          'available_ram_percent','commit_used_percent')
    require(all(all(k in row for k in keys) for row in rows),'sample_fields')
    return dict(original_completed_sample_count=count,tail_limit=8,existing_samples_only=True,
        additional_native_queries_started=False,samples=[{k:row[k] for k in keys} for row in rows])
