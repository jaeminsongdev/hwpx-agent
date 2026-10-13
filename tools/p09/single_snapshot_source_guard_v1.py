"""Opt-in metadata source predicates from one fresh no-follow stat.

For ordinary Windows non-reparse paths, one stat supplies regular-file, not-
symlink and not-junction predicates. Other reparse tags, missing/invalid Windows
fields or a stat failure use the exact original method; no cached stat/read/
hash/JSON and no original resource/open/parse/final-freshness guards are skipped.
This does not replace held-path Native guards or establish freeze causality.
"""
import hashlib
import os
import stat

import audit_evidence_io as original

SELF = "tools/p09/single_snapshot_source_guard_v1.py"
TEST = "tools/p09/tests/test_single_snapshot_source_guard_v1.py"
ORIGINAL_PIN = dict(path="tools/p09/audit_evidence_io.py", bytes=5653,
    sha256="84b7dae287ac01c7ec308ca302762ec283406fca3fa43bc469882a3913578a8f")
REPARSE = 0x400
DIRECTORY = 0x10
DEVICE = 0x40


def require(ok, code):
    if not ok:
        raise ValueError("SINGLE_SOURCE_STAT_" + code)


class Counters:
    def __init__(self):
        self.calls = self.attempts = self.normal = self.fallbacks = self.denied = 0

    def summary(self):
        return dict(source_requests=self.calls, fresh_no_follow_stat_attempts=self.attempts,
            ordinary_windows_snapshot_decisions=self.normal,
            exact_original_fallback_requests=self.fallbacks, ordinary_nonfile_rejections=self.denied,
            original_logical_source_predicates_retained=True,
            stat_result_cached_or_reused_between_source_requests=False,
            original_default_reader_mutated=False, held_Native_path_guard_replaced=False,
            extra_sampler_query_thread_or_process=False,
            complete_source_reads_rates_or_deadlines_reduced=False,
            actual_whole_Native_or_product_connection_qualified=False, PC_freeze_resolved=False)


def source(reader, name, original_source, counters, *, query=os.stat):
    counters.calls += 1
    path = reader.root / name
    counters.attempts += 1
    try:
        # lstat/no-follow is intentional. A reparse tag never takes this fast
        # path; fallback preserves the original follow/link/junction behavior.
        value = query(path, follow_symlinks=False)
    except OSError:
        counters.fallbacks += 1
        return original_source(name)
    attrs = getattr(value, "st_file_attributes", None)
    tag = getattr(value, "st_reparse_tag", None)
    mode = getattr(value, "st_mode", None)
    ordinary = (type(attrs) is int and 0 <= attrs <= 0xffffffff
        and type(tag) is int and tag == 0 and type(mode) is int and mode >= 0
        and not attrs & (REPARSE | DEVICE)
        and bool(attrs & DIRECTORY) == stat.S_ISDIR(mode))
    if not ordinary:
        counters.fallbacks += 1
        return original_source(name)
    counters.normal += 1
    regular = stat.S_ISREG(mode)
    if not regular:
        counters.denied += 1
    # Original conjunction: regular-file AND not-symlink AND not-junction.
    # No reparse bit/tag on an ordinary path proves the last two false. Unknown
    # kinds are never promoted to regular files merely because DIRECTORY is 0.
    original.require(regular, "sql_source_link_or_missing")
    return path


def reader_type(base, raw):
    require(type(raw) is bytes and len(raw) == ORIGINAL_PIN["bytes"]
        and hashlib.sha256(raw).hexdigest() == ORIGINAL_PIN["sha256"], "EXACT_ORIGINAL_SOURCE")
    require(isinstance(base, type) and original.AuditEvidenceReader in base.__mro__, "ORIGINAL_READER_ANCESTOR")
    require(base._source is original.AuditEvidenceReader._source, "UNCHANGED_ORIGINAL_SOURCE_METHOD")

    class SnapshotReader(base):
        def __init__(self, *args, **kw):
            super().__init__(*args, **kw)
            self._single_snapshot_source_counters = Counters()

        def _source(self, name):
            return source(self, name, super()._source, self._single_snapshot_source_counters)

        def source_snapshot_diagnostics(self):
            return self._single_snapshot_source_counters.summary()

    return SnapshotReader, dict(only_source_predicate_query_implementation_changed=True,
        original_source_predicate_conjunction_retained=True,
        other_reparse_missing_invalid_or_error_cases_use_exact_original=True,
        unchanged_original_MRO_after_one_wrapper=True,
        original_read_checkpoints_open_pacing_hashes_and_freshness_replaced=False,
        ordinary_path_snapshot_cannot_prove_later_open_identity=True,
        original_time_of_check_to_open_race_not_claimed_eliminated=True,
        runtime_or_freeze_resolution_qualified=False)
