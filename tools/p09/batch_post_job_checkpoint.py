"""Follow the original writer's post-Job checkpoint, never a closed Job.

Opt-in Handoff subclass; published original modules remain unchanged. Before
the original writer's exact guarded transition, delegate the original Handoff
including metadata pressure/recursion checks. After it, call the unchanged
post_guard only in the same original writer, owner, sampler and live Frame.
No resource policy, sampling cadence, deadline, cleanup or GO is replaced.
"""
import hashlib
import sys
from types import CodeType, FunctionType

SELF = 'tools/p09/batch_post_job_checkpoint.py'
TEST = 'tools/p09/tests/test_batch_post_job_checkpoint.py'
SOURCE = dict(path='tools/p09/run_case112_current_stored.py', bytes=23159,
    sha256='6f2a79556ebcfae40765ebd127a8fcc1022e5ee8611d666fd3daa723a4236713')


def require(ok, code):
    if not ok:
        raise ValueError('BATCH_POST_JOB_' + code)


def shape(code):
    return (code.co_code, tuple(shape(v) if type(v) is CodeType else v for v in code.co_consts),
        code.co_names, code.co_varnames, code.co_freevars, code.co_cellvars,
        code.co_argcount, code.co_posonlyargcount, code.co_kwonlyargcount, code.co_flags,
        code.co_exceptiontable)


def codes(raw):
    require(type(raw) is bytes and len(raw) == SOURCE['bytes']
        and hashlib.sha256(raw).hexdigest() == SOURCE['sha256'], 'EXACT_WHOLE_ORIGINAL_ENGINE')
    def nested(code, name):
        found = [v for v in code.co_consts if type(v) is CodeType and v.co_name == name]
        require(len(found) == 1, 'ONE_ORIGINAL_NESTED_FUNCTION')
        return found[0]
    run = nested(compile(raw, SOURCE['path'], 'exec'), 'run_owned')
    writer = nested(run, 'write')
    return writer, nested(writer, 'post_guard'), nested(run, 'sampled')


def cells(function):
    return dict(zip(function.__code__.co_freevars, (c.cell_contents for c in function.__closure__ or ())))


def handoff_type(original, raw):
    """Keep original preparation/Native ownership, add a proven final phase.

    The caller must supply the separately pinned original Handoff class. The
    complete frozen engine source is compiled, NOT executed or imported.
    """
    writer_code, guard_code, sampler_code = codes(raw)
    writer_shape, guard_shape, sampler_shape = map(shape, (writer_code, guard_code, sampler_code))

    class Handoff(original):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.post_job_guard = self.native_context = None
            self.post_job_checks = self.post_job_bindings = 0
            self.post_job_codes = None

        def admit_metadata(self, reader, context):
            # Original admission calls self.check while the metadata guard is
            # active; no new path is eligible then.
            super().admit_metadata(reader, context)
            self.native_context = context

        def _post_job(self, actual):
            self._owner()
            require(self.phase == 'NATIVE' and not self.checking, 'SAME_NATIVE_NO_RECURSION')
            context = self.native_context
            state = self.result.assembled.batch.parent_connection.state
            require(context is not None and context.parent is state and context.active is True
                and context.attempts == state.attempts == context.jobs == 1
                and context.restorations == 0 and len(state.frames) == 1,
                'SAME_ACTIVE_ORIGINAL_CONTEXT_AND_ONE_JOB_FRAME')
            pressure = self.pressure
            require(pressure.active is False and pressure.restored is True and pressure.latched is False
                and self.reader.checkpoint is self.original
                and pressure.original is pressure.hard is self.original,
                'ORIGINAL_METADATA_PRESSURE_RESTORED_NOT_REUSED')
            expected_codes = self.post_job_codes
            require(type(actual) is FunctionType and type(self.original) is FunctionType
                and actual.__globals__ is self.original.__globals__
                and (shape(actual.__code__) == guard_shape if expected_codes is None
                    else actual.__code__ is expected_codes[0])
                and actual.__defaults__ is None and actual.__kwdefaults__ is None,
                'EXACT_ORIGINAL_POST_JOB_GUARD')
            closed = cells(actual)
            sampler = closed['sampled']
            require(type(sampler) is FunctionType and sampler.__globals__ is actual.__globals__
                and (shape(sampler.__code__) == sampler_shape if expected_codes is None
                    else sampler.__code__ is expected_codes[1]), 'SAME_ORIGINAL_SAMPLER_BODY')
            sampling = cells(sampler)
            frame = state.frames[0]
            require(closed['frame'] is sampling['frame'] is frame
                and sampling['owner'] is pressure.owner
                and closed['windows_instance'] is sampling['windows_instance']
                and closed['global_deadline'] == sampling['global_deadline']
                == cells(self.original)['global_deadline'], 'SAME_SAMPLER_OWNER_FRAME_AND_DEADLINE')
            # The original write body creates this callback only after it has
            # observed complete product capture and positive original cleanup.
            # Require that exact still-active writer; no arbitrary replacement
            # owner callback or synthetic cleanup row can select this path.
            caller = sys._getframe(1)
            while caller is not None and caller.f_code.co_name != 'write':
                caller = caller.f_back
            require(caller is not None and caller.f_globals is actual.__globals__
                and (shape(caller.f_code) == writer_shape if expected_codes is None
                    else caller.f_code is expected_codes[2]), 'EXACT_ACTIVE_ORIGINAL_WRITER')
            live = caller.f_locals
            row = live.get('row')
            require(live.get('post_guard') is actual and live.get('owner') is pressure.owner
                and live.get('frame') is frame and live.get('product') is True and type(row) is dict
                and row.get('state') == 'PASS_SCOPED_NOT_GATE'
                and row.get('cleanup_confirmed') is True and row.get('owned_tree_empty') is True
                and row.get('owned_limits_readback', {}).get('verified') is True,
                'ORIGINAL_PRODUCT_CAPTURE_AND_CLEANUP_BEFORE_POST_JOB_CHECK')
            if self.post_job_guard is None:
                self.post_job_guard = actual
                self.post_job_bindings += 1
                self.post_job_codes = actual.__code__, sampler.__code__, caller.f_code
            require(actual is self.post_job_guard, 'ONE_UNCHANGED_POST_JOB_GUARD')
            self.checking = True
            try:
                self.post_job_checks += 1
                return actual()  # Same original sampler/limits/deadlines, no old Job accounting.
            finally:
                self.checking = False

        def check(self, *args, **kwargs):
            try:
                if self.phase == 'NATIVE' and self.pressure is not None:
                    owner_check = self.pressure.owner.checkpoint_io
                    # A restored reader retains the OLD guarded() closure.
                    # Follow only the original writer's proven new guard.
                    if (self.post_job_guard is not None or
                            (type(owner_check) is FunctionType and owner_check.__code__.co_name == 'post_guard')):
                        require(not args and not kwargs, 'ORIGINAL_POST_JOB_NO_ARGUMENTS')
                        return self._post_job(owner_check)
                return super().check(*args, **kwargs)
            except BaseException:
                self.broken = True
                raise

        def evidence(self):
            return dict(super().evidence(), original_post_Job_guard_bindings=self.post_job_bindings,
                original_post_Job_guard_checks=self.post_job_checks,
                post_Job_guard_body_or_sampler_or_limits_changed=False,
                original_modules_mutated=False, actual_post_Job_runtime_qualified=False)

    return Handoff
