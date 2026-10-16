"""Connect the current75 parent to the existing full lossless oracle.

Construction only: no metadata callback, Frame, Job, worker, GO or product.
The frozen constructor otherwise connects only the old whole oracle. Intercept
its one explicit oracle dependency to install the existing additional metadata/
Frame accounting check BEFORE the existing recovery-window connector. Retain
the original checker and all its scope, source, resource and window predicates.
"""
from types import SimpleNamespace as NS

SELF = 'tools/p09/native009_full75_dispatch_connection_v1.py'
TEST = 'tools/p09/tests/test_native009_full75_dispatch_connection_v1.py'


def require(ok, label):
    if not ok: raise ValueError('FULL75_DISPATCH_CONNECTION_'+label)


def oracle_loader(root, loader, configuration, metadata, a, oracle_pin):
    """One explicit private dependency; no default imports or hidden modules."""
    state = NS(loads=0, source_proofs=[], oracle=None)
    def load(actual_root, pins, reuse):
        if not any(pin['path'] == oracle_pin['path'] for pin in pins):
            return loader.load(actual_root, pins, reuse)
        require(actual_root == root and pins == [oracle_pin] and set(reuse) == {'current_queue_successor_connections'}
            and reuse['current_queue_successor_connections'] is metadata, 'EXACT_ORACLE_DEPENDENCY')
        require(state.loads == 0, 'ONE_ORACLE_CONNECTION_NO_RETRY')
        state.loads += 1
        observed = []
        def original_load(r, p, aliases):
            require(r == root and p == [oracle_pin] and set(aliases) == {'current_queue_successor_connections'}
                and aliases['current_queue_successor_connections'] is metadata and not observed, 'ONE_ORIGINAL_ORACLE_LOAD')
            value = loader.load(r, p, aliases); observed.append(value)
            return value
        proxy = NS(namespace_bundle=NS(**{**vars(loader), 'load': original_load}))
        oracle = configuration.oracle_namespace(root, proxy, metadata, a)
        require(len(observed) == 1 and observed[0][0].current_queue_successor_oracle is oracle, 'SAME_ORIGINAL_PRIVATE_ORACLE')
        state.oracle = oracle; state.source_proofs = observed[0][1]
        return observed[0]
    return NS(**{**vars(loader), 'load': load}), state


def verify_checker(checker, graph, configuration):
    """Inspect actual connected functions; do not fabricate a candidate PASS."""
    checked = checker.validate_candidate
    require(checker.environment['validate_candidate'] is checked and checked.__closure__ is not None,
        'SAME_PUBLIC_AND_FAMILY_FULL_CHECKER')
    cells = dict(zip(checked.__code__.co_freevars, (c.cell_contents for c in checked.__closure__)))
    require(set(cells) == {'a', 'binding', 'index', 'whole'} and cells['binding'] is graph.binding,
        'EXISTING_ADDITIONAL_ACCOUNTING_CHECKER')
    original = cells['whole']
    require(original.__globals__ is checker.environment and callable(original), 'WHOLE_ORIGINAL_PRIVATE_CHECKER_RETAINED')
    require(checked.__globals__['validate_accounting'] is configuration.validate_accounting,
        'EXISTING_FULL_METADATA_FRAME_ACCOUNTING_REQUIRED')
    require(checker.environment['prior'].WINDOW.SECONDS == 10, 'ORIGINAL_RECOVERY_WINDOW10')
    return dict(original_whole_checker_retained=True, existing_additional_lossless_accounting_connected=True,
        metadata_and_Frame_shared5_check_connected=True, original_recovery_window10_retained=True,
        actual_current_candidate_checked=False, actual_Native_or_product_or_acceptance_qualified=False)


def validate_metadata(proof, a):
    a.fields(proof, dict(state='PASS_FULL75_ACTUAL_PARENT_METADATA_AND_SHARED_DECODER_NOT_NATIVE_FRAME_OR_PRODUCT',
        semantic_inputs=3259, metadata_fresh_inputs=3263, metadata_final_fresh_hashes=3263,
        fresh_inputs=399, final_fresh_hashes=399, descriptor_count=75, all75_fresh_initial_and_final_decodes=True,
        previous_scope_and_budget_exactly_reconstructed=True, persisted_scope_uses_original_noninjecting_union=True,
        original_whole_parent_callback_executions=1, actual_product_or_Native_executed=False,
        actual_Native_Frame_created=False, subprocess_creation_attempts=0, cleanup_confirmed=True), 'EXACT_CURRENT_METADATA75')
    a.fields(proof['shared_decoder'], dict(shared_limit_seconds=5.0, metadata_registered=True, Frame_registered=False,
        metadata_completed=153, Frame_completed=0, terminal_error_seen=False), 'METADATA_ONLY_NOT_SHARED_NATIVE_PASS')
    require(proof['shared_decoder']['total_decoder_work_seconds'] <= 5.0, 'ORIGINAL_SHARED5')
    require(proof['additional_readiness_seconds_without_old_credit'] == 15, 'ADDITIONAL_READY15')
    return True
