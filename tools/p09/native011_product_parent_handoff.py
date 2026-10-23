"""Lazy worker202 transfer in the actual original Window10/Job/Frame chain.

Installation is inert. The unchanged strict-window body keeps its code and
closure; only its private component's connect dependency is selected. Actual
source handles are borrowed only at the original Popen, after the first full
Native byte boundary. No authorization, Job, Frame or process is manufactured.
"""
import ast
import hashlib
import sys
from pathlib import Path
from types import CodeType, FunctionType, SimpleNamespace as NS

SELF='tools/p09/native011_product_parent_handoff.py'
TEST='tools/p09/tests/test_native011_product_parent_handoff.py'
STRICT=dict(path='tools/p09/strict_product_window_connection_v1.py',bytes=5489,
    sha256='f5d6e5c1792464a3699272c62e6175a3607d15f213c6e3444fb2f4a0fe24510c')
ENTRY='tools/p09/native011_product_worker_entry.py'
TASK='case165-current-r011-tests'
OUTPUT='implementation/p09/evidence/p09-361-native011-current805-product-parent-handoff-construct002.v1.json'
CONTROLS=(SELF,TEST,'tools/p09/native009_parent_launch_v1.py',
    'tools/p09/native009_worker_launch_v1.py','tools/p09/worker_readiness_connection_v1.py')


def require(ok,code):
    if not ok:raise ValueError('PRODUCT_PARENT_HANDOFF_'+code)


def closure(fn):
    require(type(fn) is FunctionType,'ORIGINAL_FUNCTION')
    return dict(zip(fn.__code__.co_freevars,(cell.cell_contents for cell in fn.__closure__ or ())))


def strict_body(raw,fn,component):
    """Whole original execute code, not a name-only or partial AST match."""
    require(type(raw) is bytes and len(raw)==STRICT['bytes']
        and hashlib.sha256(raw).hexdigest()==STRICT['sha256'],'EXACT_STRICT_CONNECTION_SOURCE')
    require(type(fn) is FunctionType and fn.__code__.co_filename.replace('\\','/').endswith(STRICT['path']),
        'ACTUAL_ORIGINAL_STRICT_ENGINE')
    def matches(code):
        found=[]
        for value in code.co_consts:
            if type(value) is CodeType:
                if value.co_name=='execute':found.append(value)
                found.extend(matches(value))
        return found
    source=compile(raw,fn.__code__.co_filename,'exec')
    expected=matches(source)
    if not (len(expected)==1 and expected[0]==fn.__code__):
        tree=ast.parse(raw)
        nodes=[n for n in tree.body if isinstance(n,(ast.Assign,ast.FunctionDef,ast.ClassDef))]
        expected=matches(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),
            fn.__code__.co_filename,'exec'))
    require(len(expected)==1 and expected[0]==fn.__code__,'WHOLE_ORIGINAL_STRICT_EXECUTE_CODE')
    cells=closure(fn)
    require(cells.get('component') is component and cells.get('env') is fn.__globals__
        and type(cells.get('calls')) is list and cells['calls']==[],'EXACT_UNUSED_STRICT_COMPONENT_CLOSURE')
    return cells


class LazyHandoff:
    """No Frame lookup at construction: the original engine creates it later."""
    def __init__(self,context,connection,root,entry_pin,required,api,coverage):
        self.context=context;self.connection=connection;self.root=root;self.entry_pin=dict(entry_pin)
        self.required={name:dict(pin) for name,pin in required.items()};self.api=api;self.coverage=coverage
        self.actual=None;self.attempts=0;self.failed=False
    def spawn(self,factory,command,**options):
        require(self.attempts==0 and self.actual is None and not self.failed,'ONE_LAZY_HANDOFF_NO_RETRY')
        self.attempts+=1
        try:
            self.context.checkpoint()
            frame=self.context.parent.frames[0]
            require(type(frame) is self.connection.frame_type,'SAME_ACTUAL_PARENT_FRAME_TYPE')
            self.actual=self.api.transfer.Handoff(self.root,self.entry_pin,frame,self.required,
                self.coverage,self.api.inheritance,self.api.bridge,self.api.protocol,self.context.checkpoint,
                frame_type=self.connection.frame_type)
            return self.actual.spawn(factory,command,**options)
        except BaseException:self.failed=True;raise
    def live(self):
        require(self.actual is not None and not self.failed,'ACTUAL_HANDOFF_REQUIRED');return self.actual
    def bind_gate(self,gate):return self.live().bind_gate(gate)
    def gate_checkpoint(self):return self.live().gate_checkpoint()
    def verify_owned(self,process,verify):return self.live().verify_owned(process,verify)
    def cleanup_handles(self):
        if self.actual is None:return True
        ok=self.actual.cleanup_handles()
        if not ok:self.failed=True
        return ok
    def summary(self):
        return dict(lazy_spawn_attempts=self.attempts,actual_source_handoff_constructed=self.actual is not None,
            failed=self.failed,handoff=None if self.actual is None else self.actual.summary())


def install(root,c,linked,actual,owner,required,entry_pin,api,coverage,strict_raw,*,authorize=None):
    """Install in one unopened private parent. A caller must supply GO authority.

    authorize=None is a permanent deny for this installed instance. Construction
    probes use that form; passing the model tests never grants Native permission.
    """
    connection=owner.parent_connection;component=linked.window.WINDOW
    require(type(component) is NS and component.SECONDS==10 and api.protocol.SECONDS==15
        and component.GO==api.protocol.GO,'PRIVATE_WINDOW10_AND_ORIGINAL_GATE15')
    require(connection.parent is actual and connection.state.attempts==0 and connection.state.frames==[]
        and len(connection.frame_type.__mro__)==5 and owner.phase=='NEW'
        and owner.shared.metadata is owner.shared.frame is None and not owner.shared.restored
        and owner.metadata_connection.original_run is linked.engine.run_owned
        and owner.metadata_connection.readers==owner.metadata_connection.budgets==[]
        and linked.state.attempts==linked.state.calls==0 and actual.worker is linked.original_worker,
        'ONE_UNUSED_ACTUAL_SHARED_PARENT_NOT_RECONSTRUCTED')
    require(type(required) is dict and len(required)==202 and required.get(ENTRY)==entry_pin
        and entry_pin.get('path')==ENTRY,'EXACT_QUALIFIED202_WORKER_ENTRY')
    require(authorize is None or callable(authorize),'EXPLICIT_EXTERNAL_AUTHORIZATION_DEPENDENCY')
    original_run=actual.run_owned;original_connect=component.connect
    strict_body(strict_raw,linked.engine.run_owned,component)
    strict_code=linked.engine.run_owned.__code__;strict_closure=linked.engine.run_owned.__closure__
    require(type(original_run) is FunctionType and type(original_connect) is FunctionType,
        'ORIGINAL_PARENT_AND_COMPONENT_FUNCTIONS')
    require(original_connect.__code__.co_name=='connect'
        and original_connect.__code__.co_filename.replace('\\','/').endswith('tools/p09/strict_product_window_v1.py'),
        'ONE_ORIGINAL_WINDOW_CONNECT_NOT_AN_EXISTING_SELECTOR')
    # family() preserves every original function code/default/closure. source()
    # still freshly verifies the actual declared entry at the original launch.
    launch=api.family(api.launch,dict(ENTRY=ENTRY,TASK=TASK))
    context=api.parent.Context(c,launch);context.bind_parent(connection.state)
    original_component=NS(**vars(component))
    lazy=LazyHandoff(context,connection,root,entry_pin,required,api,coverage)
    state=NS(attempts=0,failed=False,cleanup_confirmed=None,component_connections=0)
    def connect(factory,capture_type):
        require(context.active and not context.bindings and state.component_connections==0,
            'ONE_COMPONENT_CONNECTION_IN_ORIGINAL_OWNER_SCOPE')
        state.component_connections+=1
        binding=api.transfer.connect(lazy,launch,root,entry_pin,original_component,api.protocol,api.readiness,
            factory,capture_type,c.subprocess,context.owned,context.checkpoint)
        context.bindings.append(binding);return binding
    check=require
    def execute(run):
        check(type(run) is int and run==1 and state.attempts==0 and not state.failed,'ONE_LOGICAL_RUN1_NO_RETRY')
        # Denial happens before mutation, original Job creation or any IO.
        check(authorize is not None and authorize() is True,'EXTERNAL_NATIVE_GO_AUTHORITY_REQUIRED')
        state.attempts+=1
        try:
            with context.owner_scope():result=original_run(run)
        except BaseException:state.failed=True;raise
        finally:
            try:state.cleanup_confirmed=lazy.cleanup_handles()
            except BaseException:state.cleanup_confirmed=False
            if not state.cleanup_confirmed:state.failed=True
        check(state.cleanup_confirmed,'SOURCE_HANDLE_CLEANUP_UNCONFIRMED')
        return result
    wrapped=FunctionType(execute.__code__,original_run.__globals__,name=execute.__name__,
        argdefs=execute.__defaults__,closure=execute.__closure__)
    wrapped.__kwdefaults__=execute.__kwdefaults__
    component.connect=connect
    actual.run_owned=wrapped
    try:
        require(closure(linked.engine.run_owned)['component'] is component
            and linked.engine.run_owned.__code__ is strict_code and linked.engine.run_owned.__closure__ is strict_closure
            and owner.metadata_connection.original_run is linked.engine.run_owned,
            'SAME_ACTUAL_COMPONENT_AND_METADATA_CHAIN_AFTER_INSTALL')
    except BaseException:
        component.connect=original_connect;actual.run_owned=original_run;raise
    def evidence():
        return dict(actual_private_parent_launch_dependency_installed=True,
            original_strict_engine_code_and_closure_retained=True,
            original_metadata_reader_and_shared_Frame_chain_retained=True,
            worker_source_handles_created_only_at_original_Popen=True,
            original_owner=context.evidence(),handoff=lazy.summary(),execution_attempts=state.attempts,
            component_connections=state.component_connections,cleanup_confirmed=state.cleanup_confirmed,
            authorization_dependency_present=authorize is not None,GO_authorized=False,
            actual_Native_Frame_or_worker_or_product_qualified=False,accepted_count_delta=0)
    return NS(context=context,handoff=lazy,state=state,evidence=evidence,original_run=original_run,
        original_component=original_component)


def driver_type(base):
    """Same real common constructor with an explicitly denied product route."""
    class Driver(base):
        def __init__(self):super().__init__();self.output=OUTPUT;self.handoff_declaration=None;self.parent_handoff=None
        def bind(self,root,a,c,guards,loader,control):
            super().bind(root,a,c,guards,loader,control);before=control.admit
            def declared(q,a,scope,**options):
                require(self.handoff_declaration is None,'ONE_PARENT_HANDOFF_DECLARATION')
                value=before(q,a,scope,**options)
                require(len(value.control_names)==59 and not set(CONTROLS)&set(value.control_names),
                    'EXACT64_NAMED_CONTROLS_NOT_OBSERVED_SOURCE_UNION')
                self.handoff_declaration=value
                return NS(**{**vars(value),'control_names':value.control_names+CONTROLS})
            control.admit=declared
        def run(self,root,q,a,loader,entry,batch,data,prepared,bound,resources,checked,row,private_load,publisher):
            value=super().run(root,q,a,loader,entry,batch,data,prepared,bound,resources,checked,row,private_load,publisher)
            require(self.construct_only and self.parent_handoff is None and self.handoff_declaration is not None,
                'CONSTRUCTION_ONLY_WITHOUT_EXECUTION_AUTHORITY')
            names=('native009_parent_launch_v1','native009_worker_launch_v1','batch_worker_launch',
                'native011_product_source_handoff','native011_worker_source_inheritance',
                'native011_inherited_source_probe_child','worker_readiness_v1','worker_readiness_connection_v1',
                'native011_source_coverage')
            # The original q has already closed exactly once. A second finish
            # would duplicate its counters and whole history IO. This new,
            # same-guard reader witnesses only the connection's explicit inputs;
            # none of its reads count as Native byte-boundary credit.
            connection_reader=a.AcceptanceReader(root,q.checkpoint)
            for name in (SELF,TEST):connection_reader.pin(name)
            libraries,_=private_load(loader,root,connection_reader,a,names,
                {'runtime_input_frame':a.native.frames,'current_stored_runtime_scope':batch.scope})
            api=NS(parent=libraries.native009_parent_launch_v1,launch=libraries.native009_worker_launch_v1,
                family=libraries.batch_worker_launch.family,transfer=libraries.native011_product_source_handoff,
                inheritance=libraries.native011_worker_source_inheritance,bridge=libraries.native011_inherited_source_probe_child,
                protocol=libraries.worker_readiness_v1,readiness=libraries.worker_readiness_connection_v1)
            coverage=libraries.native011_source_coverage
            require(coverage.verify.__globals__['frames'] is a.native.frames,
                'ACTUAL_COVERAGE_USES_SAME_ORIGINAL_NATIVE_FRAME_BASE')
            a.exact(connection_reader.pin(STRICT['path']),STRICT,'EXACT_ORIGINAL_STRICT_ENGINE_CONNECTION')
            pin,raw=connection_reader._read(STRICT['path'],parse=True)
            connection_reader._bind(pin['path'],pin);a.exact(pin,STRICT,'FRESH_STRICT_CONNECTION')
            owner=data.planned.batch;actual=owner.parent_connection.parent;required=self.handoff_declaration.required
            require(prepared.linked.engine.run_owned.__globals__['c'] is self.c,'SAME_ORIGINAL_WINDOWS_AND_SUBPROCESS_OWNER')
            self.parent_handoff=install(root,self.c,prepared.linked,actual,owner,required,required[ENTRY],api,coverage,bytes(raw))
            proof=self.parent_handoff.evidence()
            require(proof['execution_attempts']==proof['component_connections']==0
                and proof['original_owner']['observed_original_Jobs']==0
                and proof['handoff']['actual_source_handoff_constructed'] is False
                and proof['authorization_dependency_present'] is False,'INERT_ACTUAL_CHAIN_NOT_EXECUTED')
            require(set(connection_reader.snapshots)=={SELF,TEST,STRICT['path'],*('tools/p09/'+name+'.py' for name in names)},
                'EXACT12_NAMED_CONNECTION_INPUTS_NO_UNDECLARED_READS')
            for name,pin in connection_reader.snapshots.items():
                a.exact(dict(data.planned.current[name]),pin,'EVERY_CONNECTION_SOURCE_DIRECT_CURRENT_NATIVE_INPUT')
            connection_reader.finish();connection_reader.checkpoint()
            require(connection_reader.final_fresh_hashes==len(connection_reader.snapshots)==12,
                'ALL12_CONNECTION_INPUTS_FRESH_AND_CLOSING_ONCE')
            proof.update(connection_fresh_inputs=len(connection_reader.snapshots),
                connection_final_fresh_hashes=connection_reader.final_fresh_hashes,
                connection_source_pins=list(connection_reader.snapshots.values()),
                original_closed_reader_reused_or_reset=False)
            return dict(value,state='PASS_ACTUAL_PARENT_WORKER202_LAUNCH_DEPENDENCY_CONSTRUCTION_NOT_NATIVE',
                actual_product_launch_handoff_installed=True,actual_parent_handoff_connection=proof,
                actual_worker202_GO_or_Native_qualified=False)
    return Driver


def main():
    require(sys.argv[1:]==[],'CLOSED_CONSTRUCTION_ONLY_NO_GO_ENTRY');sys.dont_write_bytecode=True
    root=Path(__file__).resolve().parents[2]
    require(not(root/OUTPUT).exists(),'EXCLUSIVE_NEW_HANDOFF_CONSTRUCTION')
    def fresh(name,limit):
        path=root/name
        for member in (path,*path.parents):
            require(not member.is_symlink() and not member.is_junction(),'DIRECT_BOOTSTRAP')
            if member==root:break
        with path.open('rb') as stream:raw=stream.read(limit+1)
        require(0<len(raw)<=limit,'BOUNDED_FRESH_BOOTSTRAP');return raw
    loader_pin=dict(path='tools/p09/runtime_envelope_namespace_bundle_v1.py',bytes=3320,
        sha256='385778d26e0c5d99ac6d38ccaeb6afd24bb4029e01b4a6e91683cb80e5e2da62')
    raw=fresh(loader_pin['path'],loader_pin['bytes'])
    require(len(raw)==loader_pin['bytes'] and hashlib.sha256(raw).hexdigest()==loader_pin['sha256'],'EXACT_ORIGINAL_LOADER')
    env=dict(__name__='p09_product_parent_handoff_bootstrap',__file__=loader_pin['path'])
    exec(compile(raw,loader_pin['path'],'exec'),env)
    names=('native011_product_parent_construction','native011_product_worker_scope','native011_engine_owned_metadata_validation',
        'native011_engine_owned_metadata_entry','native011_readonly_frame_driver','native011_ready_native_construction')
    pins=[]
    for name in names:
        path='tools/p09/'+name+'.py';raw=fresh(path,65536)
        pins.append(dict(path=path,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
    libs,_=NS(**env).load(root,pins,{})
    adapter=libs.native011_engine_owned_metadata_validation;common=libs.native011_ready_native_construction
    raw=fresh(adapter.SOURCE['path'],adapter.SOURCE['bytes']);validator,projection=adapter.project(raw,common.validate)
    execute,entry_projection=adapter.bind_entry(raw,common.main,validator)
    owned=libs.native011_engine_owned_metadata_entry.driver_type(libs.native011_readonly_frame_driver.Driver,
        dict(validator=projection,entry=entry_projection))
    worker202=libs.native011_product_parent_construction.driver_type(owned,libs.native011_product_worker_scope)
    return execute(driver=driver_type(worker202)())


if __name__=='__main__':raise SystemExit(main())
