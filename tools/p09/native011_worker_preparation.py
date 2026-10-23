"""Prepare a real run011 engine from published data, without a product launch.

The unchanged complete builder retains the product10 literal. Only the
builder's run/identity data are projected, with a whole recursive inverse.
Callers own the serial guard, closing source hashes, Job and EOF/GO boundary.
"""
import ast
import hashlib
import importlib
import os
from pathlib import Path
import sys
from types import FunctionType, SimpleNamespace as NS
import native011_preparation as preparation
import native011_worker_transport as transport
import native011_zlib_binding as zlib

SELF = 'tools/p09/native011_worker_preparation.py'
CANONICAL = transport.PREFIX+'current-runtime-run011.v1.json'
PACKAGE = (
    dict(path=zlib.MANIFEST,bytes=99480,sha256='d08ab299f5af47054a820dfcb47c62ca669df7fb1dda291c973b0aacd40524c3'),
    dict(path=zlib.WIRE,bytes=15058,sha256='a4056d0770b7cc87a469438408e3aaa00e9cd644592e41db3e1e0001b2537f3f'),
    dict(path=zlib.BOOTSTRAP,bytes=4898,sha256='1a1a9d6c15e91fc861baf65389f5f0f85f99a23a810954eb360cd1b3fbab02d9'))
PROFILE = dict(path=transport.PREFIX+'native009-verified-source-profile002.v1.json',bytes=110395,
    sha256='1ca00eeb366959d7e957b96e986f21651c17c2837a77d2a6707a43cd0d2934c4')
STEP = dict(path=transport.PREFIX+'step-config001.v1.json',bytes=685,
    sha256='2b549a20ad4f46b7d146b935b0ff103e92db0411ad195f6038457e994b973e7c')


def literal_code_pins(tree,scope):
    """Extract only closed literal pins; never execute code or infer a hash."""
    rows=[]
    for node in ast.walk(tree):
        values=None
        if isinstance(node,ast.Dict) and len(node.keys)==3 and all(isinstance(k,ast.Constant)
            and type(k.value) is str for k in node.keys):
            values=dict(zip((k.value for k in node.keys),node.values))
        elif (isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='dict'
            and not node.args and len(node.keywords)==3):
            values={kw.arg:kw.value for kw in node.keywords}
        if values is None or set(values)!={'path','bytes','sha256'}:continue
        try:row={key:ast.literal_eval(value) for key,value in values.items()}
        except (ValueError,TypeError):continue
        if (type(row['path']) is str and row['path'].endswith('.py')
            and row['path'].startswith(('tools/p09/','implementation/p09/evidence/'))):
            scope.pins([row]);rows.append(row)
    return rows


def engine_builder(raw,expected,runtime,engine_raw,runtime_raw):
    """Select complete original builder definitions, not rewritten AST bodies."""
    require = transport.require
    require(type(raw) is bytes and len(raw)==expected['bytes']
        and hashlib.sha256(raw).hexdigest()==expected['sha256'],'WORKER_EXACT_BUILDER_POLICY_SOURCE')
    tree=ast.parse(raw)
    wanted={'require','_constant_shape','_code_shape','prepare_engine_builder'}
    nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in wanted]
    require(len(nodes)==4 and {n.name for n in nodes}==wanted,'WORKER_COMPLETE_ORIGINAL_BUILDER_DEFINITIONS')
    constants={n.targets[0].id:ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign)
        and len(n.targets)==1 and isinstance(n.targets[0],ast.Name)
        and n.targets[0].id in ('ENGINE','ENGINE_SHA','RUNTIME','RUNTIME_SHA')}
    require(len(constants)==4,'WORKER_EXACT_ORIGINAL_TEMPLATE_SOURCE_CONSTANTS')
    env=dict(ast=ast,hashlib=hashlib,FunctionType=FunctionType,NS=NS,**constants)
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),expected['path'],'exec'),env)
    selected,proof=transport._project(env['prepare_engine_builder'],env,{
        10:11,'case165-current-r010-tests':transport.TASK,
        transport.PREFIX+'current-runtime-run010.v1.json':CANONICAL})
    builder=selected(engine_raw,runtime,runtime_raw)
    require(builder.task==transport.TASK and builder.receipt==CANONICAL
        and builder.proof['target_physical_run']==11 and builder.proof['target_descriptors']==162
        and builder.proof['original_product10_retained'] is True,'WORKER_NEW_IDENTITY_ORIGINAL_PRODUCT10')
    return builder,proof


def prepare(root,q,a,scope,bytes_policy,source_loader):
    """One full fresh entry and engine construction; no encoder or publisher."""
    require=transport.require
    require(not (root/CANONICAL).exists(),'WORKER_NEW_CANONICAL_RESULT_ABSENT')
    for name in (SELF,preparation.SELF,transport.SELF,zlib.SELF):q.pin(name)
    worker=transport.connect(preparation.bounded_read(q,a,transport.SOURCE,65536))
    binding=zlib.connect(preparation.bounded_read(q,a,zlib.SOURCE,65536))
    context=preparation.constructor_context(root,q,a,scope,bytes_policy,source_loader)
    declaration=context.libraries.zlib165_mapping_declaration_v1
    a.exact(q.pin(PACKAGE[0]['path']),PACKAGE[0],'WORKER_SAME_PUBLISHED_NEW_MANIFEST')
    read=lambda pin,limit:preparation.bounded_read(q,a,pin,limit)
    def reference_factory(prior,packet,check):
        old,proof=context.api.reconstruct(prior,packet,check)
        a.exact(dict(old.binding.manifest_pin),dict(declaration.REFERENCE_MANIFEST),'WORKER_ORIGINAL009_REFERENCE')
        return binding.connect(root,context.loader,scope,old,declaration,
            context.libraries.batch_zlib_mapping,context.libraries.current_queue_successor_binding,check),proof
    def transport_factory(reference,step,check):
        item=binding.worker_graph(root,context.loader,context.known,context.api,
            context.libraries.bounded_successor_capsule_wire_v2,bytes_policy,reference,step,declaration,worker,check)
        return item.graph,item.runtime
    entry=binding.entry_reconstructor(worker,context.api.metadata)(transport.TASK,PACKAGE[2],read,
        reference_factory,transport_factory,q.checkpoint)
    a.exact(dict(entry.graph.binding.manifest_pin),PACKAGE[0],'WORKER_ACTUAL_NEW_MANIFEST')
    require(entry.runtime.PINS and len(entry.runtime.PINS)==2,'WORKER_CLOSED_ORIGINAL_TEMPLATE_PAIR')
    known=scope.extend(context.known,scope.pins(entry.runtime.PINS))
    known=scope.extend(known,scope.pins([STEP]))
    # Reuse only this sealed code allow-list, not the former full-source PASS.
    # Source opens requested by the real initializer are freshly pinned below.
    profile=a.read_exact(q,PROFILE)
    a.fields(profile,dict(state='PASS_NATIVE009_FRESH_VERIFIED_SOURCE9_AND_PARENT_COST_NOT_FRAME_OR_NATIVE',
        GO_authorized=False,actual_worker_product_or_Native_executed=False,cleanup_confirmed=True,
        fresh_inputs=527,final_fresh_hashes=527),'WORKER_HISTORICAL_SOURCE_DECLARATIONS_ONLY')
    declared=scope.pins([p for p in profile['source_pins'] if p['path'].startswith('tools/p09/')
        and p['path'].endswith('.py') and not p['path'].startswith('tools/p09/tests/')])
    require(len(declared)==252,'WORKER_CLOSED252_SOURCE_DECLARATION_NOT_FRESHNESS')
    known=scope.extend(known,declared)
    archived_code=scope.pins([p for p in profile['source_pins'] if p['path'].endswith('.py')
        and not p['path'].startswith('tools/p09/') and '/tests/' not in p['path']])
    known=scope.extend(known,archived_code)
    # Initializers hash both code and test source bytes without running tests.
    # Complete their intrinsic literal declarations before any initializer, so
    # missing files are not discovered by repeatedly launching the whole graph.
    known=scope.extend(known,scope.pins([p for p in profile['source_pins'] if p['path'].endswith('.py')]))
    initializers=[p for p in declared.values() if p['path'].startswith('tools/p09/flat_')]
    require(len(initializers)==36 and sum(p['bytes'] for p in initializers)==509413,
        'WORKER_CLOSED36_INITIALIZER_DECLARATION_SOURCES')
    intrinsic_rows=[]
    for initializer in initializers:
        tree=ast.parse(preparation.bounded_read(q,a,initializer,65536))
        intrinsic_rows.extend(literal_code_pins(tree,scope))
    require(bool(intrinsic_rows),'WORKER_NONEMPTY_INTRINSIC_CODE_DECLARATIONS')
    intrinsic={}
    for pin in intrinsic_rows:
        require(pin['path'] not in intrinsic or intrinsic[pin['path']]==pin,
            'WORKER_INTRINSIC_CODE_PIN_CONFLICT_NOT_REBASE')
        intrinsic[pin['path']]=dict(pin)
    intrinsic=scope.pins(list(intrinsic.values()))
    known=scope.extend(known,intrinsic)
    paced=type(context.paced)(context.paced.original,q,known)
    names,_=paced.api.load(root,[known['tools/p09/native009_full72_construction_v1.py']],{})
    loader,_=names.native009_full72_construction_v1.private_runtime_imports(paced.api)
    names,_=loader.load(root,[known['tools/p09/'+n+'.py'] for n in
        ('post_product_recovery_connection_v1','post_product_recovery_window_v1')],{})
    recovery,window=names.post_product_recovery_connection_v1,names.post_product_recovery_window_v1
    policy_pin=known['tools/p09/batch_verification.py']
    builder,projection=engine_builder(preparation.bounded_read(q,a,policy_pin,262144),policy_pin,entry.runtime,
        preparation.bounded_read(q,a,known['tools/p09/native009_engine_connection_v1.py'],65536),
        preparation.bounded_read(q,a,known['tools/p09/current_queue_successor_runtime.py'],65536))
    a.exact(q.pin(STEP['path']),STEP,'WORKER_STEP_BEFORE_ENGINE')
    audit_state=dict(active=True,checking=False,opens=0,pyc_denied=0)
    observed=set()
    def audit(event,args):
        if (not audit_state['active'] or audit_state['checking'] or event!='open' or not args
            or not isinstance(args[0],(str,bytes))):
            return
        path=Path(os.fsdecode(args[0])).absolute()
        if not path.is_relative_to(root):return
        mode=args[1] if len(args)>1 else None;flags=args[2] if len(args)>2 else 0
        require(not (isinstance(mode,str) and any(v in mode for v in 'wax+'))
            and not (isinstance(flags,int) and flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC)),
            'WORKER_READONLY_ENGINE_CONSTRUCTION')
        if path.suffix in ('.pyc','.pyo'):
            audit_state['pyc_denied']+=1;raise OSError('WORKER_SOURCE_REQUIRED_NOT_BYTECODE')
        name=path.relative_to(root).as_posix()
        if name not in known:q.missing_worker_construction_input=name
        require(name in known,'WORKER_ENGINE_OPEN_EXPLICITLY_DECLARED')
        audit_state['checking']=True
        try:
            q.checkpoint()
            a.exact(q.pin(name),known[name],'WORKER_ACTUAL_DEFAULT_INITIALIZER_SOURCE_PIN')
            observed.add(name);audit_state['opens']+=1
        finally:audit_state['checking']=False
    sys.addaudithook(audit)
    try:
        envelope=importlib.import_module('flat_current_queue_envelope_runtime_v25')
        class WindowSource:
            def read_bytes(self):return preparation.bounded_read(q,a,window.WINDOW_PIN,65536)
        class Root:
            def __fspath__(self):return os.fspath(root)
            def __truediv__(self,name):
                return WindowSource() if name==window.WINDOW_PIN['path'] else root/name
        linked=builder.build(Root(),loader,NS(runtime=entry.runtime),entry.graph,envelope.prior,
            recovery,window,q.checkpoint)
    finally:audit_state['active']=False
    require(linked.state.attempts==linked.state.calls==0 and linked.window.WINDOW.SECONDS==10,
        'WORKER_ORIGINAL_PRODUCT10_AND_UNEXECUTED_BODY')
    require(linked.names.task(165)==transport.TASK and linked.names.physical_run(165)==11
        and linked.names.root_path(NS(index=165))==CANONICAL,'WORKER_REAL_RUN011_IDENTITIES')
    helpers=[]
    for module in tuple(sys.modules.values()):
        filename=getattr(module,'__file__',None)
        if filename:
            path=Path(filename).absolute()
            if path.suffix=='.py' and path.is_relative_to(root/'tools/p09'):
                helpers.append(path.relative_to(root).as_posix())
    q.worker_default_helper_count=len(set(helpers))
    require(q.worker_default_helper_count<=64,'WORKER_ORIGINAL_DEFAULT_HELPER64_BOUND')
    for name in sorted(set(helpers)):
        actual=q.pin(name)
        if name in known:a.exact(actual,known[name],'WORKER_DEFAULT_HELPER_DECLARATION')
    return NS(linked=linked,entry=entry,proof=dict(task=transport.TASK,physical_run=11,descriptor_count=162,
        published_pins=list(PACKAGE),engine_builder_inverse=projection,
        actual_original_engine_and_worker_constructed=True,product_window_seconds=10,
        observed_declared_initializer_sources=len(observed),initializer_source_opens=audit_state['opens'],
        bytecode_reads_denied=audit_state['pyc_denied'],default_helper_count=len(set(helpers)),
        historical252_used_only_as_declared_code_allow_list=True,
        archived_code_declarations=len(archived_code),intrinsic_bootstrap_code_declarations=len(intrinsic),
        intrinsic_declaration_sources=list(initializers),
        whole_historical_source_freshness_claimed=False,
        encoded_new_package=False,files_published=False,worker_calls=0,worker_attempts=0,
        readiness_event_or_Native_Frame_or_dispatch_qualified=False,GO_authorized=False))
