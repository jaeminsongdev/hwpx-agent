"""Diagnostic workload shape only, not actual decode or Native evidence."""
import unittest
import probe_batch_decoder_budget as module


class WorkloadContracts(unittest.TestCase):
    def fixture(self):
        return [dict(semantic_original_pin=dict(path='semantic'+str(n)),
            physical_envelope_pin=dict(path='carrier'+str(n))) for n in range(162)]

    def test_all162_two_passes_in_each_role(self):
        descriptors=self.fixture();tasks=module.workload(descriptors)
        self.assertEqual(len(tasks),648)
        for role in ('metadata','frame'):
            for number in (1,2):
                self.assertEqual([d for r,p,d in tasks if (r,p)==(role,number)],descriptors)

    def test_subset_and_empty_rejected(self):
        for descriptors in ([],self.fixture()[:-1]):
            with self.assertRaisesRegex(ValueError,'EXACT_UNIQUE162'):module.workload(descriptors)

    def test_duplicate_semantic_rejected(self):
        descriptors=self.fixture();descriptors[-1]['semantic_original_pin']=descriptors[0]['semantic_original_pin']
        with self.assertRaisesRegex(ValueError,'EXACT_UNIQUE162'):module.workload(descriptors)

    def test_duplicate_physical_rejected(self):
        descriptors=self.fixture();descriptors[-1]['physical_envelope_pin']=descriptors[0]['physical_envelope_pin']
        with self.assertRaisesRegex(ValueError,'EXACT_UNIQUE162'):module.workload(descriptors)


if __name__=='__main__':unittest.main()
