"""Run9 readiness in the original parent Job and live Frame checkpoint.

Only source-pinned private template dependencies differ. Original Job creation,
sampler, cleanup, strict10 Input/Capture and the complete engine body remain.
No Job, Windows sampler, process or Frame is created during construction.
"""
from contextlib import contextmanager
from types import FunctionType,SimpleNamespace as NS
from unittest.mock import patch

SELF='tools/p09/native009_parent_launch_v1.py'
TEST='tools/p09/tests/test_native009_parent_launch_v1.py'


def require(ok,label):
    if not ok:raise ValueError('NATIVE009_PARENT_LAUNCH_'+label)


class Context:
    def __init__(self,c,launch):
        self.c=c;self.launch=launch;self.parent=None;self.active=False;self.attempts=0
        self.owner=None;self.job=None;self.jobs=0;self.restorations=0;self.frame_checks=0
        self.windows=[];self.bindings=[];self.original_runs=[]
    def bind_parent(self,parent):
        require(self.parent is None and type(parent.frames) is list and not parent.frames
            and parent.attempts==0,'ONE_UNEXECUTED_ORIGINAL_PARENT_STATE')
        self.parent=parent
    def checkpoint(self):
        require(self.active and self.jobs==1 and self.owner is not None and self.job is not None,
            'ORIGINAL_ACTIVE_OWNER_JOB_REQUIRED')
        require(self.parent is not None and len(self.parent.frames)==1,'ONE_ACTUAL_PARENT_FRAME_REQUIRED')
        frame=self.parent.frames[0]
        # Original check includes the registry/owner, held checkpoint/CPU/RAM
        # guard and original lock deadline. It is not a metadata-only Guard.
        frame.check();self.frame_checks+=1
        require(frame.state=='BEFORE_READ' and not frame.reading and len(frame.boundaries)==1,
            'ORIGINAL_FIRST_FULL_BYTE_BOUNDARY_BEFORE_GO')
    def owned(self,actual):
        require(self.active and self.jobs==1 and self.owner is not None and self.job is not None
            and len(self.bindings)==1,'ORIGINAL_SINGLE_OWNER_AND_BINDING')
        expected=self.bindings[0].launch_state.actual
        return self.launch.same_owned_job(self.owner,self.job,expected,actual)
    @contextmanager
    def owner_scope(self):
        require(not self.active and self.attempts==0 and self.parent is not None,'ONE_ORIGINAL_EXECUTION_NO_RETRY')
        self.attempts+=1;self.active=True
        cls=self.c.Windows;original=cls.job
        def job(owner,*args,**kwargs):
            require(self.active and self.jobs==0,'ONE_ORIGINAL_JOB_CREATION')
            handle=original(owner,*args,**kwargs)
            # Do not throw after allocation and lose the original runner's
            # handle. It receives and cleans exactly this original Job.
            self.owner=owner;self.job=handle;self.jobs+=1
            return handle
        try:
            with patch.object(cls,'job',job):yield
        finally:
            try:
                for binding in self.bindings:
                    for event in binding.events:event.close()
            finally:self.active=False;self.restorations+=1
    def evidence(self):
        return dict(original_parent_owner_execution_attempts=self.attempts,observed_original_Jobs=self.jobs,
            original_owner_Job_scope_restorations=self.restorations,original_live_Frame_checkpoints=self.frame_checks,
            production_launch_bindings=len(self.bindings),added_Job_or_sampler_or_Frame=False,
            actual_Native_source_or_product_or_acceptance_qualified=False)


def recovery_api(recovery,root,entry_pin,launch,protocol,connection,c):
    """One actual private window returned to the existing api.build contract."""
    context=Context(c,launch)
    def current_window(original,tool,raw):
        require(not context.windows,'ONE_CURRENT_WINDOW_CONSTRUCTION')
        window,proof=recovery.current_window(original,tool,raw)
        require(window.WINDOW.SECONDS==10 and protocol.SECONDS==15,'ORIGINAL_PRODUCT10_PLUS_PREPARATION15')
        original_component=window.WINDOW;original_link=window.WINDOW_LINK
        def connect(factory,capture_type):
            require(context.active and not context.bindings,'ONE_ACTUAL_PARENT_LAUNCH_BINDING')
            binding=launch.connect(root,entry_pin,original_component,protocol,connection,factory,capture_type,
                c.subprocess,context.owned,context.checkpoint)
            context.bindings.append(binding)
            return binding
        component=NS(**{**vars(original_component),'connect':connect})
        def connect_engine(engine,selected):
            require(selected is component,'SAME_PRIVATE_READINESS_COMPONENT')
            connected,state=original_link.connect_engine(engine,selected)
            original_run=connected.run_owned
            context.original_runs.append(original_run)
            scope=context.owner_scope;check=require
            def execute(run):
                check(type(run) is int and run==1,'ONE_CURRENT_LOGICAL_RUN1')
                with scope():return original_run(run)
            wrapped=FunctionType(execute.__code__,original_run.__globals__,name=execute.__name__,
                argdefs=execute.__defaults__,closure=execute.__closure__)
            require(wrapped.__globals__ is original_run.__globals__,'SAME_PRIVATE_PARENT_BINDING_GLOBALS')
            return NS(**{**vars(connected),'run_owned':wrapped}),state
        link=NS(**{**vars(original_link),'connect_engine':connect_engine})
        template=recovery.clone(window.template,WINDOW=component,WINDOW_LINK=link)
        require(template.__code__ is window.template.__code__ and template.__defaults__ is window.template.__defaults__
            and template.__closure__ is window.template.__closure__,'ENTIRE_ORIGINAL_TEMPLATE_CODE_DEFAULTS_CLOSURE')
        result=NS(**{**vars(window),'WINDOW':component,'WINDOW_LINK':link,'template':template})
        context.windows.append(NS(window=result,original_window=window,component=component,link=link))
        return result,dict(proof,run9_production_launch_and_original_owner_Job_checkpoint_dependencies_connected=True,
            original_template_code_defaults_closure_and_complete_capture_checker_retained=True,
            actual_Native_source_Frame_or_dispatch_qualified=False)
    return NS(**{**vars(recovery),'current_window':current_window}),context
