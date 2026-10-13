"""P227 adapter: 원 parent STOP row만 종료 뒤 새 sidecar로 보존한다.

원 PASS packed writer와 frame guard는 그대로 둔다. live CPU STOP 중에는 row 참조만
보관하며 copy/gzip/새 읽기/새 감시기/쓰기/제품 재시도를 하지 않는다.
old parent가 종료된 뒤 caller가 frame·owner 정리를 완료해야 기록할 수 있다.
"""
import resume_packed_pressure_runtime as original
import terminal_failure_receipt_r2 as failure

SELF='tools/p09/deferred_parent_failure.py'
TEST='tools/p09/tests/test_deferred_parent_failure.py'


def require(ok,code):
    original.require(ok,'DEFERRED_FAILURE_'+code)


class Capture:
    def __init__(self,frame,completed,index,name,binding):
        self.frame=frame;self.completed=completed;self.index=index;self.name=name;self.binding=binding
        self._document=None;self._written=False;self._seen=False
        self._pass_writer=original.parent_writer(frame,completed)

    @property
    def pending(self):return self._document is not None

    def writer(self,document,stream,**keywords):
        require(keywords==dict(ensure_ascii=False,indent=2),'ORIGINAL_KEYWORDS')
        require(not self._seen and not self.pending and not self._written,'ONE_PARENT_TERMINAL')
        self._seen=True
        if document.get('state')=='PASS_SCOPED_NOT_GATE':
            return self._pass_writer(document,stream,**keywords)
        self._parent_closed(document)
        self._identity(document)
        # 원 parent run은 dump 뒤 상태를 변경하지 않고 요약 출력 후 반환한다.
        # source/Job 원 검사는 이미 수행됐지만 STOP는 runtime 수용이 아니다.
        self._document=document
        return None

    def _identity(self,document):
        require(document.get('schema_version')==original.p.SCHEMA
            and document.get('selected_test_names')==[self.name]
            and document.get('binding')==self.binding
            and document.get('test_arguments')==original.p.v.arguments(self.name)
            and document.get('task')==f'p204-r07-case-{self.index:03}-tests','EXACT_ORIGINAL_PARENT')

    def _parent_closed(self,document):
        failure.validate_parent(document)

    def write_terminal(self,stream,owner,out):
        require(self.pending and not self._written,'ONE_PENDING_FAILURE_WRITE')
        require(owner.done.is_set() and out.get('resource_watcher_cleanup_confirmed') is True
            and owner.reason in (None,failure.STOP),'ORIGINAL_OWNER_CLOSED')
        snapshot=self.frame.summary();held=snapshot['handles'];borrowed=held['borrowed_byte_streams']
        lifecycle=dict(owner_done=owner.done.is_set(),owner_cleanup_confirmed=out['resource_watcher_cleanup_confirmed'],
            frame_state=snapshot['frame_state'],input_lock_cleanup_confirmed=held['input_lock_cleanup_confirmed'],
            original_stop_reason=self._document['stop_reason'],
            input_lock_handles_remaining=held['input_lock_handles_remaining'],
            duplicate_handles_remaining=borrowed['duplicate_handles_remaining'],
            active_byte_streams=held['active_byte_streams'])
        require(snapshot['registered_live_frame'] is False and held['active_reader_bindings']==0
            and held['handle_close_failed_attempts']==0 and borrowed['duplicate_close_failed_attempts']==0,
            'NO_REMAINING_OR_FAILED_NATIVE_CLOSE')
        self._parent_closed(self._document)
        self._identity(self._document)
        # 쓰기 실패도 재시도하지 않는다. partial sidecar는 caller가 보존한다.
        self._written=True
        return failure.dump(self._document,stream,lifecycle=lifecycle)
