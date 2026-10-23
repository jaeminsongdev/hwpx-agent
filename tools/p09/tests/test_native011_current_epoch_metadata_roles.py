"""New complete named metadata roles; no original transaction or product replay."""
from types import SimpleNamespace as NS
import unittest
import current_stored_runtime_scope as scope
import native011_current_epoch_scope as epoch
import native011_current_epoch_binding as binding


class RoleContracts(unittest.TestCase):
    def test_exact_ten_code_and_three_intrinsic_data_roles_no_observed_union(self):
        names=binding.metadata_control_names(scope,epoch)
        self.assertEqual(len(names),13)
        self.assertEqual(names,set(binding.METADATA_CODE)|{binding.FRESH['path'],epoch.BODY['path'],scope.LIST_PIN['path']})
        self.assertIn('tools/p09/native011_current_cohort_listing.py',names)
        self.assertIn('tools/p09/packed_receipt_json.py',names)
        self.assertNotIn('implementation/p09/evidence/unrelated-new-result.json',names)

    def test_unknown_helper_identity_cannot_expand_metadata_control_set(self):
        bad=NS(**{**vars(epoch),'SELF':'tools/p09/unrelated.py'})
        with self.assertRaisesRegex(ValueError,'FIXED_METADATA_HELPER_IDENTITIES'):
            binding.metadata_control_names(scope,bad)


if __name__=='__main__':unittest.main()
