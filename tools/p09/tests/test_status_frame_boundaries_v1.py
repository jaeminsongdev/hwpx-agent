"""Status-only batching equivalence; original pins validates every test member."""
import copy
import unittest

import current_stored_runtime_scope as scope
import status_frame_boundaries_v1 as tested


class Boundaries(unittest.TestCase):
    def setUp(self):
        self.documents = ["CURRENT_STATE.md", "implementation/p09/P09-361_SCAN_CANDIDATE_RETENTION.md"]
        self.frames = [[dict(path=f"fixtures/frame{i}/input{j}.json", bytes=j + 1,
                             sha256="a" * 64) for j in range(129)] for i in range(6)]
        self.calls = 0

    def checkpoint(self):
        self.calls += 1

    def inspect(self, frames=None, batch_size=64, checkpoint=None):
        return tested.inspect_frames(self.frames if frames is None else frames,
                                     self.documents, scope.pins,
                                     self.checkpoint if checkpoint is None else checkpoint,
                                     batch_size)

    def test_all_original_rows_and_bounded_maps(self):
        expected = set().union(*(set(scope.pins(rows)) for rows in self.frames))
        self.assertTrue(set(self.documents).isdisjoint(expected))
        result = self.inspect()
        self.assertEqual(result["frame_member_counts"], [129] * 6)
        self.assertEqual(result["all_frame_members_checked"], 774)
        self.assertEqual(result["maximum_temporary_pin_map"], 64)
        self.assertEqual(result["batches_checked"], 18)
        self.assertEqual(self.calls, 36)
        self.assertFalse(result["product_Native_or_queue_acceptance"])

    def test_documents_rejected_in_each_of_six_frames(self):
        for index in range(6):
            for document in self.documents:
                rows = copy.deepcopy(self.frames)
                rows[index][-1]["path"] = document
                with self.assertRaisesRegex(ValueError, "DOCUMENT_IN_FROZEN_FRAME"):
                    self.inspect(rows)

    def test_cross_batch_duplicate_rejected(self):
        rows = copy.deepcopy(self.frames)
        rows[5][-1] = dict(rows[5][0])
        with self.assertRaises(ValueError):
            scope.pins(rows[5])
        with self.assertRaisesRegex(ValueError, "CROSS_BATCH_DUPLICATE_PIN"):
            self.inspect(rows)

    def test_original_pin_predicates_reject_malformed_rows(self):
        mutations = [dict(path="../outside"), dict(bytes=True), dict(bytes=0),
                     dict(sha256="BAD"), dict(extra="unrecognized")]
        for mutation in mutations:
            rows = copy.deepcopy(self.frames)
            rows[3][-1].update(mutation)
            with self.assertRaises(ValueError):
                scope.pins(rows[3])
            with self.assertRaises(ValueError):
                self.inspect(rows)

    def test_whole_frame_bounds_retained(self):
        for count in (0, 4097):
            rows = copy.deepcopy(self.frames)
            rows[0] = [dict(path=f"fixtures/large/input{j}", bytes=1, sha256="a" * 64)
                       for j in range(count)]
            with self.assertRaises(ValueError):
                scope.pins(rows[0])
            with self.assertRaisesRegex(ValueError, "ORIGINAL_FRAME_COUNT"):
                self.inspect(rows)

    def test_batch_and_frame_set_must_remain_bounded(self):
        for value in (0, 65, True, 64.0):
            with self.assertRaises(ValueError):
                self.inspect(batch_size=value)
        with self.assertRaises(ValueError):
            self.inspect(self.frames[:5])

    def test_owner_stop_is_not_swallowed_or_retried(self):
        def stop():
            raise ValueError("STOP_METADATA_WARNING_BEFORE_COOLING_OR_RESUME")
        with self.assertRaisesRegex(ValueError, "STOP_METADATA_WARNING"):
            self.inspect(checkpoint=stop)


if __name__ == "__main__":
    unittest.main()
