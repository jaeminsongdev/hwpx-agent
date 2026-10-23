"""Live original Frame coverage, not a serialized lease or IO exemption.

No worker reader/check/clock is changed. Parent/child delegation is deliberately
unavailable until the actual Native owner and scope connection are qualified.
"""
from types import MappingProxyType
import runtime_input_frame as frames
import current_stored_runtime_scope as scope

SELF='tools/p09/native011_source_coverage.py'


def require(ok,code):
    if not ok:raise ValueError('NATIVE011_SOURCE_COVERAGE_'+code)


def verify(frame,required,*,frame_type,boundary):
    """Prove exact worker pin coverage at an actual before/after byte boundary."""
    require(type(frame_type) is type and issubclass(frame_type,frames.Frame)
        and type(frame) is frame_type,'ORIGINAL_FRAME_REFERENCE_NOT_SERIALIZED_DATA')
    require(boundary in ('before','after'),'CLOSED_BOUNDARY_ROLE')
    frame.check()  # Original registry, owner, live handles, deadline and guard.
    require(frame.registered and not frame.reading and frame.registry.active is frame,
        'SAME_LIVE_REGISTERED_FRAME')
    require(type(frame.inputs) is MappingProxyType,'ORIGINAL_IMMUTABLE_INPUT_MAPPING')
    expected=scope.pins(list(required.values()))
    require(expected==required,'EXACT_REQUIRED_MAPPING_KEYS')
    actual={name:dict(pin) for name,pin in frame.inputs.items()}
    require(set(expected)<=set(actual),'EVERY_WORKER_INPUT_IN_CURRENT_FRAME')
    require(all(actual[name]==pin for name,pin in expected.items()),'EXACT_PINS_NOT_PATH_ONLY_COVERAGE')
    count=1 if boundary=='before' else 2
    state='BEFORE_READ' if boundary=='before' else 'AFTER_READ'
    require(frame.state==state and len(frame.boundaries)==len(frame.readers)==count,
        'EXACT_ORIGINAL_BYTE_BOUNDARY_STATE')
    for index,record in enumerate(frame.boundaries):
        role='before' if index==0 else 'after'
        require(record['role']==role and record['actual_byte_pins']==list(actual.values()),
            'WHOLE_ORIGINAL_FRAME_BYTE_PINS_NOT_WORKER_SUBSET')
        diagnostic=record['reader_diagnostics']
        require(diagnostic['read_passes']==len(actual)
            and diagnostic['bytes_read']==sum(pin['bytes'] for pin in actual.values()),
            'ACTUAL_FULL_BOUNDARY_BYTE_ACCOUNTING')
    require(frame.held.acquired and not frame.held.closed and not frame.held.releasing,
        'LIVE_HELD_OS_HANDLES')
    require(frame.held.stream_read_counts=={name:count for name in actual},
        'ORIGINAL_SAME_STREAM_IDENTITY_READ_COUNTS')
    identity=frame.held.verify_held_identities()
    require(identity['held_identity_checks_complete'] and identity['regular_file_count']==len(actual),
        'FRESH_OS_HANDLE_IDENTITY_AND_WHOLE_SCOPE')
    return dict(worker_required_count=len(expected),parent_input_count=len(actual),boundary=boundary,
        actual_parent_byte_boundaries=count,exact_whole_worker_pin_coverage=True,
        live_original_registry_and_OS_handles_verified=True,serialized_pin_used_as_handle=False,
        worker_IO_exemptions_applied=False,child_boundary_delegation_qualified=False,
        Native_Frame_or_product_or_GO_qualified=False)
