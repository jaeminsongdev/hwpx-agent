"""Exact two 20->15 product-reservation terms, only with actual window binding.

All acquisition/bytes/Native600/margin60/early11/diagnostic2.05/finalsample
terms remain unchanged. This is a plan, not actual deadline/GO evidence.
"""
import ast
import copy
from types import SimpleNamespace as NS

SELF="tools/p09/strict_product_window_model_v1.py"
TEST="tools/p09/tests/test_strict_product_window_model_v1.py"

def require(ok,code):
    if not ok:raise ValueError("STRICT_WINDOW_MODEL_"+code)

def project(original,raw,policy,scope):
    node=policy.verified_node(raw,policy.MODEL_PIN,"model",ast.FunctionDef)
    # Reproduce the already-qualified V17 one-call cooling dependency projection.
    cost_calls=[n for n in ast.walk(node) if isinstance(n,ast.Call)
        and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name)
        and n.func.value.id=="scope" and n.func.attr=="cost"]
    require(len(cost_calls)==1,"ONE_QUALIFIED_COST_CALL")
    cost_calls[0].func=ast.Name(id="_no_cooling_cost",ctx=ast.Load())
    env=dict(original.__globals__)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[copy.deepcopy(node)],type_ignores=[])),
        original.__code__.co_filename,"exec",dont_inherit=True),env)
    require(env["model"].__code__==original.__code__,"EXACT_QUALIFIED_V17_MODEL")
    before=ast.dump(node,include_attributes=False);changed=[]
    assignments=[n for n in node.body if isinstance(n,ast.Assign)
        and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id=="total"]
    require(len(assignments)==1,"ONE_COMPLETE_RUNTIME_TOTAL")
    constants=[n for n in ast.walk(assignments[0].value) if isinstance(n,ast.Constant) and type(n.value) is int and n.value==20]
    # Inventory divisor /20 is a distinct physical pacing term, NOT a product reservation.
    adds=[n for n in ast.walk(assignments[0].value) if isinstance(n,ast.BinOp) and isinstance(n.op,ast.Add)
        and isinstance(n.right,ast.Constant) and type(n.right.value) is int and n.right.value==20]
    require(len(constants)==2 and len(adds)==1,"ONLY_PRODUCT_ADD_NOT_INVENTORY_DIVISOR")
    adds[0].right._window_old=20;adds[0].right.value=15;changed.append("total_product_add")
    fields=[n for n in ast.walk(node) if isinstance(n,ast.keyword) and n.arg=="product_allowance_seconds"]
    require(len(fields)==1 and isinstance(fields[0].value,ast.Constant)
        and type(fields[0].value.value) is int and fields[0].value.value==20,"ONE_PRODUCT_ALLOWANCE_FIELD")
    fields[0].value._window_old=20;fields[0].value.value=15;changed.append("product_field")
    class Undo(ast.NodeTransformer):
        def visit_Constant(self,n):
            if hasattr(n,"_window_old"):n.value=n._window_old
            return n
    require(ast.dump(Undo().visit(copy.deepcopy(node)),include_attributes=False)==before,"EVERY_OTHER_MODEL_TERM_UNCHANGED")
    env=dict(original.__globals__)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),
        original.__code__.co_filename,"exec",dont_inherit=True),env)
    revised=env["model"]
    def model(required,requests,*,PDH_seconds=2.05):
        row=revised(required,requests,PDH_seconds=PDH_seconds)
        require(row["product_allowance_seconds"]==15 and row["unallocated_margin_seconds"]==60
            and row["additional_early_source_wait_allowance_seconds"]==11
            and row["unchanged_lock_deadline_seconds"]==600,"ONLY_ENFORCED_PRODUCT_WINDOW")
        return dict(row,strict_GO_to_complete_capture_window_seconds=15,
            actual_window_binding_and_complete_capture_required_before_acceptance=True,
            old_product_reservation_seconds=20,product_reservation_reduction_seconds=5,
            input_scope_reduction_or_rate_change=False)
    return model,dict(changed_product_reservation_terms=changed,all_other_model_AST_unchanged=True,
        actual_window_enforcement_required=True,GO_authorized=False)
