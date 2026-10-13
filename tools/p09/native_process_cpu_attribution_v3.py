"""Native observer successor uses bounded SnapshotV2 with explicit provenance.

Budget50ms/total2s/query128/same owner/cold8/warning75 and original K32 remain.
Partial snapshots never become baselines/valid samples. API construction cost
joins setup budget; old V1/V2 modules and actual147/148 receipts remain intact.
"""
import math
import os
import threading
import time
from types import SimpleNamespace as NS

import native_process_cpu_attribution_v2 as prior
import bounded_cpu_attribution_probe_v2 as native

SELF="tools/p09/native_process_cpu_attribution_v3.py"
TEST="tools/p09/tests/test_native_process_cpu_attribution_v3.py"
BACKEND="NATIVE_TOOLHELP_PROCESS_TIMES_V3"


class Probe(prior.Probe):
    def __init__(self,processors,*,api=None,clock=time.monotonic,
                 identity=lambda:(os.getpid(),threading.get_ident())):
        self.cooperative_budget_stops=0
        self.partial_captures_discarded=0
        self.api_constructor_seconds=0.
        if api is None:
            started=clock();api=native.Snapshot()
            self.api_constructor_seconds=clock()-started
            prior.prior.require(math.isfinite(self.api_constructor_seconds) and self.api_constructor_seconds>=0,"API_CLOCK")
        super().__init__(processors,api=api,clock=clock,identity=identity)
        self.total_latency+=self.api_constructor_seconds
        self.maximum_latency=max(self.maximum_latency,self.total_latency)
        if self.total_latency>prior.prior.MAX_SAMPLE_SECONDS or self.total_latency>prior.prior.MAX_TOTAL_SECONDS:
            self.disabled_reason="MEASUREMENT_COST_BUDGET_EXCEEDED";self.close()

    def capture(self):
        api=self.api
        flags=[]
        def collect():
            row=api.capture()
            flags.append(row.get("measurement_budget_exceeded") is True)
            return row
        self.api=NS(capture=collect)
        try:
            result=super().capture()
        finally:
            self.api=api
        if flags and flags[0]:
            # Explicit flag also protects injected clocks/API test doubles.
            self.cooperative_budget_stops+=1
            self.partial_captures_discarded+=1
            self.disabled_reason="MEASUREMENT_COST_BUDGET_EXCEEDED"
            self.close();return None
        return result

    def summary(self):
        row=super().summary()
        row.update(backend=BACKEND,capture_api_source=native.SELF,
          capture_api_constructor_seconds=self.api_constructor_seconds,
          constructor_and_first_capture_share_setup_budget=True,
          cooperative_capture_deadline_seconds=native.MAX_CAPTURE_SECONDS,
          cooperative_budget_stops=self.cooperative_budget_stops,
          partial_captures_discarded=self.partial_captures_discarded,
          partial_capture_never_baseline_or_valid_sample=True,
          time_scratch_allocations_per_capture=1,
          create_and_close_in_capture_clock=True,
          OS_call_hard_preemption_guaranteed=False)
        return row


def windows_type(original,objects,*,factory=Probe,clock=time.monotonic):
    return prior.windows_type(original,objects,factory=factory,clock=clock)


def close(objects):
    return prior.close(objects)


def summary(objects):
    row=prior.summary(objects);row["backend"]=BACKEND
    return row
