"""New build-to-list binding models; no binary or test-body launch."""
from pathlib import Path
import unittest
import native011_current_cohort_listing as listing


class ListingContracts(unittest.TestCase):
    def fixture(self):
        return dict(state='PASS_CURRENT805_BUILD_ONLY_NOT_LISTING_RUNTIME_OR_GATE',
            build_generation=2,build_exit_code=0,stderr_bytes=0,cleanup_confirmed=True,
            source_inventory_before_after=True,full805_current_source_bytes_verified=True,
            product_tests_executed=False,GO_authorized=False,accepted_count_delta=0,artifact_pin=dict(listing.EXE),
            fresh_inputs=843,final_fresh_hashes=843,build_proof=dict(catalog_profile=dict(
                opt_level='1',debuginfo='line-tables-only',debug_assertions=True,overflow_checks=True,test=True),
                validated_stream=dict(all_records_validated=True)))

    def test_exact_build_and_only_fixed_list_arguments(self):
        listing.build_contract(self.fixture());args=listing.list_arguments(Path('D:/example'))
        self.assertEqual(args[1:],['--list','--format=terse'])
        self.assertTrue(args[0].endswith('form_stored_provider-p361-native011-g002.exe'))

    def test_incomplete_or_runtime_or_old_generation_refused(self):
        for key,value in (('cleanup_confirmed',False),('final_fresh_hashes',842),
                          ('product_tests_executed',True),('build_generation',1),('stderr_bytes',1),
                          ('GO_authorized',True),('build_exit_code',False),('accepted_count_delta',False)):
            row=self.fixture();row[key]=value
            with self.assertRaisesRegex(ValueError,'EXACT_BUILD_ONLY_SOURCE_COHORT'):listing.build_contract(row)

    def test_compiler_profile_and_all_records_remain_required(self):
        row=self.fixture();row['build_proof']['catalog_profile']['overflow_checks']=False
        with self.assertRaisesRegex(ValueError,'ORIGINAL_PROFILE_AND_ALL_RECORDS'):listing.build_contract(row)
        row=self.fixture();row['build_proof']['validated_stream']['all_records_validated']=False
        with self.assertRaisesRegex(ValueError,'ORIGINAL_PROFILE_AND_ALL_RECORDS'):listing.build_contract(row)


if __name__=='__main__':unittest.main()
