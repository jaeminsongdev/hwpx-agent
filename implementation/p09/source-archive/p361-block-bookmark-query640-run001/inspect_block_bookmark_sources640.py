"""Bounded existing HWPX query for BOOKMARK ranges, never Native qualification.

Only declared fixture/evidence roots; no target/cache/global-drive scan, no Native
activation, no raw bookmark names/text and no mutation of original files.
"""
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sys
import time
import xml.etree.ElementTree as ET
import zipfile

import named_style_verification_runtime as r
import run_prepared_bookmark_native631 as publisher
import metadata_forensic_retention615 as retention
from verify_prepared_bookmark631 import command

SELF = 'tools/p09/inspect_block_bookmark_sources640.py'
TEST = 'tools/p09/tests/test_block_bookmark_sources640.py'
OUTPUT = 'implementation/p09/evidence/p09-361-block-bookmark-source-query640-run001.v1.json'
SPOOL = 'implementation/p09/evidence/private/p09-361-block-bookmark-source-query640-run001-forensic'
ROOTS = ('fixtures', 'implementation/p09/evidence/private', 'implementation/p08/evidence/private')
HP = '{http://www.hancom.co.kr/hwpml/2011/paragraph}'
MAX_FILES = 2048
MAX_BYTES = 256*1024*1024


def require(ok, code):
    if not ok:
        raise ValueError('P640_' + code)


def inspect(raw, checkpoint=lambda: None):
    require(type(raw) is bytes and 0 < len(raw) <= 4*1024*1024, 'DOCUMENT_BYTE_BOUND')
    rows = []
    point_count = 0
    node_count = 0
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        entries = archive.infolist()
        require(0 < len(entries) <= 256, 'ZIP_ENTRY_BOUND')
        names = [p.filename for p in entries]
        require(len({p.casefold() for p in names}) == len(names)
            and all(not p.startswith('/') and '\\' not in p and ':' not in p
                and not any(v in ('.', '..') for v in p.split('/')) for p in names), 'ZIP_NAMES')
        require(sum(p.file_size for p in entries) <= 32*1024*1024, 'ARCHIVE_EXPANDED_BOUND')
        parts = [p for p in entries if re.fullmatch(r'Contents/section[0-9]+\.xml', p.filename)]
        require(1 <= len(parts) <= 32 and sum(p.file_size for p in parts) <= 8*1024*1024, 'SECTION_INVENTORY')
        for part in parts:
            checkpoint()
            require(0 < part.file_size <= 1024*1024, 'SECTION_BYTE_BOUND')
            data = archive.read(part)
            require(len(data) == part.file_size and b'<!DOCTYPE' not in data.upper() and b'<!ENTITY' not in data.upper(), 'XML_NO_DTD_OR_ENTITY')
            root = ET.fromstring(data)
            stack = []
            ids = set()
            part_rows = []
            for n in root.iter():
                node_count += 1
                require(node_count <= 100000, 'XML_NODE_BOUND')
                if node_count % 256 == 0:
                    checkpoint()
                if n.tag == HP+'bookmark':
                    point_count += 1
                elif n.tag == HP+'fieldBegin':
                    identifier = n.get('id')
                    require(identifier is not None and identifier not in ids and len(stack) < 64, 'FIELD_BEGIN_BINDING')
                    ids.add(identifier)
                    keys = [p.get('name', '') for p in n.iter() if p.tag in (HP+'stringParam', HP+'integerParam', HP+'booleanParam')]
                    stack.append(dict(identifier=identifier, kind=n.get('type'), start=node_count,
                        parameter_key_hashes=sorted(hashlib.sha256(p.encode('utf-8')).hexdigest() for p in keys), texts=[]))
                elif n.tag == HP+'fieldEnd':
                    require(stack and stack[-1]['identifier'] == n.get('beginIDRef'), 'FIELD_END_BINDING')
                    field = stack.pop()
                    if field['kind'] == 'BOOKMARK':
                        text = ''.join(field['texts'])
                        part_rows.append(dict(section=part.filename, begin_node_ordinal=field['start'], end_node_ordinal=node_count,
                            parameter_key_hashes=field['parameter_key_hashes'], body_text_utf8_bytes=len(text.encode('utf-8')),
                            body_text_sha256=hashlib.sha256(text.encode('utf-8')).hexdigest(),
                            Native_provenance_or_target_binding_qualified=False))
                        require(len(part_rows) <= 128, 'BLOCK_FIELD_BOUND')
                elif n.tag == HP+'t':
                    text = ''.join(n.itertext())
                    require(len(text.encode('utf-8')) <= 65536, 'FIELD_TEXT_BOUND')
                    for field in stack:
                        if field['kind'] == 'BOOKMARK':
                            field['texts'].append(text)
            require(not stack, 'UNFINISHED_FIELD_RANGE')
            rows.extend(part_rows)
    return dict(point_markers=point_count, block_field_candidates=rows, scanned_nodes=node_count,
        candidate_only_not_actual_Native_or_block_content_support=True)


def discover(guard):
    paths = []
    excluded = []
    visited = 0
    for name in ROOTS:
        root = r.c.ROOT/name
        if not root.exists():
            excluded.append(dict(path=name, reason='declared_root_absent'))
            continue
        require(not root.is_symlink() and not root.is_junction(), 'DIRECT_ROOT')
        pending = [root]
        while pending:
            guard.check()
            current = pending.pop()
            with os.scandir(current) as items:
                for item in items:
                    visited += 1
                    require(visited <= 65536, 'METADATA_ENTRY_BOUND')
                    if visited % 128 == 0:
                        guard.check()
                    p = Path(item.path)
                    if item.is_symlink() or p.is_junction():
                        excluded.append(dict(path=p.relative_to(r.c.ROOT).as_posix(), reason='reparse_not_followed'))
                    elif item.is_dir(follow_symlinks=False):
                        pending.append(p)
                    elif item.is_file(follow_symlinks=False) and p.suffix.casefold() == '.hwpx':
                        size = item.stat(follow_symlinks=False).st_size
                        paths.append(dict(path=p.relative_to(r.c.ROOT).as_posix(), bytes=size))
                        require(len(paths) <= MAX_FILES, 'HWPX_FILE_COUNT_BOUND')
    return sorted(paths, key=lambda p:p['path']), excluded, visited


def main():
    require(sys.argv[1:] == ['--existing-hwpx-query-only'], 'READONLY_MODE')
    require(not (r.c.ROOT/OUTPUT).exists(), 'IMMUTABLE_OUTPUT')
    r.tools.select_own_single_cpu()
    r.shared.host.configure_host_policy(r.c)
    guard = r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))()
    q = None
    start = time.monotonic()
    row = dict(state='FAILED640_EXISTING_BLOCK_SOURCE_QUERY', roots=list(ROOTS), files=[], excluded=[], steps=[],
        Native_started=False, previous_test_suite_replayed=False, P09_complete=False, block_content_support_qualified=False)
    try:
        guard.acquire()
        q = r.a.AcceptanceReader(r.c.ROOT, guard.check)
        for name in (SELF, TEST, 'tools/p09/metadata_forensic_retention615.py', 'tools/p09/audit_evidence_io.py'):
            q.pin(name)
        result = command(guard, [sys.executable, '-B', str(r.c.ROOT/TEST)], r.audit.environment(), row, 'new_block_query_controls7')
        require({k:result[k] for k in ('run','errors','failures','skipped')} == dict(run=7,errors=0,failures=0,skipped=0), 'NEW_QUERY_CONTROLS')
        paths, excluded, visited = discover(guard)
        row.update(discovered_files=len(paths), metadata_entries=visited, excluded=excluded)
        total = 0
        for index, item in enumerate(paths, 1):
            guard.check()
            if not 0 < item['bytes'] <= 4*1024*1024 or total+item['bytes'] > MAX_BYTES:
                row['excluded'].append(dict(item, reason='document_or_aggregate_byte_budget_not_scanned'))
                continue
            pin = q.pin(item['path'])
            require(pin['bytes'] == item['bytes'], 'DISCOVERED_SIZE_UNCHANGED')
            total += pin['bytes']
            # Exact bounded copy for ZIP/XML parsing, not package rewriting.
            with (q.root/item['path']).open('rb') as stream:
                raw = stream.read(pin['bytes']+1)
            require(len(raw) == pin['bytes'] and hashlib.sha256(raw).hexdigest() == pin['sha256'], 'PARSED_SOURCE_SHA')
            try:
                value = inspect(raw, guard.check)
                row['files'].append(dict(pin=pin, **value))
            except (ValueError, ET.ParseError, zipfile.BadZipFile) as error:
                code = str(error)
                row['excluded'].append(dict(pin=pin, reason=code if re.fullmatch(r'P640_[A-Z0-9_]+',code) else 'package_or_XML_parse_failed_not_scanned'))
            if index % 20 == 0:
                print(json.dumps(dict(state='QUERY640_PROGRESS', files_considered=index, files_total=len(paths),
                    system_CPU=guard.samples[-1]['system_cpu_percent'], available_RAM_percent=guard.samples[-1]['available_ram_percent'])), flush=True)
        final_paths, final_excluded, final_visited = discover(guard)
        require(paths == final_paths and excluded == final_excluded and visited == final_visited, 'FINAL_METADATA_INVENTORY_UNCHANGED')
        q.finish()
        guard.check(force=True)
        candidates = [v for v in row['files'] if v['block_field_candidates']]
        row.update(state='OBSERVED640_BOUNDED_EXISTING_HWPX_BLOCK_RANGE_QUERY_NOT_NATIVE_OR_GATE',
            parsed_files=len(row['files']), parsed_bytes=total, candidate_files=len(candidates),
            candidate_pins=[v['pin'] for v in candidates], complete_declared_roots_query=not row['excluded'])
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        row.update(**publisher.runtime.io.safe_failure(error))
        if isinstance(error,ValueError) and re.fullmatch(r'P640_[A-Z0-9_]{1,100}',str(error)):
            row['error_code']=str(error)
    finally:
        guard.close()
        row.update(cleanup=guard.cleanup and all(v['cleanup'] for v in row['steps']),
            source_pins=[] if q is None else list(q.snapshots.values()),
            fresh_inputs=0 if q is None else len(q.snapshots), final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
            elapsed_seconds=round(time.monotonic()-start,3),
            system_CPU_max=max((s['system_cpu_percent'] for s in guard.samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent'] for s in guard.samples),default=None))
        row,retained=retention.retain(r.c.ROOT,SPOOL,row)
        pin=publisher.publish(OUTPUT,row)
        print(json.dumps({**{k:row.get(k) for k in ('state','error_code','cleanup','discovered_files','parsed_files','candidate_files',
            'complete_declared_roots_query','fresh_inputs','final_fresh_hashes','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'excluded_count':len(row['excluded']),'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('OBSERVED640_') and row['cleanup'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
