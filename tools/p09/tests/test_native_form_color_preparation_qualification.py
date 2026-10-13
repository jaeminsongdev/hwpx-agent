import json
import unittest
from tools.p09 import qualify_native_form_color_preparation as q

class NativeFormColorQualificationGuards(unittest.TestCase):
    def test_frozen_local_receipt_and_original_sources_are_not_reclassified(self):
        raw,value=q.local_receipt()
        self.assertEqual(len(raw),20860);self.assertEqual(q.io.sha(raw),q.LOCAL_SHA)
        self.assertEqual(len(value['source_sha256']),16)
        self.assertFalse(value['claims']['whole_archived_source_successor_qualified'])
        self.assertFalse(value['claims']['native_color_fix_qualified'])
        self.assertEqual(len(q.pins()),23)

    def test_complete_current_graph_uses_live_color_roots_and_whole_original_graph(self):
        graph=q.current_graph();_,original,_=q.history.select()
        self.assertEqual(set(graph['source_sha256']),set(original)|set(q.SOURCES))
        for name in q.progress.CHANGED:
            self.assertNotEqual(graph['source_sha256'][name],original[name])
            self.assertEqual(graph['source_sha256'][name],q.io.sha(q.io.read(q.ROOT/name)))
        for name,digest in original.items():
            if name not in q.progress.CHANGED:self.assertEqual(graph['source_sha256'][name],digest)
        self.assertLessEqual(graph['files'],q.history.LIMIT_FILES)
        self.assertLessEqual(graph['bytes'],q.history.LIMIT_BYTES)

    def test_raw_archives_and_frozen_predecessor_receipts_remain_exact(self):
        _,local=q.local_receipt()
        self.assertEqual(q.progress.preserve(),local['preservation'])
        for name,(archive,digest,_) in q.progress.CHANGED.items():
            self.assertEqual(q.progress.inverse(name,q.io.read(q.ROOT/name)),digest)
            q.io.checked(q.ROOT/(q.progress.ARCHIVE+archive),digest)

    def test_guard_protocol_rejects_missing_duplicate_extra_filter_skip_or_failed_body(self):
        rows=[]
        for name in sorted(q.GUARDS):
            module='test_pre_native_form_color_reproduction' if name in {
                'test_authentic_complete_source_view_overrides_predecessor_with_original_p46_pins',
                'test_exact_original_cli_protocol_rejects_missing_extra_coerced_failure_and_duplicate',
                'test_short_source_boundary_rejects_workspace_root_other_parent_and_other_name',
                'test_original_launch_retains_installed_dependencies_without_environment_or_authority_override',
                'test_diagnostic_protocol_is_not_cli_success_and_rejects_duplicate_missing_or_exit_mismatch'} else 'test_native_form_color_preparation_qualification'
            owner='PreColorSourceReproductionTests' if module.startswith('test_pre_') else 'NativeFormColorQualificationGuards'
            rows.append(f'{name} (tools.p09.tests.{module}.{owner}.{name}) ... ok')
        text='\n'.join(rows)+'\n\nRan 11 tests in 1.000s\n\nOK\n'
        self.assertEqual(q.guard_protocol(0,b'',text.encode())['passed'],11)
        self.assertEqual(q.guard_protocol(0,b'',text.replace('\n','\r\n').encode())['passed'],11)
        for mutated in (text.replace(rows[0],'',1),text+rows[0],text.replace(' ... ok',' ... skipped',1),text.replace(' ... ok',' ... FAIL',1)):
            with self.assertRaises(ValueError):q.guard_protocol(0,b'',mutated.encode())
        with self.assertRaises(ValueError):q.guard_protocol(1,b'',text.encode())
        with self.assertRaises(ValueError):q.guard_protocol(0,b'other',text.encode())

    def test_exclusive_output_boundary_rejects_old_private_alias_and_traversal_paths(self):
        self.assertEqual(q.evidence_path(q.ROOT/q.CAPSULE),q.ROOT/q.CAPSULE)
        for path in (q.ROOT/q.progress.CAPSULE,q.ROOT/q.history.ORIGINAL,q.ROOT/'implementation/p09/evidence/private/result.json',
                     q.ROOT/'implementation/p09/evidence/../evidence/p09-48-native-form-color-preparation.source-qualified.v1.json'):
            with self.assertRaisesRegex(ValueError,'color_qualification_output_boundary'):q.evidence_path(path)

    def test_diagnostic_and_original_cli_claims_remain_distinct(self):
        self.assertIn('--verify',q.history.original_command())
        self.assertIn('diagnostic_only_original_p46_body_not_cli_qualification',q.history.DIAGNOSTIC_CODE)
        self.assertNotIn('diagnostic',q.history.EXPECTED)
        self.assertFalse(q.history.EXPECTED['native_session_started'])
        self.assertEqual(q.history.EXPECTED['green_rows'],0)
        with self.assertRaises(ValueError):q.history.protocol(0,json.dumps({'state':'pass','scope':'diagnostic_only_original_p46_body_not_cli_qualification'}).encode(),b'')

if __name__=='__main__':unittest.main()
