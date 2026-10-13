"""Owner-local read gate for a future explicitly qualified batch connection.

No IO, Native acquisition, source partition selection, model discount or GO.
The producer still must prove actual fresh whole-byte observations and a live
Native frame. A serialized record cannot replace that frame. Contract-only
completion here never authorizes queue acceptance or reduces current scopes.
"""
import os
import threading
import current_stored_runtime_scope as scope
import runtime_input_frame as frames

SELF="tools/p09/phased_preservation_read_gate_v1.py"
TEST="tools/p09/tests/test_phased_preservation_read_gate_v1.py"

def require(ok,code):
    if not ok:raise ValueError("PHASED_READ_GATE_"+code)

class Gate:
    def __init__(self,whole,native,historical,*,identity=lambda:(os.getpid(),threading.get_ident())):
        require(callable(identity),"OWNER_IDENTITY")
        self.identity=identity;self.owner=identity()
        self.whole=scope.pins(list(whole.values()))
        self.native=scope.pins(list(native.values()))
        require(type(historical) is dict,"HISTORICAL_MAPPING")
        self.historical=scope.pins(list(historical.values())) if historical else {}
        require(self.whole==whole and self.native==native and self.historical==historical,"EXACT_KEY_PIN_BINDING")
        require(not set(self.native)&set(self.historical)
            and {**self.native,**self.historical}==self.whole,"LOSSLESS_DISJOINT_WHOLE")
        self.phase="PREPARATION";self.frame=None;self.reads=0;self.blocked=0
        self.reader=None;self.original_read=None;self.wrapper=None;self.restored=False

    def check_owner(self):require(self.identity()==self.owner,"SAME_OWNER_PROCESS_AND_THREAD")

    def native_started(self,whole_initial_pins,frame):
        self.check_owner();require(self.phase=="PREPARATION","ONE_INITIAL_BOUNDARY")
        require(scope.pins(whole_initial_pins)==self.whole,"INITIAL_WHOLE_BYTE_PINS")
        require(type(frame) is frames.Frame and frame.registered
            and frame.state=="HELD" and frame.held.acquired and not frame.held.closed,"LIVE_NATIVE_FRAME_NOT_SERIALIZED")
        frame.check()
        require({n:dict(p) for n,p in frame.inputs.items()}==self.native,"EXACT_LIVE_NATIVE_SCOPE")
        self.frame=frame;self.phase="NATIVE_ACTIVE"

    def native_finished(self,frame):
        self.check_owner();require(self.phase=="NATIVE_ACTIVE" and frame is self.frame,"SAME_FRAME_REFERENCE")
        require(frame.state=="COMMITTED" and not frame.registered and frame.held.closed
            and len(frame.boundaries)==2,"ORIGINAL_COMMIT_AND_BOTH_BOUNDARIES")
        require(frame.owned_cleanup_seen is True and type(frame.identity_after) is dict
            and frame.identity_after.get("held_identity_checks_complete") is True,"ORIGINAL_FINAL_IDENTITY_CHECKS")
        for boundary,role in zip(frame.boundaries,("before","after")):
            require(boundary.get("role")==role
                and scope.pins(boundary["actual_byte_pins"])==self.native,"BOTH_EXACT_NATIVE_BYTE_BOUNDARIES")
            reads=boundary["reader_diagnostics"]
            require(type(reads.get("read_passes")) is int and reads["read_passes"]==len(self.native)
                and type(reads.get("bytes_read")) is int and reads["bytes_read"]==sum(p["bytes"] for p in self.native.values())
                and reads.get("original_owned_read_operations_preserved") is True,"ORIGINAL_COMPLETE_NATIVE_BYTE_ACCOUNTING")
        diagnostic=frame.held.summary()
        require(diagnostic["input_lock_handles_remaining"]==0
            and diagnostic["input_lock_cleanup_confirmed"] is True
            and type(diagnostic.get("input_lock_handles_opened")) is int and diagnostic["input_lock_handles_opened"]>0
            and diagnostic["input_lock_handles_closed"]==diagnostic["input_lock_handles_opened"],"NATIVE_CLEANUP_BEFORE_CLOSING")
        self.phase="WHOLE_CLOSING"

    def finish(self,whole_final_pins):
        self.check_owner();require(self.phase=="WHOLE_CLOSING","NO_FINISH_BEFORE_NATIVE_CLEANUP")
        require(scope.pins(whole_final_pins)==self.whole,"FINAL_FRESH_WHOLE_BYTE_PINS")
        self.phase="CONTRACT_COMPLETE_NOT_ACCEPTED"

    def bind(self,reader):
        self.check_owner();require(self.reader is None and callable(reader._read)
            and callable(reader.checkpoint),"ONE_ORIGINAL_READER")
        self.reader=reader;self.original_read=reader._read
        def wrapped(name,parse=False):
            # Original hard resource errors take precedence. No cached value,
            # hash-only substitution or new observer/sampler is introduced.
            reader.checkpoint();self.check_owner()
            require(reader._read is self.wrapper,"EXACT_ACTIVE_READER_BINDING")
            require(self.phase in ("PREPARATION","NATIVE_ACTIVE","WHOLE_CLOSING"),"OPEN_PHASE_REQUIRED")
            if self.phase=="NATIVE_ACTIVE" and name in self.historical:
                self.blocked+=1;raise ValueError("PHASED_READ_GATE_HISTORICAL_READ_DURING_NATIVE")
            self.reads+=1
            return self.original_read(name,parse=parse)
        self.wrapper=wrapped;reader._read=wrapped;return self

    def restore(self):
        # Cleanup never waits/samples and never closes the frame's handles.
        self.check_owner()
        if self.restored:return
        require(self.reader is not None and self.reader._read is self.wrapper,"RESTORE_EXACT_READER")
        self.reader._read=self.original_read;self.restored=True

    def diagnostics(self):
        self.check_owner()
        return dict(phase=self.phase,forwarded_read_attempts=self.reads,
            historical_reads_blocked_during_Native=self.blocked,
            original_reader_restored=self.restored,
            Native_scope_selection_authorized=False,actual_whole_byte_reads_proven=False,
            actual_Native_product_qualified=False,queue_advance_authorized=False,
            accepted_count_delta=0,PC_freeze_resolved=False)
