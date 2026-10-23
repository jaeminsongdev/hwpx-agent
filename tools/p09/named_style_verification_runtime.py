"""Bounded entry to existing verified runtime functions; no recursion-limit or guard policy change."""
# Load the actual base once before optional observer modules. Do not chain new drivers to every past run.
import run_stored_note_kind_components as shared
import run_whitespace_patch_components as tools
import run_sql23_storage as closure
import run_named_paragraph_styles as observer
c,a=shared.c,shared.a
compact,harness,audit=closure.compact,closure.harness,closure.audit
snapshot=observer.snapshot
