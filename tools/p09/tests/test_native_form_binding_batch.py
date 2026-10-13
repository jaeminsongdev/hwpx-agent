"""Real candidate/source checks and synthetic negative binders; NEVER native proof."""
import ast
import copy
from pathlib import Path
import unittest
from tools.p09 import qualify_native_form_binding_batch as q
from tools.p09 import run_native_form_binding_batch as run


class NativeFormBindingBatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = q.candidate.validate_manifest(q.read_json(q.candidate.MANIFEST, 524288))
        cls.plan = q.read_json(q.candidate.MANIFEST.parent/cls.rows[0]['plan_file'], 262144)

    def failed_trace(self):
        value = dict.fromkeys(run.TRACE_KEYS)
        value.update(schema_version='hwpx-agent.p09-50-native-form-control-binding-target-trace/v1',
            state='effect_unknown', started_at_utc='2026-10-03T01:02:03.1234567Z',
            completed_at_utc='2026-10-03T01:02:04.1234567Z', target=copy.deepcopy(run.TARGET),
            input_sha256=self.rows[0]['package_sha256'], input_bytes=self.rows[0]['package_bytes'],
            security_module={'name': 'FilePathCheckerModuleExample',
                'sha256': '9ac5b97c47ac8aed1e8bca27a3eef39411361d8f68c262509f0c40a8f9d21bb6',
                'preflight_state': 'pass'}, sessions=[self.session('save', 10001)], quit_invoked=False,
            remaining_hwp_process_count=0, failed_phase='first_native_form_binding_and_application',
            error_code='P09_FORM_NATIVE_BINDING_FAILED', native_form_plan_sha256=self.rows[0]['plan_sha256'],
            native_form_binding_library_sha256=q.LIBRARY_SHA)
        value.update({key: False for key in run.FALSE_FIELDS})
        value.update({key: 'not_run' for key in run.LIFECYCLE})
        value['first_open'] = 'pass'
        return value

    def session(self, label, pid):
        return {'label': label, 'version': '11.0.0.9136', 'register_module_return': False,
            'process': {'process_id': pid, 'session_id': 1, 'executable_sha256': run.TARGET['executable_sha256'],
                        'command_line_sha256': 'a'*64}}

    def managed(self, verify):
        anchors = []
        counts = {'secd': 1}
        for control in self.plan['controls']:
            anchor = {**control['runtime_anchor_candidate'], 'Pos': 23}
            anchors.append({'ctrl_type': control['native_ctrl_type'], 'local_anchor': anchor.copy(),
                            'top_anchor': anchor.copy(), 'root_anchor': anchor.copy()})
            kind = control['native_ctrl_type']; counts[kind] = counts.get(kind, 0)+1
        return {'state': 'managed_property_check_pass_not_saved_package_qualification',
            'matched_controls': self.rows[0]['controls'], 'walked_controls': sum(counts.values()), 'verify_only': verify,
            'observed_control_type_counts': counts, 'observed_anchor_inventory': anchors,
            'binding_uses_collection_index_or_reservation_id': False, 'pos_inferred_from_xml': False,
            'unmanaged_runtime_parameters_checked': not verify, 'native_save_reopen_render_qualified': False,
            'p09_complete': False}

    def pass_trace(self):
        value = self.failed_trace()
        value.update(state='pass', quit_invoked=True, error_code=None, failed_phase=None,
                     sessions=[self.session('save', 10001), self.session('reopen', 10002)])
        value.update({key: 'pass' for key in run.LIFECYCLE})
        value.update({key: self.managed(i != 0) for i, key in enumerate(run.MANAGED)})
        artifacts = {}
        for name, (stem, _, _) in run.OUTPUTS.items():
            raw = b'%PDF-synthetic-unit-test-only' if name.endswith('.pdf') else b'synthetic-unit-test-only-not-HWPX'
            value[f'{stem}_sha256'], value[f'{stem}_bytes'] = q.sha(raw), len(raw)
            artifacts[name] = raw
        return value, artifacts

    def reject(self, value, code=2):
        with self.assertRaises(ValueError):
            run.bind_case(value, self.rows[0], self.plan, code)

    def test_complete_candidate_and_progress_graph_is_exact(self):
        value = q.inherited()
        inventory = value['complete_candidate_inventory']
        self.assertEqual((inventory['cases'], inventory['controls'], len(inventory['files'])), (15, 17, 31))
        self.assertEqual(inventory['candidate_and_plan_total_bytes'], 261216)
        self.assertEqual(value['p51_progress_sha256'], q.PROGRESS_SHA)
        self.assertFalse(value['predecessor_full_workflows_reexecuted_here'])

    def test_all_fifteen_fixed_cases_and_unused_paths_are_required(self):
        cases = q.case_plan(self.rows)
        self.assertEqual(len(cases), 15)
        self.assertEqual(sum(row['controls'] for row, *_ in cases), 17)
        self.assertEqual(len({case[3] for case in cases}), 15)
        for index, (row, source, plan, directory) in enumerate(cases, 1):
            self.assertEqual(row['case_id'], f'P09-35-C{index:02}')
            self.assertEqual(directory, q.run_directory(index))
            self.assertEqual(source.parent, q.candidate.MANIFEST.parent)
            self.assertEqual(plan.parent, source.parent)
            self.assertFalse(directory.exists())

    def test_case_subset_reordering_substitution_or_prior_prefix_is_rejected(self):
        altered = copy.deepcopy(self.rows); altered[0]['file'] = altered[1]['file']
        for rows in (self.rows[:1], self.rows[:-1], list(reversed(self.rows)), altered):
            with self.assertRaises(ValueError): q.case_plan(rows)
        with self.assertRaises(ValueError): q.case_plan(self.rows, 'p09-35-20261003-r05')
        for index in (True, 0, 16, '1'):
            with self.assertRaises(ValueError): q.run_directory(index)

    def test_probe_is_exact_line_normalized_pre_native_prefix_and_stops_before_run(self):
        self.assertTrue(q.prefix_inverse()['new_run_directory_and_native_body_excluded'])
        raw = q.candidate.bounded(q.ROOT/q.PROBE)
        self.assertNotIn(b'CreateDirectory($run)', raw)
        self.assertNotIn(b"$phase = 'first_session_create'", raw)
        self.assertTrue(raw.rstrip().endswith(b'exit 0'))
        self.assertIn(b'P09_52_EXACT_PRE_NATIVE_PREFIX_PASS', raw)

    def test_child_environment_changes_only_module_path_not_parent_or_policy(self):
        parent = {'PATH': 'unchanged', 'PSModulePath': 'parent', 'P09_TEST': 'kept'}
        child = q.environment.child_environment(parent)
        self.assertEqual(parent, {'PATH': 'unchanged', 'PSModulePath': 'parent', 'P09_TEST': 'kept'})
        self.assertEqual(child, {**parent, 'PSModulePath': ';'.join(q.environment.LEGACY_PATHS)})
        command = q.command_for(*q.case_plan(self.rows)[0])
        self.assertIn('-STA', command); self.assertNotIn('-ExecutionPolicy', command)
        self.assertNotIn('-NonInteractive', command)

    def test_fixed_receipt_boundaries_reject_alias_relative_or_traversal(self):
        self.assertEqual(q.fixed_path(q.ROOT/q.ADMISSION, 'admission'), q.ROOT/q.ADMISSION)
        for path in (Path(q.ADMISSION), q.ROOT/'other.json',
                     q.ROOT/'implementation/p09/evidence/../evidence'/Path(q.ADMISSION).name,
                     q.ROOT/q.DISPATCH):
            with self.assertRaises(ValueError): q.fixed_path(path, 'admission')

    def test_trace_rejects_foreign_target_input_plan_library_and_cleanup(self):
        base = self.failed_trace()
        for key, value in (('target', {**run.TARGET, 'build': 'other'}), ('input_sha256', 'b'*64),
            ('input_bytes', 1), ('native_form_plan_sha256', 'c'*64),
            ('native_form_binding_library_sha256', 'd'*64), ('remaining_hwp_process_count', 1),
            ('security_module', {})):
            changed = copy.deepcopy(base); changed[key] = value; self.reject(changed)

    def test_synthetic_failed_trace_stays_failed_without_inventing_saved_outputs(self):
        trace = self.failed_trace()
        result = run.bind_case(trace, self.rows[0], self.plan, 2)
        self.assertEqual((result['lifecycle'], result['managed_stages_passed']), ('fail', 0))
        self.assertFalse(result['native_package_semantics_render_or_product_qualified'])
        self.assertEqual(run.bind_artifacts(trace, {}), {})
        self.reject(trace, 0)
        changed = copy.deepcopy(trace); changed['state'] = 'pass'; self.reject(changed, 0)

    def test_synthetic_pass_trace_requires_all_lifecycle_and_managed_stages(self):
        trace, _ = self.pass_trace()
        result = run.bind_case(trace, self.rows[0], self.plan, 0)
        self.assertEqual((result['lifecycle'], result['managed_stages_passed']), ('pass', 4))
        self.assertFalse(result['native_package_semantics_render_or_product_qualified'])
        for key in run.LIFECYCLE+run.MANAGED:
            changed = copy.deepcopy(trace); changed[key] = 'not_run' if key in run.LIFECYCLE else None
            self.reject(changed, 0)
        changed = copy.deepcopy(trace)
        changed[run.MANAGED[0]]['observed_anchor_inventory'][0]['root_anchor']['Para'] += 1
        self.reject(changed, 0)

    def test_trace_rejects_coercion_native_promotions_missing_sessions_and_duplicate_pid(self):
        trace, _ = self.pass_trace()
        for key, value in (('input_bytes', str(trace['input_bytes'])), ('remaining_hwp_process_count', False),
            ('quit_invoked', 1), ('sessions', []), ('completed_at_utc', '2026-10-02T01:02:03.123Z')):
            changed = copy.deepcopy(trace); changed[key] = value; self.reject(changed, 0)
        for key in run.FALSE_FIELDS:
            changed = copy.deepcopy(trace); changed[key] = True; self.reject(changed, 0)
        changed = copy.deepcopy(trace); changed['sessions'][1]['process']['process_id'] = 10001
        self.reject(changed, 0)
        changed = copy.deepcopy(trace); changed['extra'] = True; self.reject(changed, 0)
        changed = copy.deepcopy(trace); changed[run.MANAGED[0]]['matched_controls'] = True
        self.reject(changed, 0)

    def test_artifact_hashes_sizes_claims_and_partial_files_are_bound(self):
        trace, files = self.pass_trace()
        self.assertEqual(len(run.bind_artifacts(trace, files)), 4)
        for name in files:
            changed = files.copy(); changed[name] += b'x'
            with self.assertRaises(ValueError): run.bind_artifacts(trace, changed)
            changed = files.copy(); del changed[name]
            with self.assertRaises(ValueError): run.bind_artifacts(trace, changed)
        partial = run.bind_artifacts(self.failed_trace(), {'saved.hwpx': b'partial-failed-unqualified'})
        self.assertTrue(partial['saved.hwpx']['partial_unqualified_preserved'])
        self.assertFalse(partial['saved.hwpx']['lifecycle_claim_bound'])

    def test_unknown_artifact_names_and_unclaimed_pass_outputs_are_rejected(self):
        with self.assertRaises(ValueError): run.bind_artifacts(self.failed_trace(), {'unexpected.txt': b'x'})
        trace, files = self.pass_trace()
        trace['output_sha256'] = trace['output_bytes'] = None
        with self.assertRaises(ValueError): run.bind_artifacts(trace, files)
        trace, files = self.pass_trace()
        files['saved.pdf'] = b'NOT-PDF'; trace['pdf_sha256'] = q.sha(files['saved.pdf']); trace['pdf_bytes'] = 7
        with self.assertRaises(ValueError): run.bind_artifacts(trace, files)

    def test_native_failure_inventory_is_bounded_and_never_contains_names_or_text(self):
        trace = self.failed_trace()
        trace['native_form_binding_failure'] = {'error_code': 'P09_FORM_NATIVE_UNDECLARED_FORM_TYPE',
            'rollback_state': 'not_needed', 'observed_control_type_counts': {'secd': 1, 'form': 1},
            'observed_anchor_inventory': [], 'raw_names_text_or_payload_present': False}
        self.assertEqual(run.bind_case(trace, self.rows[0], self.plan, 2)['lifecycle'], 'fail')
        for key, value in (('name', 'must-not-be-accepted'), ('observed_control_type_counts', {'secd': True}),
            ('raw_names_text_or_payload_present', True), ('rollback_state', 'pass')):
            changed = copy.deepcopy(trace); changed['native_form_binding_failure'][key] = value; self.reject(changed)

    def test_no_com_prefix_rejects_substituted_input_plan_and_library_hashes(self):
        results = q.actual_prefix_rejections()
        self.assertEqual(len(results), 3)
        self.assertTrue(all(r['exit_code'] == 1 and not r['native_session_started']
                            and not r['new_run_directory_created'] for r in results))

    def test_dispatcher_has_only_complete_run_no_selection_retry_kill_or_public_action(self):
        source = q.candidate.bounded(q.ROOT/'tools/p09/run_native_form_binding_batch.py').decode('utf-8')
        tree = ast.parse(source)
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)]
        names = [n.func.attr if isinstance(n.func, ast.Attribute) else n.func.id
                 for n in calls if isinstance(n.func, (ast.Name, ast.Attribute))]
        self.assertEqual(names.count('Popen'), 1)
        for forbidden in ('kill', 'terminate', 'unlink', 'rmtree', 'replace', 'system', 'eval', 'exec'):
            # String.replace is solely ISO timestamp parsing, not filesystem replacement.
            if forbidden != 'replace': self.assertNotIn(forbidden, names)
        self.assertIn('a.case_plan(rows)', source); self.assertIn('len(sys.argv) == 1', source)
        self.assertNotIn('a.qualify()', source); self.assertNotIn('timeout=', source)
        self.assertIn("with output.open('xb')", source)


if __name__ == '__main__':
    unittest.main()
