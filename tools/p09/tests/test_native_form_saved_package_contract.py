"""Actual SDK source/old-native files; synthetic protocol inverses are NOT native proof."""
import copy
from pathlib import Path
import unittest
from tools.p09 import verify_native_form_saved_package_contract as q


class NativeFormSavedPackageContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = q.fresh_cli('--source-self-check')
        cls.historical = q.fresh_cli('--historical')

    def test_real_complete_candidate_and_historical_stage_results_are_separate(self):
        q.validate_source(self.source); q.validate_historical(self.historical)
        self.assertEqual(len(self.source['cases']), 15)
        self.assertEqual(sum(len(row)-2 for row in self.historical['cases']), 30)
        self.assertFalse(self.source['native_acceptance_qualified'])
        self.assertFalse(self.historical['new_native_repair_or_p52_current_batch_qualified'])
        self.assertTrue(all(row['source_self_contract']['complete_state_exact'] for row in self.source['cases']))
        self.assertTrue(all(row[stage]['state'] == 'rejected' for row in self.historical['cases'] for stage in ('saved','reopened')))

    def test_source_protocol_rejects_inventory_substitution_native_claims_or_changed_hash(self):
        for key, value in (('cases', self.source['cases'][:1]), ('cases', list(reversed(self.source['cases']))),
            ('native_acceptance_qualified', True), ('green_rows', 1), ('p09_complete', True),
            ('manifest_sha256', '0'*64), ('native_session_started', 1)):
            changed = copy.deepcopy(self.source); changed[key] = value
            with self.assertRaises(ValueError): q.validate_source(changed)
        for key, value in (('package_sha256', '0'*64), ('complete_controls_exact', False),
            ('full_package_bindings_exact', 1), ('expected_state_sha256', '1'*64),
            ('render_or_differential_or_product_or_p09_gate_qualified', True)):
            changed = copy.deepcopy(self.source); changed['cases'][0]['source_self_contract'][key] = value
            with self.assertRaises(ValueError): q.validate_source(changed)
        changed = copy.deepcopy(self.source)
        changed['cases'][0]['source_self_contract']['expanded_parts']['xml_or_document_metadata_normalized'] = True
        with self.assertRaises(ValueError): q.validate_source(changed)

    def test_historical_original_source_bindings_and_native_failures_cannot_be_promoted(self):
        for key, value in (('cases', self.historical['cases'][:-1]), ('new_native_repair_or_p52_current_batch_qualified', True),
                          ('recovery_sha256', '0'*64), ('green_rows', 1)):
            changed = copy.deepcopy(self.historical); changed[key] = value
            with self.assertRaises(ValueError): q.validate_historical(changed)
        changed = copy.deepcopy(self.historical)
        changed['cases'][0]['actual_original_input_sha256'] = self.source['cases'][0]['source_self_contract']['package_sha256']
        # C01 is intentionally byte-exact; choose the genuinely coupled C03 source.
        changed['cases'][2]['actual_original_input_sha256'] = self.source['cases'][2]['source_self_contract']['package_sha256']
        with self.assertRaises(ValueError): q.validate_historical(changed)
        for stage in ('saved', 'reopened'):
            changed = copy.deepcopy(self.historical); changed['cases'][0][stage]['state'] = 'exact_package_contract_not_native_acceptance'
            with self.assertRaises(ValueError): q.validate_historical(changed)
        changed = copy.deepcopy(self.historical)
        changed['cases'][0]['saved']['complete_policy_binding'] = 'pass'
        with self.assertRaises(ValueError): q.validate_historical(changed)

    def test_current_dispatch_missing_is_not_run_without_fabricated_cases(self):
        value = q.current_observation()
        q.validate_not_run(value)
        self.assertEqual(value['actual_current_cases'], 0)
        self.assertFalse((q.ROOT/q.CURRENT_CAPSULE).exists())
        for key, changed_value in (('state', 'pass'), ('actual_current_cases', 15), ('green_rows', True), ('cases', [])):
            changed = value.copy(); changed[key] = changed_value
            with self.assertRaises(ValueError): q.validate_not_run(changed)

    def envelope(self):
        admitted = q.admission.admitted()
        value = {'schema_version': 'hwpx-agent.p09-52-native-form-binding-dispatch/v1',
            'state': 'all_fifteen_actual_attempts_terminal_non_green', 'prefix': q.admission.PREFIX,
            'admission_sha256': q.ADMISSION_SHA, 'source_sha256': admitted['source_sha256'],
            'harness_sha256': q.admission.HARNESS_SHA, 'binding_library_sha256': q.admission.LIBRARY_SHA,
            'permission_click_attestation': 'not_attested', 'computer_use_click_or_type_invoked': False,
            'claims': {'complete_fifteen_actual_diagnostic_attempts': True,
                'native_package_semantics_render_differential_or_product_qualified': False, 'green_rows': 0, 'p09_complete': False},
            'cases': [{'case_id': f'P09-35-C{i:02}'} for i in range(1,16)],
            'native_evidence_sha256': {f'synthetic-unit-only-{i}': 'a'*64 for i in range(15)}}
        return value, admitted

    def test_current_dispatch_envelope_rejects_subset_foreign_sources_or_native_promotions(self):
        value, admitted = self.envelope()
        q.validate_dispatch_envelope(value, admitted)  # Envelope only, NOT actual trace/evidence binding.
        for key, changed_value in (('prefix', 'p09-35-20261003-r05'), ('source_sha256', {}),
            ('admission_sha256', '0'*64), ('harness_sha256', '0'*64), ('cases', value['cases'][:1]),
            ('cases', list(reversed(value['cases']))), ('native_evidence_sha256', {}),
            ('computer_use_click_or_type_invoked', True)):
            changed = copy.deepcopy(value); changed[key] = changed_value
            with self.assertRaises(ValueError): q.validate_dispatch_envelope(changed, admitted)
        changed = copy.deepcopy(value); changed['claims']['p09_complete'] = True
        with self.assertRaises(ValueError): q.validate_dispatch_envelope(changed, admitted)

    def test_fixed_exclusive_evidence_paths_and_preserved_source_graph(self):
        before = q.preservation()
        self.assertEqual(len(before['all_seventy_five_original_native_sha256']), 75)
        self.assertFalse(before['predecessor_workflows_reexecuted_here'])
        self.assertEqual(q.evidence_path(q.ROOT/q.SOURCE_CAPSULE), q.ROOT/q.SOURCE_CAPSULE)
        for path in (Path(q.SOURCE_CAPSULE), q.ROOT/q.CURRENT_CAPSULE, q.ROOT/'other.json',
                     q.ROOT/'implementation/p09/evidence/../evidence'/Path(q.SOURCE_CAPSULE).name):
            with self.assertRaises(ValueError): q.evidence_path(path)
        self.assertEqual(q.preservation(), before)

    def test_synthetic_current_results_bind_every_saved_stage_without_native_promotion(self):
        # In-memory protocol fixture only; NEVER writes a dispatch, trace or native capsule.
        rows = q.admission.candidate.validate_manifest(q.admission.read_json(q.admission.candidate.MANIFEST, 524288))
        dispatch, _ = self.envelope()
        observed = {'schema_version': 'hwpx-agent.p09-53-saved-package-contract-current/v1', 'state': 'pass',
            'scope': 'actual_current_fifteen_bound_saved_package_checks_not_render_or_product',
            'actual_dispatch_sha256': 'a'*64, 'candidate_manifest_sha256': self.source['manifest_sha256'],
            'native_session_started': False, 'raw_document_values_or_private_paths_present': False,
            'native_identity_or_setter_or_rollback_qualified': False, 'render_or_differential_or_product_qualified': False,
            'green_rows': 0, 'p09_complete': False, 'cases': []}
        for row, source, record in zip(rows, self.source['cases'], dispatch['cases'], strict=True):
            record['artifacts'] = {f'{stage}.hwpx': {'sha256': row['package_sha256'], 'bytes': row['package_bytes'],
                'lifecycle_claim_bound': True, 'partial_unqualified_preserved': False} for stage in ('saved', 'reopened')}
            observed['cases'].append({'case_id': row['case_id'], 'actual_candidate_input_sha256': row['package_sha256'],
                'saved': copy.deepcopy(source['source_self_contract']), 'reopened': copy.deepcopy(source['source_self_contract'])})
        q.validate_current(observed, dispatch, 'a'*64)
        for key, value in (('green_rows', True), ('p09_complete', True), ('native_session_started', True),
                          ('render_or_differential_or_product_qualified', True), ('cases', observed['cases'][:1])):
            changed = copy.deepcopy(observed); changed[key] = value
            with self.assertRaises(ValueError): q.validate_current(changed, dispatch, 'a'*64)
        for stage in ('saved', 'reopened'):
            changed = copy.deepcopy(observed); changed['cases'][14][stage]['package_sha256'] = '0'*64
            with self.assertRaises(ValueError): q.validate_current(changed, dispatch, 'a'*64)
        unsaved = copy.deepcopy(dispatch); unsaved['cases'][0]['artifacts'] = {}
        with self.assertRaises(ValueError): q.validate_current(observed, unsaved, 'a'*64)
        changed = copy.deepcopy(observed)
        for stage in ('saved', 'reopened'):
            changed['cases'][0][stage] = {'state': 'not_run', 'reason': 'actual_native_stage_not_saved',
                'native_package_semantics_or_render_or_product_qualified': False}
        q.validate_current(changed, unsaved, 'a'*64)


if __name__ == '__main__':
    unittest.main()
