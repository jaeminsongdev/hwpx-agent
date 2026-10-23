"""Eight memory contracts; no actual Native parent/Frame or scope application."""
import copy
from types import SimpleNamespace as NS
import unittest
import batch_verification as batch
import native011_scope_delta as delta
import native011_scope_map as mapping


def pin(name,number=1):return dict(path=name,bytes=number,sha256='a'*64)


class ScopeDeltaContracts(unittest.TestCase):
    def fixture(self):
        existing=pin('tools/p09/existing-control.py')
        cold=pin('implementation/p09/evidence/p09-361-case164-current-runtime-run001.v1.json')
        current={existing['path']:existing};history={cold['path']:cold};whole={**current,**history}
        owner=batch.Batch(whole,current,history,first_index=165,checkpoint=lambda:None)
        plan=NS(batch=owner,current=copy.deepcopy(current),history=copy.deepcopy(history),
            whole=copy.deepcopy(whole),logical=copy.deepcopy(whole))
        required=[existing]+[pin(name) for name in delta.ROLES]
        changes=delta.derive(required,current,whole)
        return plan,required,changes

    def test_exact_eight_roles_no_original_mutation(self):
        plan,required,changes=self.fixture();before=copy.deepcopy((plan.current,plan.whole,required))
        self.assertEqual(set(changes['additions']),set(delta.ROLES))
        self.assertEqual(len(changes['control_code_pins']),5);self.assertEqual(len(changes['control_data_pins']),3)
        self.assertFalse(changes['whole_native011_scope_qualified'])
        self.assertEqual((plan.current,plan.whole,required),before)

    def test_alias_is_not_raw_file_coverage(self):
        old=pin('implementation/p09/evidence/old.json');new=pin('implementation/p09/evidence/old.envelope.v1.json')
        representation=dict(semantic_source_freeze=[old],physical_source_freeze=[new],descriptors=[dict(
            schema_version='hwpx-agent.p09-lossless-runtime-source-projection/v1',next_case=165,
            semantic_original_pin=old,physical_envelope_pin=new)])
        result=mapping.compare([old],representation,prior_frame_count=1)
        self.assertEqual(result['counts']['PHYSICAL_ALIAS_ONLY_NOT_RAW_LOCK'],1)
        self.assertEqual(result['counts']['DIRECT_PIN_DECLARED'],0)
        self.assertFalse(result['live_parent_Frame_coverage_qualified'])

    def test_conflicting_same_path_never_direct_coverage(self):
        old=pin('implementation/p09/evidence/old.json');wrong=dict(old,bytes=2)
        new=pin('implementation/p09/evidence/alias.envelope.v1.json')
        representation=dict(semantic_source_freeze=[old],physical_source_freeze=[old],descriptors=[dict(
            schema_version='hwpx-agent.p09-lossless-runtime-source-projection/v1',next_case=165,
            semantic_original_pin=old,physical_envelope_pin=new)])
        result=mapping.compare([wrong],representation,prior_frame_count=1)
        self.assertEqual(result['counts']['PIN_CONFLICT'],1)

    def test_missing_role_or_extra_missing_input_rejected(self):
        plan,required,_=self.fixture()
        for bad in (required[:-1],required+[pin('tools/p09/undeclared-new-control.py')]):
            with self.assertRaisesRegex(ValueError,'ONLY_EIGHT_NAMED_MISSING_ROLES'):
                delta.derive(bad,plan.current,plan.logical)

    def test_actual_original_batch_constructor_retains_cold_partition(self):
        plan,required,changes=self.fixture();before=copy.deepcopy((plan.current,plan.whole,plan.history,plan.logical))
        result,proof=delta.extend_plan(plan,changes,required,batch,lambda:None)
        self.assertIs(type(result.batch),batch.Batch);self.assertIsNot(result.batch,plan.batch)
        self.assertEqual(result.history,plan.history);self.assertEqual(batch.plain(result.batch.history),plan.history)
        self.assertEqual(len(result.current),9);self.assertEqual(result.batch.phase,'NEW')
        self.assertEqual((plan.current,plan.whole,plan.history,plan.logical),before)
        self.assertEqual(proof['full_worker_pin_coverage'],9)
        self.assertFalse(proof['actual_Native_parent_or_Frame_constructed'])

    def test_started_batch_rejected_before_partition_change(self):
        plan,required,changes=self.fixture();plan.batch.phase='READY';before=copy.deepcopy(plan.current)
        with self.assertRaisesRegex(ValueError,'UNOPENED_ORIGINAL_BATCH_ONLY'):
            delta.extend_plan(plan,changes,required,batch,lambda:None)
        self.assertEqual(plan.current,before)

    def test_changed_delta_or_reapplication_rejected(self):
        plan,required,changes=self.fixture();changed=copy.deepcopy(changes)
        changed['additions'][delta.ROLES[0]]['bytes']=2
        with self.assertRaisesRegex(ValueError,'EXACT_REDERIVED_EIGHT_ROLE_DELTA'):
            delta.extend_plan(plan,changed,required,batch,lambda:None)
        result,_=delta.extend_plan(plan,changes,required,batch,lambda:None)
        with self.assertRaisesRegex(ValueError,'ONLY_EIGHT_NAMED_MISSING_ROLES'):
            delta.extend_plan(result,changes,required,batch,lambda:None)

    def test_prior_logical_role_cannot_be_reclassified_as_new(self):
        plan,required,_=self.fixture();logical=copy.deepcopy(plan.logical)
        logical[delta.ROLES[0]]=pin(delta.ROLES[0])
        with self.assertRaisesRegex(ValueError,'NEW_CONTROL_NOT_PRIOR_LOGICAL_RECLASSIFICATION'):
            delta.derive(required,plan.current,logical)


if __name__=='__main__':unittest.main()
