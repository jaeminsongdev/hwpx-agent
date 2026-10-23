"""Read-only reuse audit for the preserved P09-19/20 caption campaigns.

Reproduce the ORIGINAL bounded qualifiers; never create COM, open Hangul,
render a PDF, generate fixtures, compile Rust, run a product, or change a Gate.
Original failures and non-green limitations must survive byte-for-byte.
"""
import hashlib
import json
from pathlib import Path
import sys
import time
from unittest.mock import patch

SELF = 'tools/p09/audit_caption_target_evidence_reuse.py'
ROOT = Path(__file__).resolve().parents[2]
BASE = 'implementation/p09/evidence/'
PRIVATE = BASE + 'private/p09-17-field-auto-number-target-'
MANIFEST = 'fixtures/target-build/p09-19-object-caption-number-target-20261002-02/output/fixture-manifest.json'
CANONICAL_MANIFEST = 'fixtures/target-build/p09-20-canonical-picture-number-target-20261002-03/output/fixture-manifest.json'
CASES = (
    ('P09-19-C01', 'c01', '01', 5819, 'c60164f16a6c0119d6e61a4f3dad2b3c5e47b89cee8e2e6a15045234507447be'),
    ('P09-19-C03', 'c03', '01', 5816, '7a5ea2be62e9b6ef97010f296b435912953f2152ab34b79f4b73f017b24453ef'),
    ('P09-19-C04', 'c04', '01', 5831, 'a50e11dfd3909224d64cf38b8841c29719b821ec2803e864dfac4bdba7745bb6'),
    ('P09-19-C02', 'c02', '01', 3630, '2e4ebc7cab300cbc3759c2c1f68e72639645088808dea6a0a49796c9c26551c0'),
    ('P09-19-C02', 'c02', '02', 3630, 'f2f9877a6b695e54e3ed502527ecd6360d4ae02dd822e98c20592a7a289ce0a7'),
)


def require(ok, code):
    if not ok:
        raise ValueError('CAPTION_REUSE_' + code)


def main():
    sys.path.insert(0, str(ROOT / 'tools/p09'))
    sys.dont_write_bytecode = True
    import accept_case112_current_epoch as a
    import conservative_maintenance as c
    import prepared_run_closure_v1 as host
    import owned_cpu_baseline_v1 as baseline
    import preparation_attributed_cpu_v1 as policy
    import distinct_final_sample_guard_v1 as final
    host.configure_host_policy(c)
    denied = []
    def audit(event, args):
        if event in ('subprocess.Popen', 'os.system', 'os.startfile', 'os.exec', 'os.posix_spawn', 'os.fork'):
            denied.append(event)
            raise ValueError('CAPTION_REUSE_PROCESS_DENIED')
    sys.addaudithook(audit)
    guard = baseline.guard_type(policy.guard_type(final.guard_type(a.Guard), role='whole_metadata_preflight'))()
    q = None
    started = time.monotonic()
    row = dict(state='FAILED_CAPTION_HISTORICAL_REUSE_AUDIT', historical_records=[],
        accepted_count_delta=0, official_accepted_count=158, next_case=165,
        GO_authorized=False, actual_Hangul_or_COM_or_product_run=False,
        fixture_or_PDF_generation=False, Native010_execution_authority_received=False,
        P09_gate='OPEN', P10_started=False, PC_freeze_resolved=False)
    try:
        guard.acquire()
        q = a.AcceptanceReader(ROOT, guard.check)
        q.pin(SELF)
        # Only bounded original parsers are imported; no entrypoint is run.
        import qualify_field_object_caption_target as original
        import qualify_canonical_picture_caption_target as canonical
        raw_reader = original.oracle.bounded_bytes
        for name in (*canonical.SOURCES, 'tools/p09/inspect_field_auto_number_target.py',
                     'tools/p09/validate_field_auto_number_hwpx_contract.py'):
            q.pin(name)
        # Preserve the complete original bounded reader. Add the same serial
        # guard around it and bind its returned bytes to the fresh audit reader.
        # No file content or parsed tree is cached by this wrapper.
        def bounded(path, maximum):
            guard.check()
            raw = raw_reader(path, maximum)
            relative = Path(path).absolute().relative_to(ROOT).as_posix()
            pin = q.pin(relative)
            a.exact(pin, dict(path=relative, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()),
                'EXACT_ORIGINAL_BOUNDED_READ_BYTES')
            guard.check()
            return raw
        with patch.object(original.oracle, 'bounded_bytes', bounded), \
                patch.object(original.lifecycle, 'bounded_bytes', bounded):
            specifications = list(CASES) + [('P09-19-C02', 'canonical', '01', 6285,
                '66504fbde191d7841aa19ea6eeb8af90c32875fb395f2bd616d1147361346e5b')]
            for case_id, short, attempt, size, digest in specifications:
                guard.check()
                canonical_case = short == 'canonical'
                if canonical_case:
                    public = BASE + 'p09-20-canonical-picture-caption-target-c02-20261002-attempt01.v1.json'
                    private = PRIVATE + 'p09-20-20261002-c02-attempt01'
                    manifest = CANONICAL_MANIFEST
                else:
                    public = BASE + f'p09-19-object-caption-target-{short}-20261002-attempt{attempt}.v1.json'
                    private = PRIVATE + f'p09-19-20261002-{short}-attempt{attempt}'
                    manifest = MANIFEST
                a.exact(q.pin(public), dict(path=public, bytes=size, sha256=digest), 'PRESERVED_PUBLIC_QUALIFICATION')
                historical = q.json(public)
                if canonical_case:
                    reproduced = canonical.qualify(ROOT / manifest, historical['fixture_manifest_sha256'],
                        ROOT / private, historical['lifecycle_trace_sha256'], access_attested=True)
                else:
                    reproduced = original.qualify(ROOT / manifest, historical['fixture_manifest_sha256'], case_id,
                        ROOT / private, historical['lifecycle_trace_sha256'], access_attested=True)
                a.exact(original.lifecycle.canonical_bytes(reproduced),
                    bounded(ROOT / public, 256 * 1024), 'BYTE_EXACT_ORIGINAL_QUALIFICATION_REPRODUCTION')
                # Keep the original historical source locks; do not rebase old
                # receipts if source code has changed since the target campaign.
                for name, expected in historical['source_sha256'].items():
                    require(q.snapshots[name]['sha256'] == expected, 'ORIGINAL_QUALIFIER_SOURCE_UNCHANGED')
                claims = reproduced['claims']
                require(claims['green_rows'] == 0 and claims['p09_complete'] is False
                    and claims['product_complete'] is False and claims['product_field_update_api_qualified'] is False
                    and claims['general_numbering_algorithm_qualified'] is False
                    and claims['render'] == claims['automation_fallback'] == claims['differential'] == 'not_run',
                    'NO_HISTORICAL_SCOPE_PROMOTION')
                successful = short in ('c01', 'c03', 'c04', 'canonical')
                require(reproduced['state'] == ('bounded_semantic_non_green' if successful else 'failed_lifecycle_non_green')
                    and claims['actual_open_save_fresh_reopen'] is successful, 'SUCCESS_AND_FAILURE_SEPARATE')
                numbers = [reproduced['input']['caption_number']]
                numbers += [reproduced['snapshots'][stage]['caption_number'] for stage in ('saved', 'reopened')] if successful else []
                row['historical_records'].append(dict(public_pin=q.snapshots[public], case_id=case_id,
                    canonical_picture_successor=canonical_case, state=reproduced['state'],
                    original_record_reproduced_byte_exact=True,
                    actual_target_campaign_reexecuted=False, historical_caption_numbers=numbers,
                    remaining_hwp_processes_at_historical_run=reproduced['remaining_hwp_process_count_at_run'],
                    green_rows=0))
            control = PRIVATE + 'p09-19-20261002-c02-seed-control01/target-trace.json'
            q.json(control)
            require(q.snapshots[control]['sha256'] == 'e720accd15af809cd54161dcca71f2eccd48a11e57cc070dd2309f04712cbc83',
                'PRESERVED_UNNUMBERED_PICTURE_CONTROL_FAILURE')
            row['preserved_unnumbered_picture_control_pin'] = q.snapshots[control]
        require(len(row['historical_records']) == 6 and not denied, 'ALL_SIX_RECORDS_WITHOUT_PROCESS')
        q.finish()
        guard.check(force=True)
        row.update(state='PASS_CAPTION_HISTORICAL_EVIDENCE_REUSE_NOT_GENERAL_PRODUCT_OR_GATE',
            historical_bounded_semantic_cases=4, preserved_failed_picture_cases=2,
            source_pins=list(q.snapshots.values()), fresh_inputs=len(q.snapshots),
            final_fresh_hashes=q.final_fresh_hashes)
    except (ValueError, OSError, KeyError, TypeError, AttributeError) as error:
        import re
        code = str(error)
        row['error_type'] = type(error).__name__
        if re.fullmatch('[A-Za-z0-9_]{1,180}', code):
            row['error_code'] = code
        row['inspected_file_count'] = 0 if q is None else len(q.snapshots)
    finally:
        guard.close()
        row.update(cleanup_confirmed=guard.cleanup, process_creation_attempts=len(denied),
            elapsed_seconds=time.monotonic() - started,
            original_resource_samples=guard.samples)
        if guard.cleanup is not True:
            row['state'] = 'CLEANUP_FAILED_CAPTION_REUSE_AUDIT'
    print(json.dumps(row, ensure_ascii=True, allow_nan=False))
    return 0 if row['state'].startswith('PASS_') and guard.cleanup and not denied else 2


if __name__ == '__main__':
    raise SystemExit(main())
