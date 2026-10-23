"""Reuse the existing bounded V4 observer on ONE guard Windows instance only.
No changed CPU/RAM decisions, second system sample, WMI/PDH/thread/process.
"""
import time
import native_process_cpu_attribution_v4 as backend
import serial_observer_attribution as intervals
SELF='tools/p09/metadata_cpu_observer620.py'
def require(ok,code):
    if not ok:raise ValueError('META_CPU620_'+code)
class Attached:
    def __init__(self,guard,*,factory=backend.Probe,clock=time.monotonic):
        self.window=guard.windows;self.clock=clock;self.last=None;self.closed=False;self.calls=0
        require(not getattr(self.window,'_metadata_cpu_observer620',False),'ALREADY_ATTACHED')
        self.original_sample=self.window.sample
        self.had_instance_sample='sample'in vars(self.window)
        self.original_instance_sample=vars(self.window).get('sample')
        self.probe=factory(self.window.processors)
        def sample():
            before=self.window.last;row=self.original_sample();self.calls+=1
            row['existing_system_time_breakdown']=intervals.split(before,self.window.last)
            now=self.clock()
            if self.last is None or now-self.last>=intervals.COLD_SECONDS or row['system_cpu_percent']>=backend.WARNING_PERCENT:
                diagnostic=self.probe.sample(row);self.last=now
                diagnostic['fresh_for_this_original_resource_sample']=True
            else:diagnostic=dict(available=False,reason='NOT_SAMPLED_COLD_INTERVAL',values=None,fresh_for_this_original_resource_sample=False)
            row['serial_cpu_attribution']=diagnostic
            return row
        self.window._metadata_cpu_observer620=True;self.window.sample=sample
    def close(self):
        if self.closed:return self.probe.cleanup
        try:return self.probe.close()
        finally:
            if self.had_instance_sample:self.window.sample=self.original_instance_sample
            else:del self.window.sample
            del self.window._metadata_cpu_observer620;self.closed=True
    def summary(self):
        return dict(scope='one_current_metadata_guard_instance',original_sample_calls=self.calls,
            cold_interval_seconds=intervals.COLD_SECONDS,backend=self.probe.summary(),
            global_Windows_type_modified=False,guard_CPU_RAM_decisions_replaced=False,
            extra_system_CPU_sample_thread_process_or_WMI=False,causal_trigger_attribution_established=False,
            PC_freeze_resolved=False,closed=self.closed)
