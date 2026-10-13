"""Attach fixed PDH reads to the EXISTING Windows.sample owner only.

Cold reads at most once/8s; original>=75% warning forces a fresh bounded read.
Each observation records its longer PDH interval: never relabel as K32's0.5s.
Kernel/user split uses existing GetSystemTimes tuple, no extra K32 query.
"""
import time
from types import SimpleNamespace as NS

import serial_cpu_attribution as p

SELF="tools/p09/serial_observer_attribution.py"
TEST="tools/p09/tests/test_serial_observer_attribution.py"
COLD_SECONDS=8.
WARNING=75


def split(before,after):
    idle,kernel,user=(b-a for a,b in zip(before,after))
    total=kernel+user
    if min(idle,kernel,user)<0 or total<=0 or idle>kernel:return None
    return dict(kernel_busy_machine_percent=100*(kernel-idle)/total,user_machine_percent=100*user/total,
        extra_system_time_query=False,original_K32_resource_CPU_replaced=False)


def windows_type(original,objects,*,factory=p.Probe,clock=time.monotonic):
    class Windows(original):
        def __init__(self):
            super().__init__()
            self.attribution_probe=factory(self.processors);self.attribution_last=None
            objects.append(self)
        def sample(self):
            before=self.last
            row=super().sample()  # Original CPU/RAM values and errors retained.
            row['existing_system_time_breakdown']=split(before,self.last)
            now=clock()
            if (self.attribution_last is None or now-self.attribution_last>=COLD_SECONDS
                or row['system_cpu_percent']>=WARNING):
                diagnostic=self.attribution_probe.sample();self.attribution_last=now
                diagnostic['fresh_for_this_original_resource_sample']=True
            else:
                diagnostic=dict(available=False,reason='NOT_SAMPLED_COLD_INTERVAL',values=None,
                    fresh_for_this_original_resource_sample=False)
            row['serial_cpu_attribution']=diagnostic
            return row
    return Windows


def close(objects):
    clean=True
    for window in objects:clean=window.attribution_probe.close() and clean
    return clean


def summary(objects):
    return dict(existing_observer_instances=len(objects),second_sampler_thread_or_process=False,
        cold_counter_interval_seconds=COLD_SECONDS,original_warning_for_forced_read_percent=WARNING,
        original_CPU_RAM_decisions_replaced=False,additional_PDH_queries_explicit=True,
        PDH_interval_identical_to_K32_interval=False,
        probes=[window.attribution_probe.summary() for window in objects])
