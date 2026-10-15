import ast
import copy
from types import SimpleNamespace as NS
import unittest


class Tests(unittest.TestCase):
    def test_ast_and_compiled_code_exact_with_independent_mutables(self):
        original=ast.parse("def f(x):\n return [x+1, {'a': x}]\n")
        changed=MODULE.deepcopy(original)
        self.assertEqual(ast.dump(changed,include_attributes=True),ast.dump(original,include_attributes=True))
        self.assertEqual(compile(changed,"same-source","exec"),compile(original,"same-source","exec"))
        changed.body[0].body.append(ast.Pass());self.assertEqual(len(original.body[0].body),1)

    def test_shared_ast_aliases_preserved(self):
        node=ast.Name(id="a",ctx=ast.Load());value=[node,node]
        result=MODULE.deepcopy(value)
        self.assertIs(result[0],result[1]);self.assertIsNot(result[0],node)

    def test_ast_locations_and_extra_attributes_preserved(self):
        node=ast.parse("x = 1");node.extra={"values":[1,2]}
        result=MODULE.deepcopy(node)
        self.assertEqual(ast.dump(result,include_attributes=True),ast.dump(node,include_attributes=True))
        result.extra["values"].append(3);self.assertEqual(node.extra["values"],[1,2])

    def test_cycles_and_standard_fallback(self):
        values=[];values.append(values);result=MODULE.deepcopy(values);self.assertIs(result[0],result)
        value=NS(a=[1,2]);result=MODULE.deepcopy(value);result.a.append(3);self.assertEqual(value.a,[1,2])
        source=[];tu=(source,);source.append(tu)
        cloned=MODULE.deepcopy(tu);self.assertIs(cloned[0][0],cloned)

    def test_original_loader_and_copy_module_not_mutated(self):
        original=ENVELOPE.namespace_bundle;before=original.load.__globals__["copy"].deepcopy
        fast=MODULE.connect(original)
        self.assertIs(fast.load.__code__,original.load.__code__)
        self.assertIs(fast.load.__defaults__,original.load.__defaults__)
        self.assertIsNot(fast.load.__globals__,original.load.__globals__)
        self.assertIs(original.load.__globals__["copy"].deepcopy,before)
        self.assertIs(copy.deepcopy,before)

    def test_actual_namespace_load_retains_all_original_program_nodes(self):
        modules,proof=MODULE.connect(ENVELOPE.namespace_bundle).load(ROOT,[PIN],{})
        self.assertEqual(modules.ast_clone_namespace_v1.SOURCE,MODULE.SOURCE)
        self.assertTrue(proof[0]["original_function_class_constants_and_initialization_AST_retained"])
        self.assertFalse(proof[0]["actual_module_imported_or_sys_modules_hidden"])

    def test_fresh_source_pin_failures_still_rejected(self):
        fast=MODULE.connect(ENVELOPE.namespace_bundle)
        for pin in (dict(PIN,bytes=PIN["bytes"]+1),dict(PIN,sha256="0"*64)):
            with self.assertRaises(ValueError):fast.load(ROOT,[pin],{})

    def test_whole_current_and_frozen_module_compilation_equal(self):
        for path in ("tools/p09/xz_unified_runtime_v1.py","tools/p09/prepared_run_closure_v1.py","tools/p09/xz_unified_native_entry_v1.py"):
            source=ast.parse((ROOT/path).read_bytes());revised=MODULE.deepcopy(source)
            self.assertEqual(ast.dump(source,include_attributes=True),ast.dump(revised,include_attributes=True))
            self.assertEqual(compile(source,path,"exec"),compile(revised,path,"exec"))
