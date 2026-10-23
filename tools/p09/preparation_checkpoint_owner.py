"""Coalesce only the original profiler's recursive preparation requests.

The original profile callback still runs. While the same serial resource
checkpoint is in flight, that exact callback requests the same check again;
it must not resample or observe a half-completed sample. The outer original
check completes before caller IO resumes. All other reentry fails closed.
Native checkpoints are delegated unchanged, including their recursion latch.
No sampler, thread, threshold, deadline or original guard method is changed.
"""
import ast
import copy
import hashlib
import os
import sys
import threading
from types import CodeType, FunctionType

SELF = 'tools/p09/preparation_checkpoint_owner.py'
TEST = 'tools/p09/tests/test_preparation_checkpoint_owner.py'
SOURCE = dict(path='tools/p09/batch_verification.py', bytes=63495,
    sha256='296b4fe1070a6e5e4cfb882ba0ad9ca252edc702fc2441e970292cf5ad76dff9')


def require(ok, code):
    if not ok:
        raise ValueError('PREPARATION_CHECKPOINT_OWNER_' + code)


def shape(code):
    return (code.co_code, tuple(shape(v) if type(v) is CodeType else v for v in code.co_consts),
        code.co_names, code.co_varnames, code.co_freevars, code.co_cellvars,
        code.co_argcount, code.co_posonlyargcount, code.co_kwonlyargcount, code.co_flags,
        code.co_exceptiontable)


def original_profile_factory(raw):
    require(type(raw) is bytes and len(raw) == SOURCE['bytes']
        and hashlib.sha256(raw).hexdigest() == SOURCE['sha256'], 'EXACT_WHOLE_ORIGINAL_SOURCE')
    outer = next(n for n in ast.parse(raw).body if isinstance(n, ast.FunctionDef) and n.name == 'construct_runtime')
    node = next(n for n in outer.body if isinstance(n, ast.FunctionDef) and n.name == 'profile')
    factory = ast.parse('def make(audit_state, reader):\n pass').body[0]
    factory.body = [copy.deepcopy(node), ast.Return(value=ast.Name(id='profile', ctx=ast.Load()))]
    env = {}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[factory], type_ignores=[])), SOURCE['path'], 'exec'), env)
    return env['make']


class Checkpoint:
    def __init__(self, relay, original, raw, *, profile=sys.getprofile,
                 identity=lambda: (os.getpid(), threading.get_ident())):
        require(all(callable(v) for v in (original, profile, identity)), 'EXPLICIT_OWNER_AND_ORIGINAL_CHECK')
        self.relay, self.original, self.profile, self.identity = relay, original, profile, identity
        self.owner = identity()
        self.profile_shape = shape(original_profile_factory(raw)({}, None).__code__)
        self.reader = None
        self.inflight = self.failed = False
        self.delegated = self.coalesced = self.native = 0
        self.checkpoint = self.check

    def bind_reader(self, reader):
        require(self.reader is None and self.relay.phase == 'PREPARATION' and callable(reader.checkpoint),
            'ONE_SOURCE_READER_BEFORE_CONSTRUCTION')
        self.reader = reader

    def _original_profile_request(self):
        profile = self.profile()
        if type(profile) is not FunctionType or shape(profile.__code__) != self.profile_shape:
            return False
        cells = dict(zip(profile.__code__.co_freevars, (c.cell_contents for c in profile.__closure__ or ())))
        if set(cells) != {'audit_state', 'reader'} or cells['reader'] is not self.reader:
            return False
        state = cells['audit_state']
        if type(state) is not dict or state.get('active') is not True or state.get('checking') is not False:
            return False
        # No arbitrary caller can reuse this optimization. Match the actual
        # callback frame, directly or through the actual reader's Closing.
        frame = sys._getframe(2)
        checkpoint = self.reader.checkpoint
        if checkpoint is self.checkpoint:
            return frame.f_code is profile.__code__
        owner = getattr(checkpoint, '__self__', None)
        function = getattr(checkpoint, '__func__', None)
        return (type(function) is FunctionType and frame.f_code is function.__code__
            and frame.f_locals.get('self') is owner
            and getattr(owner, 'original_checkpoint', None) is self.checkpoint
            and frame.f_back is not None and frame.f_back.f_code is profile.__code__)

    def check(self, *args, **kwargs):
        try:
            require(self.identity() == self.owner and not self.failed, 'SAME_SERIAL_OWNER_NOT_FAILED')
            if self.relay.phase != 'PREPARATION':
                self.native += 1
                return self.original(*args, **kwargs)
            if self.inflight:
                require(not args and not kwargs and self.reader is not None and self._original_profile_request(),
                    'ONLY_EXACT_ORIGINAL_PROFILER_REENTRY')
                self.coalesced += 1
                return None
            self.inflight = True
            try:
                self.delegated += 1
                return self.original(*args, **kwargs)
            finally:
                self.inflight = False
        except BaseException:
            self.failed = True
            raise

    def evidence(self):
        return dict(original_preparation_checks_completed_or_attempted=self.delegated,
            original_profiler_duplicate_requests_coalesced=self.coalesced,
            original_Native_checkpoints_forwarded=self.native, failed=self.failed,
            original_profile_callbacks_skipped=False, original_guard_or_samples_or_policies_mutated=False,
            new_sampler_or_query_or_thread=False, Native_recursion_guard_replaced=False,
            IO_allowed_to_resume_before_outer_original_check_completes=False,
            GO_authorized=False, actual_Native_or_product_qualified=False)
