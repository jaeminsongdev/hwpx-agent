"""Bounded sequential reader bindings for both Native boundaries and closing.

V1 state/whole-pin/live-frame/hard-error contracts unchanged. No Native or GO.
"""
import phased_preservation_read_gate_v1 as original
from phased_preservation_read_gate_v1 import frames,scope,require

SELF="tools/p09/phased_preservation_read_gate_v2.py"
TEST="tools/p09/tests/test_phased_preservation_read_gate_v2.py"
MAX_BINDINGS=8

class Gate(original.Gate):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.bindings=0;self.restored_bindings=0
    def bind(self,reader):
        self.check_owner()
        require(self.bindings<MAX_BINDINGS,"BOUNDED_SEQUENTIAL_BINDINGS")
        require(self.reader is None or self.restored,"RESTORE_PREVIOUS_BEFORE_NEXT_READER")
        if self.reader is not None:
            require(self.reader._read is self.original_read,"PREVIOUS_ORIGINAL_STILL_RESTORED")
        self.reader=None;self.original_read=None;self.wrapper=None;self.restored=False
        super().bind(reader);self.bindings+=1;return self
    def restore(self):
        was=self.restored
        super().restore()
        if not was:self.restored_bindings+=1
    def diagnostics(self):
        return dict(super().diagnostics(),reader_bindings=self.bindings,
            reader_bindings_restored=self.restored_bindings,
            active_reader_bindings=self.bindings-self.restored_bindings,
            maximum_reader_bindings=MAX_BINDINGS,
            same_original_phase_and_whole_and_Native_contracts=True)
