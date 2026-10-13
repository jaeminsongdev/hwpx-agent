"""Native observer successor avoids optional process queries at CPU warning.
Original K32/RAM/source/Job decisions and low-load attribution stay unchanged.
Explicit unavailable result at>=75;no fabricated CPU,baseline,cleanup or retry.
"""
import math
import threading
import native_process_cpu_attribution_v3 as prior

SELF="tools/p09/native_process_cpu_attribution_v4.py"
TEST="tools/p09/tests/test_native_process_cpu_attribution_v4.py"
BACKEND="NATIVE_TOOLHELP_PROCESS_TIMES_V4"
WARNING_PERCENT=75
SUPPRESSED="HOST_CPU_WARNING_OPTIONAL_ATTRIBUTION_SUPPRESSED"

class Probe(prior.Probe):
    def __init__(self,*args,**kwargs):
        self.warning_attribution_suppressions=0
        super().__init__(*args,**kwargs)
    def sample(self,original_sample):
        prior.prior.prior.require(self.identity()==self.owner,"SAME_OBSERVER_OWNER")
        cpu=original_sample["system_cpu_percent"]
        prior.prior.prior.require(type(cpu) in (int,float) and math.isfinite(cpu) and 0<=cpu<=100,"ORIGINAL_CPU_VALUE")
        if cpu>=WARNING_PERCENT:
            self.warning_attribution_suppressions+=1
            return dict(available=False,reason=SUPPRESSED,values=None,
             optional_native_query_attempted=False,
             original_K32_CPU_RAM_decisions_replaced=False,diagnostic_measurement_fresh=False)
        return super().sample(original_sample)
    def summary(self):
        row=super().summary()
        row.update(backend=BACKEND,warning_optional_attribution_suppressed=True,
          warning_suppression_percent=WARNING_PERCENT,
          warning_attribution_suppressions=self.warning_attribution_suppressions,
          original_low_load_sample_code_retained=True,
          suppressed_result_is_unavailable_not_zero=True,
          suppression_does_not_change_original_guard_decisions=True,
          suppression_does_not_close_reset_or_rebaseline_probe=True)
        return row

def windows_type(original,objects,*,factory=Probe,clock=prior.time.monotonic):
    return prior.windows_type(original,objects,factory=factory,clock=clock)

def close(objects):return prior.close(objects)
def summary(objects):
    row=prior.summary(objects);row["backend"]=BACKEND
    row["warning_optional_attribution_suppressed"]=True
    row["warning_suppression_percent"]=WARNING_PERCENT
    return row
