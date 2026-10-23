"""Bounded read-only native-control inventory, NOT a complete reference reader.

One sequential expansion per member and one streaming XML pass. No repair,
typed-state invention, product execution, external entities, extraction or writes.
The command only inspects the four pinned caption inputs; it never runs Native.
"""
import hashlib
import io
import json
from pathlib import Path
import re
import stat
import struct
import sys
import time
import zipfile
from xml.etree import ElementTree as ET

SELF = 'tools/p09/reference_source_inventory.py'
TEST = 'tools/p09/tests/test_reference_source_inventory.py'
ROOT = Path(__file__).resolve().parents[2]
CONTROL_MANIFEST = 'fixtures/target-build/p09-19-caption-isolation-controls-20261017-01/control-manifest.v1.json'
MAX_ARCHIVE = 32 * 1024 * 1024
MAX_EXPANDED = 16 * 1024 * 1024
MAX_MEMBER = 2 * 1024 * 1024
MAX_ENTRIES = 256
MAX_ELEMENTS = 100_000
MAX_DEPTH = 128
CHUNK = 65536
PARAGRAPH_NS = 'http://www.hancom.co.kr/hwpml/2011/paragraph'
CONTROLS = ('fieldBegin', 'fieldEnd', 'bookmark', 'autoNum', 'caption',
            'footNote', 'endNote', 'pic', 'rect', 'tbl', 'equation')
FIELD_TYPES = frozenset(('HYPERLINK', 'FORMULA', 'CROSSREF', 'BOOKMARK',
                        'PAGE', 'NUMPAGES', 'DATE', 'TIME', 'DOCSUMMARY', 'UNKNOWN'))
QUALIFICATION = 'observed_native_controls_only_not_complete_reference_state_or_product_validation'


def require(ok, code):
    if not ok:
        raise ValueError('REFERENCE_INVENTORY_' + code)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def archive_directory_bound(raw):
    # Bound central-directory allocation BEFORE ZipFile materializes its entries.
    require(type(raw) is bytes and 22 <= len(raw) <= MAX_ARCHIVE, 'ARCHIVE_SIZE')
    tail_start = max(0, len(raw) - 65557)
    end = raw.rfind(b'PK\x05\x06', tail_start)
    require(end >= 0 and end + 22 <= len(raw), 'EOCD')
    _, disk, start_disk, disk_count, count, size, offset, comment = struct.unpack_from('<4s4H2LH', raw, end)
    require(end + 22 + comment == len(raw) and disk == start_disk == 0
        and disk_count == count and 0 < count <= MAX_ENTRIES
        and 0 < size <= MAX_ENTRIES * 1024 and offset + size == end, 'CLOSED_BOUNDED_DIRECTORY')
    return count


def direct_member(info):
    name = info.filename
    require(type(name) is str and info.orig_filename == name
        and 0 < len(name) <= 512 and not info.is_dir()
        and not any(ord(c) < 32 for c in name)
        and not any(c in name for c in '\\:*?<>|"') and not name.startswith('/')
        and all(p not in ('', '.', '..') and not p.endswith((' ', '.')) for p in name.split('/')),
        'DIRECT_MEMBER_NAME')
    mode = info.external_attr >> 16
    require(not stat.S_ISLNK(mode) and not info.flag_bits & 1
        and info.compress_type in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)
        and 0 <= info.file_size <= MAX_MEMBER, 'BOUNDED_PLAIN_MEMBER')


def member_bytes(archive, info, checkpoint):
    chunks = []
    count = 0
    with archive.open(info) as stream:
        while True:
            checkpoint()
            piece = stream.read(CHUNK)
            count += len(piece)
            require(count <= info.file_size <= MAX_MEMBER, 'EXPANSION_SIZE')
            if not piece:
                break
            chunks.append(piece)
    require(count == info.file_size, 'EXACT_EXPANSION_SIZE')
    return b''.join(chunks)


def scan_xml(raw, checkpoint=lambda: None, *, remaining=MAX_ELEMENTS):
    require(type(raw) is bytes and 0 < len(raw) <= MAX_MEMBER, 'XML_SIZE')
    # Closed UTF-8 profile prevents UTF-16/NUL encodings hiding active DTD syntax.
    text = raw.decode('utf-8-sig')
    lowered = text.lower()
    require('\x00' not in text and '<!doctype' not in lowered and '<!entity' not in lowered,
        'INACTIVE_UTF8_XML')
    declaration = re.match(r'\s*<\?xml\s+([^?]*)\?>', text)
    if declaration:
        encoding = re.search(r'''encoding\s*=\s*['"]([^'"]+)['"]''', declaration[1], re.I)
        require(encoding is None or encoding[1].lower() in ('utf-8', 'utf8'), 'UTF8_DECLARATION')
    counts = dict.fromkeys(CONTROLS, 0)
    fields = {}
    unknown = missing = elements = 0
    stack = []
    parser = ET.iterparse(io.StringIO(text), events=('start', 'end'))
    for event, element in parser:
        if event == 'start':
            checkpoint()
            elements += 1
            stack.append(element)
            require(elements <= remaining and len(stack) <= MAX_DEPTH, 'XML_ELEMENT_OR_DEPTH_LIMIT')
            tag = element.tag
            if isinstance(tag, str) and tag.startswith('{' + PARAGRAPH_NS + '}'):
                local = tag.split('}', 1)[1]
                if local in counts:
                    counts[local] += 1
                if local == 'fieldBegin':
                    value = element.get('type')
                    if value is None:
                        missing += 1
                    elif value in FIELD_TYPES:
                        fields[value] = fields.get(value, 0) + 1
                    else:
                        unknown += 1  # Never emit caller-controlled field values.
        else:
            stack.pop()
            if stack:
                stack[-1].remove(element)
            element.clear()
    return dict(elements=elements, controls=counts, field_types=fields,
        unknown_field_types=unknown, missing_field_types=missing)


def inspect(raw, checkpoint=lambda: None):
    checkpoint()
    declared = archive_directory_bound(raw)
    totals = dict.fromkeys(CONTROLS, 0)
    field_types = {}
    xml_parts = []
    unknown = missing = elements = expanded = 0
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        entries = archive.infolist()
        require(len(entries) == declared, 'DIRECTORY_COUNT')
        seen = set()
        for info in entries:
            checkpoint()
            direct_member(info)
            name = info.filename.casefold()
            require(name not in seen, 'NO_DUPLICATE_OR_CASE_ALIAS')
            seen.add(name)
            expanded += info.file_size
        require(expanded <= MAX_EXPANDED and 'mimetype' in archive.namelist(), 'PACKAGE_BOUNDS_AND_MIMETYPE')
        # All members, including opaque binaries, are expanded once for CRC/integrity.
        for ordinal, info in enumerate(entries):
            data = member_bytes(archive, info, checkpoint)
            if info.filename == 'mimetype':
                require(data == b'application/hwp+zip', 'HWPX_MIMETYPE')
            if info.filename.lower().endswith(('.xml', '.hpf')):
                row = scan_xml(data, checkpoint, remaining=MAX_ELEMENTS - elements)
                elements += row['elements']
                unknown += row['unknown_field_types']
                missing += row['missing_field_types']
                for key, value in row['controls'].items():
                    totals[key] += value
                for key, value in row['field_types'].items():
                    field_types[key] = field_types.get(key, 0) + value
                xml_parts.append(dict(ordinal=ordinal, bytes=len(data), sha256=digest(data), **row))
    require(bool(xml_parts), 'XML_REQUIRED')
    checkpoint()
    return dict(schema_version='hwpx-agent.p09-reference-source-inventory/v1',
        qualification=QUALIFICATION, package_bytes=len(raw), package_sha256=digest(raw),
        archive_members=declared, expanded_bytes=expanded, xml_elements=elements,
        observed_controls=totals, observed_field_types=field_types,
        unknown_field_types=unknown, missing_field_types=missing, xml_parts=xml_parts,
        xml_role_assignment_or_spine_completeness_qualified=False,
        targets_or_reference_edges_resolved=False, typed_state_created=False,
        product_reference_validation_executed=False, external_sources_accessed=False,
        member_expansion_passes=1, XML_scan_passes=1, files_written=0)


def console_summary(row):
    """Keep bounded stdout sufficient to bind observations without a part dump."""
    result = {k: v for k, v in row.items() if k not in ('inventories', 'original_resource_samples')}
    result['inventories'] = []
    for item in row['inventories']:
        inventory = item['inventory']
        result['inventories'].append(dict(case_id=item['case_id'], role=item['role'],
            package_sha256=inventory['package_sha256'], qualification=inventory['qualification'],
            xml_parts=len(inventory['xml_parts']), xml_elements=inventory['xml_elements'],
            observed_controls=inventory['observed_controls'], observed_field_types=inventory['observed_field_types'],
            unknown_field_types=inventory['unknown_field_types'], missing_field_types=inventory['missing_field_types']))
    samples = row['original_resource_samples']
    def aggregate(key, function):
        return function((s[key] for s in samples if s.get(key) is not None), default=None)
    result['resource_summary'] = dict(samples=len(samples),
        system_CPU_max_percent=aggregate('system_cpu_percent', max),
        owned_CPU_max_machine_percent=aggregate('parent_cpu_machine_percent', max),
        private_MiB_max=aggregate('parent_private_mib', max),
        available_RAM_min_percent=aggregate('available_ram_percent', min),
        commit_used_max_percent=aggregate('commit_used_percent', max))
    result['stdout_is_summary_not_lossless_per_part_or_sample_record'] = True
    return result


def main():
    require(sys.argv[1:] == ['--inspect-caption-controls'], 'EXPLICIT_READ_ONLY_MODE')
    sys.path.insert(0, str(ROOT / 'tools/p09'))
    import accept_case112_current_epoch as a
    import conservative_maintenance as c
    import prepared_run_closure_v1 as host
    import owned_cpu_baseline_v1 as baseline
    import preparation_attributed_cpu_v1 as policy
    import distinct_final_sample_guard_v1 as final
    host.configure_host_policy(c)
    def no_process(event, args):
        if event in ('subprocess.Popen', 'os.system', 'os.startfile', 'os.exec', 'os.posix_spawn', 'os.fork'):
            raise ValueError('REFERENCE_INVENTORY_PROCESS_DENIED')
    sys.addaudithook(no_process)
    g = baseline.guard_type(policy.guard_type(final.guard_type(a.Guard), role='whole_metadata_preflight'))()
    started = time.monotonic()
    q = None
    row = dict(state='FAILED_REFERENCE_SOURCE_INVENTORY', inventories=[], GO_authorized=False,
        accepted_count_delta=0, official_accepted_count=158, next_case=165, P09_gate='OPEN',
        P10_started=False, actual_product_or_Hangul_or_COM_executed=False)
    try:
        g.acquire()
        q = a.AcceptanceReader(ROOT, g.check)
        q.pin(SELF)
        q.pin(TEST)
        manifest = q.json(CONTROL_MANIFEST)
        require(manifest['schema_version'] == 'hwpx-agent.p09-caption-isolation-control-manifest/v1'
            and manifest['fixture_only'] is True and len(manifest['controls']) == 2, 'CONTROL_MANIFEST')
        for control in manifest['controls']:
            for kind in ('package_pin', 'numbered_input_pin'):
                pin = control[kind]
                actual, data = q._read(pin['path'], parse=True)
                q._bind(pin['path'], actual)
                require(actual == pin, 'EXACT_FIXTURE_PIN')
                row['inventories'].append(dict(case_id=control['case_id'], role=kind,
                    input_pin=actual, inventory=inspect(bytes(data), g.check)))
        q.finish()
        g.check(force=True)
        row.update(state='PASS_FOUR_PINNED_SOURCE_INVENTORIES_NOT_PRODUCT_REFERENCE_VALIDATION',
            fresh_inputs=len(q.snapshots), final_fresh_hashes=q.final_fresh_hashes,
            source_pins=list(q.snapshots.values()))
    except (ValueError, OSError, KeyError, TypeError, AttributeError, zipfile.BadZipFile, ET.ParseError) as error:
        row['error_type'] = type(error).__name__
        if error.args and type(error.args[0]) is str and re.fullmatch('[A-Za-z0-9_]{1,160}', error.args[0]):
            row['error_code'] = error.args[0]
    finally:
        g.close()
        row.update(cleanup_confirmed=g.cleanup, elapsed_seconds=time.monotonic() - started,
            original_resource_samples=g.samples)
        if not g.cleanup:
            row['state'] = 'CLEANUP_FAILED_REFERENCE_SOURCE_INVENTORY'
    print(json.dumps(console_summary(row), ensure_ascii=True, allow_nan=False))
    return 0 if row['state'].startswith('PASS_') and g.cleanup else 2


if __name__ == '__main__':
    raise SystemExit(main())
