"""Constant-size terminal counters, including after a latched resource stop.

기존 reader의 완료 카운터만 확인한다. 파일 재읽기, sampler, 재시도 및
scope 축소를 수행하지 않으며 중단 결과를 준비 완료로 승격하지 않는다.
"""
SELF="tools/p09/preparation_terminal_progress_v1.py"
TEST="tools/p09/tests/test_preparation_terminal_progress_v1.py"
PHASES=frozenset(("admission","source_pins","controller_import","whole_binding",
    "final_freshness","checkpoint_export","completed"))

def summary(reader,phase):
    if type(phase) is not str or phase not in PHASES:
        raise ValueError("PREPARATION_PROGRESS_EXACT_PHASE")
    result=dict(phase=phase,reader_created=reader is not None,
        existing_completed_counters_only=True,additional_read_or_sample_or_retry=False,
        whole_scope_or_runtime_qualified=False)
    if reader is None:return result
    if type(reader.snapshots) is not dict:
        raise ValueError("PREPARATION_PROGRESS_SNAPSHOT_MAPPING")
    values=dict(bound_inputs=len(reader.snapshots),read_passes=reader.read_passes,
        bytes_read=reader.bytes_read,final_fresh_hashes=reader.final_fresh_hashes)
    if not all(type(v) is int and v>=0 for v in values.values()):
        raise ValueError("PREPARATION_PROGRESS_TYPED_COUNTERS")
    if values["final_fresh_hashes"]>values["bound_inputs"]:
        raise ValueError("PREPARATION_PROGRESS_FINAL_COUNT")
    result.update(values)
    return result
