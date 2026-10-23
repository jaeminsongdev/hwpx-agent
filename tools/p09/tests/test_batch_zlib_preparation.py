"""Preparation-only dependency selection; no Native or process qualification."""
import json
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch
import batch_zlib_preparation as module


class Base:
    def __init__(self):self.calls=0
    def close(self):self.calls+=1


class Tests(unittest.TestCase):
    def fixture(self):
        self.roles=[]
        def guard_type(original,*,role):
            self.roles.append(role)
            class Guard(original):
                def __init__(self):
                    super().__init__();self.preparation_CPU=NS(summary=lambda:dict(Native_policy_changed=False))
                    self.preparation_limits={'readback_verified':True}
            return Guard
        self.policy=NS(guard_type=guard_type)
        self.old=NS(guard_type=lambda cls:'old-warning',untouched=True)
        self.libs=NS(terminal_metadata_pressure_v1=self.old,other='same')
        self.loader=NS(load=lambda *args:(self.libs,'original-proof'))
        self.pins=[{'path':n} for n in module.GUARD_BOOTSTRAP]

    def test_only_first_exact_preparation_guard_bundle_is_selected(self):
        self.fixture();instances=[];loader=module.policy_loader(self.loader,self.policy,instances)
        actual,proof=loader.load(None,self.pins,{})
        self.assertEqual(proof,'original-proof');self.assertEqual(actual.other,'same')
        self.assertIsNot(actual.terminal_metadata_pressure_v1,self.old)
        self.assertIs(loader.load,self.loader.load)
        g=actual.terminal_metadata_pressure_v1.guard_type(Base)()
        self.assertEqual(self.roles,['dispatch_construction']);self.assertEqual(instances,[g])
        g.close();self.assertEqual(g.calls,1)
        again,_=loader.load(None,self.pins,{})
        self.assertIs(again.terminal_metadata_pressure_v1,self.old)
        self.assertEqual(self.old.guard_type(Base),'old-warning')

    def test_native_or_arbitrary_pressure_loads_remain_original(self):
        self.fixture();loader=module.policy_loader(self.loader,self.policy,[])
        actual,_=loader.load(None,[{'path':'tools/p09/terminal_metadata_pressure_v1.py'}],{})
        self.assertIs(actual,self.libs);self.assertEqual(self.roles,[])

    def parent(self):
        def original():return 'whole original body'
        self.fixture()
        return NS(main=original,bootstrap=lambda root:(self.loader,'entry','profile'),source_table=lambda *args:{})

    def test_complete_parent_main_code_and_original_namespace_retained(self):
        parent=self.parent();original=parent.main;selected=module.connect(parent,self.policy,{'closed':True})
        self.assertIs(selected.__code__,original.__code__)
        self.assertIs(selected.__closure__,original.__closure__)
        self.assertEqual(selected(),'whole original body')
        self.assertEqual(selected.__globals__['GRAPH'],module.GRAPH)
        self.assertNotIn('GRAPH',original.__globals__)

    def test_no_expected_policy_evidence_before_actual_guard_exists(self):
        parent=self.parent();selected=module.connect(parent,self.policy,{})
        with self.assertRaisesRegex(ValueError,'ONE_ACTUAL_PREPARATION_GUARD'):
            selected.__globals__['json'].dumps({'state':'not-executed'})

    def test_json_adds_measured_policy_without_relabelling_failure(self):
        parent=self.parent();selected=module.connect(parent,self.policy,{'closed':True})
        loader,_,_=selected.__globals__['bootstrap']('root')
        actual,_=loader.load(None,self.pins,{})
        actual.terminal_metadata_pressure_v1.guard_type(Base)()
        result=json.loads(selected.__globals__['json'].dumps({'state':'FAILED_ORIGINAL','GO_authorized':False}))
        self.assertEqual(result['state'],'FAILED_ORIGINAL');self.assertFalse(result['GO_authorized'])
        self.assertFalse(result['Native_policy_changed']);self.assertTrue(result['original_parent_main_code_unchanged'])

    def test_only_explicit_policy_sources_added_and_exact_pins_required(self):
        parent=self.parent();selected=module.connect(parent,self.policy,{})
        expected={p['path']:p for p in (module.POLICY,module.WITNESS,module.DESIGN,module.PROBE,module.CONNECTION,
            *module.READERS,module.READER_SOURCE)}
        def pin(name):return expected.get(name,dict(path=name,bytes=1,sha256='0'*64))
        scope=NS(extend=lambda a,b:{**a,**b})
        result=selected.__globals__['source_table'](None,NS(pin=pin),None,None,scope)
        self.assertEqual(set(result),set(module.EXTRA))
        with self.assertRaisesRegex(ValueError,'EXACT_POLICY_DECLARATION'):
            selected.__globals__['source_table'](None,NS(pin=lambda n:dict(pin(n),bytes=2)),None,None,scope)

    def test_native_product_and_worker_modes_rejected_before_imports(self):
        for flag in ('--native','--owned-worker','--task','--accept','--GO'):
            with patch.object(module.sys,'argv',['entry',flag]):
                with self.assertRaisesRegex(ValueError,'PREPARATION_ONLY_NO_NATIVE_OR_PRODUCT_MODE'):module.main()

    def test_reader_dependency_is_private_and_only_current_reader_is_measured(self):
        import accept_case112_current_epoch as original_a
        before=original_a.AcceptanceReader
        class Reader:
            def __init__(self,*args,**kwargs):pass
            def source_snapshot_diagnostics(self):return {'fresh':True}
        parent=self.parent()
        selected=module.connect(parent,self.policy,{},reader=Reader,chunk=NS(summary=lambda r:{'allocations':1}))
        api=selected.__builtins__['__import__']('accept_case112_current_epoch')
        self.assertIs(original_a.AcceptanceReader,before);self.assertIsNot(api.AcceptanceReader,before)
        api.AcceptanceReader('root',lambda:None)
        loader,_,_=selected.__globals__['bootstrap']('root');actual,_=loader.load(None,self.pins,{})
        actual.terminal_metadata_pressure_v1.guard_type(Base)()
        row=json.loads(selected.__globals__['json'].dumps({'state':'FAILED_ORIGINAL'}))
        self.assertEqual(row['state'],'FAILED_ORIGINAL')
        self.assertEqual(row['reader_optimization']['chunk']['allocations'],1)
        self.assertIs(original_a.AcceptanceReader,before)


if __name__=='__main__':unittest.main()
