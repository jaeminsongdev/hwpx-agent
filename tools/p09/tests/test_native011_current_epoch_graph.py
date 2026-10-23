"""Version adapter models retain original162 call-through, guards and identity."""
from types import SimpleNamespace as NS
import unittest
import current_stored_runtime_scope as scope
import native011_current_epoch_plan as plan
import native011_current_epoch_graph as adapter


def pin(name,value='a'):return dict(path=name,bytes=1,sha256=value*64)


class OriginalBinding:
    def __init__(self):
        self.next_case=165;self.manifest_pin=pin('manifest.json');self.calls=0
        self.rows=[dict(semantic_original_pin=pin(f'logical/d{i}.json'),physical_envelope_pin=pin(f'physical/d{i}.json','c')) for i in range(162)]
        self.originals={r['semantic_original_pin']['path']:r['semantic_original_pin'] for r in self.rows}
        self.physical={r['physical_envelope_pin']['path']:r['physical_envelope_pin'] for r in self.rows}
        self.reverse={r['physical_envelope_pin']['path']:r['semantic_original_pin']['path'] for r in self.rows}
    def descriptors(self):return self.rows
    def semantic_union(self,rows,check):
        check();self.calls+=1;result={}
        for name,p in rows.items():
            if name in self.reverse:
                if p!=self.physical[name]:raise ValueError('ORIGINAL_BAD_ALIAS')
                name=self.reverse[name];p=self.originals[name]
            if name in self.originals and p!=self.originals[name]:raise ValueError('ORIGINAL_BAD_SEMANTIC')
            result[name]=dict(p)
        if not set(self.originals)<=set(result):raise ValueError('ORIGINAL_MISSING162')
        return result,dict(original_called=True)
    def project(self,rows,check):return self.semantic_union(rows,check)


class GraphContracts(unittest.TestCase):
    def fixture(self):
        triples=[]
        for i in range(5):
            old=pin(f'crates/x/f{i}.rs');triples.append(dict(original_pin=old,
                current_pin=pin(old['path'],'b'),proposed_archive_pin=dict(old,path='archive/'+old['path'])))
        identity=NS(normalize=scope.pins,to_physical=scope.pins)
        versions=plan.Versions(identity,triples,scope,{r['original_pin']['path'] for r in triples})
        binding=OriginalBinding();rows=scope.extend(binding.originals,{binding.manifest_pin['path']:binding.manifest_pin})
        return binding,versions,triples,rows

    def test_same_instance_and_all_class_methods_retained_with_actual_original_call(self):
        binding,versions,triples,rows=self.fixture();before=dict(vars(type(binding)))
        proof=adapter.attach(binding,versions,scope,lambda:None)
        old=triples[0]['original_pin'];rows=scope.extend(rows,{old['path']:old})
        result,observed=binding.project(rows,lambda:None)
        archive=triples[0]['proposed_archive_pin'];self.assertEqual(result[archive['path']],archive)
        self.assertNotIn(old['path'],result);self.assertEqual(binding.calls,1)
        self.assertTrue(observed['original_called']);self.assertEqual(dict(vars(type(binding))),before)
        self.assertEqual(len(binding.descriptors()),162);self.assertTrue(proof['same_binding_instance_retained'])

    def test_original_missing162_and_bad_alias_errors_remain_failures(self):
        binding,versions,triples,rows=self.fixture();adapter.attach(binding,versions,scope,lambda:None)
        with self.assertRaisesRegex(ValueError,'ORIGINAL_MISSING162'):
            binding.semantic_union({triples[0]['current_pin']['path']:triples[0]['current_pin']},lambda:None)
        first=next(iter(binding.physical.values()));rows=scope.extend(rows,{first['path']:dict(first,bytes=2)})
        with self.assertRaisesRegex(ValueError,'ORIGINAL_BAD_ALIAS'):binding.semantic_union(rows,lambda:None)

    def test_unknown_third_version_and_second_adapter_are_rejected(self):
        binding,versions,triples,rows=self.fixture();adapter.attach(binding,versions,scope,lambda:None)
        with self.assertRaisesRegex(ValueError,'NO_PREVIOUS_INSTANCE_ADAPTER'):
            adapter.attach(binding,versions,scope,lambda:None)
        new=triples[0]['current_pin'];rows=scope.extend(rows,{new['path']:dict(new,bytes=2)})
        with self.assertRaisesRegex(ValueError,'NO_THIRD_SOURCE_VERSION_OR_HASH_REBASE'):
            binding.semantic_union(rows,lambda:None)
