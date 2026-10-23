"""Precise byte pacing for an unused original Native BoundaryReader only.

No original class/global/defaults, byte rate, burst credit, resource checkpoint
or deadline is changed. Never replace a pacer after any IO or pacing attempt.
"""
import time

SELF='tools/p09/native011_precise_boundary_pacer.py'
TEST='tools/p09/tests/test_native011_precise_boundary_pacer.py'


def require(ok,label):
    if not ok:raise ValueError('PRECISE_NATIVE_PACER_'+label)


def connect(reader,pressure):
    original=reader.pacer;before=dict(vars(reader));saved=dict(vars(original))
    require(type(original) is pressure.OwnedPacer and reader.read_passes==reader.bytes_read==0
        and reader.final_fresh_hashes==0 and not reader.snapshots,'ORIGINAL_UNUSED_READER_ONLY')
    require(original.clock is time.monotonic and original.sleeper is time.sleep
        and original.tokens==65536 and original.bytes_paced==0 and original.requested_sleep_seconds==0
        and original.bytes_by_kind=={'binary':0,'other':0} and original.kind=='other',
        'NO_CONSUMED_CREDIT_SLEEP_OR_REUSED_PACER')
    require(pressure.BINARY_RATE==1048576 and pressure.OTHER_RATE==2097152,'ORIGINAL_ONE_TWO_MIB_RATES')
    candidate=pressure.OwnedPacer(clock=time.perf_counter,sleeper=original.sleeper)
    require(type(candidate) is type(original) and set(vars(candidate))==set(saved)
        and all(vars(candidate)[key]==value for key,value in saved.items() if key not in ('clock','last')),
        'ONLY_FRESH_CLOCK_AND_ITS_ORIGIN_DIFFER')
    require(vars(original)==saved and reader.pacer is original,'ORIGINAL_PACER_NOT_MUTATED')
    reader.pacer=candidate
    require(set(vars(reader))==set(before)
        and all(vars(reader)[key] is value for key,value in before.items() if key!='pacer'),
        'EVERY_OTHER_ORIGINAL_READER_FIELD_RETAINED')
    return dict(actual_reader_class_unchanged=True,original_pacer_class_algorithms_and_sleeper_retained=True,
        before_clock='monotonic',after_clock='perf_counter',
        before_clock_resolution=time.get_clock_info('monotonic').resolution,
        after_clock_resolution=time.get_clock_info('perf_counter').resolution,
        rates=dict(binary=pressure.BINARY_RATE,other=pressure.OTHER_RATE),maximum_burst_bytes=65536,
        read_hash_parse_counter_checkpoint_or_deadline_changed=False,
        used_pacer_or_failed_reader_may_be_reused=False,actual_Native_Frame_or_product_qualified=False)
