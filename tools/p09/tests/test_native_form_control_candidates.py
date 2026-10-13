"""Actual persisted complete candidates, independent plans and source-preservation guards."""
import copy
import json
import unittest
from tools.p09 import verify_native_form_control_candidates as q


class NativeFormControlCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=q.bounded(q.MANIFEST,512*1024)
        cls.manifest=json.loads(cls.raw,object_pairs_hook=q.prior.io.duplicate_guard)
        cls.old=q.originals()

    def test_all_fifteen_persisted_actual_sdk_candidates_and_seventeen_python_plans_are_exact(self):
        inspected=q.inspect_files()
        self.assertEqual(inspected['cases'],15);self.assertEqual(inspected['controls'],17)
        self.assertEqual(len(inspected['files']),31)
        self.assertTrue(inspected['sdk_and_independent_python_full_worker_plans_exact'])
        self.assertFalse(inspected['native_runtime_or_anchor_mapping_or_render_qualified'])

    def test_actual_fresh_rust_cli_reconstructs_all_candidates_and_checks_all_persisted_files(self):
        inspected=q.inspect_files();result=q.fresh_sdk(inspected)
        self.assertEqual(result['files'],31);self.assertFalse(result['native_session_started'])

    def test_manifest_rejects_inventory_substitution_coercion_extra_keys_and_native_promotions(self):
        mutations=[]
        for key,value in [('actual_hangul',True),('native_runtime_qualified',True),('green_rows',False),
                          ('raw_document_values_present',True),('signed_form_publication_or_p09_gate',True)]:
            v=copy.deepcopy(self.manifest);v[key]=value;mutations.append(v)
        v=copy.deepcopy(self.manifest);v['cases'].pop();mutations.append(v)
        v=copy.deepcopy(self.manifest);v['unexpected']='value';mutations.append(v)
        for key,value in [('file','../original.hwpx'),('controls',True),('plan_bytes','100'),
                          ('original_package_sha256','0'*64),('native_runtime_qualified',True),
                          ('package_sha256','0'*64),('complete_map',{}),('policy_sha256','0'*64)]:
            v=copy.deepcopy(self.manifest);v['cases'][0][key]=value;mutations.append(v)
        for changed in mutations:
            with self.assertRaises(ValueError):q.validate_manifest(changed)

    def test_sdk_worker_plan_rejects_any_name_tab_color_identity_coordinate_or_type_drift(self):
        row=self.manifest['cases'][0];raw=q.bounded(q.MANIFEST.parent/row['file'])
        actual=json.loads(q.bounded(q.MANIFEST.parent/row['plan_file']))
        for key,value in [('name','different'),('tab_order',1),('foreground_rgb',1),
                          ('native_identity_observation','reservation'),('native_ctrl_type','+rbt'),
                          ('run_ordinal',1),('shape_locked',0),('section_sha256','0'*64)]:
            changed=copy.deepcopy(actual);changed['controls'][0][key]=value
            with self.assertRaises(ValueError):q.verify_plan(self.old[0],row,raw,changed)
        changed=copy.deepcopy(actual);changed['controls'][0]['runtime_anchor_candidate']['Pos']=8
        with self.assertRaises(ValueError):q.verify_plan(self.old[0],row,raw,changed)
        with self.assertRaises(ValueError):q.verify_plan(self.old[0],row,raw+b'changed',actual)

    def test_fake_fresh_sdk_results_cannot_promote_native_partial_or_unbound_output(self):
        inspected=q.inspect_files()
        expected={'state':'pass','scope':'fresh_complete_sdk_candidates_and_plans','cases':15,'controls':17,'files':31,
            'manifest_sha256':inspected['manifest_sha256'],'native_session_started':False,'green_rows':0}
        self.assertEqual(q.verify_sdk_result(expected,inspected),expected)
        for key,value in [('cases',1),('controls',True),('files',30),('manifest_sha256','0'*64),
                          ('native_session_started',True),('green_rows',1)]:
            changed=copy.deepcopy(expected);changed[key]=value
            with self.assertRaises(ValueError):q.verify_sdk_result(changed,inspected)

    def test_original_frozen_sources_native_evidence_and_worker_library_remain_preserved(self):
        self.assertEqual(len(q.pins()),9)
        preserved=q.preservation()
        self.assertTrue(preserved['original_native_files_receipts_archives_and_harness_exact'])
        self.assertFalse(preserved['predecessor_full_workflows_reexecuted_here'])
        self.assertEqual(q.evidence_path(q.ROOT/q.CAPSULE),q.ROOT/q.CAPSULE)
        for path in (q.MANIFEST,q.ROOT/q.prior.CAPSULE,q.ROOT/'implementation/p09/evidence/private/result.json',
                     q.ROOT/'implementation/p09/evidence/../evidence/p09-51-native-form-control-candidates.progress.v1.json'):
            with self.assertRaises(ValueError):q.evidence_path(path)


if __name__=='__main__':unittest.main()
