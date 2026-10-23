"""One explicit diagnostic receipt prefix, never a canonical Native result.

Reuse the original recursive receipt-metadata inverse. Only the unique
closure path to that literal is rebuilt; every other closure cell survives.
The private original strict-window connector receives the projected engine
before the parent/Frame composition retains its actual original reference.
"""
from types import CellType,CodeType,FunctionType,SimpleNamespace as NS

SELF='tools/p09/batch_pre_go_receipt.py'
TEST='tools/p09/tests/test_batch_pre_go_receipt.py'
ORIGINAL='implementation/p09/evidence/p09-361-case165-current-runtime-run'
DIAGNOSTIC='implementation/p09/evidence/p09-361-case165-pre-go-runtime-diagnostic001-run'
RECEIPT=DIAGNOSTIC+'010.v1.json'


def require(ok,code):
    if not ok:raise ValueError('BATCH_PRE_GO_RECEIPT_'+code)


def literals(code,value):
    count=0
    for item in code.co_consts:
        if type(item) is str:count+=item==value
        elif type(item) is CodeType:count+=literals(item,value)
        elif type(item) is tuple:count+=sum(type(v) is str and v==value for v in item)
    return count


def project_engine(engine,metadata):
    """No invocation, arbitrary source rewrite, globals edit or counter edit."""
    original=engine.run_owned
    require(type(original) is FunctionType and callable(metadata),'ORIGINAL_ENGINE_AND_METADATA_PROJECTOR')
    nodes=[];found=[];active=set();visited=set()
    def visit(fn,path):
        require(len(path)<=12 and len(nodes)<64,'BOUNDED_ORIGINAL_FUNCTION_CLOSURE_GRAPH')
        require(id(fn) not in active and id(fn) not in visited,'NO_CYCLIC_OR_SHARED_FUNCTION_CLOSURE_PATH')
        active.add(id(fn));visited.add(id(fn));nodes.append(fn)
        old=literals(fn.__code__,ORIGINAL);new=literals(fn.__code__,DIAGNOSTIC)
        require(new==0,'NO_EXISTING_DIAGNOSTIC_LITERAL')
        require(old<=1,'ONE_RECEIPT_LITERAL_PER_FUNCTION')
        if old:found.append((fn,path))
        for index,cell in enumerate(fn.__closure__ or ()):
            value=cell.cell_contents
            if type(value) is FunctionType:visit(value,(*path,(fn,index)))
        active.remove(id(fn))
    visit(original,())
    require(len(found)==1,'ONE_EXACT_ORIGINAL_RECEIPT_IN_ENGINE_CLOSURES')
    leaf,path=found[0]
    revised=metadata(leaf,{ORIGINAL:DIAGNOSTIC})
    require(type(revised) is FunctionType and revised.__globals__ is leaf.__globals__
        and revised.__defaults__ is leaf.__defaults__ and revised.__closure__ is leaf.__closure__
        and revised.__kwdefaults__ is leaf.__kwdefaults__,'ORIGINAL_METADATA_PROJECTOR_DEPENDENCIES')
    require(literals(revised.__code__,ORIGINAL)==0 and literals(revised.__code__,DIAGNOSTIC)==1,
        'EXACT_ONE_CHANGED_RECEIPT_LITERAL')
    undo=metadata(revised,{DIAGNOSTIC:ORIGINAL})
    require(undo.__code__==leaf.__code__,'ENTIRE_ORIGINAL_ENGINE_CODE_INVERSE')
    steps=[]
    for parent,index in reversed(path):
        old=parent.__closure__;closure=tuple(CellType(revised) if i==index else c for i,c in enumerate(old))
        changed=FunctionType(parent.__code__,parent.__globals__,name=parent.__name__,
            argdefs=parent.__defaults__,closure=closure)
        changed.__kwdefaults__=parent.__kwdefaults__
        require(changed.__code__ is parent.__code__ and changed.__globals__ is parent.__globals__
            and changed.__defaults__ is parent.__defaults__ and changed.__kwdefaults__ is parent.__kwdefaults__
            and all(i==index or a is b for i,a,b in zip(range(len(old)),old,changed.__closure__)),
            'ENTIRE_ENCLOSING_CODE_AND_ALL_OTHER_CELLS')
        steps.append(dict(function=parent.__name__,file=parent.__code__.co_filename.replace('\\','/').rsplit('/',1)[-1],
            closure_dependency=parent.__code__.co_freevars[index],entire_code_defaults_globals_unchanged=True))
        revised=changed
    proof=dict(original_prefix=ORIGINAL,diagnostic_prefix=DIAGNOSTIC,diagnostic_receipt=RECEIPT,
        exact_original_literal_count=1,original_closure_functions_inspected=len(nodes),
        leaf_function=leaf.__name__,leaf_file=leaf.__code__.co_filename.replace('\\','/').rsplit('/',1)[-1],
        reconstructed_closure_path=steps,complete_code_inverse=True,
        original_worker_retained=True,canonical_Native_receipt_or_intent_authorized=False,
        original_execution_counters_changed=False,GO_authorized=False)
    return NS(**{**vars(engine),'run_owned':revised}),proof


def recovery_api(recovery,state):
    original_current=recovery.current_window
    def current_window(*args,**kwargs):
        require(not state.windows,'ONE_ORIGINAL_CURRENT_WINDOW')
        window,proof=original_current(*args,**kwargs);state.windows+=1
        original_link=window.WINDOW_LINK
        def connect_engine(engine,component):
            require(not state.links,'ONE_ORIGINAL_STRICT_CONNECTOR')
            projected,record=project_engine(engine,recovery.receipt_namespace)
            state.links+=1;state.projection=record
            return original_link.connect_engine(projected,component)
        link=NS(**{**vars(original_link),'connect_engine':connect_engine})
        template=recovery.clone(window.template,WINDOW_LINK=link)
        require(template.__code__ is window.template.__code__ and template.__defaults__ is window.template.__defaults__
            and template.__closure__ is window.template.__closure__,'ORIGINAL_TEMPLATE_WITH_EXPLICIT_LINK_DEPENDENCY')
        return NS(**{**vars(window),'WINDOW_LINK':link,'template':template}),dict(proof,
            diagnostic_receipt_dependency_connected=True,actual_Native_or_product_qualified=False)
    return NS(**{**vars(recovery),'current_window':current_window})


def parent_api(parent):
    """One declared loader dependency; keep the sealed construction body."""
    state=NS(loads=0,windows=0,links=0,projection=None)
    original_package=parent.connect_package
    def connect_package(*args,**kwargs):
        connected=original_package(*args,**kwargs);original_loader=connected.loader
        def load(root,pins,reuse):
            modules,proof=original_loader.load(root,pins,reuse)
            if hasattr(modules,'native009_parent_launch_v1'):
                require(state.loads==0,'ONE_DECLARED_PARENT_LAUNCH_NAMESPACE')
                state.loads+=1;original=modules.native009_parent_launch_v1
                def connect(recovery,*args,**kwargs):
                    return original.recovery_api(recovery_api(recovery,state),*args,**kwargs)
                selected=NS(**{**vars(original),'recovery_api':connect})
                modules=NS(**{**vars(modules),'native009_parent_launch_v1':selected})
            return modules,proof
        return NS(**{**vars(connected),'loader':NS(**{**vars(original_loader),'load':load})})
    return NS(**{**vars(parent),'connect_package':connect_package}),state
