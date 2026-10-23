"""Bounded semantic triage of actual generated/captured files, not acceptance.

No Native, field refresh, product mutation, rendering, private values or retries.
Observations must identify the next product fix; they are not a Gate validator.
"""
import hashlib
import json
from pathlib import Path
import sys
import time
import zipfile
import xml.etree.ElementTree as ET

import run_prepared_bookmark_native631 as entry
import prepared_bookmark632_receipt as carrier

r = entry.r
runtime = entry.runtime
SELF = 'tools/p09/inspect_prepared_bookmark633.py'
OUTPUT = 'implementation/p09/evidence/p09-361-prepared-bookmark633-semantic-triage001.v1.json'
RECOVERED = 'implementation/p09/evidence/p09-361-prepared-bookmark631-recovered632.v1.json'
RECOVERED_SHA = '3488031c67cccc998e621c001c3ec1afc0de5b02609e0137a65fb5a324f00aed'
HP = '{http://www.hancom.co.kr/hwpml/2011/paragraph}'


def require(ok, code):
    if not ok:
        raise ValueError('P633_'+code)


def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def section(reader, path):
    require(reader.pin(path)['bytes'] <= 4194304, 'HWPX_COMPRESSED_BOUND')
    reader.checkpoint()
    with zipfile.ZipFile(reader.root/path) as package:
        infos = package.infolist()
        require(0 < len(infos) <= 128 and len({i.filename for i in infos}) == len(infos)
                and all(not i.flag_bits & 1 and 0 <= i.file_size <= 4194304 for i in infos)
                and sum(i.file_size for i in infos) <= 8388608, 'BOUNDED_UNENCRYPTED_UNIQUE_ZIP')
        sections = [i for i in infos if i.filename.startswith('Contents/section') and i.filename.endswith('.xml')]
        require(len(sections) == 1 and sections[0].filename == 'Contents/section0.xml'
                and sections[0].file_size <= 1048576, 'FIXED_SINGLE_SECTION_PROFILE')
        data = package.read(sections[0])
    require(b'<!DOCTYPE' not in data.upper() and b'<!ENTITY' not in data.upper(), 'NO_DTD_ENTITIES')
    root = ET.fromstring(data)
    require(sum(1 for _ in root.iter()) <= 10000, 'XML_NODE_BOUND')
    reader.checkpoint()
    return root


def observe(root):
    parents = {child: parent for parent in root.iter() for child in parent}
    fields = []
    bookmark_nodes = []
    for node in root.iter():
        if node.tag == HP+'bookmark':
            bookmark_nodes.append(dict(name_sha256=digest(node.get('name', '')), id=node.get('id')))
        if node.tag != HP+'fieldBegin' or node.get('type') != 'CROSSREF':
            continue
        parameters = {}
        for item in node.iter():
            if item is node or 'name' not in item.attrib:
                continue
            name = item.attrib['name']
            require(name not in parameters, 'UNIQUE_PARAMETER_NAMES')
            parameters[name] = ''.join(item.itertext())
        # Read display text from the balanced field span in paragraph document
        # order, not from all paragraph text or arbitrary text matching.
        ancestor = node
        while ancestor in parents and ancestor.tag != HP+'p':
            ancestor = parents[ancestor]
        require(ancestor.tag == HP+'p', 'FIELD_PARAGRAPH')
        inside = False
        ended = False
        text = []
        nested = 0
        for item in ancestor.iter():
            if item is node:
                inside = True
                continue
            if not inside:
                continue
            if item.tag == HP+'fieldBegin':
                nested += 1
            if item.tag == HP+'fieldEnd':
                if nested:
                    nested -= 1
                else:
                    require(item.get('beginIDRef') == node.get('id'), 'MATCHED_FIELD_END')
                    ended = True
                    break
            if item.tag == HP+'t':
                require(len(item) == 0, 'PLAIN_FIELD_DISPLAY_PROFILE')
                text.append(item.text or '')
        require(ended, 'COMPLETE_FIELD_SPAN')
        display = ''.join(text)
        fields.append(dict(id=node.get('id'), dirty=node.get('dirty'),
            parameter_names=sorted(parameters), parameter_hashes={k: digest(v) for k, v in sorted(parameters.items())},
            command_sha256=digest(parameters.get('Command', '')),
            display_sha256=digest(display), display_characters=len(display),
            display_is_ascii_integer=bool(display) and display.isascii() and display.isdecimal(),
            display_is_empty=not display))
    return dict(crossref_count=len(fields), crossrefs=fields, bookmark_count=len(bookmark_nodes),
                bookmarks=bookmark_nodes)


def main():
    require(sys.argv[1:] == ['--inspect-captured-only'], 'READONLY_CAPTURE_MODE')
    runtime.prepared.require_absent(r.c.ROOT, OUTPUT)
    r.tools.select_own_single_cpu()
    r.shared.host.configure_host_policy(r.c)
    guard = r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))()
    q = None
    start = time.monotonic()
    row = dict(state='FAILED633_CAPTURED_FIELD_TRIAGE', actual_native_started=False,
               semantic_acceptance_qualified=False, render_qualified=False, P09_complete=False, cases=[])
    try:
        guard.acquire()
        q = r.a.AcceptanceReader(r.c.ROOT, guard.check)
        for name in (SELF, 'tools/p09/prepared_bookmark632_receipt.py', 'tools/p09/receipt_xz_envelope_v1.py'):
            q.pin(name)
        original = carrier.unpack(q.json(RECOVERED), guard.check)
        require(q.snapshots[RECOVERED]['sha256'] == RECOVERED_SHA and original['cleanup'] is True,
                'RECOVERED_COMPLETE_CAPTURE_NOT_NATIVE_PERMISSION')
        prepared = q.json(runtime.prepared.PREPARED)
        require(q.pin(runtime.prepared.SOURCE) == runtime.prepared.SOURCE_PIN, 'UNCHANGED_BOOKMARK_SOURCE')
        row['source_observation'] = observe(section(q, runtime.prepared.SOURCE))
        captures = original['retained_cases']['cases']+original['artifacts']['cases']
        require(len(captures) == len(prepared['cases']) == 8, 'ALL_EIGHT_IN_ORDER')
        for index, (case, capture) in enumerate(zip(prepared['cases'], captures), 1):
            require(case['case_index'] == capture['source_case_index'] == index, 'EXACT_SOURCE_CASE')
            stages = dict(candidate=case['output'])
            stages.update({k.removesuffix('.hwpx'): v for k, v in capture['artifacts'].items() if k.endswith('.hwpx')})
            require(set(stages) == {'candidate', 'initial', 'saved', 'reopened'}, 'FOUR_DOCUMENT_STAGES')
            observed = {}
            for label, pin in stages.items():
                require(q.pin(pin['path']) == pin, 'CAPTURE_ARTIFACT_UNCHANGED')
                observed[label] = observe(section(q, pin['path']))
            row['cases'].append(dict(case_index=index, display=case['display'], hyperlink=case['hyperlink'], stages=observed))
        q.finish()
        guard.check(force=True)
        row['state'] = 'OBSERVED633_ACTUAL_EIGHT_FIELD_SPANS_NOT_SEMANTIC_OR_RENDER_ACCEPTANCE'
    except (ValueError, OSError, KeyError, TypeError, AttributeError, ET.ParseError, zipfile.BadZipFile, KeyboardInterrupt) as error:
        row.update(**runtime.io.safe_failure(error))
    finally:
        guard.close()
        row.update(cleanup=guard.cleanup, fresh_inputs=0 if q is None else len(q.snapshots),
                   final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
                   elapsed_seconds=round(time.monotonic()-start, 3),
                   source_pins=[] if q is None else list(q.snapshots.values()),
                   system_CPU_max=max((s['system_cpu_percent'] for s in guard.samples), default=None),
                   available_RAM_min_percent=min((s['available_ram_percent'] for s in guard.samples), default=None))
        pin = entry.publish(OUTPUT, row)
        summary = [dict(case=v['case_index'], display=v['display'],
            stages={k: dict(crossrefs=z['crossref_count'], dirty=[f['dirty'] for f in z['crossrefs']],
                            display_lengths=[f['display_characters'] for f in z['crossrefs']]) for k, z in v['stages'].items()}) for v in row['cases']]
        print(json.dumps({**{k: row.get(k) for k in ('state', 'error_code', 'cleanup', 'fresh_inputs', 'final_fresh_hashes',
            'elapsed_seconds', 'system_CPU_max', 'available_RAM_min_percent')}, 'cases': summary, 'receipt': pin}), flush=True)
    return 0 if row['state'].startswith('OBSERVED633_') and row['cleanup'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
