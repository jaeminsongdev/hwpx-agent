"""Acceptance-only isolated window AST marker; original runtime V1 retained.

Nested pressure projections keep their own markers. Undo only the two product
window expectation nodes, never already-qualified pressure changes. Original
runtime source stays byte-identical; no product/Native replay or row mutation.
"""
import ast
import copy
from types import SimpleNamespace as NS
import strict_product_window_connection_v1 as original

SELF="tools/p09/strict_product_window_acceptance_connection_v2.py"
TEST="tools/p09/tests/test_strict_product_window_acceptance_connection_v2.py"
clone=original.clone
require=original.require

def product_expectation(node):
    before=ast.dump(node,include_attributes=False);revised=copy.deepcopy(node);changed=0
    for call in ast.walk(revised):
        if not (isinstance(call,ast.Call) and isinstance(call.func,ast.Name) and call.func.id=="fields"
            and len(call.args)==3 and isinstance(call.args[2],ast.Constant) and call.args[2].value=="RUNTIME_COST"):
            continue
        dictionary=call.args[1]
        require(isinstance(dictionary,ast.Call) and isinstance(dictionary.func,ast.Name)
            and dictionary.func.id=="dict","ORIGINAL_RUNTIME_COST_DICTIONARY")
        fields=[k for k in dictionary.keywords if k.arg=="product_allowance_seconds"]
        require(len(fields)==1 and isinstance(fields[0].value,ast.Constant)
            and type(fields[0].value.value) is int and fields[0].value.value==20,"ORIGINAL_PRODUCT20_EXPECTATION")
        previous=copy.deepcopy(fields[0].value);value=ast.copy_location(ast.Constant(15),previous)
        value._strict_window_before=previous;fields[0].value=value;changed+=1
    require(changed==1,"ONE_PRODUCT15_EXPECTATION")
    class Undo(ast.NodeTransformer):
        def visit(self,n):
            if hasattr(n,"_strict_window_before"):return copy.deepcopy(n._strict_window_before)
            return super().visit(n)
    require(ast.dump(Undo().visit(copy.deepcopy(revised)),include_attributes=False)==before,
        "ALL_EXISTING_PRESSURE_AND_ORACLE_NODES_UNCHANGED")
    return revised

def direct_oracle(previous_direct,new_native):
    budget=clone(previous_direct.runtime_budget,views=new_native)
    cost=clone(previous_direct.cost,runtime_budget=budget)
    retained=clone(previous_direct.retained_evidence,runtime_budget=budget)
    def mechanics(node):return product_expectation(previous_direct.mechanics_projection(node))
    return NS(**{**vars(previous_direct),"runtime_budget":budget,"cost":cost,
        "retained_evidence":retained,"mechanics_projection":mechanics})
