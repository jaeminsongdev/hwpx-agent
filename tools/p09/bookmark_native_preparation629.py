"""Read-only prepared-eight boundary. No Native launcher, admission or saved permit.

The prepared files contain NEW fields. This is not the consumed SDK-insertion
batch and cannot issue its live handoff. Current lifecycle and effect evidence
must still be obtained by a separately verified/authorized execution entry.
"""
from pathlib import Path
import sys

import crossref_external_host_inspection as inspection
import crossref_runtime004_admission as runtime

SELF = 'tools/p09/bookmark_native_preparation629.py'
PREPARED = 'implementation/p09/evidence/p09-361-stored-bookmark-insertion628-prepared-batch.v1.json'
PRIOR = 'implementation/p09/evidence/p09-361-stored-bookmark-insertion628-audit002.v1.json'
PRIOR_SHA = 'fea499f9da6db8d6f345d4a1542f0f1f5773abf8dc5f9060f4e8dd453a48a99a'
DIRECTORY = 'implementation/p09/evidence/private/p09-361-bookmark-insertion628-prepared-001'
SOURCE = 'implementation/p09/evidence/private/p09-361-crossref-discovery-inputs-20261017-r01/source-with-bookmark.hwpx'
SOURCE_PIN = dict(path=SOURCE, bytes=14425, sha256='64539a2dc6e76f0301c8beba20cf24083810fdf571f1f5dabbbf2764cd1ee184')
DISPLAYS = ('page', 'bookmark_name', 'content', 'relative_position')


def require(ok, code):
    if not ok:
        raise ValueError('P629_' + code)


def loaded_dependencies(root):
    root = Path(root)
    paths = set()
    for module in tuple(sys.modules.values()):
        name = getattr(module, '__file__', None)
        if name:
            path = Path(name).absolute()
            if path.is_relative_to(root / 'tools/p09') and path.suffix == '.py':
                paths.add(path.relative_to(root).as_posix())
    return paths


def require_absent(root, name):
    path = Path(root) / name
    for parent in path.parent.parents:
        require(parent.is_dir() and not parent.is_symlink() and not parent.is_junction(), 'DIRECT_OUTPUT_ANCESTORS')
    require(path.parent.is_dir() and not path.parent.is_symlink() and not path.parent.is_junction(), 'DIRECT_OUTPUT_PARENT')
    require(not path.exists() and not path.is_symlink() and not path.is_junction(), 'IMMUTABLE_OUTPUT_NO_REPLAY')


def validate_prepared(reader, unpack):
    """Bind actual files to the immutable stored-source receipt, never to JSON claims alone."""
    prepared = reader.json(PREPARED)
    require(prepared['schema'] == 'hwpx-agent.private.bookmark-insertion-prepared-batch/v1'
            and prepared['state'] == 'EIGHT_PRIVATE_CANDIDATE_COPIES_PREPARED_NOT_NATIVE_ENTRY_READY_OR_EXECUTION_AUTHORITY',
            'EXACT_PREPARED_SCHEMA')
    require(prepared['source_receipt'] == dict(path=PRIOR, sha256=PRIOR_SHA)
            and prepared['source'] == SOURCE_PIN, 'EXACT_PRIOR_AND_SOURCE')
    for key in ('native_execution_authorized', 'native_entry_ready', 'actual_native_executed',
                'automatic_execution_or_retry', 'reuse_consumed_001_to010_or_Native008_to011',
                'initial_display_text_is_computed_or_refreshed',
                'operating_SQL_scanner_key_custody_or_product_route_qualified',
                'private_files_are_user_revisions_or_result_ingestion'):
        require(prepared[key] is False, 'PREPARED_IS_NOT_AUTHORITY')
    require(prepared['P09_gate'] == 'OPEN', 'OPEN_GATE')
    prior = unpack(reader.json(PRIOR))
    require(reader.snapshots[PRIOR]['sha256'] == PRIOR_SHA
            and prior['state'] == 'PASS628_CURRENT_STORED_INSERTION8_AND_PRIVATE_OUTPUT8_NOT_CAS_NATIVE_OR_ROUTE'
            and prior['cleanup'] is True and type(prior['fresh_inputs']) is int
            and prior['fresh_inputs'] == prior['final_fresh_hashes'] == 930,
            'EXACT_STORED_SOURCE_RECEIPT_NOT_NATIVE')
    observed = prior['actual_current_stored_observation']['observations']
    require(type(prepared['cases']) is list and type(observed) is list
            and len(prepared['cases']) == len(observed) == 8, 'WHOLE_EIGHT_NO_SUBSET')
    require(reader.pin(SOURCE) == SOURCE_PIN, 'CURRENT_ORIGINAL_SOURCE')
    rows = []
    for index, (case, actual) in enumerate(zip(prepared['cases'], observed), 1):
        require(type(case['case_index']) is int and case['case_index'] == index
                and type(actual['case_index']) is int and actual['case_index'] == index
                and case['display'] == DISPLAYS[(index - 1) // 2]
                and type(case['hyperlink']) is bool and case['hyperlink'] is (index % 2 == 0),
                'EXACT_CASE_ORDER_AND_TYPED_MODES')
        output = case['output']
        require(output == actual['output'] and output['path'] == DIRECTORY + f'/case-{index:02}.hwpx'
                and type(output['bytes']) is int and 0 < output['bytes'] <= 65536
                and output['sha256'] == case['output_sha256']
                and bytes(actual['receipt']['output']['command_sha256']).hex() == case['command_sha256'],
                'EXACT_CURRENT_PRODUCT_OUTPUT')
        require(reader.pin(output['path']) == output, 'CURRENT_PREPARED_FILE_BYTES')
        rows.append(dict(case_index=index, display=case['display'], hyperlink=case['hyperlink'], output=output))
    return dict(cases=rows, source=SOURCE_PIN, actual_file_count=8,
                prior_is_stored_candidate_not_operating_route=True, native_entry_ready=False,
                initial_result_evaluated=False, native_execution_authorized=False)


def inspect_current(windows, checkpoint, fresh_native_pin, current_runtime):
    """Only current kernel observations and EMPTY jobs, using qualified current Python images."""
    checkpoint()
    current_runtime()  # Qualified two-image profile, not historic single-image hash.
    before = inspection.current_identity(windows)
    prerequisites = inspection.prerequisites.inspect(windows, checkpoint, fresh_native_pin)
    layout = None
    if prerequisites['all_observed_prerequisites_passed']:
        inspection.prerequisites.startup.parent_without_prompt_kill(windows)
        layout = inspection.empty_resource_layout(windows, checkpoint, fresh_native_pin)
    checkpoint()
    require(inspection.current_identity(windows) == before, 'SAME_KERNEL_CREATOR')
    current_runtime()
    if layout is not None:
        inspection.prerequisites.startup.parent_without_prompt_kill(windows)
    return dict(prerequisites=prerequisites, empty_resource_layout=layout,
                external_jobless_prerequisites_observed=prerequisites['all_observed_prerequisites_passed'],
                process_created=False, COM_activated=False, document_opened_or_saved=False,
                permission_dialog_requested=False, native_startup_qualified=False,
                native_execution_authorized=False, native_entry_ready=False,
                future_execution_requires_current_lifecycle_and_own_verified_entry=True)


def safe_code(error):
    import re
    value = error.args[0] if error.args else None
    return value if type(value) is str and re.fullmatch('[A-Z][A-Z0-9_]{1,159}', value) else 'P629_FAILURE_NO_RAW_VALUES'
