"""Parent projection and NO-GO wiring contracts, not Native acceptance."""
import copy
from pathlib import Path
from types import SimpleNamespace as NS
import sys
import unittest
import batch_zlib_engine as module
import current_stored_runtime_scope as scope


def pin(name,digit='0'):return dict(path=name,bytes=1,sha256=digit*64)


class ProjectionContracts(unittest.TestCase):
    def fixture(self):
        before=[];after=[]
        for i in range(162):
            original=pin(f'implementation/p09/evidence/original-{i}.json')
            old=pin(f'implementation/p09/evidence/old-{i}.json','1')
            new=pin(f'implementation/p09/evidence/new-{i}.json','2')
            before.append(dict(semantic_original_pin=original,physical_envelope_pin=old))
            after.append(dict(semantic_original_pin=copy.deepcopy(original),physical_envelope_pin=new))
        reverse={r['physical_envelope_pin']['path']:r for r in before}
        def normalize(rows):
            result={}
            for name,value in scope.pins(rows).items():
                if name in reverse:
                    old=reverse[name]
                    module.require(value==old['physical_envelope_pin'],'TEST_EXACT_OLD_ALIAS')
                    value=old['semantic_original_pin'];name=value['path']
                module.require(name not in result or result[name]==value,'TEST_NO_ALIAS_CONFLICT')
                result[name]=dict(value)
            return result
        hot={r['physical_envelope_pin']['path']:r['physical_envelope_pin'] for r in before}
        exe=pin('target/original.exe');hot[exe['path']]=exe
        cold=pin('implementation/p09/evidence/p09-361-case100-current-runtime-run001.v1.json')
        history={cold['path']:cold};whole={**hot,**history}
        logical={r['semantic_original_pin']['path']:r['semantic_original_pin'] for r in before}
        logical.update({exe['path']:exe,**history})
        self.batch=NS(scope=scope,Batch=lambda *args,**kwargs:NS(args=args,kwargs=kwargs))
        self.data=NS(declared=NS(normalize=normalize),manifest=dict(descriptors=before),
            planned=NS(whole=copy.deepcopy(whole),current=copy.deepcopy(hot),history=copy.deepcopy(history),logical=copy.deepcopy(logical)))
        self.manifest=dict(descriptors=after);self.add=pin('tools/p09/new-explicit.py')

    def apply(self,additions=None):
        return module.project_plan(self.data,self.manifest,{self.add['path']:self.add} if additions is None else additions,
            self.batch,lambda:None)

    def test_all162_semantics_cold_set_and_ordinary_binary_preserved(self):
        self.fixture();prior=copy.deepcopy(self.data.planned.history);proof=self.apply()
        self.assertEqual(proof['physical_carriers_replaced'],162)
        self.assertEqual(self.data.planned.history,prior)
        self.assertEqual((len(self.data.planned.whole),len(self.data.planned.current)),(165,164))
        self.assertIn('target/original.exe',self.data.planned.current)
        self.assertFalse(any(n.startswith('implementation/p09/evidence/old-') for n in self.data.planned.whole))

    def test_changed_original_or_subset_rejected(self):
        for change in ('hash','subset'):
            self.fixture()
            if change=='hash':self.manifest['descriptors'][0]['semantic_original_pin']['sha256']='3'*64
            else:self.manifest['descriptors'].pop()
            with self.assertRaises(ValueError):self.apply()

    def test_old_and_new_exact_aliases_collapse_without_extra_scope(self):
        self.fixture();old=self.data.manifest['descriptors'][0]['physical_envelope_pin']
        new=self.manifest['descriptors'][0]['physical_envelope_pin']
        self.apply({old['path']:old,new['path']:new})
        self.assertEqual(len(self.data.planned.whole),164)

    def test_wrong_new_alias_hash_rejected(self):
        self.fixture();p=dict(self.manifest['descriptors'][0]['physical_envelope_pin'],sha256='3'*64)
        with self.assertRaisesRegex(ValueError,'EXACT_NEW_ALIAS'):self.apply({p['path']:p})

    def test_cold_carrier_cannot_be_silently_reclassified(self):
        self.fixture();p=self.data.manifest['descriptors'][0]['physical_envelope_pin']
        self.data.planned.history[p['path']]=self.data.planned.current.pop(p['path'])
        with self.assertRaisesRegex(ValueError,'PRESERVATION'):self.apply()

    def test_duplicate_new_carrier_rejected(self):
        self.fixture();self.manifest['descriptors'][1]['physical_envelope_pin']=copy.deepcopy(self.manifest['descriptors'][0]['physical_envelope_pin'])
        with self.assertRaisesRegex(ValueError,'BIJECTIVE'):self.apply()


class WiringContracts(unittest.TestCase):
    def test_diagnostic_factory_only_adds_no_go_and_zlib_flags(self):
        root=Path('D:/exact-root');task='case165-current-r010-tests';path='tools/p09/batch_worker_launch.py'
        command=[sys.executable,'-B',str(root/path),'--ready-handle','123','--task',task];seen=[]
        def original(root,pin,component,protocol,connection,factory,*args,**options):return factory(command,original_flags=True)
        launch=NS(connect=original,TASK=task);selected=module.diagnostic_launch(launch,task,path)
        factory=lambda command,**kwargs:seen.append((command,kwargs)) or 'owned'
        self.assertEqual(selected.connect(root,None,None,None,None,factory,None,None,None,None),'owned')
        self.assertEqual(seen,[([*command[:3],'--probe-no-go','--zlib',*command[3:]],{'original_flags':True})])
        self.assertIs(launch.connect,original)
        command[-1]='case165-current-r009-tests'
        with self.assertRaisesRegex(ValueError,'EXACT_DIAGNOSTIC_PARENT_COMMAND'):
            selected.connect(root,None,None,None,None,factory,None,None,None,None)

    def test_loader_changes_only_private_worker_launch_dependency(self):
        original=NS(launch_api=lambda *args:NS(connect=lambda:None),TASK='case165-current-r010-tests',SELF='worker.py')
        loader=NS(load=lambda *args:(NS(batch_worker_launch=original,other='unchanged'),'original-proof'))
        selected,proof=module.loader_for_parent(loader).load(None,None,None)
        self.assertEqual(proof,'original-proof');self.assertEqual(selected.other,'unchanged')
        self.assertIsNot(selected.batch_worker_launch,original)
        self.assertTrue(selected.batch_worker_launch.launch_api(None,None).zlib_diagnostic_only)


if __name__=='__main__':unittest.main()
