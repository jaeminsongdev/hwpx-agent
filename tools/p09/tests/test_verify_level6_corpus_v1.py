import copy
import unittest
import verify_level6_corpus_v1 as module
import recompress_preparation_corpus_v1 as corpus


class Tests(unittest.TestCase):
    def setup_data(self):
        rows = [dict(schema_version="hwpx-agent.p09-lossless-runtime-source-projection/v1", next_case=165,
            semantic_original_pin=dict(path=f"implementation/p09/evidence/p09-361-case112-current-runtime-run{i:03}.v1.json", bytes=100, sha256="a"*64),
            physical_envelope_pin=dict(path=f"implementation/p09/evidence/p361-lossless-runtime-inputs/case112-runtime-run{i:03}.envelope.v1.json", bytes=50, sha256="b"*64)) for i in range(1,69)]
        batches = []
        for first in range(1,69,8):
            selected = rows[first-1:first+7]; samples = []
            for i, old in enumerate(selected, first):
                pin = dict(path=corpus.destination(old["physical_envelope_pin"]["path"]), bytes=40, sha256="c"*64)
                samples.append(dict(ordinal=i, baseline_descriptor=copy.deepcopy(old), level6_descriptor=corpus.new_descriptor(old,pin), bytes_saved=10))
            batches.append(dict(state=corpus.PASS, cleanup_confirmed=True, product_or_Native_executed=False,
                accepted_count_delta=0, original_or_existing_derivative_rewritten=False, first=first, count=len(selected),
                fresh_inputs=5, final_fresh_hashes=5, completed_samples=samples))
        return rows, batches

    def test_complete68(self):
        rows,batches=self.setup_data()
        self.assertEqual(len(module.coverage(rows,batches,corpus)),68)

    def test_gap_duplicate_and_out_of_order(self):
        for mutation in (lambda b:b.pop(1),lambda b:b.insert(1,copy.deepcopy(b[0])),lambda b:b.reverse()):
            rows,batches=self.setup_data(); mutation(batches)
            with self.assertRaises(ValueError): module.coverage(rows,batches,corpus)

    def test_failed_or_unfinished_batches(self):
        for key,value in (("state","FAILED"),("cleanup_confirmed",False),("final_fresh_hashes",4),("product_or_Native_executed",True)):
            rows,batches=self.setup_data(); batches[0][key]=value
            with self.assertRaises(ValueError): module.coverage(rows,batches,corpus)

    def test_changed_original_and_ordinal(self):
        for key,value in (("ordinal",True),("baseline_descriptor",{})):
            rows,batches=self.setup_data(); batches[0]["completed_samples"][0][key]=value
            with self.assertRaises(ValueError): module.coverage(rows,batches,corpus)

    def test_changed_semantic_or_destination(self):
        for key,value in (("next_case",166),("semantic_original_pin",{})):
            rows,batches=self.setup_data(); batches[0]["completed_samples"][0]["level6_descriptor"][key]=value
            with self.assertRaises(ValueError): module.coverage(rows,batches,corpus)

    def test_wrong_byte_statistics(self):
        rows,batches=self.setup_data(); batches[0]["completed_samples"][0]["bytes_saved"]=11
        with self.assertRaises(ValueError): module.coverage(rows,batches,corpus)
