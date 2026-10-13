"""One-query, partial diagnostic scheduler; product/guard checks unchanged.

Cold intervals are explicitly NOT OBSERVED. Resumption discards a genuine
fresh collection, so an average across the cold gap is never emitted as a
current hot sample. No saved sample/cache, PID or authorization is replayed.
"""
import math
import os
import time
import json
from datetime import datetime,timezone
import run_observed_stored_full as original

SELF='tools/p09/adaptive_host_cpu_sampler.py'
FOOTER=b'P164_SAMPLING:'
FOOTER_LIMIT=512
KEYS=('host_polls','query_calls','emitted_samples','discarded_resume_warm_calls',
      'skipped_cold_polls','skipped_budget_polls','high_host_polls')

def require(ok,code):original.require(ok,'ADAPTIVE_'+code)

class Sampler:
    def __init__(self):
        self.counts={k:0 for k in KEYS};self.warmed=False;self.resume_warm_required=False

    def initial_warm(self):
        require(not self.warmed and self.counts['host_polls']==0,'ONE_INITIAL_WARM')
        self.warmed=True;self.counts['query_calls']=1

    def poll(self,host,collect):
        require(self.warmed,'WARM_BEFORE_POLL')
        require(type(host) in (float,int) and math.isfinite(host) and 0<=host<=100,'HOST_NUMBER')
        require(self.counts['host_polls']<1201,'POLL_BOUND')
        c=self.counts;c['host_polls']+=1;hot=host>=original.HOT_DIAGNOSTIC_PERCENT
        c['high_host_polls']+=int(hot)
        if c['emitted_samples']>=original.MAX_SAVED:
            c['skipped_budget_polls' if hot else 'skipped_cold_polls']+=1
            return ('budget' if hot else 'cold'),None
        if c['emitted_samples']>=2 and not hot:
            c['skipped_cold_polls']+=1;self.resume_warm_required=True
            return 'cold',None
        c['query_calls']+=1
        value=collect()  # Caller validates every executed native collection.
        require(value is not None,'REAL_COLLECTION_REQUIRED')
        if self.resume_warm_required:
            self.resume_warm_required=False;c['discarded_resume_warm_calls']+=1
            return 'warm',None
        c['emitted_samples']+=1
        return 'sample',value

    def summary(self):
        result=dict(self.counts);validate_schedule(result);return result

def validate_schedule(row):
    require(type(row) is dict and set(row)==set(KEYS),'SCHEDULE_KEYS')
    require(all(type(v) is int and 0<=v<=1202 for v in row.values()),'SCHEDULE_NUMBERS')
    require(2<=row['emitted_samples']<=original.MAX_SAVED and 2<=row['host_polls']<=1201,'TWO_INITIAL_AND_BOUND')
    require(row['query_calls']==1+row['emitted_samples']+row['discarded_resume_warm_calls']
        and row['host_polls']==row['emitted_samples']+row['discarded_resume_warm_calls']
            +row['skipped_cold_polls']+row['skipped_budget_polls'],'SCHEDULE_ACCOUNTING')
    require(row['discarded_resume_warm_calls']<=row['skipped_cold_polls']
        and row['skipped_budget_polls']<=row['high_host_polls']<=row['host_polls']
        and (row['skipped_budget_polls']==0 or row['emitted_samples']==original.MAX_SAVED),'SCHEDULE_BOUNDARIES')
    return row

def unique_pairs(pairs):
    out={}
    for key,value in pairs:
        require(key not in out,'DUPLICATE_FOOTER_KEY');out[key]=value
    return out

class Capture(original.Capture):
    """Original all249 parser plus additional truthful scheduling footer."""
    def __init__(self,*args,**kw):
        self.schedule=None;self.schedule_pending=bytearray();self.schedule_error=None
        super().__init__(*args,**kw)

    def _accept(self,name,chunk):
        super()._accept(name,chunk)
        if name!='stderr':return
        with self.lock:
            if self.schedule_error:return
            self.schedule_pending.extend(chunk)
            try:
                while b'\n' in self.schedule_pending:
                    raw,_,tail=self.schedule_pending.partition(b'\n');self.schedule_pending=bytearray(tail)
                    if not raw.startswith(FOOTER):continue
                    require(len(raw)+1<=FOOTER_LIMIT and self.schedule is None,'ONE_BOUNDED_FOOTER')
                    self.schedule=validate_schedule(json.loads(raw[len(FOOTER):],object_pairs_hook=unique_pairs))
                require(len(self.schedule_pending)<=original.MAX_FRAME,'PENDING_BOUND')
            except (ValueError,KeyError,TypeError,AttributeError,OverflowError):
                self.schedule_error='P164_CLOSED_SCHEDULE_REJECTED';self.error='live_progress_marker_scope'

    def communicate(self,timeout):
        result=super().communicate(timeout)
        if self.process.returncode==0:
            require(self.schedule is not None and not self.schedule_error and not self.schedule_pending,'EXPLICIT_SCHEDULE_REQUIRED')
            close=self.records[-1];schedule=self.schedule
            require(close['kind']=='closed' and close['total_samples']==schedule['host_polls']
                and close['saved_samples']==schedule['emitted_samples']
                and close['high_samples']==schedule['high_host_polls']
                and close['unsaved_high_samples']==schedule['skipped_budget_polls'],'SCHEDULE_FRAME_BINDING')
        return result

    def diagnostics(self):
        result=super().diagnostics()
        with self.lock:result.update(adaptive_schedule=dict(self.schedule) if self.schedule is not None else None,
            adaptive_schedule_error_code=self.schedule_error,adaptive_footer_limit_bytes=FOOTER_LIMIT,
            legacy_total_samples_counts_host_polls=True,resume_warm_sample_discard_required=True,
            cold_periods_are_not_native_observations=True)
        return result

def observed_call(args,**kw):
    c=original.c
    require(args==[str(c.ROOT/original.original.inventory.build.executable_name(1)),
        '--test-threads=1','--format=terse'] and kw.get('cwd')==c.ROOT
        and kw.get('stdin')==original.subprocess.DEVNULL and kw['env'].get('RUST_TEST_NOCAPTURE')=='0','EXACT_UNFILTERED_EXE')
    windows=c.Windows();member=c.w.BOOL()
    require(windows.k.IsProcessInJob(windows.k.GetCurrentProcess(),None,c.ctypes.byref(member)) and member.value,'JOB_BEFORE_QUERY')
    observer=original.group.Observer(windows.processors);process=None;sampler=Sampler();budget=False
    try:
        require(observer.collect() is None,'INITIAL_NATIVE_WARM');sampler.initial_warm()
        process=original.subprocess.Popen(args,**kw)
        original.emit(dict(kind='ready',worker_pid=os.getpid(),test_pid=process.pid,processor_count=windows.processors))
        while True:
            time.sleep(original.OBSERVATION_SECONDS);host=windows.sample()['system_cpu_percent']
            def collect():
                start=time.monotonic();snapshot=observer.collect((os.getpid(),));elapsed=time.monotonic()-start
                require(snapshot is not None and snapshot['stable_candidate_count']>0,'NATIVE_SAMPLE')
                row=dict(kind='sample',worker_pid=os.getpid(),test_pid=process.pid,
                    sequence=sampler.counts['emitted_samples']+1,
                    observed_at=datetime.now(timezone.utc).isoformat(),collect_seconds=elapsed,
                    system_cpu_percent=host,observation=snapshot)
                original.valid_record(row);return row
            action,row=sampler.poll(host,collect)
            if action=='sample':original.emit(row)
            if action=='budget' and not budget:
                original.emit(dict(kind='budget',saved_samples=original.MAX_SAVED,diagnostic_budget_limited=True));budget=True
            result=process.poll()
            # Preserve two genuine initial diagnostic samples even for a short
            # command, with no new subprocess; the same process is already done.
            if result is not None and sampler.counts['emitted_samples']>=2:break
    finally:observer.close()
    schedule=sampler.summary()
    # The legacy total_samples field counts host polling opportunities here;
    # this explicit footer separates actual query calls and cold/warm skips.
    footer=FOOTER+json.dumps(schedule,separators=(',',':')).encode('ascii')+b'\n'
    require(len(footer)<=FOOTER_LIMIT,'FOOTER_BOUND')
    original.sys.stderr.write(footer.decode('ascii'));original.sys.stderr.flush()
    original.emit(dict(kind='closed',query_cleanup_confirmed=True,total_samples=schedule['host_polls'],
        saved_samples=schedule['emitted_samples'],high_samples=schedule['high_host_polls'],
        unsaved_high_samples=schedule['skipped_budget_polls'],diagnostic_budget_limited=budget))
    return result
