"""Prepare two UNQUALIFIED controls by reversing an exact P09-19 insertion.

Only fixture preparation: no product caption-delete API, Rust change, COM,
Hangul, PDF render, Native010 execution, acceptance or Gate qualification.
The old manifest's pre-insertion section SHA is mandatory; all other expanded
package parts remain byte-exact. Publication is exclusive and never retries.
"""
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sys
import time
import zipfile
from xml.etree import ElementTree as ET

SELF = 'tools/p09/prepare_caption_isolation_controls.py'
TEST = 'tools/p09/tests/test_caption_isolation_controls.py'
ROOT = Path(__file__).resolve().parents[2]
MANIFEST = 'fixtures/target-build/p09-19-object-caption-number-target-20261002-02/output/fixture-manifest.json'
MANIFEST_SHA = '42a9d18eb18dac2d34185297fb8cf0b18b10658e3e5b327839a14c770fb22a48'
OUTPUT = 'fixtures/target-build/p09-19-caption-isolation-controls-20261017-01'
SECTION = 'Contents/section0.xml'
CASES = ('P09-19-C01', 'P09-19-C04')
MAX_PACKAGE = 4 * 1024 * 1024


def require(ok, code):
    if not ok:
        raise ValueError('CAPTION_CONTROL_' + code)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def remove_number(section, expected):
    require(type(section) is bytes and 0 < len(section) <= 2 * 1024 * 1024
        and b'<!doctype' not in section.lower() and b'<!entity' not in section.lower(), 'BOUNDED_INACTIVE_SECTION')
    root = ET.fromstring(section)
    fields = [e for e in root.iter() if e.tag == '{http://www.hancom.co.kr/hwpml/2011/paragraph}autoNum']
    controls = re.findall(br'<hp:ctrl><hp:autoNum\b.*?</hp:ctrl>', section, re.S)
    require(len(fields) == len(controls) == 1 and fields[0].get('num') == '19', 'ONE_ORIGINAL_NUMBER19_CONTROL')
    baseline = section.replace(controls[0], b'', 1)
    require(type(expected) is str and re.fullmatch('[a-f0-9]{64}', expected)
        and digest(baseline) == expected, 'EXACT_OLD_MANIFEST_PREINSERTION_SECTION')
    require(not any(e.tag.endswith('}autoNum') for e in ET.fromstring(baseline).iter()), 'NO_REMAINING_NUMBER')
    return baseline


def prove_preparation(baseline, source, case_id, caption):
    if case_id == 'P09-19-C01':
        require(source.count(b'numberingType="NONE"') == 1
            and source.replace(b'numberingType="NONE"', b'numberingType="PICTURE"', 1) == baseline,
            'ONLY_PREDECLARED_RECTANGLE_CATEGORY_PREPARATION')
    elif case_id == 'P09-19-C04':
        require(source.count(b'<hp:caption') == 0 and baseline.count(caption) == 1
            and baseline.replace(caption, b'', 1) == source,
            'ONLY_PREDECLARED_EQUATION_CAPTION_PREPARATION')
    else:
        require(False, 'CLOSED_TWO_CASE_SCOPE')


def rebuild(raw, section, checkpoint=lambda: None):
    require(type(raw) is bytes and 0 < len(raw) <= MAX_PACKAGE, 'BOUNDED_ORIGINAL_ARCHIVE')
    target = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(raw)) as original, zipfile.ZipFile(target, 'w') as output:
        entries = original.infolist()
        require(0 < len(entries) <= 64 and sum(e.file_size for e in entries) <= 8 * 1024 * 1024
            and len({e.filename for e in entries}) == len(entries)
            and sum(e.filename == SECTION for e in entries) == 1, 'BOUNDED_UNIQUE_PACKAGE_MEMBERS')
        for entry in entries:
            checkpoint()
            name = entry.filename
            require(not entry.is_dir() and not entry.flag_bits & 1 and '\\' not in name and ':' not in name
                and not name.startswith('/') and all(p not in ('', '.', '..') for p in name.split('/'))
                and 0 <= entry.file_size <= 2 * 1024 * 1024, 'DIRECT_BOUNDED_PACKAGE_MEMBER')
            value = section if name == SECTION else original.read(entry)
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = entry.compress_type
            info.external_attr = entry.external_attr
            info.create_system = entry.create_system
            output.writestr(info, value)
    value = target.getvalue()
    require(0 < len(value) <= MAX_PACKAGE, 'BOUNDED_REBUILT_CONTROL')
    return value


def direct(path):
    require(not any(p.is_symlink() or p.is_junction() for p in (path, *path.parents)), 'NO_LINKED_PATH')


def publish(path, raw):
    direct(path)
    require(path.parent.is_dir() and not path.exists(), 'EXCLUSIVE_DIRECT_OUTPUT')
    with path.open('xb') as stream:
        require(stream.write(raw) == len(raw), 'COMPLETE_CONTROL_PUBLICATION')
        stream.flush()
        os.fsync(stream.fileno())


def main():
    sys.path.insert(0, str(ROOT / 'tools/p09'))
    sys.dont_write_bytecode = True
    import accept_case112_current_epoch as a
    import conservative_maintenance as c
    import prepared_run_closure_v1 as host
    import owned_cpu_baseline_v1 as baseline_policy
    import preparation_attributed_cpu_v1 as policy
    import distinct_final_sample_guard_v1 as final
    host.configure_host_policy(c)
    denied = []
    def audit(event, args):
        if event in ('subprocess.Popen', 'os.system', 'os.startfile', 'os.exec', 'os.posix_spawn', 'os.fork'):
            denied.append(event)
            raise ValueError('CAPTION_CONTROL_PROCESS_DENIED')
    sys.addaudithook(audit)
    guard = baseline_policy.guard_type(policy.guard_type(final.guard_type(a.Guard), role='whole_metadata_preflight'))()
    q = None
    started = time.monotonic()
    row = dict(state='FAILED_CAPTION_ISOLATION_CONTROL_PREPARATION', created_controls=[],
        GO_authorized=False, accepted_count_delta=0, official_accepted_count=158, next_case=165,
        actual_Hangul_COM_or_product_run=False, fixture_only=True, P09_gate='OPEN', P10_started=False,
        product_caption_delete_API_claimed=False, render_or_semantic_target_qualified=False)
    try:
        guard.acquire()
        q = a.AcceptanceReader(ROOT, guard.check)
        for name in (SELF, TEST, 'tools/p09/inspect_field_object_caption_target.py', 'tools/p09/inspect_field_auto_number_target.py'):
            q.pin(name)
        import inspect_field_object_caption_target as oracle
        manifest = q.json(MANIFEST)
        require(q.snapshots[MANIFEST]['sha256'] == MANIFEST_SHA, 'EXACT_ORIGINAL_MANIFEST')
        directory = ROOT / OUTPUT
        direct(directory)
        require(directory.parent == ROOT / 'fixtures/target-build' and directory.parent.is_dir()
            and not directory.exists(), 'ONE_NEW_DIRECT_FIXTURE_DIRECTORY_NO_RETRY')
        prepared = []
        caption_source = ROOT / manifest['caption_seed_relative']
        q.pin(manifest['caption_seed_relative'])
        caption_section, _, _ = oracle.package_snapshot(caption_source, manifest['caption_seed_package_sha256'])
        captions = re.findall(br'<hp:caption\b.*?</hp:caption>', caption_section, re.S)
        require(len(captions) == 1, 'EXACT_OLD_CAPTION_SEED')
        for case in manifest['cases']:
            if case['case_id'] not in CASES:
                continue
            guard.check()
            name = Path(MANIFEST).parent.as_posix() + '/' + case['file']
            pin, raw = q._read(name, parse=True)
            q._bind(name, pin)
            require(pin['sha256'] == case['output_package_sha256'], 'EXACT_NUMBERED_INPUT')
            section, _, parts = oracle.package_snapshot(ROOT / name, pin['sha256'])
            baseline = remove_number(section, case['prepared_caption_section_sha256'])
            q.pin(case['source_relative'])
            source, _, source_parts = oracle.package_snapshot(ROOT / case['source_relative'], case['source_package_sha256'])
            require(digest(source) == case['source_section_sha256'] and source_parts == parts,
                'EXACT_SOURCE_AND_ALL_UNRELATED_PARTS')
            prove_preparation(baseline, source, case['case_id'], captions[0])
            result = rebuild(bytes(raw), baseline, guard.check)
            require(rebuild(bytes(raw), baseline, guard.check) == result, 'DETERMINISTIC_CONTROL_ARCHIVE')
            prepared.append((case, name, pin, baseline, parts, result))
        require(len(prepared) == 2, 'BOTH_CONTROLS_PREPARED_BEFORE_PUBLICATION')
        directory.mkdir()  # Exclusive, no source package is edited or deleted.
        for case, original_name, original_pin, section, parts, result in prepared:
            file = case['file'].replace('.hwpx', '.unnumbered-control.hwpx')
            relative = OUTPUT + '/' + file
            publish(ROOT / relative, result)
            pin = q.pin(relative)
            readback, _, actual_parts = oracle.package_snapshot(ROOT / relative, pin['sha256'])
            require(readback == section and actual_parts == parts, 'PUBLISHED_CONTROL_SECTION_AND_PARTS_EXACT')
            row['created_controls'].append(dict(case_id=case['case_id'], path=relative,
                package_pin=pin, numbered_input_pin=original_pin,
                section_sha256=digest(section), old_preinsertion_section_sha256=case['prepared_caption_section_sha256'],
                all_nonsection_parts_unchanged=True, removed_auto_number_controls=1,
                lifecycle='not_run', render='not_run', green_rows=0))
        metadata = dict(schema_version='hwpx-agent.p09-caption-isolation-control-manifest/v1',
            fixture_only=True, actual_Hangul_COM_or_product_run=False, P09_gate='OPEN',
            source_manifest_pin=q.snapshots[MANIFEST], controls=row['created_controls'])
        manifest_name = OUTPUT + '/control-manifest.v1.json'
        publish(ROOT / manifest_name, (json.dumps(metadata, ensure_ascii=True, indent=2) + '\n').encode('utf-8'))
        q.pin(manifest_name)
        require(not denied, 'NO_PROCESS_ATTEMPTS')
        q.finish()
        guard.check(force=True)
        row.update(state='PASS_TWO_STATIC_CAPTION_ISOLATION_CONTROLS_NOT_PRODUCT_OR_TARGET',
            control_manifest_pin=q.snapshots[manifest_name], fresh_inputs=len(q.snapshots),
            final_fresh_hashes=q.final_fresh_hashes, source_pins=list(q.snapshots.values()))
    except (ValueError, OSError, KeyError, TypeError, AttributeError, zipfile.BadZipFile, ET.ParseError) as error:
        row['error_type'] = type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch('[A-Za-z0-9_]{1,180}', error.args[0]):
            row['error_code'] = error.args[0]
    finally:
        guard.close()
        row.update(cleanup_confirmed=guard.cleanup, process_creation_attempts=len(denied),
            elapsed_seconds=time.monotonic() - started, original_resource_samples=guard.samples)
        if guard.cleanup is not True:
            row['state'] = 'CLEANUP_FAILED_CAPTION_ISOLATION_CONTROLS'
    print(json.dumps(row, ensure_ascii=True, allow_nan=False))
    return 0 if row['state'].startswith('PASS_') and guard.cleanup and not denied else 2


if __name__ == '__main__':
    raise SystemExit(main())
