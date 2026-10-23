"""Consume the real engine's fresh q.pacer=OwnedPacer() assignment exactly once.

Uninstalled product-path component. The original allocator/assignment remains;
only its unused per-reader pacer is adapted to exact reservations. Keep 1/2MiB,
all original read/source/semantic wrappers, fresh IO and source closing. Never
restart an already used/failed reader or transfer old timing/reservation credit.
"""
import threading
import time
from types import SimpleNamespace as NS

SELF='tools/p09/native011_engine_owned_metadata_adoption.py'
TEST='tools/p09/tests/test_native011_engine_owned_metadata_adoption.py'
ATTRIBUTE='_p09_engine_owned_metadata_adoption'


def require(ok,code):
    if not ok:raise ValueError('ENGINE_OWNED_METADATA_ADOPTION_'+code)


def reader_type(base,exact,pressure,*,precise=True):
    require(type(base) is type and issubclass(base,pressure.prior.WeightedReader)
        and type(precise) is bool,'EXPLICIT_PREPARED_METADATA_READER')
    require(all('__setattr__' not in vars(cls) for cls in base.__mro__ if cls is not object),
        'NO_UNDECLARED_ATTRIBUTE_WRAPPER_BYPASSED')
    Pacer=exact.pacer_type(pressure.OwnedPacer)
    class Reader(base):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs)
            require(ATTRIBUTE not in vars(self) and hasattr(self,'_exact_input_sizes')
                and hasattr(self,'_exact_read_proxy') and self.read_passes==self.bytes_read==self.final_fresh_hashes==0
                and not self.snapshots,'UNUSED_EXACT_METADATA_ALLOCATOR_RESULT')
            super().__setattr__(ATTRIBUTE,NS(owner=threading.get_ident(),attempts=0,completed=0,failed=False,
                source_table=self._exact_input_sizes,read_proxy=self._exact_read_proxy))
        def __setattr__(self,name,value):
            state=vars(self).get(ATTRIBUTE)
            if name!='pacer' or state is None:return super().__setattr__(name,value)
            try:
                require(threading.get_ident()==state.owner and not state.failed,'SAME_UNFAILED_ASSIGNMENT_OWNER')
                state.attempts+=1
                require(state.attempts==1 and state.completed==0,'ONE_ORIGINAL_ENGINE_ASSIGNMENT_NO_RESET')
                require(self.read_passes==self.bytes_read==self.final_fresh_hashes==0 and not self.snapshots
                    and self._exact_input_sizes is state.source_table and self._exact_read_proxy is state.read_proxy
                    and self._exact_read_proxy.calls==0 and self._exact_read_proxy.stream is None
                    and self.open_pacer.requests==self.open_pacer.wait_seconds==0
                    and self.pacer.bytes_paced==self.pacer.requested_sleep_seconds==0
                    and self.pacer.reservations==0 and self.pacer.pending is self.pacer.request is None
                    and not self.pacer.failed,'NO_OLD_IO_OR_RESERVED_TIMING_CREDIT')
                require(type(value) is pressure.OwnedPacer and value.tokens==65536
                    and value.bytes_paced==value.requested_sleep_seconds==0
                    and value.bytes_by_kind=={'binary':0,'other':0} and value.kind=='other'
                    # OwnedPacer inherits WeightedPacer.__init__; its unused
                    # initial rate is 4MiB. Original select(name) sets 1/2MiB
                    # before EVERY actual read, and exact.reserve enforces it.
                    and value.rate==pressure.prior.OTHER_RATE
                    and value.clock is time.monotonic and value.sleeper is time.sleep,
                    'EXACT_ORIGINAL_UNUSED_OWNED_ONE_TWO_MIB_PACER')
                saved=dict(vars(value))
                selected=Pacer(clock=time.perf_counter if precise else value.clock,sleeper=value.sleeper)
                require(vars(value)==saved,'ORIGINAL_ASSIGNED_OBJECT_UNCHANGED')
                super().__setattr__(name,selected);state.completed+=1
            except BaseException:
                state.failed=True;raise
        def _read(self,name,parse=False):
            state=vars(self)[ATTRIBUTE]
            try:
                # Preserve original resource-error priority; do not run a new
                # sampler or otherwise substitute this check for old wrappers.
                self.checkpoint()
                require(threading.get_ident()==state.owner and not state.failed
                    and state.attempts==state.completed==1,'ORIGINAL_ENGINE_ASSIGNMENT_REQUIRED_BEFORE_IO')
                return super()._read(name,parse=parse)
            except BaseException:
                state.failed=True;raise
    require(Reader.__mro__[1:]==base.__mro__ and Reader._source is base._source
        and Reader.pin is base.pin and Reader.json is base.json and Reader.finish is base.finish,
        'ENTIRE_ORIGINAL_SOURCE_AND_PUBLIC_METHOD_CHAIN_RETAINED')
    return Reader,dict(original_engine_assignment_required_before_IO=True,
        original_owned_binary1_other2_MiB_rates_retained=True,all_original_read_wrappers_still_called=True,
        default_classes_or_engine_body_modified=False,used_or_failed_pacer_reset_permitted=False,
        original_Native_guard_deadline_or_shared_budget_changed=False,
        installed_in_product_entry=False,GO_authorized=False)


def summary(reader):
    state=vars(reader)[ATTRIBUTE]
    require(threading.get_ident()==state.owner,'ACTUAL_ADOPTION_OWNER_SUMMARY')
    return dict(assignment_attempts=state.attempts,assignment_completed=state.completed,failed=state.failed,
        failed_flag_covers_assignment_or_read_not_external_validator=True,
        original_engine_owned_assignment_adopted=state.attempts==state.completed==1 and not state.failed,
        physical_read_passes=reader.read_passes,physical_bytes_read=reader.bytes_read,
        semantic_fresh_inputs=len(reader.snapshots),semantic_final_fresh_hashes=reader.final_fresh_hashes,
        original_owned_rates=dict(binary=1048576,other=2097152),
        source_table_and_read_proxy_retained=reader._exact_input_sizes is state.source_table
            and reader._exact_read_proxy is state.read_proxy,
        actual_Native_or_product_qualified=False)
