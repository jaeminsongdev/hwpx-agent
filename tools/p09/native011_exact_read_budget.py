"""Candidate exact-size IO reservations, not installed in a Native dispatcher.

A reservation precedes EVERY actual read, including a one-byte EOF probe.
Fresh actual bytes/hash/parse/identity/closing checks and the 64KiB workspace
remain. Only the byte amount reserved and the corresponding OS read limit
change together. The original fixed-chunk path remains untouched.
"""
import ast
import copy
import hashlib
import math
import sys
import threading
from types import FunctionType,MappingProxyType,SimpleNamespace as NS

SELF='tools/p09/native011_exact_read_budget.py'
TEST='tools/p09/tests/test_native011_exact_read_budget.py'
CHUNK=65536
ORIGINAL=dict(path='tools/p09/audit_evidence_io.py',bytes=5653,
    sha256='84b7dae287ac01c7ec308ca302762ec283406fca3fa43bc469882a3913578a8f')


def require(ok,code):
    if not ok:raise ValueError('EXACT_READ_BUDGET_'+code)


def pacer_type(base):
    class Pacer(base):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs)
            self.owner=threading.get_ident();self.pending=None;self.request=None;self.failed=False
            self.reservations=0;self.reserved_bytes=0;self.refunded_bytes=0
        def valid(self):
            require(threading.get_ident()==self.owner and not self.failed,'SAME_UNFAILED_PACER_OWNER')
        def request_bytes(self,count):
            self.valid()
            try:
                require(type(count) is int and 1<=count<=CHUNK and self.pending is self.request is None,
                    'ONE_BOUNDED_REQUEST_BEFORE_RESERVATION')
                self.request=count
            except BaseException:self.failed=True;raise
        def reserve(self,checkpoint):
            self.valid();require(self.request is not None and self.pending is None,'EXPLICIT_READ_REQUEST')
            count=self.request;attempts=0
            try:
                require(type(self.rate) is int and self.rate in (1048576,2097152),'ORIGINAL_ONE_TWO_MIB_SELECTED_RATE')
                while True:
                    now=self.clock()
                    require(type(now) in (int,float) and math.isfinite(now) and now>=self.last,'ORIGINAL_MONOTONIC_CLOCK')
                    self.tokens=min(CHUNK,self.tokens+(now-self.last)*self.rate);self.last=now
                    if self.tokens>=count:
                        self.tokens-=count;self.pending=count;self.request=None
                        self.reservations+=1;self.reserved_bytes+=count;return
                    attempts+=1;require(attempts<=64,'ORIGINAL_BOUNDED_CLOCK_PROGRESS')
                    delay=min(.05,max(.000001,(count-self.tokens)/self.rate))
                    checkpoint();self.sleeper(delay);self.requested_sleep_seconds+=delay;checkpoint()
            except BaseException:self.failed=True;raise
        def refund(self,count):
            self.valid()
            try:
                require(type(count) is int and self.pending is not None and 0<=count<=self.pending,
                    'ACTUAL_COUNT_WITHIN_RESERVED_OS_READ')
                unused=self.pending-count;self.tokens=min(CHUNK,self.tokens+unused)
                self.bytes_paced+=count;self.bytes_by_kind[self.kind]+=count
                self.refunded_bytes+=unused;self.pending=None
            except BaseException:self.failed=True;raise
    return Pacer


def begin(reader,name):
    reader.pacer.valid()
    require(name in reader._exact_input_sizes,'DECLARED_INPUT_ONLY_BEFORE_STREAM_OPEN')


def reserve(reader,name,size,checkpoint):
    remaining=reader._exact_input_sizes[name]-size
    require(remaining>=0,'OBSERVED_SIZE_NOT_PAST_DECLARATION')
    reader.pacer.request_bytes(min(CHUNK,remaining) if remaining else 1)
    reader.pacer.reserve(checkpoint)


class LimitedRead:
    """One reusable serial adapter per reader; never stores file bytes."""
    def __init__(self):
        self.owner=threading.get_ident();self.stream=None;self.request=None;self.used=False;self.calls=0
    def readinto(self,buffer):
        require(threading.get_ident()==self.owner and self.stream is not None and not self.used,
            'ONE_ACTUAL_READ_IN_CURRENT_RESERVATION')
        require(len(buffer)==CHUNK,'SAME_ORIGINAL_WORKSPACE')
        self.used=True;self.calls+=1
        count=self.stream.readinto(buffer[:self.request])
        require(type(count) is int and 0<=count<=self.request,'OS_READ_WITHIN_RESERVED_AMOUNT')
        return count


def read_chunk(stream,workspace,reader,chunk_api):
    requested=reader.pacer.pending;adapter=reader._exact_read_proxy
    require(type(requested) is int and 1<=requested<=CHUNK,'ACTUAL_READ_MUST_FOLLOW_RESERVATION')
    require(adapter.stream is None and adapter.request is None and threading.get_ident()==adapter.owner,
        'NO_REENTRANT_OR_STALE_READ_ADAPTER')
    adapter.stream=stream;adapter.request=requested;adapter.used=False
    # Original workspace counters, fresh read, invalid-count checks and returned
    # slice are used. No previous buffer contents are substituted for IO.
    try:return chunk_api._read_chunk(adapter,workspace)
    finally:adapter.stream=None;adapter.request=None


def observed(reader,name,size):
    require(size<=reader._exact_input_sizes[name],'FRESH_EXTRA_BYTE_NOT_DECLARED_EOF')


def project(raw,original,chunk_api):
    require(type(raw) is bytes and len(raw)==ORIGINAL['bytes']
        and hashlib.sha256(raw).hexdigest()==ORIGINAL['sha256'],'EXACT_ORIGINAL_LEAF_SOURCE')
    cls=next(n for n in ast.parse(raw).body if isinstance(n,ast.ClassDef) and n.name=='AuditEvidenceReader')
    before=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='_read')
    node=copy.deepcopy(before);hits=[]
    def same(a,text):return ast.dump(a,include_attributes=False)==ast.dump(ast.parse(text).body[0],include_attributes=False)
    class Change(ast.NodeTransformer):
        def visit_Expr(self,n):
            if same(n,'self.pacer.reserve(self.checkpoint)'):
                after=ast.parse('_reserve(self,name,size,self.checkpoint)').body[0]
                after._exact_before=copy.deepcopy(n);hits.append('reserve');return after
            return self.generic_visit(n)
        def visit_Assign(self,n):
            if same(n,'chunk = stream.read(CHUNK_BYTES)'):
                after=ast.parse('chunk = _read_chunk(stream,_workspace,self)').body[0]
                after._exact_before=copy.deepcopy(n);hits.append('read');return after
            return self.generic_visit(n)
        def visit_With(self,n):
            self.generic_visit(n)
            require(len(n.items)==1,'ONE_ORIGINAL_STREAM_CONTEXT')
            wrapper=ast.parse('with _workspace_for(self).lease() as _workspace: pass').body[0]
            wrapper.body=n.body;wrapper._exact_unwrap=True;n.body=[wrapper];hits.append('workspace');return n
    node=Change().visit(node)
    start=ast.parse('_begin(self,name)').body[0];start._exact_added=True;node.body.insert(1,start)
    require(sorted(hits)==['read','reserve','workspace'],'EXACT_THREE_LEAF_ADAPTATIONS')
    # Keep all original byte accounting before refusing a freshly observed extra
    # byte. A failed/short/changed stream is never a valid completed boundary.
    for statement in ast.walk(node):
        if isinstance(statement,ast.While):
            locations=[i for i,n in enumerate(statement.body) if same(n,'self.bytes_read += len(chunk)')]
            require(len(locations)==1,'ORIGINAL_ACTUAL_BYTE_COUNTER')
            guard=ast.parse('_observed(self,name,size)').body[0];guard._exact_added=True
            statement.body.insert(locations[0]+1,guard)
    body=node.body
    failure=ast.parse('try:\n pass\nexcept BaseException:\n self.pacer.failed=True\n raise').body[0]
    failure.body=body;failure._exact_try=True;node.body=[failure]
    class Undo(ast.NodeTransformer):
        def visit(self,n):
            if hasattr(n,'_exact_before'):return copy.deepcopy(n._exact_before)
            if hasattr(n,'_exact_added'):return None
            return super().visit(n)
        def visit_With(self,n):
            self.generic_visit(n);return n.body if hasattr(n,'_exact_unwrap') else n
        def visit_Try(self,n):
            self.generic_visit(n);return n.body if hasattr(n,'_exact_try') else n
    require(ast.dump(Undo().visit(copy.deepcopy(node)),include_attributes=False)==ast.dump(before,include_attributes=False),
        'ENTIRE_ORIGINAL_LEAF_AST_INVERSE')
    env=dict(vars(original),_begin=begin,_reserve=reserve,_observed=observed,
        _workspace_for=chunk_api._workspace_for,
        _read_chunk=lambda stream,workspace,reader:read_chunk(stream,workspace,reader,chunk_api))
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),ORIGINAL['path'],'exec'),env)
    return env['_read'],dict(entire_original_leaf_AST_inverse=True,actual_EOF_read_retained=True,
        all_original_hash_parse_accounting_checkpoint_and_closing_statements_retained=True,
        file_content_hash_JSON_or_AST_cache=False,original_fixed_chunk_path_mutated=False)


def prepare(raw,pressure,original,chunk_api):
    """Compile helper definitions before a boundary, never cache input bytes.

    The caller must freshly admit and close these source pins. Neither a pin
    nor a compiled helper supplies any file-read/hash/parse/closing credit.
    """
    leaf,proof=project(raw,original,chunk_api)
    expected,_=chunk_api.project_read(raw)
    Pacer=pacer_type(pressure.OwnedPacer)
    def bind(reader,pins):
        return _attach(reader,pins,pressure,original,leaf,proof,expected.__code__,Pacer)
    return bind


def attach(reader,pins,pressure,original,chunk_api,raw):
    return prepare(raw,pressure,original,chunk_api)(reader,pins)


def inspect_reader_type(reader_type,pressure,original,workspace_code):
    definitions=[(cls,vars(cls)['_read']) for cls in reader_type.__mro__ if '_read' in vars(cls)]
    selector=pressure.prior.WeightedReader._read
    require(len(definitions) in (2,3) and definitions[0][1] is selector
        and definitions[-1][0] is original.AuditEvidenceReader
        and (len(definitions)==2 or definitions[1][0].__name__=='ChunkLeaf'),
        'NO_UNDECLARED_READ_WRAPPERS_BYPASSED')
    if len(definitions)==3:
        require(definitions[1][1].__code__==workspace_code,'EXACT_ORIGINAL_WORKSPACE_LEAF_NOT_NAME_ONLY')


def _attach(reader,pins,pressure,original,leaf,proof,workspace_code,Pacer):
    require(0<len(pins)<=4096 and reader.read_passes==reader.bytes_read==reader.final_fresh_hashes==0
        and not reader.snapshots and not hasattr(reader,'_exact_input_sizes'),'UNUSED_DECLARED_READER_ONLY')
    sizes={}
    for name,pin in pins.items():
        require(type(pin) is dict and set(pin)=={'path','bytes','sha256'} and pin['path']==name
            and type(pin['bytes']) is int and pin['bytes']>0,'EXACT_POSITIVE_INPUT_SIZE_DECLARATION')
        sizes[name]=pin['bytes']
    old=reader.pacer
    require(type(old) is pressure.OwnedPacer and old.tokens==CHUNK and old.bytes_paced==0
        and old.requested_sleep_seconds==0 and old.bytes_by_kind=={'binary':0,'other':0},'NO_REUSED_PACING_CREDIT')
    # Only the original weighted selection wrapper and original/frozen chunk
    # leaf may define _read; do not bypass any additional native wrappers.
    inspect_reader_type(type(reader),pressure,original,workspace_code)
    base=type(reader)
    class Reader(base):
        def _read(self,name,parse=False):
            self.pacer.select(name)  # Original inherited name/rate selection.
            return leaf(self,name,parse=parse)
    reader.__class__=Reader
    reader.pacer=Pacer(clock=old.clock,sleeper=old.sleeper)
    reader._exact_input_sizes=MappingProxyType(sizes)
    reader._exact_read_proxy=LimitedRead()
    return dict(proof,original_base_reader_classes_and_methods_unchanged=True,
        original_selected_byte_rates=dict(binary=1048576,other=2097152),maximum_burst_bytes=CHUNK,
        every_actual_read_preceded_by_sufficient_byte_reservation=True,
        EOF_probe_read_limit=1,installed_in_product=False,actual_whole_Native_or_product_qualified=False)


def connect_private_factory(linked,original_reader,pins,raw):
    """Explicit optional slot, preserving the actual workspace class identity.

    Prepare from freshly admitted source before Native starts. The existing
    precise factory is called once for each real boundary; no default module,
    engine function, reader class or source read is replaced or replayed.
    """
    require(linked.state.attempts==linked.state.calls==0,'BEFORE_ANY_WORKER_ATTEMPT')
    run=linked.engine.run_owned;require(type(run) is FunctionType,'ORIGINAL_PRIVATE_ENGINE_FUNCTION')
    env=run.__globals__
    require(not any(getattr(m,'__dict__',None) is env for m in tuple(sys.modules.values()) if m),
        'NO_DEFAULT_ENGINE_NAMESPACE_MUTATION')
    require(type(original_reader) is type and callable(env.get('BoundaryReader')),'EXISTING_ORIGINAL_READER_FACTORY')
    leaves=[vars(cls)['_read'] for cls in original_reader.__mro__ if cls.__name__=='ChunkLeaf' and '_read' in vars(cls)]
    require(len(leaves)==1,'EXACT_ONE_EXISTING_WORKSPACE_LEAF')
    workspace_globals=leaves[0].__globals__['_workspace_for'].__globals__
    require(workspace_globals['SELF']=='tools/p09/reusable_audit_chunk_v1.py','ACTUAL_EXISTING_WORKSPACE_NAMESPACE')
    chunk_api=NS(**workspace_globals);pressure=env['byte_policy'];original=chunk_api.original
    expected,_=chunk_api.project_read(raw)
    inspect_reader_type(original_reader,pressure,original,expected.__code__)
    bind=prepare(raw,pressure,original,chunk_api);previous=env['BoundaryReader'];saved=dict(env)
    state=NS(attempts=0,completed=0,failed=False,proofs=[])
    def factory(*args,**kwargs):
        require(not state.failed and state.attempts<2,'TWO_ORIGINAL_BOUNDARIES_ONLY_NO_RETRY')
        state.attempts+=1
        try:
            reader=previous(*args,**kwargs)
            require(type(reader) is original_reader,'ORIGINAL_FACTORY_READER_BEFORE_EXACT_ADOPTION')
            state.proofs.append(bind(reader,pins));state.completed+=1;return reader
        except BaseException:state.failed=True;raise
    env['BoundaryReader']=factory
    require(set(env)==set(saved) and all(env[key] is value for key,value in saved.items() if key!='BoundaryReader')
        and linked.engine.run_owned is run,'ONLY_ONE_EXPLICIT_FACTORY_DEPENDENCY')
    return NS(state=state,factory=factory,previous=previous),dict(
        original_workspace_class_identity_retained=True,helper_compiled_before_Native_without_source_freshness_credit=True,
        original_precise_factory_invoked_at_both_original_boundary_sites=True,
        existing_default_modules_and_reader_methods_changed=False,
        actual_reader_method_chain_verified_before_Native=True,
        factory_attempts_during_construction=0,installed_in_product=False,actual_Native_qualified=False)
