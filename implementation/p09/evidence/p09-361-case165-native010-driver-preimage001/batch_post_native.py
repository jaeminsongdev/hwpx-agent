"""One-way post-Native whole closing and original oracle coordination.

Construct with the original source checkpoint BEFORE readers/loaders capture
it. Supply construction_api() to metadata.construct and checkpoint to readers.
Only the original committed Frame may enter the one read-only closing owner.
No Native execution, GO permission, retry, queue writer or method replacement.
"""
import os
import threading
from types import FunctionType, SimpleNamespace as NS

SELF = 'tools/p09/batch_post_native.py'
TEST = 'tools/p09/tests/test_batch_post_native.py'


def require(ok, code):
    if not ok:
        raise ValueError('BATCH_POST_NATIVE_' + code)


class Closing:
    def __init__(self, relay, original_checkpoint, guard_factory, exact, *,
                 identity=lambda: (os.getpid(), threading.get_ident())):
        require(all(callable(v) for v in (original_checkpoint, guard_factory, exact, identity)),
            'EXPLICIT_ORIGINAL_DEPENDENCIES')
        self.relay = relay
        self.original_checkpoint = original_checkpoint
        self.guard_factory = guard_factory
        self.exact = exact
        self.identity = identity
        self.owner = identity()
        self.phase = 'ORIGINAL'
        self.broken = False
        self.context = self.result = self.guard = self.closing_reader = None
        self.original_checker = self.checker_shape = None
        self.guard_creations = self.oracle_attempts = 0
        self.cleanup = None
        # Keep one bound callable for ALL original lazy readers and loaders.
        self.checkpoint = self.check

    def _owner(self):
        require(self.identity() == self.owner and not self.broken, 'SAME_OWNER_NO_RETRY')

    def check(self, *args, **kwargs):
        try:
            if self.phase == 'ORIGINAL':
                self.original_checkpoint(*args, **kwargs)
            else:
                require(self.phase in ('CLOSING', 'ORACLE') and self.guard is not None,
                    'LIVE_POST_NATIVE_READER_ONLY')
                self.guard.check(*args, **kwargs)
                require(not self.context.active and self.relay.phase == 'NATIVE_TERMINAL'
                    and not self.relay.broken, 'ORIGINAL_NATIVE_MUST_STAY_TERMINAL')
            self._owner()
        except BaseException:
            self.broken = True
            raise

    def construction_api(self):
        self._owner()
        require(self.phase == 'ORIGINAL' and self.context is None, 'CONSTRUCTION_ONLY')
        return NS(check=self.checkpoint, bind=self.relay.bind)

    def bind_context(self, context):
        try:
            self._owner()
            require(self.phase == 'ORIGINAL' and self.context is None
                and self.relay.phase == 'PREPARATION' and self.relay.result is not None,
                'ONE_ACTUAL_UNEXECUTED_CONSTRUCTION')
            result = self.relay.result
            batch = result.assembled.batch
            require(context.parent is batch.parent_connection.state and not context.active
                and context.attempts == context.jobs == context.restorations == 0
                and context.parent.attempts == 0 and context.parent.frames == [],
                'SAME_UNEXECUTED_PARENT_CONTEXT')
            require(batch.checkpoint is self.checkpoint, 'ORIGINAL_BATCH_USES_FORWARD_SOURCE_DEPENDENCY')
            checker = result.assembled.checker.validate_candidate
            require(type(checker) is FunctionType, 'ORIGINAL_FULL_CHECKER_FUNCTION')
            self.original_checker = checker
            self.checker_shape = (checker.__code__, checker.__globals__, checker.__defaults__,
                checker.__closure__, None if checker.__kwdefaults__ is None else dict(checker.__kwdefaults__))
            self.result, self.context = result, context
        except BaseException:
            self.broken = True
            raise

    def _checker(self):
        checker = self.result.assembled.checker.validate_candidate
        code, env, defaults, closure, keywords = self.checker_shape
        require(checker is self.original_checker and checker.__code__ is code
            and checker.__globals__ is env and checker.__defaults__ is defaults
            and checker.__closure__ is closure and checker.__kwdefaults__ == keywords,
            'UNCHANGED_ORIGINAL_FULL_CHECKER')
        return checker

    def _terminal(self):
        self._owner()
        require(self.context is not None and self.result is self.relay.result
            and self.relay.phase == 'NATIVE_TERMINAL' and not self.relay.broken,
            'SUCCESSFUL_ORIGINAL_HANDOFF_TERMINAL')
        context = self.context
        batch = self.result.assembled.batch
        state = batch.parent_connection.state
        require(not context.active and context.parent is state
            and context.attempts == context.jobs == context.restorations == state.attempts == 1
            and len(context.bindings) == 1 and context.frame_checks > 0 and len(state.frames) == 1,
            'ONE_ORIGINAL_TERMINAL_OWNER_JOB_AND_FRAME')
        require(batch.phase in ('READY', 'SOURCE_BOUNDARIES_COMPLETE_NOT_ACCEPTED')
            and batch.active is None and not batch.metadata_reader_active and len(batch.cases) == 1,
            'ONE_ORIGINAL_COMMITTED_CASE_NOT_NO_GO_ABORT')
        index, gate = batch.cases[0]
        frame = state.frames[0]
        require(index == batch.first_index and gate.frame is frame
            and gate.phase in ('WHOLE_CLOSING', 'CONTRACT_COMPLETE_NOT_ACCEPTED'),
            'SAME_ORIGINAL_FINISHED_CASE_GATE')
        batch._check_parent_frame(frame)  # Original exact class/method/owner checks.
        require(frame.state == 'COMMITTED' and not frame.registered
            and frame.registry.active is None and frame.held.closed and frame.owned_cleanup_seen is True
            and len(frame.boundaries) == 2
            and [b['role'] for b in frame.boundaries] == ['before', 'after'],
            'BOTH_ORIGINAL_BYTE_BOUNDARIES_AND_COMMIT')
        handles = frame.held.summary()
        require(handles['input_lock_cleanup_confirmed'] is True
            and type(handles['input_lock_handles_opened']) is int
            and handles['input_lock_handles_opened'] > 0
            and handles['input_lock_handles_opened'] == handles['input_lock_handles_closed']
            and handles['input_lock_handles_remaining'] == 0, 'ALL_ORIGINAL_HANDLES_RELEASED')
        require(frame.raw_policy.restored is True and frame.raw_policy.installed is False,
            'ORIGINAL_RAW_POLICY_RESTORED')
        require(self.relay.pressure.restored is True and self.relay.pressure.latched is False,
            'ORIGINAL_METADATA_PRESSURE_RESTORED_NOT_FAILED')
        return batch, frame

    def start_closing(self):
        try:
            self._owner()
            require(self.phase == 'ORIGINAL' and self.guard_creations == 0, 'ONE_FORWARD_CLOSING_OWNER')
            self._terminal()  # Never acquire another guard for NO-GO/failed Native.
            self.guard_creations += 1
            self.guard = self.guard_factory('whole_metadata_preflight')
            self.guard.acquire()
            self.guard.check(force=True)
            self._terminal()
            self.phase = 'CLOSING'
        except BaseException:
            self.broken = True
            self.close()
            raise

    def finish_whole(self, reader):
        try:
            self.check()
            require(self.phase == 'CLOSING' and self.closing_reader is None
                and reader.checkpoint is self.checkpoint, 'ONE_ORIGINAL_WHOLE_CLOSING_READER')
            batch, _ = self._terminal()
            summary = batch.finish(reader)  # Original full fresh closing, exactly once.
            batch._closed_oracle_case(batch.first_index)
            self.guard.check(force=True)
            self.closing_reader = reader
            self.phase = 'ORACLE'
            return summary
        except BaseException:
            self.broken = True
            self.close()
            raise

    def verify(self, reader, row, listing, oldbody, fresh, ctx, *, flat=True):
        try:
            self.check()
            require(self.phase == 'ORACLE' and self.oracle_attempts == 0
                and type(flat) is bool and reader is not self.closing_reader
                and reader is not self.result.assembled.batch.initial_reader
                and reader.checkpoint is self.checkpoint
                and reader.read_passes == reader.bytes_read == 0 and reader.snapshots == {},
                'ONE_FRESH_ORIGINAL_ORACLE_READER')
            batch, frame = self._terminal()
            batch._closed_oracle_case(batch.first_index)
            for name, expected in dict(selected_test_index=batch.first_index,
                    cleanup_confirmed=True, owned_tree_empty=True, product_body_observed=True,
                    actual_product_child_executed=True, Native_source_frame_qualified=True,
                    current_generation_runtime_candidate_qualified=True, accepted_count_delta=0).items():
                self.exact(row[name], expected, 'ORIGINAL_NATIVE_CANDIDATE_REQUIRED')
            self.exact(row['source_frame'], frame.summary(), 'SAME_ACTUAL_COMMITTED_FRAME_SUMMARY')
            # Do not clone, rewrite or replace the full lossless/accounting checker.
            self.oracle_attempts += 1
            result = self._checker()(
                reader, row, listing, oldbody, fresh, ctx, flat)
            reader.finish()
            self._checker()
            self.guard.check(force=True)
            self.phase = 'CHECKED_NOT_ACCEPTED'
            self.close()
            require(self.cleanup is True, 'ORIGINAL_READ_ONLY_OWNER_CLEANUP')
            return result
        except BaseException:
            self.broken = True
            self.close()
            raise

    def close(self):
        # Cleanup is unconditional on CPU/RAM or sticky policy failure.
        guard, self.guard = self.guard, None
        if guard is not None:
            try:
                guard.close()
            finally:
                self.cleanup = guard.cleanup
                if self.cleanup is not True:
                    self.broken = True
        if self.phase != 'CHECKED_NOT_ACCEPTED':
            self.phase = 'CLOSED_NOT_ACCEPTED'

    def evidence(self):
        return dict(phase=self.phase, failed=self.broken, closing_guard_creations=self.guard_creations,
            original_oracle_attempts=self.oracle_attempts, closing_owner_cleanup=self.cleanup,
            Native_clock_or_limit_reset=False, extra_whole_finish_or_case_replay=False,
            original_Frame_Job_or_oracle_methods_replaced=False, accepted_count_delta=0,
            GO_authorized=False, queue_advance_authorized=False,
            actual_Native_or_product_or_queue_qualified=False)
