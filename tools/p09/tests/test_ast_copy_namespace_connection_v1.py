import ast
import copy
import hashlib
import importlib
import unittest

MODULE=None
CANDIDATE=None
ORIGINAL=None
ROOT=None


def pin(path):
    raw=(ROOT/path).read_bytes();return dict(path=path,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())


class Tests(unittest.TestCase):
    def test_complete_original_loader_code_and_default_modules_retained(self):
        before_copy=copy.deepcopy;before_import=importlib.import_module
        loader,proof=MODULE.connect(ORIGINAL,CANDIDATE)
        self.assertIs(loader.load.__code__,ORIGINAL.load.__code__)
        self.assertIs(loader.load.__defaults__,ORIGINAL.load.__defaults__)
        self.assertIs(copy.deepcopy,before_copy);self.assertIs(importlib.import_module,before_import)
        self.assertFalse(proof['byte_hash_AST_or_JSON_cache'])

    def test_private_helper_copy_import_routes_before_initialization(self):
        loader,_=MODULE.connect(ORIGINAL,CANDIDATE)
        nodes,_=loader.load(ROOT,[pin('tools/p09/ast_clone_namespace_v1.py')],{})
        helper=nodes.ast_clone_namespace_v1
        self.assertIs(helper.copy.deepcopy,CANDIDATE.deepcopy)
        self.assertIsNot(helper.copy,copy)
        self.assertIs(copy.deepcopy,ORIGINAL.copy.deepcopy)

    def test_unrelated_stdlib_imports_and_source_proofs_unchanged(self):
        loader,_=MODULE.connect(ORIGINAL,CANDIDATE)
        nodes,proof=loader.load(ROOT,[pin(MODULE.SELF)],{})
        helper=nodes.ast_copy_namespace_connection_v1
        self.assertTrue(callable(helper.connect));self.assertEqual(len(proof),1)
        self.assertTrue(proof[0]['original_function_class_constants_and_initialization_AST_retained'])
        self.assertFalse(proof[0]['actual_module_imported_or_sys_modules_hidden'])

    def test_fresh_pin_and_undeclared_project_import_rejection_preserved(self):
        loader,_=MODULE.connect(ORIGINAL,CANDIDATE);correct=pin(MODULE.SELF)
        for bad in (dict(correct,bytes=correct['bytes']+1),dict(correct,sha256='0'*64)):
            with self.assertRaises(ValueError):loader.load(ROOT,[bad],{})
        with self.assertRaises(ValueError):loader.load(ROOT,[pin('tools/p09/weighted_audit_io.py')],{})

    def test_actual_profile_helper_compiled_code_and_copy_results_equal(self):
        pinset=[pin('tools/p09/xz_closed_preparation_v1.py')]
        regular,_=ORIGINAL.load(ROOT,pinset,{})
        loader,_=MODULE.connect(ORIGINAL,CANDIDATE);fast,_=loader.load(ROOT,pinset,{})
        self.assertIs(fast.xz_closed_preparation_v1.copy.deepcopy,CANDIDATE.deepcopy)
        self.assertEqual(regular.xz_closed_preparation_v1.projected.__code__,fast.xz_closed_preparation_v1.projected.__code__)
        tree=ast.parse('def f(x):\n return x+1\n')
        copied=fast.xz_closed_preparation_v1.copy.deepcopy(tree)
        self.assertEqual(ast.dump(tree,include_attributes=True),ast.dump(copied,include_attributes=True))
        self.assertIsNot(tree,copied)

    def test_default_import_outside_private_loader_stays_original(self):
        MODULE.connect(ORIGINAL,CANDIDATE)
        self.assertIs(importlib.import_module('copy'),copy)
        self.assertIs(ORIGINAL.load.__globals__['importlib'],importlib)

    def test_stdlib_copy_helpers_other_than_deepcopy_not_replaced(self):
        loader,_=MODULE.connect(ORIGINAL,CANDIDATE)
        nodes,_=loader.load(ROOT,[pin('tools/p09/xz_closed_preparation_v1.py')],{})
        facade=nodes.xz_closed_preparation_v1.copy
        self.assertIs(facade.copy,copy.copy);self.assertIs(facade.Error,copy.Error)

    def test_original_main_invocation_rejects_unrelated_function(self):
        with self.assertRaises(ValueError):MODULE.invoke(lambda:None,object())
