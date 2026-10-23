"""New phase-latch and mechanical-construction extraction models only."""
import ast
import copy
import hashlib
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
import native011_metadata_epochs as epochs


class EpochContracts(unittest.TestCase):
    def fixture(self):
        created=[];identity=[(1,2)];context=NS(active=False)
        class Guard:
            def __init__(self):
                self.cleanup=False;self.fail=None;self.deadline=600
                self.samples=[];self.preparation_CPU=NS(summary=lambda:{'Native_policy_changed':False})
                self.preparation_limits={'one_logical_CPU':True}
            def acquire(self):pass
            def check(self,**kwargs):
                if self.fail:raise self.fail
            def close(self):self.cleanup=True
        def factory(role):created.append(Guard());return created[-1]
        def validate(ctx):
            if ctx.active:raise ValueError('MODEL_NATIVE_OR_METADATA_ACTIVE')
        e=epochs.Epochs(factory,validator=validate,identity=lambda:identity[0])
        return e,created,context,identity

    def test_four_exact_preparation_stages_and_original_guards(self):
        e,guards,ctx,_=self.fixture();e.advance('construction');e.bind(ctx)
        e.advance('opening');e.advance('metadata');e.advance('closing');e.close()
        self.assertEqual(len(guards),4);self.assertTrue(all(g.cleanup and g.deadline==600 for g in guards))
        self.assertEqual([r['stage'] for r in e.records],list(epochs.STAGES))
    def test_wrong_order_is_sticky_and_does_not_create_a_guard(self):
        e,guards,ctx,_=self.fixture()
        with self.assertRaises(ValueError):e.advance('closing')
        with self.assertRaises(ValueError):e.advance('construction')
        self.assertTrue(e.broken);self.assertEqual(guards,[])
    def test_resource_failure_never_rotates_to_a_fresh_guard(self):
        e,guards,ctx,_=self.fixture();e.advance('construction');e.bind(ctx)
        original=ValueError('ORIGINAL_RAM_STOP');guards[0].fail=original
        with self.assertRaises(ValueError) as caught:e.advance('opening')
        self.assertIs(caught.exception,original)
        with self.assertRaises(ValueError):e.advance('opening')
        self.assertEqual(len(guards),1);e.close();self.assertTrue(guards[0].cleanup)
    def test_native_or_live_metadata_state_refuses_rotation(self):
        e,guards,ctx,_=self.fixture();e.advance('construction');e.bind(ctx);ctx.active=True
        with self.assertRaisesRegex(ValueError,'MODEL_NATIVE_OR_METADATA_ACTIVE'):e.advance('opening')
        self.assertEqual(len(guards),1);e.close()
    def test_owner_change_stays_blocked_even_if_owner_changes_back(self):
        e,guards,ctx,owner=self.fixture();e.advance('construction');e.bind(ctx);owner[0]=(3,4)
        with self.assertRaises(ValueError):e.check()
        owner[0]=(1,2)
        with self.assertRaises(ValueError):e.advance('opening')
        e.close()
    def test_actual_context_is_bound_only_once_before_rotation(self):
        e,guards,ctx,_=self.fixture();e.advance('construction');e.bind(ctx)
        with self.assertRaises(ValueError):e.bind(ctx)
        self.assertTrue(e.broken);e.close()
    def test_closed_controller_cannot_restart(self):
        e,guards,ctx,_=self.fixture();e.advance('construction');e.close()
        with self.assertRaises(ValueError):e.advance('opening')
        self.assertEqual(len(guards),1)


class ExtractionContract(unittest.TestCase):
    def test_whole_qualified_construction_block_retained(self):
        root=Path(__file__).resolve().parents[3]
        archive=root/'implementation/p09/evidence/p09-native011-shared-parent-generation001-code/native011_parent_plan.py'
        raw=archive.read_bytes()
        self.assertEqual((len(raw),hashlib.sha256(raw).hexdigest()),(24042,'99a687ff82d9d120db3b833e3fcdb8c2b10cee01f50f6e573393cfb9c137a0b1'))
        old=next(n for n in ast.parse(raw).body if isinstance(n,ast.FunctionDef) and n.name=='main')
        attempt=next(n for n in old.body if isinstance(n,ast.Try))
        begin=next(i for i,n in enumerate(attempt.body) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call)
            and ast.unparse(n.value)=='q.pin(SELF)')
        end=next(i for i,n in enumerate(attempt.body) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call)
            and ast.unparse(n.value)=='q.finish()')
        reference=attempt.body[begin:end]
        actual=next(n for n in ast.parse((root/'tools/p09/native011_parent_plan.py').read_bytes()).body
            if isinstance(n,ast.FunctionDef) and n.name=='construct')
        class Undo(ast.NodeTransformer):
            def visit_Name(self,node):
                return ast.Attribute(value=ast.Name(id='c',ctx=ast.Load()),attr='ROOT',ctx=ast.Load()) if node.id=='root' else node
            def visit_Assign(self,node):
                if any(isinstance(t,ast.Attribute) and isinstance(t.value,ast.Name) and t.value.id=='context' for t in node.targets):return None
                if (isinstance(node.value,ast.Constant) and node.value.value is None
                    and all(isinstance(t,ast.Name) and t.id in ('shared_resources','oracle_result','bound') for t in node.targets)):return None
                if len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id=='oracle_result':
                    return ast.Expr(value=self.visit(node.value))
                return self.generic_visit(node)
            def visit_Return(self,node):
                return None if isinstance(node.value,ast.Name) and node.value.id=='context' else self.generic_visit(node)
        body=Undo().visit(copy.deepcopy(actual)).body
        body=[n for n in body if not (isinstance(n,ast.Expr) and isinstance(n.value,ast.Constant) and isinstance(n.value.value,str))]
        shape=lambda rows:ast.dump(ast.Module(body=rows,type_ignores=[]),include_attributes=False)
        self.assertEqual(shape(body),shape(reference))


if __name__=='__main__':unittest.main()
