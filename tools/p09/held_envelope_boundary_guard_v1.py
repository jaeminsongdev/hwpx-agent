"""Decode guard includes the original live Native boundary guard.

CODE13 writer/budget/reader source remains immutable. This private subclass
scopes the shared budget callback to the actual reader's pressure/Frame guard,
restoring it on every exit. No new sampler, read, delay or deadline extension.
"""
import runtime_envelope_physical_io_v1 as original
SELF="tools/p09/held_envelope_boundary_guard_v1.py"
TEST="tools/p09/tests/test_held_envelope_boundary_guard_v1.py"


def boundary_reader_type(base, projection, budget):
    New=original.boundary_reader_type(base,projection,budget)
    original_budget_callback=budget.checkpoint
    physical_names=frozenset(p["path"] for p in projection._bindings.values())
    class Reader(New):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs)
            self.envelope_original_boundary_guard_calls=0
        def _read(self,name,parse=False):
            if name not in physical_names:return super()._read(name,parse=parse)
            previous=budget.checkpoint
            def guarded():
                previous()
                self.checkpoint()
                self.envelope_original_boundary_guard_calls+=1
            budget.checkpoint=guarded
            try:return super()._read(name,parse=parse)
            finally:budget.checkpoint=previous
        def diagnostics(self):
            row=super().diagnostics()
            return dict(row,original_live_boundary_guard_during_decode=dict(
                calls=self.envelope_original_boundary_guard_calls,
                original_reader_pressure_Frame_and_lock_checkpoint_retained=True,
                shared_budget_callback_restored=budget.checkpoint is original_budget_callback,
                new_sampler_thread_read_delay_or_deadline=False))
    return Reader
