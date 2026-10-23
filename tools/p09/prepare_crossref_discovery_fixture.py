"""One private, unqualified input for a future complete eight-variant discovery.

Never starts a process or native session. The original Hancom-saved package is
immutable; only a new paragraph is inserted in a separate preparation copy.
"""
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import time
import zipfile
from xml.etree import ElementTree as ET

if __package__:
    from . import prepare_caption_isolation_controls as package_tools
else:
    import prepare_caption_isolation_controls as package_tools

ROOT = Path(__file__).resolve().parents[2]
SELF = 'tools/p09/prepare_crossref_discovery_fixture.py'
TEST = 'tools/p09/tests/test_crossref_discovery_fixture.py'
BASE = 'implementation/p09/evidence/private/p09-14-hyperlink-discovery-20260912-attempt02/after.hwpx'
BASE_SHA = 'feb312b974de2dd7d0275e6043e927ea5cf8348cfc0a04b44045e0bf669d4480'
OUTPUT = 'implementation/p09/evidence/private/p09-361-crossref-discovery-inputs-20261017-r01'
INPUT = OUTPUT + '/source-with-bookmark.hwpx'
MANIFEST = OUTPUT + '/source-input-manifest.v1.json'
BOOKMARK = 'p09_crossref_discovery_anchor'
TEXT = 'P09_CROSSREF_DISCOVERY_TARGET_TEXT'
HP = '{http://www.hancom.co.kr/hwpml/2011/paragraph}'
HS = '{http://www.hancom.co.kr/hwpml/2011/section}'


def require(ok, code):
    if not ok:
        raise ValueError('CROSSREF_FIXTURE_' + code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def insert_paragraph(section):
    require(type(section) is bytes and 0 < len(section) <= 2 * 1024 * 1024
            and b'\x00' not in section and b'<!doctype' not in section.lower()
            and b'<!entity' not in section.lower(), 'SECTION_BOUNDARY')
    root = ET.fromstring(section)
    require(root.tag == HS + 'sec' and not list(root.iter(HP + 'bookmark')), 'ONE_SECTION_NO_BOOKMARKS')
    paragraphs = list(root.findall(HP + 'p'))
    require(paragraphs and paragraphs[0].find(HP + 'run') is not None, 'EXISTING_BODY_STYLE')
    ids = [p.get('id', '') for p in root.iter(HP + 'p')]
    require(all(re.fullmatch('[0-9]{1,10}', value) for value in ids), 'OBSERVED_PARAGRAPH_IDS')
    next_id = max(int(value) for value in ids) + 1
    require(next_id <= 4294967295, 'PARAGRAPH_ID_LIMIT')
    paragraph = re.search(br'<hp:p\b[^>]*>', section)
    run = re.search(br'<hp:run\b[^>]*>', section)
    close = re.search(br'</hs:sec>\s*$', section)
    require(paragraph is not None and run is not None and close is not None, 'EXACT_NATIVE_PREFIX_PROFILE')
    wrapper = b'<root xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph">'
    p = ET.fromstring(wrapper + paragraph[0] + b'</hp:p></root>')[0]
    r = ET.fromstring(wrapper + run[0] + b'</hp:run></root>')[0]
    require(p.attrib == paragraphs[0].attrib and r.attrib == paragraphs[0].find(HP + 'run').attrib,
            'OBSERVED_DIRECT_PARAGRAPH_AND_RUN_HEADERS')
    require('paraPrIDRef' in p.attrib and 'styleIDRef' in p.attrib and 'charPrIDRef' in r.attrib,
            'EXISTING_STYLE_REFERENCES')
    new_header, changes = re.subn(br'(?<![A-Za-z0-9_:])id=(?:"[0-9]+"|\'[0-9]+\')',
                                 b'id="' + str(next_id).encode() + b'"', paragraph[0])
    require(changes == 1, 'ONE_FRESH_PARAGRAPH_ID')
    insertion = (new_header + run[0] + ('<hp:ctrl><hp:bookmark name="' + BOOKMARK
                 + '"/></hp:ctrl><hp:t>' + TEXT + '</hp:t></hp:run></hp:p>').encode())
    offset = close.start()
    result = section[:offset] + insertion + section[offset:]
    parsed = ET.fromstring(result)
    require(len(parsed.findall(HP + 'p')) == len(paragraphs) + 1
            and len(list(parsed.iter(HP + 'bookmark'))) == 1
            and result[:offset] == section[:offset] and result[offset + len(insertion):] == section[offset:],
            'EXACT_ONE_PARAGRAPH_INSERTION')
    return result, dict(offset=offset, inserted_bytes=len(insertion), insertion_sha256=sha(insertion),
                        source_section_sha256=sha(section), output_section_sha256=sha(result),
                        original_body_paragraphs=len(paragraphs), generated_paragraph_id=next_id,
                        bookmark_name_sha256=sha(BOOKMARK.encode()), target_text_sha256=sha(TEXT.encode()))


def prepare(raw, checkpoint=lambda: None):
    require(type(raw) is bytes and len(raw) == 15097 and sha(raw) == BASE_SHA, 'EXACT_FROZEN_NATIVE_SAVED_BASE')
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        require(len(archive.infolist()) <= 64 and archive.namelist().count(package_tools.SECTION) == 1,
                'SOURCE_PACKAGE_MEMBERS')
        section = archive.read(package_tools.SECTION)
    output_section, delta = insert_paragraph(section)
    result = package_tools.rebuild(raw, output_section, checkpoint)
    with zipfile.ZipFile(io.BytesIO(raw)) as before, zipfile.ZipFile(io.BytesIO(result)) as after:
        require(before.namelist() == after.namelist(), 'SAME_MEMBER_INVENTORY_AND_ORDER')
        preserved = 0
        for name in before.namelist():
            checkpoint()
            require(after.read(name) == (output_section if name == package_tools.SECTION else before.read(name)),
                    'ALL_EXPANDED_PARTS_EXACT_EXCEPT_DECLARED_DELTA')
            preserved += name != package_tools.SECTION
    return result, dict(section_delta=delta, preserved_nonsection_parts=preserved,
                        generated_input=dict(path=INPUT, bytes=len(result), sha256=sha(result)))


def run():
    import accept_case112_current_epoch as a
    import conservative_maintenance as c
    import prepared_run_closure_v1 as host
    import owned_cpu_baseline_v1 as baseline
    import preparation_attributed_cpu_v1 as policy
    import distinct_final_sample_guard_v1 as final
    import successor_preparation_workspace_v1 as publisher
    from types import SimpleNamespace as NS
    host.configure_host_policy(c)
    def deny_process(event, args):
        if event in ('subprocess.Popen', 'os.system', 'os.startfile', 'os.exec', 'os.posix_spawn', 'os.fork'):
            raise ValueError('CROSSREF_FIXTURE_PROCESS_FORBIDDEN')
    sys.addaudithook(deny_process)
    guard = baseline.guard_type(policy.guard_type(final.guard_type(a.Guard), role='whole_metadata_preflight'))()
    q = None
    started = time.monotonic()
    row = dict(state='FAILED_CROSSREF_DISCOVERY_INPUT_PREPARATION', native_execution_authorized=False,
               native_or_SDK_executed=False, native_readback_or_open_qualified=False,
               accepted_count_delta=0, P09_gate='OPEN', P10_started=False)
    try:
        guard.acquire()
        q = a.AcceptanceReader(ROOT, guard.check)
        for name in (SELF, TEST, 'tools/p09/prepare_caption_isolation_controls.py'):
            q.pin(name)
        base_pin, raw = q._read(BASE, parse=True)
        q._bind(BASE, base_pin)
        result, details = prepare(bytes(raw), guard.check)
        directory = ROOT / OUTPUT
        package_tools.direct(directory)
        require(directory.parent == ROOT / 'implementation/p09/evidence/private'
                and directory.parent.is_dir() and not directory.exists(), 'EXCLUSIVE_PRIVATE_PREPARATION')
        directory.mkdir()
        package_tools.publish(ROOT / INPUT, result)
        require(q.pin(INPUT) == details['generated_input'], 'ACTUAL_GENERATED_INPUT_PIN')
        metadata = dict(schema_version='hwpx-agent.crossref-discovery-source-input/v1', fixture_only=True,
                        native_execution_authorized=False, native_or_SDK_executed=False,
                        native_readback_or_open_qualified=False, expected_candidate_count=8,
                        source_original_pin=base_pin, **details)
        package_tools.publish(ROOT / MANIFEST, (json.dumps(metadata, ensure_ascii=True, indent=2) + '\n').encode())
        q.pin(MANIFEST)
        q.finish()
        guard.check(force=True)
        row.update(state='PASS_ONE_GENERATED_CROSSREF_INPUT_NOT_NATIVE_OR_PRODUCT_INSERTION',
                   manifest_pin=q.snapshots[MANIFEST], generated_input_pin=q.snapshots[INPUT],
                   source_original_pin=base_pin, fresh_inputs=len(q.snapshots), final_fresh_hashes=q.final_fresh_hashes,
                   details=details)
    except (ValueError, OSError, KeyError, TypeError, AttributeError, zipfile.BadZipFile, ET.ParseError) as error:
        row['error_type'] = type(error).__name__
        row['error_code'] = error.args[0] if error.args and type(error.args[0]) is str and re.fullmatch('[A-Za-z0-9_]{1,180}', error.args[0]) else 'CROSSREF_INPUT_PREPARATION_FAILED'
    finally:
        guard.close()
        row.update(cleanup=guard.cleanup, elapsed_seconds=time.monotonic() - started,
                   source_pins=[] if q is None else list(q.snapshots.values()), resource_samples=guard.samples)
        api = NS(require=c.require, exact=lambda actual, expected, label: c.require(actual == expected, label))
        pin = publisher.publish(ROOT, 'implementation/p09/evidence/p09-361-crossref-discovery-input001.v1.json', row, api)
        print(json.dumps(dict(state=row['state'], error_code=row.get('error_code'), cleanup=row['cleanup'],
                              elapsed_seconds=row['elapsed_seconds'], manifest_pin=row.get('manifest_pin'),
                              generated_input_pin=row.get('generated_input_pin'), pin=pin)))
    return 0 if row['state'].startswith('PASS_') and row['cleanup'] else 2


if __name__ == '__main__':
    raise SystemExit(run())
