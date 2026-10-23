"""Admit the qualified child202 declarations into an unopened common parent.

Old201 remains unchanged. The new exact expected count and result labels have
an inverse to the full original inspector. No past byte boundary or READY time
becomes current Native/GO credit; every current pin closes under its owner.
"""
import ast
import copy
import hashlib
from types import CodeType,FunctionType,SimpleNamespace as NS

SELF='tools/p09/native011_product_worker_scope.py'
TEST='tools/p09/tests/test_native011_product_worker_scope.py'
SOURCE=dict(path='tools/p09/native011_ready_scope_connection.py',bytes=13232,
    sha256='b4442d1249722008a44ec725b2bb195019177c1f59772197d597863cba426a7e')
READY=dict(path='implementation/p09/evidence/p09-361-native011-current805-product-worker-ready002.v1.json',bytes=47070,
    sha256='b131b5ab1fc95db6c10d0484c43fa42232dba3b7058523db5e502bf2dcad172d')
CHILD='tools/p09/native011_product_worker_entry.py'
CONTROLS=(SELF,TEST,CHILD,'tools/p09/tests/test_native011_product_worker_entry.py',
    'tools/p09/native011_product_source_handoff.py','tools/p09/tests/test_native011_product_source_handoff.py',
    'tools/p09/native011_product_worker_ready_probe.py','tools/p09/tests/test_native011_product_worker_ready_probe.py',
    'tools/p09/native011_inherited_worker_ready_inspection.py',READY['path'])


def require(ok,code):
    if not ok:raise ValueError('PRODUCT_WORKER_SCOPE_'+code)


def pin_digest(rows):
    import json
    return hashlib.sha256(json.dumps(rows,ensure_ascii=True,allow_nan=False,sort_keys=True,
        separators=(',',':')).encode('ascii')).hexdigest()


def qualified(proof,prior,entry_pin,scope):
    require(type(prior) is dict and len(prior)==201 and CHILD not in prior and entry_pin['path']==CHILD,
        'EXACT_OLD201_PLUS_NEW_CHILD')
    required=scope.extend(prior,scope.pins([entry_pin]));child=proof['child'];gate=proof['readiness']
    require(len(required)==202 and proof['state']=='PASS_PRODUCT_CHILD202_SOURCE_AND_ORIGINAL_READY_REAL_EOF_NOT_NATIVE'
        and proof['cleanup_confirmed'] is True and proof['fresh_inputs']==proof['final_fresh_hashes']==213
        and proof['actual_source_files']==202 and proof['actual_child_launches']==1
        and proof['GO_authorized'] is False and proof['actual_product_GO_writes']==0
        and proof['parent_frame_state']=='CLOSED' and proof['inner_job_final']['active_processes']==0,
        'ACTUAL_SOURCE202_QUALIFICATION_NOT_NATIVE_COMMIT')
    require(gate['readiness_confirmed'] is True and gate['readiness_limit_seconds']==15
        and 0<gate['readiness_elapsed_seconds']<15 and gate['actual_original_GO_written'] is False and gate['stopped'] is True,
        'ORIGINAL_READY15_NO_GO')
    require(child['source_count']==child['final_fresh_hashes']==child['inherited_sources_closed']==202
        and child['source_pin_sha256']==proof['original_worker_source_scope_pin_sha256']==pin_digest(required)
        and child['original_input_reads']==1 and child['original_GO_observed'] is False
        and child['product_creation_attempts']==0 and child['original_worker_exit_code']==1
        and child['cleanup_confirmed'] is True and child['every_declared_source_read_at_least_twice'] is True,
        'EXACT_CHILD202_FIRST_CLOSING_DIGEST_AND_EOF')
    pins=scope.pins(proof['source_pins'])
    require(len(pins)==213 and all(pins.get(n)==p for n,p in required.items()),'ALL_QUALIFIED_WORKER_PINS_EXACT_NOT_COUNT_ONLY')
    require(proof['worker_source_declaration']['new_child_entry_pin']==entry_pin
        and proof['source_handoff']['failed'] is False and proof['source_handoff']['preparation_START_sent'] is True
        and proof['source_handoff']['source_flags_and_descriptor_cleanup_errors']==[],
        'SAME_EXPLICIT_ENTRY_AND_RESTORED_PARENT_HANDOFF')
    for key,count in (('first_source_boundary',1),('second_source_boundary',2)):
        row=proof[key]
        require(row['worker_required_count']==row['parent_input_count']==202 and row['actual_parent_byte_boundaries']==count
            and row['exact_whole_worker_pin_coverage'] is True,'ACTUAL_COMPLETE_TWO_SOURCE_BOUNDARIES')
    return required,pins


def inspector(raw,original):
    require(type(raw) is bytes and len(raw)==SOURCE['bytes'] and hashlib.sha256(raw).hexdigest()==SOURCE['sha256'],
        'ENTIRE_ORIGINAL_SCOPE_INSPECTOR_SOURCE')
    require(type(original) is FunctionType and original.__closure__ is None,'ENTIRE_ORIGINAL_INSPECTOR_FUNCTION_CODE')
    tree=ast.parse(raw)
    def matches(form):return any(original.__code__==code for code in form.co_consts
        if type(code) is CodeType and code.co_name=='inspect_current')
    matched=matches(compile(raw,SOURCE['path'],'exec'))
    if not matched:matched=matches(compile(ast.fix_missing_locations(ast.Module(
        body=[n for n in tree.body if not isinstance(n,(ast.Import,ast.ImportFrom))],type_ignores=[])),SOURCE['path'],'exec'))
    require(matched,'ENTIRE_ORIGINAL_INSPECTOR_FUNCTION_CODE')
    before=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='inspect_current');counts=[0,0]
    class Select(ast.NodeTransformer):
        def visit_Constant(self,node):
            if type(node.value) is int and node.value==201:after=ast.Constant(202);counts[0]+=1
            elif node.value=='EXACT_REQUIRED201_MAPPING':after=ast.Constant('EXACT_REQUIRED202_MAPPING');counts[1]+=1
            else:return node
            after._scope202_before=copy.deepcopy(node);return ast.copy_location(after,node)
    selected=Select().visit(copy.deepcopy(before));require(counts==[3,1],'ONE_COUNT_PREDICATE_TWO_REPORT_FIELDS_ONE_LABEL')
    class Undo(ast.NodeTransformer):
        def visit(self,node):
            if hasattr(node,'_scope202_before'):return copy.deepcopy(node._scope202_before)
            return super().visit(node)
    require(ast.dump(Undo().visit(copy.deepcopy(selected)),include_attributes=False)==ast.dump(before,include_attributes=False),
        'FULL_ORIGINAL_SCOPE_INSPECTOR_AST_INVERSE')
    env=dict(original.__globals__)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[selected],type_ignores=[])),SOURCE['path'],'exec'),env)
    return env['inspect_current'],dict(whole_source=dict(SOURCE),entire_original_scope_inspector_AST_inverse=True,
        expected_worker_count=202,original_partition419_raw_mapping_source_and_Frame_predicates_retained=True,
        old201_default_module_mutated=False,actual_Native_or_product_qualified=False)


def bind(control,raw):
    require(type(control) is NS,'PRIVATE_CONTROL_NAMESPACE_NOT_DEFAULT_MODULE')
    selected,projection=inspector(raw,control.inspect_current);previous=control.admit;state=NS(calls=0,admission=None)
    def admit(q,a,scope,**options):
        require(state.calls==0,'ONE_SOURCE202_ADMISSION_NO_RETRY');state.calls+=1
        base=previous(q,a,scope,**options)
        require(len(base.required)==201 and len(base.control_names)==47 and not set(CONTROLS)&set(base.control_names),
            'EXACT_OWNED_METADATA47_BASE_AND_EXPLICIT_NEW_CONTROLS')
        proof=a.read_exact(q,READY);entry=q.pin(CHILD);required,pins=qualified(proof,base.required,entry,scope)
        # The original admission just freshly checked all201. Compare these
        # same-invocation values, then read only the additional qualifier code.
        # Original constructor closing and future Native reads stay unchanged.
        for name,pin in pins.items():
            if name in required:a.exact(pin,required[name],'CURRENT_WORKER_PINS_MATCH_QUALIFIED_DECLARATIONS')
            else:a.exact(q.pin(name),pin,'FRESH_EXPLICIT_QUALIFIER_DEPENDENCY')
        state.admission=dict(qualification_pin=dict(READY),worker_sources=202,qualifier_dependency_sources=len(pins)-202,
            source_declaration_only=True,previous_byte_or_READY_result_used_as_current_Native_credit=False,
            original_201_required_retained=True,actual_Native_or_product_qualified=False,GO_authorized=False)
        return NS(**{**vars(base),'required':required,'control_names':base.control_names+CONTROLS,
            'readiness_pin':dict(READY),'product_worker202_admission':state.admission})
    control.admit=admit;control.inspect_current=selected
    return state,projection
