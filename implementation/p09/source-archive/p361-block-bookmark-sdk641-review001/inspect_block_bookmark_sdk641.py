"""Pinned SDK BookMark parameter/action page review; never COM activation.

Read-only primary documentation, not exact-build runtime behavior or Native
capture permission. Preserve derived page images privately for visual review.
"""
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import time
from pypdf import PdfReader

import named_style_verification_runtime as r
import inspect_prepared_bookmark637_render as render
import audit_evidence_io as audit
import metadata_forensic_retention615 as retention
import run_prepared_bookmark_native631 as publisher

SELF = 'tools/p09/inspect_block_bookmark_sdk641.py'
OUTPUT = 'implementation/p09/evidence/p09-361-block-bookmark-sdk641-review001.v1.json'
DIRECTORY = 'implementation/p09/evidence/private/p09-361-block-bookmark-sdk641-review001'
DOCS = (
    ('parameter', 'implementation/p00/source-archive/original/automation/ParameterSetTable_2504.pdf',
        '6fa10e0ae69711af99a03e54c321c6c922796bd943badf8c21b2c7dfb780ad6e'),
    ('action', 'implementation/p00/source-archive/original/automation/ActionTable_2504.pdf',
        'bb876a95ea4e0f4b052c94188a1390b5f981161223759f59f52fc324c8130a87'))


def require(ok, code):
    if not ok: raise ValueError('P641_'+code)


def main():
    require(sys.argv[1:] == ['--read-only-sdk-pages'], 'READONLY_MODE')
    require(not (r.c.ROOT/OUTPUT).exists() and not (r.c.ROOT/DIRECTORY).exists(), 'IMMUTABLE_RUN')
    r.tools.select_own_single_cpu()
    r.shared.host.configure_host_policy(r.c)
    guard = r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))()
    q = external = None
    start = time.monotonic()
    row = dict(state='FAILED641_SDK_BOOKMARK_REVIEW', pages=[], steps=[], derived_images=[],
        Native_or_COM_started=False, exact_2020_runtime_behavior_qualified=False,
        block_HWPX_mapping_or_content_qualified=False, native_execution_authorized=False, P09_complete=False)
    try:
        guard.acquire()
        q = r.a.AcceptanceReader(r.c.ROOT, guard.check)
        q.pin(SELF); q.pin(render.SELF)
        output = r.c.ROOT/DIRECTORY
        render.direct(output.parent); output.mkdir()
        external = audit.AuditEvidenceReader(render.POPLER, guard.check)
        for path in sorted([render.POPLER/'pdftoppm.exe', *render.POPLER.glob('*.dll')]):
            render.direct(path); external.pin(path.name)
        require(1 < len(external.snapshots) <= 256, 'RENDERER_FILE_BOUND')
        row['renderer_pins'] = list(external.snapshots.values())
        for kind, path, wanted in DOCS:
            pin = q.pin(path)
            require(pin['sha256'] == wanted and pin['bytes'] <= 4*1024*1024, 'PINNED_PRIMARY_SDK')
            pdf = PdfReader(io.BytesIO(render.read(q,pin)),strict=True)
            require(not pdf.is_encrypted and 1 <= len(pdf.pages) <= 512, 'MANUAL_PAGE_BOUND')
            hits=[]
            limit=min(len(pdf.pages),40 if kind=='parameter' else 16)
            for i in range(limit):
                guard.check()
                text=pdf.pages[i].extract_text() or ''
                require(len(text.encode('utf-8')) <= 65536, 'PAGE_TEXT_BOUND')
                if kind=='parameter':
                    found=bool(re.search(r'(?im)^\s*[0-9]+\)\s*bookmark\s*:',text))
                else:
                    found=bool(re.search(r'(?im)^\s*bookmark(?:\s|$)',text))
                if found:
                    hits.append((i,text))
            require(1 <= len(hits) <= 4, 'EXACT_BOOKMARK_PAGE_CANDIDATES')
            for index,text in hits:
                prefix=output/f'{kind}-page-{index+1:03}'
                render.render(guard,[str(render.POPLER/'pdftoppm.exe'),'-f',str(index+1),'-l',str(index+1),
                    '-singlefile','-r','144','-png',str(q.root/path),str(prefix)],row)
                image_pin=q.pin(prefix.with_suffix('.png').relative_to(q.root).as_posix())
                with render.image(render.read(q,image_pin),'PNG') as image:
                    size=list(image.size)
                # No full manual excerpt: source and rendered page remain bound.
                row['pages'].append(dict(kind=kind, source=pin, page=index+1,
                    extracted_text_sha256=hashlib.sha256(text.encode()).hexdigest(),
                    matching_ASCII_identifiers=sorted(set(re.findall(r'\b(?:BookMark|Bookmark|Command|Name|PIT_[A-Z0-9]+)\b',text))),
                    rendered_page=image_pin,raster_size=size))
                row['derived_images'].append(image_pin)
        q.finish(); external.finish(); guard.check(force=True)
        row['state']='OBSERVED641_PRIMARY_SDK_BOOKMARK_PAGES_RENDERED_NOT_NATIVE_OR_BLOCK_MAPPING'
    except (ValueError,OSError,KeyError,TypeError,AttributeError,KeyboardInterrupt) as error:
        row.update(**publisher.runtime.io.safe_failure(error))
        if isinstance(error,ValueError) and re.fullmatch(r'P641_[A-Z0-9_]{1,100}',str(error)): row['error_code']=str(error)
    finally:
        guard.close()
        row.update(cleanup=guard.cleanup and all(s['cleanup'] for s in row['steps']),
            source_pins=[] if q is None else list(q.snapshots.values()),
            fresh_inputs=0 if q is None else len(q.snapshots),final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
            runtime_fresh_inputs=0 if external is None else len(external.snapshots),
            runtime_final_fresh_hashes=0 if external is None else external.final_fresh_hashes,
            elapsed_seconds=round(time.monotonic()-start,3),
            system_CPU_max=max((s['system_cpu_percent'] for s in guard.samples),default=None),
            available_RAM_min_percent=min((s['available_ram_percent'] for s in guard.samples),default=None))
        row,retained=retention.retain(r.c.ROOT,DIRECTORY+'-forensic',row)
        pin=publisher.publish(OUTPUT,row)
        print(json.dumps({**{k:row.get(k) for k in ('state','error_code','cleanup','fresh_inputs','final_fresh_hashes',
            'runtime_fresh_inputs','runtime_final_fresh_hashes','elapsed_seconds','system_CPU_max','available_RAM_min_percent')},
            'pages':[dict(kind=p['kind'],page=p['page'],identifiers=p['matching_ASCII_identifiers']) for p in row['pages']],
            'receipt':pin}),flush=True)
    return 0 if row['state'].startswith('OBSERVED641_') and row['cleanup'] else 2

if __name__=='__main__': raise SystemExit(main())
