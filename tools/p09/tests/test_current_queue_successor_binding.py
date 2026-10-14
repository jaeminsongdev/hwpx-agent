"""Private constructor projection and unchanged full source oracles."""
import copy
import ast
import hashlib
import importlib.util
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).parents[1]))
import current_queue_successor_binding as m
import runtime_envelope_namespace_bundle_v1 as loader
import current_stored_runtime_scope as scope
import runtime_envelope_scope_binding_v1 as original

ROOT=Path(__file__).parents[3]


class Tests(unittest.TestCase):
    def graph(self, index=161, provenance=None):
        return m.connect(ROOT,loader,scope,index,{} if provenance is None else provenance)

    def fixture(self, module):
        raw=b'{"original":true}\r\n';encoded=module.source.codec.encode(raw,lambda:None)
        def pin(name,data):return dict(path=name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
        old=pin("implementation/p09/evidence/p09-361-case160-current-runtime-run011.v1.json",raw)
        new=pin(module.source.PREFIX+"case160-runtime-run011.envelope.v1.json",encoded)
        manifest=pin("implementation/p09/evidence/fixture-successor-manifest.v1.json",b"manifest")
        row=module.source.descriptor(old,new,next_case=161)
        binding=module.Binding([row],manifest,next_case=161)
        required={x["path"]:x for x in (old,manifest)}
        return binding,required,manifest,row

    def test_original_module_not_mutated_and_all_methods_retained(self):
        before=original.Binding.__init__
        module,proof=self.graph()
        self.assertIs(original.Binding.__init__,before)
        self.assertTrue(proof["exact_constructor_inverse_code_equal"])
        for name in ("semantic_union","project","runtime_budget","validate_scope_evidence"):
            self.assertIs(getattr(module.Binding,name),proof["original_methods"][name])
            self.assertIs(getattr(module.Binding,name).__code__,proof["original_methods"][name].__code__)
        for row in proof["source_proofs"]:
            self.assertFalse(row["actual_module_imported_or_sys_modules_hidden"])
            self.assertTrue(row["original_function_class_constants_and_initialization_AST_retained"])

    def test_historical_context_keeps_old_index_and_is_copied(self):
        history={"successor_context":{"next_case":160,"current160_product_or_GO_qualified":False}}
        module,_=self.graph(provenance=history);binding,required,_,_=self.fixture(module)
        history["successor_context"]["next_case"]=999
        projection,_=binding.project(required,lambda:None)
        result=binding.representation(projection)
        self.assertEqual(result["next_case"],161)
        self.assertEqual(result["historical_predecessor_provenance"]["successor_context"]["next_case"],160)
        self.assertFalse(result["historical_provenance_is_current_acceptance"])

    def test_only_exact_successor_constructor_allowed(self):
        module,_=self.graph();binding,required,manifest,row=self.fixture(module)
        for index in (True,158,160,162):
            with self.assertRaises(ValueError):module.Binding([row],manifest,next_case=index)
        for index in (True,160,250,"161",161.0):
            with self.assertRaises(ValueError):self.graph(index)

    def test_duplicate_or_conflicting_pair_not_replaced(self):
        module,_=self.graph();binding,required,manifest,row=self.fixture(module)
        with self.assertRaises(ValueError):m.descriptors(module.source,[row],[copy.deepcopy(row)],161)
        with self.assertRaises(ValueError):binding.semantic_union({manifest["path"]:manifest},lambda:None)

    def test_scope_projection_preserves_original_input_count(self):
        module,_=self.graph();binding,required,_,_=self.fixture(module)
        projection,_=binding.project(required,lambda:None)
        self.assertEqual(len(projection.semantic_pins),len(projection.physical_pins))
        self.assertEqual(set(projection.semantic_pins),set(required))

    def test_historical_failed_path_only_accepts_exact_sealed_pair(self):
        base,_=self.graph();binding,required,manifest,row=self.fixture(base)
        row=copy.deepcopy(row);row["next_case"]=160
        row["semantic_original_pin"]["path"]="implementation/p09/evidence/p09-361-case158-current-runtime-run003.v1.json"
        row["physical_envelope_pin"]["path"]=base.source.PREFIX+"case158-runtime-run003.failed.envelope.v1.json"
        module,_=m.connect(ROOT,loader,scope,161,{},[row])
        exact=module.source.descriptor(row["semantic_original_pin"],row["physical_envelope_pin"],next_case=161)
        self.assertEqual(exact["physical_envelope_pin"],row["physical_envelope_pin"])
        wrong=copy.deepcopy(row["physical_envelope_pin"]);wrong["sha256"]="0"*64
        with self.assertRaises(ValueError):module.source.descriptor(row["semantic_original_pin"],wrong,next_case=161)
        with self.assertRaises(ValueError):module.source.descriptor(row["semantic_original_pin"],row["physical_envelope_pin"],next_case=162)

    def scope_fixture(self):
        module,_=self.graph();binding,required,manifest,row=self.fixture(module)
        representation=dict(semantic_source_freeze=list(required.values()),descriptors=[row])
        fresh=[dict(row["physical_envelope_pin"]),dict(row["semantic_original_pin"]),dict(manifest)]
        return representation,fresh,{manifest["path"]:manifest}

    def test_bulk_union_matches_previous_exact_scope_with_two_extends(self):
        representation,fresh,prep=self.scope_fixture();expected=scope.pins(representation["semantic_source_freeze"])
        reverse={r["physical_envelope_pin"]["path"]:r["semantic_original_pin"] for r in representation["descriptors"]}
        for pin in fresh:
            actual=reverse.get(pin["path"],pin);expected=scope.extend(expected,{actual["path"]:actual})
        expected=scope.extend(expected,prep)
        calls=[]
        def extend(left,right):calls.append((len(left),len(right)));return scope.extend(left,right)
        private=SimpleNamespace(pins=scope.pins,require=scope.require,extend=extend)
        before=copy.deepcopy((representation,fresh,prep))
        self.assertEqual(m.inherited_scope(private,representation,fresh,prep,lambda:None),expected)
        self.assertEqual(len(calls),2)
        self.assertEqual((representation,fresh,prep),before)

    def test_bulk_union_rejects_changed_physical_alias_or_ordinary_pin(self):
        for target in (0,2):
            representation,fresh,prep=self.scope_fixture();fresh[target]["sha256"]="0"*64
            with self.assertRaises(ValueError):m.inherited_scope(scope,representation,fresh,prep,lambda:None)

    def test_bulk_union_preserves_guard_stop(self):
        representation,fresh,prep=self.scope_fixture();error=ValueError("LIVE_GUARD_STOP")
        def stop():raise error
        with self.assertRaises(ValueError) as caught:m.inherited_scope(scope,representation,fresh,prep,stop)
        self.assertIs(caught.exception,error)

    def test_prepare_has_one_terminal_finish_after_manifest_pin_and_projection(self):
        tree=ast.parse((ROOT/m.SELF).read_text(encoding="utf-8"))
        prepare=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=="prepare")
        finishes=[node for node in ast.walk(prepare) if isinstance(node,ast.Call)
            and isinstance(node.func,ast.Attribute) and isinstance(node.func.value,ast.Name)
            and node.func.value.id=="q" and node.func.attr=="finish"]
        self.assertEqual(len(finishes),1)
        pins=[node for node in ast.walk(prepare) if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute)
            and node.func.attr=="pin" and node.args and isinstance(node.args[0],ast.Name) and node.args[0].id=="manifest_name"]
        projects=[node for node in ast.walk(prepare) if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute)
            and node.func.attr=="project"]
        self.assertEqual(len(pins),1);self.assertEqual(len(projects),1)
        self.assertGreater(finishes[0].lineno,pins[0].lineno)
        self.assertGreater(finishes[0].lineno,projects[0].lineno)


if __name__=="__main__":unittest.main()
