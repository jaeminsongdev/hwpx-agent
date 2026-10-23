"""Original Batch class plus synthetic declarations only; no original tests replay."""
import copy
from types import SimpleNamespace as NS
import unittest
import batch_verification as batch
import current_stored_runtime_scope as scope
import native011_current_epoch_plan as plan


def pin(name,value='a'):return dict(path=name,bytes=1,sha256=value*64)


class BatchPlanContracts(unittest.TestCase):
    def fixture(self):
        versions=[]
        for i in range(5):
            name=f'crates/x/f{i}.rs';old=pin(name);new=pin(name,'b')
            versions.append(dict(original_pin=old,current_pin=new,proposed_archive_pin=dict(old,path='archive/'+name)))
        descriptors=[dict(semantic_original_pin=pin(f'logical/d{i}.json'),
                          physical_envelope_pin=pin(f'physical/d{i}.json','c')) for i in range(162)]
        aliases={r['physical_envelope_pin']['path']:r for r in descriptors}
        carriers={r['semantic_original_pin']['path']:r['physical_envelope_pin'] for r in descriptors}
        def normalize(values):
            result={}
            for name,p in scope.pins(values).items():
                if name in aliases:
                    row=aliases[name];self.assertEqual(p,row['physical_envelope_pin']);p=row['semantic_original_pin'];name=p['path']
                if name in carriers:self.assertEqual(p,next(r['semantic_original_pin'] for r in descriptors if r['semantic_original_pin']['path']==name))
                result[name]=dict(p)
            return result
        def physical(values):return {carriers.get(n,p)['path']:dict(carriers.get(n,p)) for n,p in normalize(values).items()}
        current=scope.pins([r['original_pin'] for r in versions]+[r['physical_envelope_pin'] for r in descriptors])
        history=scope.pins([pin(f'implementation/p09/evidence/p09-361-case{i%164+1}-current-runtime-run{i//164+1:03}.v1.json') for i in range(419)])
        whole=scope.extend(current,history);logical=normalize(list(whole.values()))
        owner=batch.Batch(whole,current,history,first_index=165,checkpoint=lambda:None)
        planned=NS(batch=owner,whole=whole,current=current,history=history,logical=logical)
        data=NS(planned=planned,declared=NS(normalize=normalize,to_physical=physical),manifest=dict(descriptors=descriptors))
        required=scope.pins([r['current_pin'] for r in versions]+[r['proposed_archive_pin'] for r in versions]
            +[next(iter(history.values())),pin('metadata/current.json')])
        cohort=NS(required=required);controls=scope.pins([pin(plan.SELF),pin(plan.TEST)])
        return data,cohort,versions,controls,{r['original_pin']['path'] for r in versions}

    def apply(self,args):return plan.apply(*args[:4],batch,scope,args[4],lambda:None)

    def test_actual_batch_NEW_preserves419_and162_and_both_source_versions(self):
        args=self.fixture();data=args[0];before=copy.deepcopy(data.planned.whole)
        projected,proof,versions=self.apply(args)
        self.assertIs(type(projected.planned.batch),batch.Batch)
        self.assertEqual(projected.planned.batch.phase,'NEW')
        self.assertEqual(projected.planned.history,data.planned.history)
        self.assertEqual(proof['history_count'],419);self.assertEqual(proof['history_reclassified'],0)
        self.assertIs(projected.manifest,data.manifest);self.assertEqual(proof['exact_unchanged_descriptors'],162)
        self.assertEqual(data.planned.whole,before);self.assertIsNot(projected.planned.batch,data.planned.batch)
        for row in args[2]:
            for pin in (row['current_pin'],row['proposed_archive_pin']):self.assertEqual(projected.planned.current[pin['path']],pin)
        self.assertFalse(set(projected.planned.current)&set(projected.planned.history))
        self.assertEqual(projected.declared.to_physical(list(projected.planned.logical.values())),projected.planned.whole)

    def test_open_connected_or_active_batch_cannot_change_epoch(self):
        for field,value in (('phase','READY'),('parent_connection',object()),('active',object()),('metadata_reader_active',True)):
            args=self.fixture();setattr(args[0].planned.batch,field,value)
            with self.assertRaisesRegex(ValueError,'UNOPENED_UNCONNECTED_BATCH_ONLY'):self.apply(args)

    def test_history_pin_change_unknown_control_and_omitted_version_rejected(self):
        args=self.fixture();name=next(iter(args[0].planned.history));args[1].required[name]=dict(args[1].required[name],bytes=2)
        with self.assertRaisesRegex(ValueError,'NO_HISTORY_PIN_CHANGE_OR_RECLASSIFICATION'):self.apply(args)
        args=list(self.fixture());args[3]=dict(args[3],extra=pin('controls/unrelated.py'))
        with self.assertRaisesRegex(ValueError,'TWO_NAMED_PROJECTOR_CONTROLS'):self.apply(args)
        args=list(self.fixture());args[2]=args[2][:-1]
        with self.assertRaisesRegex(ValueError,'EXACT_FIVE_SOURCE_VERSIONS'):self.apply(args)


if __name__=='__main__':unittest.main()
