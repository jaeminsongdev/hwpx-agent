"""P239: pre-GO STOP의 아직 생성되지 않은 Borrower를 명시적인 witness로 처리.

기존 P227 정상/PASS 및 생성된 borrower STOP 경로는 그대로 호출한다. None을
임의로 빈 counter로 바꾸지 않는다. 실제 객체/읽기/정리 상태가 모두 미생성을
증명하는 DEFERRED_NOT_STARTED에서만 종료 sidecar를 쓴다. 아직 runtime 미연결.
"""
import deferred_parent_failure as original
SELF='tools/p09/deferred_uncreated_borrower_failure.py'
TEST='tools/p09/tests/test_uncreated_borrower_failure.py'


def require(ok,code):original.require(ok,'UNCREATED_BORROWER_'+code)


def unused_witness(frame,snapshot,document):
    require(document.get('state')=='DEFERRED_NOT_STARTED'
        and document.get('actual_product_child_executed') is False
        and document.get('heavy_work_started') is False,'ONLY_BEFORE_GO_NO_BODY')
    require(hasattr(frame,'held') and hasattr(frame.held,'borrower')
        and frame.held.borrower is None and frame.held.closed is True
        and frame.readers==[] and frame.boundaries==[]
        and frame.held.active_readers==set() and frame.held.active_streams==0,
        'REAL_EXPLICIT_NONE_AND_NO_READER_OBJECTS')
    own=snapshot['handles']
    require(snapshot['frame_state']=='CLOSED' and snapshot['registered_live_frame'] is False
        and snapshot['actual_byte_boundaries']==[] and own['borrowed_byte_streams'] is None
        and own['input_lock_cleanup_confirmed'] is True
        and type(own['input_lock_handles_opened']) is int
        and own['input_lock_handles_opened']==own['input_lock_handles_closed']>0
        and all(type(own[key]) is int and own[key]==0 for key in
            ('input_lock_handles_remaining','active_reader_bindings','active_byte_streams',
            'handle_close_failed_attempts','byte_stream_identity_checks','probe_handles_opened',
            'probe_handles_closed','probe_handles_remaining')),'NO_NATIVE_BYTE_USE_AND_ALL_LOCKS_CLOSED')
    return dict(borrower_object_explicitly_not_created=True,source_boundary_reader_count=0,
        actual_byte_boundary_count=0,original_byte_stream_identity_checks=0,
        zero_duplicate_lifecycle_count_derived_from_nonexistence_not_missing_measurement=True,
        missing_job_or_native_counters_not_reported_as_measured_zero=True)


class Capture(original.Capture):
    def write_terminal(self,stream,owner,out):
        # 실제 정상 borrower 경로에서는 전체 frame.summary를 한 번 더 복제하지
        # 않고 원 writer로 즉시 위임한다. 원 writer의 모든 정리 검사는 그대로다.
        if hasattr(self.frame,'held') and hasattr(self.frame.held,'borrower') and self.frame.held.borrower is not None:
            return super().write_terminal(stream,owner,out)
        snapshot=self.frame.summary()
        if snapshot['handles']['borrowed_byte_streams'] is not None:
            return super().write_terminal(stream,owner,out)
        require(self.pending and not self._written,'ONE_PENDING_WRITE')
        require(owner.done.is_set() and out.get('resource_watcher_cleanup_confirmed') is True
            and owner.reason in (None,original.failure.STOP),'OWNER_TERMINAL')
        self._parent_closed(self._document);self._identity(self._document)
        witness=unused_witness(self.frame,snapshot,self._document)
        lifecycle=dict(owner_done=True,owner_cleanup_confirmed=True,frame_state='CLOSED',
            input_lock_cleanup_confirmed=True,original_stop_reason=self._document['stop_reason'],
            input_lock_handles_remaining=0,duplicate_handles_remaining=0,active_byte_streams=0)
        self._written=True
        stats=original.failure.dump(self._document,stream,lifecycle=lifecycle)
        return dict(**stats,uncreated_borrower_witness=witness,
            original_failure_document_and_None_summary_preserved=True,
            live_frame_or_sampler_restarted=False,runtime_connection_qualified=False)
