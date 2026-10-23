"""Read-only current capture rendering, not a replacement Native capture or Gate.

Keep PDF and native BMP profiles separate; no mask, crop, tolerance, resizing or
blank-page acceptance. Static Link annotations are compared, never activated.
"""
import hashlib
import ast
import io
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import time

from PIL import Image
from pypdf import PdfReader
import reference_pdf_render as pixels
import inspect_prepared_bookmark633 as previous
import audit_evidence_io as audit
import metadata_forensic_retention615 as retention
from verify_prepared_bookmark631 import command

r = previous.r
SELF = 'tools/p09/inspect_prepared_bookmark637_render.py'
OUTPUT = 'implementation/p09/evidence/p09-361-prepared-bookmark637-render003.v1.json'
DIRECTORY = 'implementation/p09/evidence/private/p09-361-prepared-bookmark637-render003'
SPOOL = 'implementation/p09/evidence/private/p09-361-prepared-bookmark637-render003-forensic'
TEST = 'tools/p09/tests/test_prepared_bookmark637_render.py'
TRACE_TEST = 'tools/p09/tests/test_prepared_bookmark637_trace_pin.py'
PRIOR = 'implementation/p09/evidence/p09-361-prepared-bookmark637-render002.v1.json'
ARCHIVE = 'implementation/p09/source-archive/p361-prepared-bookmark637-render002/inspect_prepared_bookmark637_render.py'
POPLER = Path(sys.executable).parent.parent/'native/poppler/Library/bin'


def require(ok, code):
    if not ok:
        raise ValueError('P637_' + code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def direct(path):
    for part in Path(path).absolute().parents:
        require(not part.is_symlink() and not part.is_junction(), 'DIRECT_PARENT')
    require(not Path(path).is_symlink() and not Path(path).is_junction(), 'DIRECT_FILE')


def read(q, pin):
    require(q.pin(pin['path']) == pin and pin['bytes'] <= 16*1024*1024, 'EXACT_CAPTURE_PIN')
    path = q.root/pin['path']
    direct(path)
    with path.open('rb') as stream:
        raw = stream.read(pin['bytes']+1)
    require(len(raw) == pin['bytes'] and sha(raw) == pin['sha256'], 'EXACT_PARSE_BYTES')
    q.checkpoint()
    return raw


def numbers(values, length=None):
    result = [float(v) for v in values]
    require((length is None or len(result) == length) and len(result) <= 16
        and all(math.isfinite(v) and abs(v) <= 14400 for v in result), 'FINITE_GEOMETRY')
    return result


def annotation(value):
    a = value.get_object()
    require(set(a) <= {'/Type', '/Subtype', '/Rect', '/C', '/Border', '/A', '/H', '/F'}
        and a.get('/Type') == '/Annot' and a.get('/Subtype') == '/Link', 'STATIC_LINK_PROFILE_ONLY')
    action = a['/A'].get_object()
    require(set(action) == {'/S', '/URI'} and action['/S'] == '/URI'
        and isinstance(action['/URI'], str) and len(action['/URI']) <= 4096, 'STATIC_URI_NOT_EXECUTION')
    require(type(a.get('/F', 0)) is not bool and int(a.get('/F', 0)) == a.get('/F', 0), 'ANNOTATION_FLAGS')
    return dict(kind='static_link', rect=numbers(a['/Rect'], 4), color=numbers(a.get('/C', [])),
        border=numbers(a.get('/Border', [])), highlight=str(a.get('/H', '')),
        flags=int(a.get('/F', 0)), uri_sha256=sha(action['/URI'].encode('utf-8')))


def pdf_metadata(raw):
    require(type(raw) is bytes and 0 < len(raw) <= 2*1024*1024 and raw.startswith(b'%PDF-'), 'PDF_BOUND')
    pdf = PdfReader(io.BytesIO(raw), strict=True)
    root = pdf.trailer['/Root'].get_object()
    require(not pdf.is_encrypted and not any(root.get(k) for k in ('/AcroForm', '/OpenAction', '/AA')),
        'NO_FORM_OR_DOCUMENT_ACTION')
    require(0 < len(pdf.pages) <= 8, 'PAGE_COUNT')
    rows = []
    for page in pdf.pages:
        require(not page.get('/AA') and float(page.get('/UserUnit', 1)) == 1, 'PAGE_ACTION_OR_UNITS')
        media, crop = numbers(page.mediabox, 4), numbers(page.cropbox, 4)
        require(media[0] <= crop[0] < crop[2] <= media[2] and media[1] <= crop[1] < crop[3] <= media[3], 'PAGE_BOUNDS')
        rotation = page.get('/Rotate', 0)
        require(type(rotation) is not bool and int(rotation) == rotation and rotation in (0, 90, 180, 270), 'ROTATION')
        pixels.font_scope(page.get('/Resources', {}))  # Existing embedded-font restrictions unchanged.
        width, height = media[2]-media[0], media[3]-media[1]
        if rotation in (90, 270):
            width, height = height, width
        sizes = {str(dpi): [math.ceil(width*dpi/72), math.ceil(height*dpi/72)] for dpi in (96, 192)}
        require(all(0 < w*h <= 8_000_000 for w, h in sizes.values()), 'RASTER_PIXEL_BOUND')
        annotations = pixels.resolved(page.get('/Annots', []))
        require(len(annotations) <= 128, 'ANNOTATION_COUNT')
        text = page.extract_text() or ''
        require(len(text.encode('utf-8')) <= 65536, 'TEXT_BOUND')
        rows.append(dict(media_box=media, crop_box=crop, rotation=int(rotation), sizes=sizes,
            annotations=[annotation(a) for a in annotations], text_sha256=sha(text.encode('utf-8')), text_characters=len(text)))
    return rows


def image(raw, expected_format, size=None):
    im = Image.open(io.BytesIO(raw))
    require(im.format == expected_format and im.mode == 'RGB'
        and 0 < im.width*im.height <= 8_000_000 and getattr(im, 'n_frames', 1) == 1, 'IMAGE_PROFILE')
    require(size is None or list(im.size) == size, 'IMAGE_GEOMETRY')
    im.load()
    return im


def compare_images(a, b):
    value = pixels.pixels(a, b)
    nonblank = value.get('left_nonwhite_bbox') is not None and value.get('right_nonwhite_bbox') is not None
    value['both_nonblank'] = nonblank
    value['accepted_pair'] = value['state'] == 'exact_pixels' and nonblank
    return value


def render(guard, args, row):
    owned = capture = None
    step = dict(stage='poppler_single_page', cleanup=False)
    row['steps'].append(step)
    start = time.monotonic()
    try:
        env = {k: v for k, v in os.environ.items() if not k.upper().startswith(('FONTCONFIG_', 'FREETYPE_'))}
        owned = r.shared.OwnedSQLJobProcess(args, windows=guard.windows, allowed_executables=[args[0]],
            cwd=r.c.ROOT, checkpoint=guard.check, env=env)
        capture = r.shared.BoundedProcessCapture(owned, output_limit=32768, parse_markers=False)
        while True:
            guard.check()
            require(time.monotonic()-start < 30, 'RENDER_DEADLINE')
            try:
                out, err = capture.communicate(timeout=.5)
                owned.observe()
                break
            except subprocess.TimeoutExpired:
                capture.progress()
                owned.observe()
        step.update(exit_code=owned.returncode, stdout_bytes=len(out.encode()), stderr_bytes=len(err.encode()),
            stdout_sha256=sha(out.encode()), stderr_sha256=sha(err.encode()))
        require(owned.returncode == 0 and not out and not err, 'CLEAN_RENDER')
    finally:
        if owned is not None:
            owned.kill()
            owned.wait(timeout=2)
            if capture is not None:
                capture.close()
            owned.close()
            step.update(cleanup=owned.profile['cleanup_confirmed'], owned_job=owned.profile)


def inspect_pdf(guard, q, output, index, capture, row):
    pins = [capture['artifacts'][s+'.pdf'] for s in ('initial', 'reopened')]
    meta = [pdf_metadata(read(q, pin)) for pin in pins]
    require(len(meta[0]) == len(meta[1]), 'SAME_PDF_PAGE_COUNT')
    cases = []
    for page in range(len(meta[0])):
        profiles = []
        for dpi in (96, 192):
            images = []
            try:
                for label, pin, metadata in zip(('initial', 'reopened'), pins, meta, strict=True):
                    name = f'c{index:02}-{label}-p{page+1:03}-{dpi}'
                    path = output/name
                    require(not path.with_suffix('.png').exists(), 'NEW_RENDER_ONLY')
                    render(guard, [str(POPLER/'pdftoppm.exe'), '-f', str(page+1), '-l', str(page+1), '-singlefile',
                        '-r', str(dpi), '-freetype', 'yes', '-aa', 'yes', '-aaVector', 'yes', '-thinlinemode', 'none',
                        '-png', str(q.root/pin['path']), str(path)], row)
                    render_pin = q.pin(path.with_suffix('.png').relative_to(q.root).as_posix())
                    require(render_pin['bytes'] <= 16*1024*1024, 'PNG_BYTE_BOUND')
                    images.append(image(read(q, render_pin), 'PNG', metadata[page]['sizes'][str(dpi)]))
                    row['derived_images'].append(render_pin)
                profiles.append(dict(dpi=dpi, **compare_images(*images)))
            finally:
                for im in images:
                    im.close()
        cases.append(dict(page=page+1, metadata_equal=meta[0][page] == meta[1][page], profiles=profiles))
    return dict(case_index=index, media='PDF_embedded_fonts_static_link_profile', source_pins=pins,
        page_metadata=meta, pages=cases, accepted_pair=all(p['metadata_equal'] and all(v['accepted_pair'] for v in p['profiles']) for p in cases))


def trace_pin_matches(pin, detail):
    require(set(detail['pin']) == {'bytes', 'sha256'}
        and {k: pin[k] for k in ('bytes', 'sha256')} == detail['pin'], 'NATIVE_TRACE_EXACT_ARTIFACT')


def inspect_bmp(guard, q, index, capture):
    trace_pin = capture['artifacts']['case-trace.json']
    trace = json.loads(read(q, trace_pin).decode('utf-8-sig'))
    left = sorted(n for n in capture['artifacts'] if n.startswith('initial-page-') and n.endswith('.bmp'))
    right = sorted(n for n in capture['artifacts'] if n.startswith('reopened-page-') and n.endswith('.bmp'))
    require(1 <= len(left) == len(right) <= 8, 'WHOLE_NATIVE_PAGE_INVENTORY')
    pages = []
    for i, names in enumerate(zip(left, right, strict=True)):
        images = []
        try:
            for label, name in zip(('initial', 'reopened'), names, strict=True):
                require(name == f'{label}-page-{i+1:03}.bmp', 'CONTIGUOUS_NATIVE_PAGES')
                detail = trace['artifacts'][name]
                require(detail['page_count'] == len(left) and detail['page_number'] == i
                    and detail['bitmap']['resolution'] == 96 and detail['bitmap']['depth'] == 24, 'NATIVE_TRACE_PAGE_BINDING')
                pin = capture['artifacts'][name]
                trace_pin_matches(pin, detail)
                images.append(image(read(q, pin), 'BMP', [detail['bitmap']['width'], detail['bitmap']['height']]))
            pages.append(dict(page=i+1, dpi=96, **compare_images(*images)))
            guard.check(force=True)
        finally:
            for im in images:
                im.close()
    return dict(case_index=index, media='Native_CreatePageImage_BMP96_RGB24', trace_pin=trace_pin,
        source_pins=[capture['artifacts'][n] for n in left+right], pages=pages,
        accepted_pair=all(p['accepted_pair'] for p in pages))


def main():
    require(sys.argv[1:] == ['--existing-captures-only'], 'READONLY_FIXED_MODE')
    require(not (r.c.ROOT/OUTPUT).exists() and not (r.c.ROOT/DIRECTORY).exists(), 'IMMUTABLE_RUN')
    r.tools.select_own_single_cpu()
    r.shared.host.configure_host_policy(r.c)
    guard = r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))()
    q = external = None
    start = time.monotonic()
    row = dict(state='FAILED637_EXISTING_RENDER_INSPECTION', cases=[], steps=[], derived_images=[],
        Native_or_COM_started=False, old_tests_or_consumed_trials_replayed=False,
        cross_media_equivalence_claimed=False, mask_crop_tolerance_or_resize=False, P09_complete=False)
    try:
        guard.acquire()
        q = r.a.AcceptanceReader(r.c.ROOT, guard.check)
        for path in (SELF, TEST, TRACE_TEST, ARCHIVE, pixels.__file__, previous.SELF, 'tools/p09/prepared_bookmark632_receipt.py',
                'tools/p09/metadata_forensic_retention615.py', 'implementation/p09/tools/prepared-bookmark631-ports.ps1'):
            q.pin(Path(path).relative_to(r.c.ROOT).as_posix() if Path(path).is_absolute() else path)
        original = previous.carrier.unpack(q.json(previous.RECOVERED), guard.check)
        require(q.snapshots[previous.RECOVERED]['sha256'] == previous.RECOVERED_SHA and original['cleanup'] is True, 'EXACT_RECOVERED_CAPTURES')
        captures = original['retained_cases']['cases']+original['artifacts']['cases']
        require(len(captures) == 8, 'EIGHT_CURRENT_CASES')
        old = previous.entry.codec.unpack(q.json(PRIOR))
        require(q.snapshots[PRIOR]['sha256'] == 'e89d3157dd0f65b4f595c0bb6a5c3315328cac2370d573268aaafeb7afa05f2b'
            and old['cleanup'] is True and old['error_code'] == 'P637_NATIVE_TRACE_EXACT_ARTIFACT'
            and [v['case_index'] for v in old['cases']] == [1, 2]
            and all(v['accepted_pair'] is True for v in old['cases']), 'EXACT_CLOSED_PDF_RESULTS_FROM_PARTIAL_FAILURE')
        oldpins = {p['path']: p for p in old['source_pins']}
        require(q.snapshots[ARCHIVE]['sha256'] == oldpins[SELF]['sha256'], 'PRESERVED_OLD_SOURCE')
        def functions(text):
            return {n.name: ast.dump(n, include_attributes=False) for n in ast.parse(text).body if isinstance(n, ast.FunctionDef)}
        before, current = functions(q.text(ARCHIVE)), functions(q.text(SELF))
        for name in ('require', 'sha', 'direct', 'read', 'numbers', 'annotation', 'pdf_metadata', 'image', 'compare_images', 'render', 'inspect_pdf'):
            require(before[name] == current[name], 'RETAINED_PDF_AND_EIGHT_CONTROL_BODIES_UNCHANGED')
        for path, pin in oldpins.items():
            if path != SELF:
                require(q.pin(path) == pin, 'RETAINED_INPUT_AND_DERIVED_PNG_UNCHANGED')
        require(len(old['steps']) == 9 and all(s['cleanup'] is True and s['exit_code'] == 0 for s in old['steps']), 'RETAINED_EIGHT_RENDER_JOBS_CLOSED')
        require(old['steps'][0]['result'] == dict(run=8, errors=0, failures=0, skipped=0), 'RETAINED_EIGHT_CONTROLS_NOT_REPLAYED')
        row.update(retained_PDF_cases=old['cases'], retained_control_count=8, retained_PDF_render_jobs_not_replayed=8,
            retained_receipt=q.snapshots[PRIOR], derived_images=old['derived_images'])
        tests = command(guard, [sys.executable, '-B', str(r.c.ROOT/TRACE_TEST)], r.audit.environment(), row, 'new_trace_pin_controls2')
        require({k: tests[k] for k in ('run', 'errors', 'failures', 'skipped')} == dict(run=2, errors=0, failures=0, skipped=0), 'NEW_TWO_TRACE_CONTROLS')
        external = audit.AuditEvidenceReader(POPLER, guard.check)
        runtime = sorted([POPLER/'pdftoppm.exe', *POPLER.glob('*.dll')])
        require(1 < len(runtime) <= 256 and sum(p.stat().st_size for p in runtime) <= 1024*1024*1024, 'BOUNDED_POPPLER_RUNTIME')
        direct(POPLER)
        for p in runtime:
            direct(p)
            external.pin(p.name)
        require(list(external.snapshots.values()) == old['poppler_runtime'], 'UNCHANGED_RETAINED_PDF_RENDER_RUNTIME')
        row['poppler_runtime'] = list(external.snapshots.values())
        output = r.c.ROOT/DIRECTORY
        direct(output.parent)
        output.mkdir()
        row['cases'] = old['cases']
        for index, capture in enumerate(captures, 1):
            require(capture['source_case_index'] == index, 'EXACT_CASE_ORDER')
            if index <= 2:
                require(row['cases'][index-1]['source_pins'] == [capture['artifacts'][s+'.pdf'] for s in ('initial', 'reopened')], 'RETAINED_CURRENT_PDF_PROFILE')
                continue
            value = inspect_bmp(guard, q, index, capture)
            row['cases'].append(value)
            print(json.dumps(dict(state='RENDER637_CASE_OBSERVED', case_index=index, accepted_pair=value['accepted_pair'],
                changed_pixels=[p.get('changed_pixels') for p in value['pages']], system_CPU=guard.samples[-1]['system_cpu_percent'])), flush=True)
        q.finish()
        external.finish()
        guard.check(force=True)
        accepted = [v['case_index'] for v in row['cases'] if v['accepted_pair']]
        row.update(state='OBSERVED637_COMPLETE_RENDER_INSPECTION_NOT_FULL_F11', completed_cases=8,
            accepted_same_media_pairs=accepted, mismatched_or_blank_cases=[v['case_index'] for v in row['cases'] if not v['accepted_pair']])
    except (ValueError, OSError, KeyError, TypeError, AttributeError, subprocess.SubprocessError, KeyboardInterrupt) as error:
        row.update(**previous.runtime.io.safe_failure(error))
        if isinstance(error, ValueError) and re.fullmatch(r'(?:P637_[A-Z0-9_]{1,100}|p57_[a-z0-9_]{1,100})', str(error)):
            row['error_code'] = str(error)
        trace = error.__traceback__
        while trace is not None:
            if Path(trace.tb_frame.f_globals.get('__file__', '')).name == Path(SELF).name:
                row['local_error_site'] = dict(function=trace.tb_frame.f_code.co_name, line=trace.tb_lineno)
            trace = trace.tb_next
    finally:
        guard.close()
        row.update(cleanup=guard.cleanup and all(s['cleanup'] for s in row['steps']),
            source_pins=[] if q is None else list(q.snapshots.values()),
            fresh_inputs=0 if q is None else len(q.snapshots), final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
            runtime_fresh_inputs=0 if external is None else len(external.snapshots),
            runtime_final_fresh_hashes=0 if external is None else external.final_fresh_hashes,
            elapsed_seconds=round(time.monotonic()-start, 3),
            system_CPU_max=max((v['system_cpu_percent'] for v in guard.samples), default=None),
            available_RAM_min_percent=min((v['available_ram_percent'] for v in guard.samples), default=None))
        row, retained = retention.retain(r.c.ROOT, SPOOL, row)
        pin = previous.entry.publish(OUTPUT, row)
        print(json.dumps({**{k: row.get(k) for k in ('state', 'error_code', 'cleanup', 'completed_cases', 'accepted_same_media_pairs',
            'mismatched_or_blank_cases', 'fresh_inputs', 'final_fresh_hashes', 'runtime_fresh_inputs', 'runtime_final_fresh_hashes',
            'elapsed_seconds', 'system_CPU_max', 'available_RAM_min_percent')}, 'receipt': pin}), flush=True)
    return 0 if row['state'].startswith('OBSERVED637_') and row['cleanup'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
