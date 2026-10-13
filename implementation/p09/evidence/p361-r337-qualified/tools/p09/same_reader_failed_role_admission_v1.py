"""Share only an exact failed-role declaration inside one private reader graph.

The existing once-reader primitive retains checkpoints, owner/ledger checks and
rejects final-phase reuse. No bytes, parsed receipt bodies or final hashes are
cached here. Installation never changes the published/default source module.
"""

SELF = "tools/p09/same_reader_failed_role_admission_v1.py"
TEST = "tools/p09/tests/test_same_reader_failed_role_admission_v1.py"


def require(ok, label):
    if not ok:
        raise ValueError("FAILED_ROLE_ONCE_" + label)


def connect(source, authority, once):
    require(type(getattr(source, "__name__", None)) is str and
            source.__name__.startswith("p09_exact_"), "PRIVATE_SOURCE_NAMESPACE")
    require(not hasattr(source, "failed_role_admission_once"), "ONE_INSTALLATION")
    original = source.admission
    require(callable(original) and callable(once.connect), "ORIGINAL_CALLABLES")
    names = ("read_exact", "fields", "exact")
    methods = tuple(getattr(authority, name) for name in names)
    require(all(callable(method) for method in methods), "EXACT_AUTHORITY_INTERFACE")

    def admit(reader):
        return original(reader, authority)

    execute, counts = once.connect(admit)

    def shared(reader, candidate_authority):
        require(candidate_authority is authority, "SAME_AUTHORITY_IDENTITY")
        require(all(getattr(authority, name) is method
                    for name, method in zip(names, methods)), "UNCHANGED_AUTHORITY_METHODS")
        return execute(reader)

    source.admission = shared
    proof = dict(actual_admissions=counts, original_admission=original,
                 same_private_source_namespace=True,
                 declaration_only_not_receipt_bytes=True,
                 final_fresh_hashes_or_reads_bypassed=False)
    source.failed_role_admission_once = proof
    return shared, proof
