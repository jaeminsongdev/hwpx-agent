"""Acquisition-only first-warning stop at EVERY existing checkpoint.

The qualified112 bridge is preserved unchanged. During acquisition its original
90% early warning cannot cool and resume: original one-way latch would reject
the next Native reservation anyway. Stop immediately, including pacer waits.
Outside acquisition the original callback/cooling, bytes/identity and cleanup
are unchanged. Reuses the sole original sampler; creates no new Native query.
"""
from types import SimpleNamespace as NS

import current_stored_native_bridge as original

SELF="tools/p09/current_queue_acquisition_checkpoint.py"
TEST="tools/p09/tests/test_current_queue_acquisition_checkpoint.py"
SOURCES=original.SOURCES
definitions=original.definitions
frames=original.frames


def load(reader,rate,c):
    api=original.load(reader,rate,c)
    class EarlySourceCheckpoint(api.EarlySourceCheckpoint):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs)
            self.acquiring=False;self.acquisition_latched=False;self.acquisition_checks=0
            self.acquisition_warning_stops=0;self.latch_callback=None
        def __call__(self):
            if not self.acquiring:return super().__call__()
            # Like the original one-way latch, a stopped acquisition never
            # restarts sampling/cooling/opening. Cleanup remains unwrapped.
            if self.acquisition_latched:raise ValueError("STOP_NATIVE_OPEN_AFTER_HOST_SATURATION")
            self.base()  # Original hard CPU/RAM/IO/lock guards FIRST.
            self.acquisition_checks+=1
            _,value=self.latest()  # Original sample validity/owner-lock checks.
            if value>=90:
                self.warning_entries+=1;self.acquisition_warning_stops+=1
                self.acquisition_latched=True
                original.require(callable(self.latch_callback),"ACQUISITION_LATCH_OWNER")
                self.latch_callback()
                raise ValueError("STOP_NATIVE_OPEN_AFTER_HOST_SATURATION")
            # Exact original normal path: base + latest + return below90.
        def summary(self):
            row=super().summary()
            row["acquisition_warning_checkpoint_stop"]=dict(
                original_warning_percent=90,checks=self.acquisition_checks,warning_stops=self.acquisition_warning_stops,
                acquisition_active=self.acquiring,latched=self.acquisition_latched,
                original_hard_guards_called_first=True,original_cached_owner_sample_used=True,
                acquisition_cooling_waits_added=0,original_outside_acquisition_cooling_retained=True,
                sampler_thread_or_native_query_added=False,CPU_or_PC_freeze_improvement_claimed=False)
            return row
    class InputLocks(api.InputLocks):
        def __init__(self,root,checkpoint,*args,**kwargs):
            original.require(isinstance(checkpoint,EarlySourceCheckpoint),"ACQUISITION_CHECKPOINT_OWNER")
            super().__init__(root,checkpoint,*args,**kwargs)
            checkpoint.latch_callback=self.latch
        def latch(self):self.saturation_checkpoint.saturation_seen=True
        def acquire(self,*args,**kwargs):
            early=self.checkpoint
            original.require(not early.acquiring,"ONE_ACQUISITION_SCOPE")
            early.acquiring=True
            try:return super().acquire(*args,**kwargs)
            finally:early.acquiring=False
        def summary(self):
            row=super().summary()
            row["all_acquisition_checkpoint_warning_fail_fast"]=self.checkpoint.summary()["acquisition_warning_checkpoint_stop"]
            return row
    return NS(**{**vars(api),"EarlySourceCheckpoint":EarlySourceCheckpoint,"InputLocks":InputLocks})
