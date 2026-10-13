"""One raw duplicate stream per input, retained ONLY inside one live frame.

Both entire byte passes, original path/stream identities, cursor reset, CPU/RAM,
clock, ownership and physical-open pacing remain. No hash/JSON/byte cache.
Only the second DuplicateHandle/CRT opening is removed; its no-longer-needed
physical-open reservation becomes the same original pressure checkpoint.
All retained duplicates are bounded with held handles and closed before originals.
"""
import ast
import copy
from contextlib import contextmanager
import hashlib
import os
from types import SimpleNamespace as NS

import borrowed_locked_streams as b
import current_queue_acquisition_checkpoint as native

SELF="tools/p09/retained_read_streams.py"
TEST="tools/p09/tests/test_retained_read_streams.py"
SOURCES=native.SOURCES
frames=native.frames
definitions=native.definitions
LOCK_PIN=dict(path="tools/p09/locked_runtime_inputs.py",bytes=15465,
    sha256="e7c40a2ec0367e01c359e3b89c179d45367e9db233348e76ba82364cc0599e14")


def require(ok,code):
    if not ok:raise ValueError("RETAINED_READ_"+code)


class RawAPI(b.NativeBorrow):
    def stream(self,fd):
        require(not os.get_inheritable(fd),'NONINHERITABLE_DESCRIPTOR')
        return os.fdopen(fd,'rb',buffering=0)


class RetainedBorrower(b.Borrower):
    def __init__(self,held,api=None,**kwargs):
        super().__init__(held,RawAPI(held.api) if api is None else api,**kwargs)
        self.retained={};self.authorized_path=None;self.new_reservations=0
        self.reuse_checkpoints=0;self.leases=0;self.lease_returns=0
        self.physical_peak=0
    def reserve(self,reader,path):
        self.check()
        key=str(path)
        require(self.active_binding and self.bound_reader is reader and id(reader) in self.held.active_readers
            and getattr(reader,'_p206_input_lock_owner',None) is self.held,'EXACT_READER_RESERVATION')
        require(self.authorized_path is None and self.loan is None and self.close_failures==0,'ONE_PENDING_RESERVATION')
        require(key in self.handles,'EXACT_HELD_REGULAR_PATH')
        entry=self.retained.get(key)
        if entry is None:
            # The original Native pacer applies before every REAL new duplicate.
            self.held.api.pacer.reserve();self.new_reservations+=1
        else:
            require(entry[0]=='stream' and not entry[1].closed,'RETAINED_STREAM_LIVE')
            # No physical handle is created here. Keep the exact original
            # pressure/lock/resource callback instead of sleeping for an open.
            self.held.api.pacer.checkpoint();self.reuse_checkpoints+=1
        self.authorized_path=key
    def close_entry(self,key):
        stage,value=self.retained[key]
        try:released=bool(getattr(self.api,'close_'+stage)(value))
        except BaseException:released=False
        if released:del self.retained[key];self.closed+=1
        else:self.close_failures+=1
        return released
    @contextmanager
    def open(self,path,mode):
        self.check();require(mode=='rb' and self.active_binding,'BOUND_READ_BINARY_ONLY')
        require(self.bound_reader is not None and id(self.bound_reader) in self.held.active_readers
            and getattr(self.bound_reader,'_p206_input_lock_owner',None) is self.held,'ORIGINAL_STREAM_WRAPPER_REQUIRED')
        require(self.loan is None and self.close_failures==0,'ONE_SERIAL_STREAM_NO_FAILED_CLEANUP')
        key=str(path);require(key in self.handles and self.authorized_path==key,'EXACT_RESERVED_HELD_PATH')
        self.authorized_path=None
        if key not in self.retained:
            require(len(self.held.owned)+len(self.retained)<b.locks.MAX_HANDLES,'TOTAL_PHYSICAL_HANDLE_CEILING')
            handle=self.api.duplicate(self.handles[key]);self.retained[key]=('handle',handle);self.opened+=1
            self.physical_peak=max(self.physical_peak,len(self.held.owned)+len(self.retained))
            try:
                fd=self.api.descriptor(handle);self.retained[key]=('fd',fd)
                stream=self.api.stream(fd);self.retained[key]=('stream',stream)
            except BaseException:
                self.close_entry(key);raise
        stage,stream=self.retained[key]
        require(stage=='stream' and not stream.closed,'RETAINED_STREAM_LIVE')
        self.loan=('retained_stream',key);self.leases+=1
        try:
            require(stream.seek(0)==0,'SHARED_OFFSET_RESET');self.resets+=1
            self.check()
            # The original P206 wrapper verifies this SAME stream's Native
            # identity before yielding any bytes on BOTH passes.
            yield stream
        finally:require(self.release(),'LOGICAL_LEASE_RETURN')
    def release(self):
        self.owner_check()
        if self.loan is not None:self.loan=None;self.lease_returns+=1
        return True
    def close_retained(self):
        self.owner_check()
        require(not self.active_binding and self.loan is None,'NO_CLOSE_DURING_READ')
        self.authorized_path=None
        for key in tuple(self.retained):self.close_entry(key)
        return not self.retained
    def summary(self):
        row=super().summary()
        row.update(duplicate_handles_remaining=len(self.retained),
            retained_within_one_live_frame_only=True,unbuffered_raw_streams=True,
            parsed_JSON_hash_or_byte_cache=False,physical_handle_ceiling=b.locks.MAX_HANDLES,
            physical_handle_peak=self.physical_peak,new_duplicate_open_reservations=self.new_reservations,
            reused_stream_pressure_checkpoints=self.reuse_checkpoints,
            logical_read_leases=self.leases,logical_read_lease_returns=self.lease_returns,
            pending_open_reservation=self.authorized_path is not None,
            resource_callback_retained_on_reuse=True,cursor_reset_and_fresh_identity_on_each_pass=True)
        return row


def reader_sources_projection(source):
    require(type(source) is bytes and len(source)==LOCK_PIN['bytes']
        and hashlib.sha256(source).hexdigest()==LOCK_PIN['sha256'],'EXACT_ORIGINAL_LOCK_BYTES')
    tree=ast.parse(source.decode('utf-8'))
    classes=[n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='InputLocks']
    require(len(classes)==1,'ONE_ORIGINAL_LOCK_CLASS')
    nodes=[n for n in classes[0].body if isinstance(n,ast.FunctionDef) and n.name=='reader_sources']
    require(len(nodes)==1,'ONE_ORIGINAL_READER_BINDING')
    node=copy.deepcopy(nodes[0]);before=ast.dump(node,include_attributes=False);changed=0
    class Project(ast.NodeTransformer):
        def visit_Expr(self,n):
            nonlocal changed
            if ast.dump(n,include_attributes=False)==ast.dump(ast.parse('held.api.pacer.reserve()').body[0],include_attributes=False):
                changed+=1;out=ast.parse('held.borrower.reserve(reader, self.path)').body[0]
                out._original_reservation=copy.deepcopy(n);return out
            return self.generic_visit(n)
    node=Project().visit(node);require(changed==1,'ONE_ONLY_PHYSICAL_OPEN_RESERVATION')
    class Undo(ast.NodeTransformer):
        def visit(self,n):
            if hasattr(n,'_original_reservation'):return copy.deepcopy(n._original_reservation)
            return super().visit(n)
    require(ast.dump(Undo().visit(copy.deepcopy(node)),include_attributes=False)==before,'ALL_ORIGINAL_BINDING_GUARDS_RETAINED')
    namespace=dict(b.locks.__dict__)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),LOCK_PIN['path'],'exec'),namespace)
    return namespace['reader_sources'],dict(original_reader_binding_AST_restored_exactly=True,
        only_physical_open_reservation_routed=True,original_path_identity_binding_and_active_stream_guards_replaced=False)


def locks_type(base,reader_sources):
    class InputLocks(base):
        @contextmanager
        def reader_sources(self,reader):
            if self.borrower is None:self.borrower=RetainedBorrower(self,self.borrow_api)
            require(isinstance(self.borrower,RetainedBorrower),'ONE_RETAINED_OWNER')
            with self.borrower.sources(reader),reader_sources(self,reader):yield
        def close(self):
            retained_clean=True
            try:
                if self.borrower is not None:retained_clean=self.borrower.close_retained()
            finally:held_clean=super().close()
            return retained_clean and held_clean
        def summary(self):
            row=super().summary()
            if self.borrower is not None and (self.borrower.retained or self.borrower.close_failures):
                row['input_lock_cleanup_confirmed']=False
            return row
    return InputLocks


def load(reader,rate,c):
    api=native.load(reader,rate,c)
    # Preserve raw bytes through the original bounded/paced reader rather than
    # Reader.text's universal-newline normalization or an unpaced extra open.
    pin,buffer=reader._read(LOCK_PIN['path'],parse=True);reader._bind(LOCK_PIN['path'],pin)
    require(pin==LOCK_PIN,'ORIGINAL_LOCK_PIN')
    projected,proof=reader_sources_projection(bytes(buffer))
    return NS(**{**vars(api),'InputLocks':locks_type(api.InputLocks,projected),'retained_binding_projection':proof})


def model(required,inventory_requests,*,PDH_seconds=2.05):
    # Removed REAL duplicate openings, not assumed overlapping waits or relaxed
    # ceilings. Original byte rates, full two reads and all margins remain.
    import current_stored_runtime_scope as scope
    require(type(inventory_requests) is int and inventory_requests>0,'INVENTORY_COUNT')
    require(type(PDH_seconds) in (int,float) and PDH_seconds==2.05,'EXPLICIT_PDH_COST')
    result=scope.cost(required,14);n=len(required);saved=n/20
    require(2*n+result['directories']<=b.locks.MAX_HANDLES,'TOTAL_PHYSICAL_HANDLE_CEILING')
    result.update(two_actual_byte_pass_native_reservations=n,
        all_native_byte_open_pacing_seconds=n/20,
        predicted_combined_seconds=result['predicted_combined_seconds']-saved,
        removed_second_duplicate_handle_reservations=n,removed_second_duplicate_pacing_seconds=saved,
        byte_or_native_costs_assumed_overlapped=False,parsed_JSON_hash_or_byte_cache=False)
    extra=20+3+inventory_requests/20+11+5+PDH_seconds
    total=result['predicted_combined_seconds']+extra
    result.update(predicted_runtime_combined_seconds=total,nominal_fits_unchanged_deadline=total<600,
        product_allowance_seconds=20,pre_GO_and_assignment_allowance_seconds=3,
        final_inventory_checkpoint_count=inventory_requests,final_inventory_pacing_seconds=inventory_requests/20,
        additional_early_source_wait_allowance_seconds=11,post_cleanup_identity_allowance_seconds=5,
        additional_serial_PDH_maximum_sample_budget_seconds=PDH_seconds,
        PDH_OS_call_latency_hard_preemption_guaranteed=False,
        unknown_pressure_waits_included=False,actual_completion_guaranteed=False)
    require(total<600,'WHOLE_CLOSURE_INSIDE_UNCHANGED600')
    return result
