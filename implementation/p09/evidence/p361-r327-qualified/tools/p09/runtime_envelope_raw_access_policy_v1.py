"""Scoped deny of mapped original-receipt path reads while a live epoch runs.

Explicitly covers Python Path/io/builtins/os open entry points only, not a
security sandbox or every OS API. Non-path descriptors and other inputs retain
the original calls. No path values/log contents, sampler or extra IO retained.
"""
import builtins
from contextlib import contextmanager,ExitStack
import io
import os
from pathlib import Path
import threading
from unittest.mock import patch
import runtime_envelope_scope_binding_v1 as source

SELF="tools/p09/runtime_envelope_raw_access_policy_v1.py"
TEST="tools/p09/tests/test_runtime_envelope_raw_access_policy_v1.py"


class Policy:
    def __init__(self,root,binding,active,checkpoint,identity=lambda:(os.getpid(),threading.get_ident())):
        source.require(type(binding) is source.Binding and callable(active) and callable(checkpoint),"RAW_POLICY_BINDING")
        self.root=os.path.abspath(os.fspath(root));self.binding=binding
        self.active,self.checkpoint,self.identity=active,checkpoint,identity;self.owner=identity()
        self.blocked=frozenset(os.path.normcase(os.path.abspath(os.path.join(self.root,n))) for n in binding.originals)
        self.path_calls=self.non_path_calls=self.raw_attempts=0;self.installed=False;self.restored=False
        self.calls_by_API={name:0 for name in ("Path.open","io.open","builtins.open","os.open")}

    def check_access(self,name,api):
        source.require(api in self.calls_by_API,"DECLARED_OPEN_API")
        same_owner=self.identity()==self.owner
        if same_owner:self.checkpoint()  # Original resource/lock stop FIRST.
        if type(name) is int:
            if same_owner:self.non_path_calls+=1
            return
        try:value=os.fspath(name)
        except TypeError:return  # Delegate the original API's argument error.
        if type(value) is bytes:value=os.fsdecode(value)
        if type(value) is not str:return
        path=os.path.normcase(os.path.abspath(value))
        if same_owner:
            self.path_calls+=1;self.calls_by_API[api]+=1
        if path in self.blocked and self.active():
            if same_owner:self.raw_attempts+=1
            raise ValueError("STOP_LIVE_RAW_ENVELOPE_RECEIPT_ACCESS")

    @contextmanager
    def install(self):
        self.checkpoint();source.require(self.identity()==self.owner and not self.installed,"ONE_OWNER_RAW_POLICY_SCOPE")
        old_path,old_io,old_builtin,old_os=Path.open,io.open,builtins.open,os.open
        def path_open(path,*args,**kwargs):
            self.check_access(path,"Path.open");return old_path(path,*args,**kwargs)
        def io_open(path,*args,**kwargs):
            self.check_access(path,"io.open");return old_io(path,*args,**kwargs)
        def builtin_open(path,*args,**kwargs):
            self.check_access(path,"builtins.open");return old_builtin(path,*args,**kwargs)
        def os_open(path,*args,**kwargs):
            self.check_access(path,"os.open");return old_os(path,*args,**kwargs)
        self.installed=True;self.restored=False
        try:
            with ExitStack() as stack:
                stack.enter_context(patch.object(Path,"open",path_open))
                stack.enter_context(patch.object(io,"open",io_open))
                stack.enter_context(patch.object(builtins,"open",builtin_open))
                stack.enter_context(patch.object(os,"open",os_open))
                yield self
        finally:
            self.installed=False
            self.restored=(Path.open is old_path and io.open is old_io and builtins.open is old_builtin and os.open is old_os)
            source.require(self.restored,"ALL_ORIGINAL_OPEN_FUNCTIONS_RESTORED")

    def evidence(self):
        return dict(mapped_raw_receipt_count=len(self.blocked),intercepted_owner_path_calls=self.path_calls,
            delegated_owner_non_path_calls=self.non_path_calls,calls_by_API=dict(self.calls_by_API),
            denied_live_raw_access_attempts=self.raw_attempts,active_scope=self.installed,
            all_original_open_function_identities_restored=self.restored,
            covered_python_open_APIs=list(self.calls_by_API),nonowner_sampler_started=False,
            additional_IO_sampler_thread_or_process=False,path_values_or_content_logged=False,
            unwrapped_OS_APIs_or_external_process_access_guarded=False,
            worker_entry_and_live_parent_connection_qualified=False,GO_authorized=False)
