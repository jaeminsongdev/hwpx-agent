"""Retain approved Batch scope AST; explicitly bind real805 listing/context."""
import ast
import builtins
import copy
from types import FunctionType, SimpleNamespace as NS

SELF='tools/p09/native011_current_epoch_metadata.py'
TEST='tools/p09/tests/test_native011_current_epoch_metadata.py'


def require(ok,code):
    if not ok:raise ValueError('CURRENT805_METADATA_'+code)


class ListingView:
    """Declarations only; the unchanged body must still fresh-read the real list."""
    def __init__(self,scope,listing,current):
        self.base=scope;self.listing=copy.deepcopy(listing)
        self.current=scope.pins(list(current.values()));self.calls=0
    def listing_inputs(self,record):
        require(record==self.listing,'EXACT_REAL_COMPILED_LIST_RECORD_NOT_OLD_SCHEMA')
        require(record['current_whole805_freshness_qualified'] is False
            and record['product_test_bodies_executed'] is False,'LIST_ONLY_NOT_RUNTIME_PROMOTION')
        self.calls+=1
        return {n:dict(p) for n,p in self.current.items()}


def connect(runtime,raw,batch_module,owner,epoch_scope):
    """Capture original install_scope output, then invert only four epoch slots."""
    require(type(batch_module.install_scope) is FunctionType,'ORIGINAL_APPROVED_BATCH_INSTALLER')
    captured=[];original_compile=builtins.compile
    def compiling(source,*args,**kwargs):
        if isinstance(source,ast.Module):
            found=[n for n in source.body if isinstance(n,ast.FunctionDef) and n.name=='current_input_scope']
            if len(found)==1 and len(found[0].body)==1 and isinstance(found[0].body[0],ast.With):
                captured.append(copy.deepcopy(source))
        return original_compile(source,*args,**kwargs)
    installer=FunctionType(batch_module.install_scope.__code__,
        dict(batch_module.install_scope.__globals__,compile=compiling),
        argdefs=batch_module.install_scope.__defaults__,closure=batch_module.install_scope.__closure__)
    installer.__kwdefaults__=batch_module.install_scope.__kwdefaults__
    approved,proof=installer(runtime,raw,owner)
    require(proof['exact_original_AST_inverse'] is True and len(captured)==1,'ONE_REAL_APPROVED_THREE_POLICY_SLOT_PROJECTION')
    baseline=captured[0];revised=copy.deepcopy(baseline);changes=[]
    def marked(after,before,label):
        after._epoch_before=copy.deepcopy(before);changes.append(label);return ast.copy_location(after,before)
    class Epoch(ast.NodeTransformer):
        def visit_Import(self,node):
            if len(node.names)==1 and node.names[0].name=='current_stored_runtime_scope' and node.names[0].asname=='scope':
                return marked(ast.parse('scope=_current_epoch_scope').body[0],node,'scope_import')
            return node
        def visit_Compare(self,node):
            pattern=ast.parse('len(rust)==787',mode='eval').body
            if ast.dump(node,include_attributes=False)==ast.dump(pattern,include_attributes=False):
                return marked(ast.parse('len(rust)==805',mode='eval').body,node,'rust_guard')
            return self.generic_visit(node)
        def visit_Constant(self,node):
            if type(node.value) is str and node.value=='source_test_names':
                return marked(ast.Constant('current_catalog_names'),node,'listing_field')
            if type(node.value) is str and node.value=='CURRENT_RUST787_AND_BINARY':
                return marked(ast.Constant('CURRENT_RUST805_AND_BINARY'),node,'rust_error_label')
            return node
    revised=Epoch().visit(revised)
    require(sorted(changes)==sorted(('scope_import','listing_field','rust_guard','rust_error_label')),
        'EXACT_FOUR_EPOCH_SLOTS_NO_OTHER_POLICY_CHANGE')
    class Undo(ast.NodeTransformer):
        def visit(self,node):
            if hasattr(node,'_epoch_before'):return copy.deepcopy(node._epoch_before)
            return super().visit(node)
    require(ast.dump(Undo().visit(copy.deepcopy(revised)),include_attributes=False)==ast.dump(baseline,include_attributes=False),
        'ENTIRE_APPROVED_BATCH_SCOPE_AST_INVERSE')
    env=dict(approved.current_input_scope.__globals__,_current_epoch_scope=epoch_scope)
    exec(original_compile(ast.fix_missing_locations(revised),batch_module.RUNTIME,'exec'),env)
    actual=env['current_input_scope']
    require(actual.__globals__['_batch'] is owner and actual.__globals__['_current_epoch_scope'] is epoch_scope,
        'SAME_REAL_BATCH_AND_EXPLICIT_EPOCH_SCOPE')
    return NS(**{**vars(approved),'current_input_scope':actual}),dict(
        approved_three_policy_slot_proof=proof,epoch_slots=changes,entire_approved_AST_inverse=True,
        original_default_scope_or_runtime_mutated=False,old_listing_PASS_fabricated=False,
        actual_Batch_begin_metadata_or_Native_qualified=False,GO_authorized=False)
