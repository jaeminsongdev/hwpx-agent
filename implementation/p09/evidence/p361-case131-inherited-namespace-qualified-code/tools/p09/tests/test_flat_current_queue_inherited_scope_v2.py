"""Exact original20 ClassDef AST plus five namespace/factory contracts."""
import ast
import copy
import hashlib
import unittest
from types import SimpleNamespace as NS
from unittest.mock import patch
import flat_current_queue_inherited_scope_runtime_v2 as m

ACTUAL=DATA=OLD_RAW=ROOT=LISTING=BODY=INHERITED=None


def old_tests(raw,variables):
    pin=m.OLD_TEST_PIN
    m.require(type(raw) is bytes and len(raw)==pin["bytes"] and hashlib.sha256(raw).hexdigest()==pin["sha256"],"EXACT_ORIGINAL20_TEST_RAW")
    tree=ast.parse(raw.decode("utf-8"));nodes=[n for n in tree.body if isinstance(n,ast.ClassDef)]
    m.require(len(nodes)==1 and nodes[0].name=="InheritedScopeTests","ONE_ORIGINAL20_CLASS")
    node=copy.deepcopy(nodes[0]);m.require(ast.dump(node,include_attributes=False)==ast.dump(nodes[0],include_attributes=False),"UNCHANGED_ALL_ORIGINAL20_TEST_AST")
    env=dict(m=m.PRISTINE,ast=ast,copy=copy,hashlib=hashlib,unittest=unittest,NS=NS,patch=patch,**variables)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),pin["path"],"exec"),env)
    return unittest.defaultTestLoader.loadTestsFromTestCase(env["InheritedScopeTests"])


class NamespaceTests(unittest.TestCase):
    def test_all_original_AST_and_no_module_side_effects(self):
        self.assertTrue(m.PROOF["original_all_v1_functions_and_constants_retained"])
        self.assertFalse(m.PROOF["full_module_or_CLI_import_executed"])
        for proof in m.PROOF["original_exact_AST_proofs"]:
            self.assertTrue(proof["original_selected_function_and_constant_AST_unchanged"])

    def test_no_full_modules_hidden_or_imported(self):
        self.assertNotIn("accept_flat_lean130_compound_parent_v1",m.sys.modules)
        self.assertNotIn("flat_current_queue_inherited_scope_runtime_v1",m.sys.modules)
        self.assertNotIn("test_flat_current_queue_inherited_scope_v1",m.sys.modules)
        self.assertFalse(m.PROOF["imported_modules_hidden_or_removed"])

    def test_original_v1_validation_globals_isolated(self):
        self.assertEqual(m.PRISTINE.own_inputs.__globals__["QUAL_PATH"],m.OLD_QUAL["path"])
        self.assertEqual(m.PRISTINE.own_inputs.__globals__["SELF"],m.NAMESPACE_PINS[1]["path"])
        self.assertEqual(m.API.own_inputs,m.own_inputs)
        self.assertEqual(m.API.template.__globals__["SELF"],m.SELF)

    def test_full_runtime_factory_code_unchanged(self):
        for name in ("template","worker","run_owned","binding_projection","previous_validation","prepare","accept"):
            self.assertEqual(getattr(m.API,name).__code__,getattr(m.PRISTINE,name).__code__)
        old,_=m.PRISTINE.template();new,_=m.API.template()
        self.assertEqual(old.run_owned.__code__,new.run_owned.__code__)
        self.assertEqual(old.worker.__code__,new.worker.__code__)
        self.assertEqual(new.run_owned.__globals__["SELF"],m.SELF)

    def test_closed_v2_DATA_and_original_whole_checker(self):
        self.assertEqual(m.validate_data(copy.deepcopy(DATA),m.base.CONFIG),DATA)
        with self.assertRaises(ValueError):m.validate_data(dict(DATA,scope_ignored=True),m.base.CONFIG)
        wrong=copy.deepcopy(DATA);wrong["namespace_source_pins"]=wrong["namespace_source_pins"][:1]
        with self.assertRaises(ValueError):m.validate_data(wrong,m.base.CONFIG)
        self.assertTrue(ACTUAL[1]["previous_actual_full_oracle_retained"])
        self.assertEqual(ACTUAL[1]["original_validator_projection"]["input_count"],1936)


if __name__=="__main__":unittest.main()
