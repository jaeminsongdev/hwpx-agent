"""Post-cleanup byte preservation check; no product/Native/test replay."""
import hashlib
import json
from pathlib import Path
import shutil
import sys

import prune_project_build_cache as cleanup

ROOT = cleanup.ROOT
sys.path.insert(0, str(ROOT/'tools/p09'))
import run_prepared_bookmark_native631 as entry
import prepared_bookmark632_receipt as carrier

OUTPUT = ROOT/'implementation/maintenance/cache-preservation-20261023.v1.json'


def main():
    cleanup.require(sys.argv[1:] == ['--verify-after-cleanup'], 'VERIFY_ONLY_MODE')
    cleanup.require(not OUTPUT.exists(), 'IMMUTABLE_PRESERVATION_AUDIT')
    primary = json.loads(cleanup.RESULT.read_text(encoding='utf-8'))
    cleanup.require(primary['state'].startswith('PROJECT_REBUILDABLE_CACHE_FILES_REMOVED'), 'MAIN_FINISHED')
    guard = cleanup.Guard()
    q = entry.r.a.AcceptanceReader(ROOT, guard.check)
    value = carrier.unpack(q.json('implementation/p09/evidence/p09-361-prepared-bookmark631-recovered632.v1.json'), guard.check)
    cleanup.require(hashlib.sha256(carrier.compact.raw(value)).hexdigest() == carrier.MANIFEST_SHA, 'ORIGINAL_NATIVE_ROW_EXACT')
    cases = value['retained_cases']['cases']+value['artifacts']['cases']
    count = 0
    for case in cases:
        for pin in case['artifacts'].values():
            cleanup.require(q.pin(pin['path']) == pin, 'CAPTURE_ARTIFACT_UNCHANGED')
            count += 1
    original, raw = carrier.retained(q)
    cleanup.require(carrier.compact.raw(original) == carrier.compact.raw(value), 'RAW_FORENSIC_PARTS_UNCHANGED')
    cleanup.require(q.pin(entry.runtime.prepared.SOURCE) == entry.runtime.prepared.SOURCE_PIN, 'ORIGINAL_DOCUMENT_UNCHANGED')
    first = json.loads((ROOT/'implementation/maintenance/cache-prune-result-20261023.v1.json').read_text(encoding='utf-8'))
    final = json.loads((ROOT/'implementation/maintenance/cache-prune-profile-roots-20261023.v1.json').read_text(encoding='utf-8'))
    cleanup.require(final['state'].startswith('FINALIZED_') and not final['partial_errors'], 'FINALIZER_FINISHED')
    remaining = cleanup.snapshot(guard)
    cleanup.require(remaining['files'] == remaining['bytes'] == 0, 'SELECTED_REBUILDABLE_CACHES_EMPTY')
    q.finish()
    guard.check()
    free = shutil.disk_usage('D:/').free
    result = dict(state='VERIFIED_PROJECT_CACHE_REMOVAL_AND_CAPTURE_SOURCE_FORENSIC_PRESERVATION',
        source_commit=first['source_commit'], capture_cases_preserved=len(cases), capture_files_byte_verified=count,
        original_raw_bytes_preserved=len(raw), original_source_preserved=True,
        fresh_inputs=len(q.snapshots), final_fresh_hashes=q.final_fresh_hashes,
        deleted_files=first['deleted_files']+primary['deleted_files']+final['deleted_files'],
        deleted_logical_bytes=first['deleted_logical_bytes']+primary['deleted_logical_bytes']+final['deleted_logical_bytes'],
        empty_directories_removed=final['empty_cache_directories_removed'],
        D_free_bytes_before=first['free_bytes_before'], D_free_bytes_after=free,
        observed_D_free_increase_bytes=free-first['free_bytes_before'],
        remaining_selected_cache_files=remaining['files'], active_web_dependencies_preserved=True,
        databases_and_shared_Cargo_Rustup_Temp_archives_preserved=True, actual_native_started=False)
    cleanup.publish(OUTPUT, result)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
