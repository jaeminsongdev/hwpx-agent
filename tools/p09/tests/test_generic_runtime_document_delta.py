import copy
import unittest
import sync_generic_runtime_document_delta as d


def fixture():
    return dict(schema_version=d.PREVIOUS_SCHEMA,state=d.PREVIOUS_PASS,document_revision=79,
        new_product_or_full_source_frame_executed=False,resource_stop_reason=None,
        resource_watcher_cleanup_confirmed=True,IO=dict(finished=True,bound_inputs=2,final_fresh_hashes=2),
        P09_gate='OPEN',A12_gate='OPEN',A13_gate='OPEN',product_complete=False,full249_current_qualified=False,
        whole1470_current_fresh_qualified=False,historical67_current_fresh_qualified=False,
        signed16_current_qualified=False,PC_freeze_resolved=False,
        bound_input_pins=[dict(path=p,bytes=1,sha256='0'*64) for p in d.ROOT_DOCS])


class DeltaTests(unittest.TestCase):
    def test_exact_owned_paths(self):
        self.assertEqual(d.paths(80,d.p.DIR+'/p215-generic-doc-sync-run01.v1.json',
            'implementation/p09/P09-216_GENERIC_RUNTIME_R0080_REPORT.md'),'implementation/p09/evidence/runtime-progress-r79/')
    def test_foreign_prior_path_rejected(self):
        with self.assertRaises(ValueError):d.paths(80,'../foreign','implementation/p09/P09-216_GENERIC_RUNTIME_R0080_REPORT.md')
    def test_wrong_report_revision_rejected(self):
        with self.assertRaises(ValueError):d.paths(80,d.p.DIR+'/p215-generic-doc-sync-run01.v1.json',
            'implementation/p09/P09-216_GENERIC_RUNTIME_R0081_REPORT.md')
    def test_prior_pins_without_mutation(self):
        doc=fixture();before=copy.deepcopy(doc);self.assertEqual(set(d.prior(doc,80)),set(d.ROOT_DOCS));self.assertEqual(doc,before)
    def test_prior_error_rejected(self):
        doc=fixture();doc['error_code']='FAILED';
        with self.assertRaises(ValueError):d.prior(doc,80)
    def test_prior_CPU_stop_rejected(self):
        doc=fixture();doc['resource_stop_reason']='STOP_SUSTAINED_SYSTEM_CPU'
        with self.assertRaises(ValueError):d.prior(doc,80)
    def test_duplicate_document_pin_rejected(self):
        doc=fixture();doc['bound_input_pins'].append(dict(doc['bound_input_pins'][0]))
        with self.assertRaises(ValueError):d.prior(doc,80)
    def test_prior_full_product_claim_rejected(self):
        doc=fixture();doc['product_complete']=True
        with self.assertRaises(ValueError):d.prior(doc,80)
