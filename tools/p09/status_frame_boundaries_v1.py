"""Bounded status-only doc-boundary checks; no runtime oracle replacement.

Keep original pin predicates and cross-batch duplicate rejection for every row.
Recheck the owner's existing guard around each batch. No file/JSON/hash cache,
new sampler, changed limits, skipped frame/member, or queue authority change.
"""


def require(ok, code):
    if not ok:
        raise ValueError("STATUS_FRAME_BOUNDARY_" + code)


def inspect_frames(frames, documents, pins, checkpoint, batch_size=64):
    require(type(frames) is list and len(frames) == 6, "ALL_SIX_FRAMES")
    require(type(documents) is list and len(documents) == 2
            and all(type(x) is str and x for x in documents)
            and len(set(documents)) == 2, "BOTH_DOCUMENTS")
    require(type(batch_size) is int and 1 <= batch_size <= 64, "BOUNDED_BATCH")
    require(callable(pins) and callable(checkpoint), "ORIGINAL_CALLBACKS")
    counts, checks, largest = [], 0, 0
    for rows in frames:
        require(type(rows) is list and 0 < len(rows) <= 4096, "ORIGINAL_FRAME_COUNT")
        seen = set()
        for start in range(0, len(rows), batch_size):
            checkpoint()
            chunk = rows[start:start + batch_size]
            current = pins(chunk)  # Exact original path/shape/type/hash predicates.
            require(type(current) is dict and len(current) == len(chunk), "ORIGINAL_BATCH_COUNT")
            require(seen.isdisjoint(current), "CROSS_BATCH_DUPLICATE_PIN")
            require(not any(name in current for name in documents), "DOCUMENT_IN_FROZEN_FRAME")
            seen.update(current)
            largest = max(largest, len(current))
            checks += 1
            checkpoint()
        require(len(seen) == len(rows), "ALL_MEMBERS_CHECKED")
        counts.append(len(seen))
    return dict(frames_checked=6, documents_checked=2, frame_member_counts=counts,
                all_frame_members_checked=sum(counts), batches_checked=checks,
                maximum_temporary_pin_map=largest, original_pin_predicates_retained=True,
                cross_batch_duplicate_rejection_retained=True,
                existing_owner_guard_checked_between_batches=True,
                whole_frame_pin_maps_or_union_materialized=False,
                file_JSON_or_hash_cache=False, new_sampler_or_guard_relaxation=False,
                product_Native_or_queue_acceptance=False)
