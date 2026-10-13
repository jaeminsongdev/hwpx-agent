"""Lossless candidate partition for bounded historical-preservation batching.

No file reads, Native calls, caches, worker/GO or acceptance authority. Matching
receipt names alone cannot authorize a reduced Native scope. The caller must
declare every current dependency and later qualify both batch byte boundaries.
All original pins remain in the full preservation scope, including failures.
"""
import re
import current_stored_runtime_scope as scope

SELF="tools/p09/historical_receipt_batch_partition_v1.py"
TEST="tools/p09/tests/test_historical_receipt_batch_partition_v1.py"
SCHEMA="hwpx-agent.p09-historical-receipt-batch-partition-candidate/v1"
PATTERNS=(
    ("runtime",re.compile(r"implementation/p09/evidence/p09-361-case([0-9]+)-current-runtime-run[0-9]{3}\.v1\.json")),
    ("acceptance",re.compile(r"implementation/p09/evidence/p09-361-case([0-9]+)-current-epoch-accept[0-9]{3}\.v1\.json")),
    ("per_case_data",re.compile(r"implementation/p09/evidence/p09-361-case([0-9]+)-.+-data[0-9]{3}\.v1\.json")),
)

def require(ok,code):
    if not ok:raise ValueError("HISTORICAL_BATCH_"+code)

def candidate(required,next_index,current_dependencies,checkpoint):
    require(type(required) is dict and type(next_index) is int and 115<=next_index<=249,"EXACT_INPUT_CONTEXT")
    require(type(current_dependencies) is tuple and current_dependencies
        and all(type(n) is str for n in current_dependencies)
        and current_dependencies==tuple(sorted(set(current_dependencies))),"EXPLICIT_CURRENT_DEPENDENCIES")
    require(callable(checkpoint),"ORIGINAL_CHECKPOINT_REQUIRED")
    checkpoint()
    rows=scope.pins(list(required.values()))
    require(rows==required and set(current_dependencies)<=set(rows),"COMPLETE_CURRENT_DEPENDENCIES_INSIDE_WHOLE")
    current=set(current_dependencies);hot={};batch={};categories={}
    for name in sorted(rows):
        checkpoint()
        category=None
        for kind,pattern in PATTERNS:
            match=pattern.fullmatch(name)
            if match and 1<=int(match[1])<next_index:
                category=kind;break
        if category is not None and name not in current:
            batch[name]=dict(rows[name]);categories[name]=category
        else:hot[name]=dict(rows[name])
    require(not (set(hot)&set(batch)) and set(hot)|set(batch)==set(rows),"LOSSLESS_DISJOINT_COMPLETE_PARTITION")
    require(all(({**hot,**batch})[n]==p for n,p in rows.items())
        and set(current_dependencies)<=set(hot),"EXACT_ORIGINAL_PINS_AND_CURRENT_DEPENDENCIES")
    checkpoint()
    return dict(schema_version=SCHEMA,state="CANDIDATE_NOT_NATIVE_OR_ACCEPTANCE_AUTHORIZED",
        next_index=next_index,current_dependencies=list(current_dependencies),
        per_case_candidate=[hot[n] for n in sorted(hot)],
        batch_preservation_candidate=[batch[n] for n in sorted(batch)],
        historical_categories=categories,full_preservation_scope=[rows[n] for n in sorted(rows)],
        original_pins_preserved=True,Native_scope_change_authorized=False,
        batch_initial_and_final_whole_bytes_required=True,
        batch_closing_actual=False,queue_advance_authorized=False,
        accepted_count_delta=0,PC_freeze_resolved=False)
