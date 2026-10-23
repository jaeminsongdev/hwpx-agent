"""Exact tail reservations underneath, not instead of, metadata wrappers.

Uninstalled component candidate. Original BuildReader/open/path/weighted/read
wrappers remain in the same relative MRO order. No source/JSON/hash credit is
cached and no metadata factory, Native Frame or product is connected here.
"""
import time
from types import FunctionType,MappingProxyType

SELF='tools/p09/native011_metadata_tail_candidate.py'
TEST='tools/p09/tests/test_native011_metadata_tail_candidate.py'


def require(ok,code):
    if not ok:raise ValueError('METADATA_TAIL_CANDIDATE_'+code)


def selected_pacer(exact,pressure,policy):
    require(type(policy) is str and policy in ('owned','metadata_weighted'),'CLOSED_ORIGINAL_PACER_POLICY')
    base=pressure.OwnedPacer if policy=='owned' else pressure.prior.WeightedPacer
    Pacer=exact.pacer_type(base)
    inverse=True
    if policy=='metadata_weighted':
        # Native exact.pacer_type still admits only its original 1/2MiB pair.
        # This freshly generated metadata-only class retains the actual
        # allocator's original 2.5/4MiB pair. Exactly one membership tuple is
        # changed, and reversing it must restore the entire original code.
        method=Pacer.reserve;code=method.__code__;before=(1048576,2097152);after=(2621440,4194304)
        positions=[i for i,value in enumerate(code.co_consts) if value==before]
        require(len(positions)==1,'ONE_ORIGINAL_RATE_MEMBERSHIP_CONSTANT')
        constants=list(code.co_consts);constants[positions[0]]=after
        revised=code.replace(co_consts=tuple(constants));restored=list(revised.co_consts);restored[positions[0]]=before
        inverse=revised.replace(co_consts=tuple(restored))==code
        require(inverse,'ENTIRE_RESERVATION_METHOD_CODE_INVERSE')
        Pacer.reserve=FunctionType(revised,method.__globals__,argdefs=method.__defaults__,closure=method.__closure__)
    return Pacer,base,inverse


def reader_type(base,pins,exact,pressure,original,chunk_api,raw,*,precise=False,query_type=None,pacer_policy='owned'):
    require(type(precise) is bool and (not precise or type(query_type) is type),
        'EXPLICIT_OPTIONAL_FRESH_CLOCKS')
    require(type(base) is type and issubclass(base,pressure.prior.WeightedReader)
        and original.AuditEvidenceReader in base.__mro__,'EXPLICIT_WEIGHTED_METADATA_BASE')
    require(type(pins) is dict and 0<len(pins)<=4096,'BOUNDED_PHYSICAL_DECLARATIONS')
    sizes={}
    for name,pin in pins.items():
        require(type(name) is str and type(pin) is dict and set(pin)=={'path','bytes','sha256'}
            and pin['path']==name and type(pin['bytes']) is int and pin['bytes']>0,
            'POSITIVE_DECLARED_PHYSICAL_PIN')
        sizes[name]=pin['bytes']
    leaf,leaf_proof=exact.project(raw,original,chunk_api)
    Pacer,expected_pacer,pacer_inverse=selected_pacer(exact,pressure,pacer_policy)
    existing=[cls for cls in base.__mro__ if cls.__name__=='ChunkLeaf' and '_read' in vars(cls)]
    require(len(existing)<=1,'ONE_EXISTING_WORKSPACE_LEAF')
    anchor=existing[0] if existing else original.AuditEvidenceReader
    if existing:
        expected,_=chunk_api.project_read(raw)
        require(anchor._read.__code__==expected.__code__,'EXACT_EXISTING_WORKSPACE_LEAF_CODE')
    # A C3 diamond inserts one leaf immediately BEFORE the original byte leaf.
    # Every original super() wrapper above it still executes, with its original
    # __class__ closure. Neither copying/rebinding wrappers nor changing their
    # globals/classes is needed.
    class Tail(anchor):
        _read=leaf
    class Reader(base,Tail):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs)
            old=self.pacer
            require(type(old) is expected_pacer and old.tokens==65536
                and old.bytes_paced==old.requested_sleep_seconds==0
                and old.bytes_by_kind=={'binary':0,'other':0}
                and self.read_passes==self.bytes_read==self.final_fresh_hashes==0
                and not self.snapshots and not hasattr(self,'_exact_input_sizes'),
                'FRESH_ORIGINAL_OWNED_PACER_AND_READER_ONLY')
            selected_clock=old.clock
            if precise:
                opened=self.open_pacer
                require(type(opened) is query_type and opened.requests==0 and opened.wait_seconds==0
                    and old.clock is opened.clock is time.monotonic
                    and old.sleeper is opened.sleep is time.sleep,
                    'EXACT_UNUSED_ORIGINAL_QUERY_AND_BYTE_CLOCKS')
                # Only unused timestamps are established in the precise time
                # domain. Never translate/reset active deadlines or counters.
                self.open_pacer=query_type(opened.checkpoint,clock=time.perf_counter,sleep=opened.sleep)
                selected_clock=time.perf_counter
            self.pacer=Pacer(clock=selected_clock,sleeper=old.sleeper)
            self._exact_input_sizes=MappingProxyType(dict(sizes))
            self._exact_read_proxy=exact.LimitedRead()
    require(Reader.__mro__[1:]==tuple(
        value for cls in base.__mro__ for value in ((Tail,cls) if cls is anchor else (cls,))),
        'ONLY_INSERTED_LEAF_ORIGINAL_MRO_ORDER')
    require(Reader._read is base._read and Reader._source is base._source
        and Reader.pin is base.pin and Reader.json is base.json and Reader.finish is base.finish,
        'ALL_ORIGINAL_PUBLIC_AND_PATH_WRAPPERS_INHERITED')
    require(all(vars(Reader).get(name) is None for name in ('_read','_source','pin','json','finish')),
        'NO_TOP_LEVEL_WRAPPER_BYPASS')
    return Reader,dict(leaf_proof,original_wrapper_MRO_order_and_method_identities_retained=True,
        no_original_class_bases_methods_or_globals_changed=True,
        original_open_path_weight_selection_and_semantic_wrappers_not_replaced=True,
        explicit_physical_sizes_not_freshness_credit=True,
        original_one_two_MiB_rates_and_64KiB_workspace_retained=pacer_policy=='owned',
        original_metadata_two_point_five_four_MiB_rates_retained=pacer_policy=='metadata_weighted',
        metadata_rate_membership_only_code_inverse=pacer_inverse,
        original_Native_pacer_or_policy_modified=False,
        existing_workspace_leaf_verified_and_reused=bool(existing),
        optional_precise_unused_clocks=precise,query_rate_algorithm_sleeper_and_checkpoint_retained=True,
        active_deadline_or_used_counter_reset=False,global_timer_resolution_or_system_settings_changed=False,
        metadata_factory_or_Native_or_product_connected=False)
