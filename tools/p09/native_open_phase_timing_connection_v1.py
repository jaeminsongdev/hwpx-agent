"""Add instance timing to the complete locally returned Native API graph.

No old bridge/class/module rewritten, no original acquire/check/read/close
method removed. All pacer/checkpoint alias objects stay identical. This helper
alone does not qualify the current controller, complete scope, cost or GO.
"""
from types import SimpleNamespace as NS

SELF = "tools/p09/native_open_phase_timing_connection_v1.py"
TEST = "tools/p09/tests/test_native_open_phase_timing_connection_v1.py"


def require(ok, label):
    if not ok:
        raise ValueError("NATIVE_PHASE_CONNECTION_" + label)


def connect_api(api, timing):
    class InputLocks(api.InputLocks):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            native = self.original_native
            require(self.api.pacer is native.pacer and self.phase_pacer is native.pacer,
                    "ORIGINAL_PACER_ALIASES_BEFORE_INSTALL")
            before = (native.pacer, native.k, native.pacer.checkpoint,
                      self.phase_checkpoint, self.original_open_checkpoint,
                      self.saturation_checkpoint.checkpoint)
            self.phase_timing, self.phase_timing_proof = timing.connect(native, self.acquisition_diagnostics)
            after = (native.pacer, native.k, native.pacer.checkpoint,
                     self.phase_checkpoint, self.original_open_checkpoint,
                     self.saturation_checkpoint.checkpoint)
            require(all(a is b for a, b in zip(before, after)) and
                    self.api.pacer is self.phase_pacer is native.pacer,
                    "EVERY_PACER_KERNEL_CHECKPOINT_ALIAS_RETAINED")

        def summary(self):
            row = super().summary()
            row["native_open_phase_timing"] = self.phase_timing.summary()
            row["native_open_phase_timing"]["complete_current_controller_or_GO_qualified"] = False
            return row

    return NS(**{**vars(api), "InputLocks": InputLocks})
