"""Inspect one UNUSED real allocator result in the unopened prepared parent.

No metadata callback, reader byte IO, decoder, Frame, whole opening, worker or
GO. Never reinitializes an allocator result or changes its class/pacer/fields.
"""
import hashlib
import sys
from pathlib import Path
from types import SimpleNamespace as NS

SELF='tools/p09/native011_metadata_reader_inspection.py'
TEST='tools/p09/tests/test_native011_metadata_reader_inspection.py'
OUTPUT='implementation/p09/evidence/p09-361-native011-current805-metadata-reader-inspection001.v1.json'
ENGINE_OUTPUT='implementation/p09/evidence/p09-361-native011-current805-engine-metadata-assignment003.v1.json'
LOADER=dict(path='tools/p09/runtime_envelope_namespace_bundle_v1.py',bytes=3320,
    sha256='385778d26e0c5d99ac6d38ccaeb6afd24bb4029e01b4a6e91683cb80e5e2da62')


def require(ok,code):
    if not ok:raise ValueError('METADATA_READER_INSPECTION_'+code)


def inspect_unused(owner,linked,root,checkpoint):
    connection=owner.metadata_connection
    require(owner.phase=='NEW' and owner.shared.metadata is owner.shared.frame is None
        and not owner.shared.restored and connection.readers==connection.budgets==[]
        and linked.state.attempts==linked.state.calls==0,'UNUSED_REAL_PARENT_AND_METADATA_CONNECTION')
    reader=connection.original_reader(root,checkpoint)
    require(reader.read_passes==reader.bytes_read==reader.final_fresh_hashes==0 and not reader.snapshots,
        'ALLOCATOR_MUST_RETURN_UNREAD_OBJECT')
    pacer=reader.pacer;opened=reader.open_pacer
    require(pacer.bytes_paced==pacer.requested_sleep_seconds==0 and pacer.tokens==65536
        and opened.requests==opened.wait_seconds==0,'NO_QUERY_OR_BYTE_RESERVATION')
    fields=dict(vars(reader));saved=dict(vars(pacer));query_saved=dict(vars(opened))
    probe=type(pacer)(clock=pacer.clock,sleeper=pacer.sleeper);rates={}
    for name in ('inspection.exe','inspection.json'):
        probe.select(name);rates[probe.kind]=probe.rate
    chain=[]
    require(len(type(reader).__mro__)<=24,'BOUNDED_ACTUAL_MRO')
    for cls in type(reader).__mro__:
        methods={}
        for name in ('__init__','_read','_source'):
            method=vars(cls).get(name);code=getattr(method,'__code__',None)
            if code is not None:methods[name]=dict(file=code.co_filename.replace('\\','/').rsplit('/',1)[-1],
                function=code.co_qualname)
        chain.append(dict(name=cls.__name__,module=cls.__module__,own_methods=methods))
    require(vars(pacer)==saved and vars(opened)==query_saved and set(vars(reader))==set(fields)
        and all(vars(reader)[key] is value for key,value in fields.items()),'ALLOCATOR_RESULT_NEVER_MUTATED')
    require(owner.shared.metadata is owner.shared.frame is None and connection.readers==connection.budgets==[]
        and linked.state.attempts==linked.state.calls==0,'NO_METADATA_BUDGET_CALLBACK_OR_WORKER_ADOPTION')
    return dict(allocator_is_class=type(connection.original_reader) is type,
        actual_MRO=chain,actual_pacer_type=type(pacer).__name__,actual_pacer_module=type(pacer).__module__,
        actual_pacer_clock=pacer.clock.__name__,actual_pacer_sleeper=pacer.sleeper.__name__,
        original_query_type=type(opened).__name__,original_query_module=type(opened).__module__,
        original_query_clock=opened.clock.__name__,original_query_sleeper=opened.sleep.__name__,
        independently_allocated_pacer_selected_rates=rates,
        actual_reader_read_passes=0,actual_reader_fresh_inputs=0,actual_query_reservations=0,
        actual_allocator_result_fields_class_pacer_or_clocks_changed=False,
        actual_metadata_callback_or_budget_or_Frame_or_worker_created=False,
        allocator_called_once=True,GO_authorized=False)


def inspect_engine_assignment(linked):
    import dis
    from types import CodeType,FunctionType,ModuleType,SimpleNamespace
    run=linked.engine.run_owned
    require(type(run) is FunctionType and linked.state.attempts==linked.state.calls==0,'UNEXECUTED_REAL_ENGINE')
    found=[];visited=set();functions=set();chain=[]
    def visit(code,depth,owner):
        if id(code) in visited:return
        require(depth<=32 and len(visited)<1024,'BOUNDED_FUNCTION_CODE_GRAPH')
        visited.add(id(code))
        if code.co_name=='input_pins':found.append((code,owner))
        for value in code.co_consts:
            if type(value) is CodeType:visit(value,depth+1,owner)
    def function(fn,depth):
        if id(fn) in functions:return
        require(depth<=32 and len(functions)<64,'BOUNDED_EXISTING_FUNCTION_LINKS')
        functions.add(id(fn));chain.append(dict(name=fn.__name__,file=fn.__code__.co_filename.replace('\\','/').rsplit('/',1)[-1]))
        visit(fn.__code__,0,fn)
        values=[]
        if fn.__closure__ is not None:
            for cell in fn.__closure__:
                try:values.append(cell.cell_contents)
                except ValueError:pass
        for name in fn.__code__.co_names:
            value=fn.__globals__.get(name)
            if type(value) is FunctionType and value.__name__ in ('run_owned','execute','input_pins','pins'):
                values.append(value)
            elif type(value) in (ModuleType,SimpleNamespace):
                values.extend(vars(value).get(key) for key in ('run_owned','original','original_run'))
        for value in values:
            if type(value) is FunctionType:function(value,depth+1)
            elif type(value) is SimpleNamespace:
                for key in ('original','original_run','run_owned'):
                    item=vars(value).get(key)
                    if type(item) is FunctionType:function(item,depth+1)
    function(run,0)
    require(len(found)<=1,'UNAMBIGUOUS_EXISTING_METADATA_INPUT_FUNCTION')
    instructions=[] if not found else list(dis.get_instructions(found[0][0]))
    require(len(instructions)<=20000,'BOUNDED_METADATA_INSTRUCTIONS')
    stores=[];owned=[]
    for index,instruction in enumerate(instructions):
        if instruction.opname=='STORE_ATTR' and instruction.argval=='pacer':
            window=instructions[max(0,index-10):index+1]
            values=[item.argval for item in window]
            owned_assignment='byte_policy' in values and 'OwnedPacer' in values and 'q' in values
            stores.append(dict(instruction_index=index,assigns_original_owned_pacer=owned_assignment))
            if owned_assignment:owned.append(index)
    policy=(found[0][1] if found else run).__globals__['byte_policy'];pacer=policy.OwnedPacer();rates={}
    for name in ('inspection.exe','inspection.json'):
        pacer.select(name);rates[pacer.kind]=pacer.rate
    require(linked.state.attempts==linked.state.calls==0,'NO_ENGINE_WORKER_OR_PRODUCT_EXECUTION')
    return dict(metadata_input_function_count=len(found),metadata_function_recognized=bool(found),
        existing_function_links=chain,visited_code_objects=len(visited),metadata_pacer_store_count=len(stores),
        original_owned_pacer_assignment_count=len(owned),pacer_stores=stores,
        original_owned_selected_rates=rates,original_owned_clock=pacer.clock.__name__,
        actual_metadata_input_body_executed=False,actual_reader_allocated=False,actual_worker_or_product_executed=False,
        readonly_factory_default_policy_not_assumed_to_be_product_policy=True,
        unrecognized_function_not_qualified_as_absent_assignment=not bool(found),GO_authorized=False)


def driver_type(base,*,inspect_engine=False):
    require(type(inspect_engine) is bool,'EXPLICIT_INSPECTION_MODE')
    class Driver(base):
        def __init__(self):
            super().__init__(7,construct_only=True);self.output=ENGINE_OUTPUT if inspect_engine else OUTPUT
        def bind(self,root,a,c,guards,loader,control):
            super().bind(root,a,c,guards,loader,control)
            previous=control.admit;state=NS(calls=0)
            def declared(q,a,scope,**options):
                require(state.calls==0 and options==dict(exact_read=True,decoder_timing=True,chunk_join=True),
                    'ONE_ORIGINAL_EXPLICIT_DECLARATION')
                value=previous(q,a,scope,**options);state.calls+=1
                require(len(value.control_names)==35 and not {SELF,TEST}&set(value.control_names),
                    'TWO_NAMED_SOURCE_ROLES_NOT_OBSERVED_NATIVE_UNION')
                return NS(**{**vars(value),'control_names':value.control_names+(SELF,TEST)})
            control.admit=declared
        def run(self,root,q,a,loader,entry,batch,data,prepared,bound,resources,checked,row,private_load,publisher):
            value=super().run(root,q,a,loader,entry,batch,data,prepared,bound,resources,checked,row,private_load,publisher)
            require(self.construct_only and self.stage=='construction' and self.native is None
                and value['actual_Native_Frame_created'] is False,'NO_WHOLE_OPENING_OR_NATIVE_ENTRY')
            if inspect_engine:
                return dict(value,state='PASS_REAL_ENGINE_METADATA_ASSIGNMENT_INSPECTION_NOT_EXECUTION',
                    engine_metadata_assignment=inspect_engine_assignment(prepared.linked))
            return dict(value,state='PASS_UNUSED_REAL_METADATA_ALLOCATOR_INSPECTION_NOT_CALLBACK_OR_NATIVE',
                unused_metadata_allocator=inspect_unused(data.planned.batch,prepared.linked,root,self.check))
    return Driver


def main():
    require(sys.argv[1:] in ([],['--engine-assignment']),'CLOSED_NO_PRODUCT_ENTRY')
    inspect_engine=bool(sys.argv[1:])
    root=Path(__file__).resolve().parents[2];sys.dont_write_bytecode=True
    require(not(root/(ENGINE_OUTPUT if inspect_engine else OUTPUT)).exists(),'EXCLUSIVE_INSPECTION_OUTPUT')
    def fresh(name,limit):
        path=root/name
        for member in (path,*path.parents):
            require(not member.is_symlink() and not member.is_junction(),'DIRECT_BOOTSTRAP_SOURCE')
            if member==root:break
        with path.open('rb') as stream:raw=stream.read(limit+1)
        require(0<len(raw)<=limit,'BOUNDED_BOOTSTRAP_SOURCE');return raw
    raw=fresh(LOADER['path'],LOADER['bytes'])
    require(len(raw)==LOADER['bytes'] and hashlib.sha256(raw).hexdigest()==LOADER['sha256'],'EXACT_LOADER')
    env=dict(__name__='p09_metadata_allocator_bootstrap',__file__=LOADER['path'])
    exec(compile(raw,LOADER['path'],'exec'),env)
    pins=[]
    for name in ('tools/p09/native011_readonly_frame_driver.py','tools/p09/native011_ready_native_construction.py'):
        raw=fresh(name,65536);pins.append(dict(path=name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
    libs,_=NS(**env).load(root,pins,{})
    before=sys.argv;sys.argv=[before[0]]
    try:return libs.native011_ready_native_construction.main(driver=driver_type(
        libs.native011_readonly_frame_driver.Driver,inspect_engine=inspect_engine)())
    finally:sys.argv=before


if __name__=='__main__':raise SystemExit(main())
