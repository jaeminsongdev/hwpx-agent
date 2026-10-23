"""Lossless BMP-to-PNG review inputs, original pixels/geometry and evidence intact.

No Native, PDF rerender, crop, resize, mask or claim that an image was visually
reviewed by this program. The later human/assistant review is separate evidence.
"""
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import time

import PIL
from PIL import Image, BmpImagePlugin, PngImagePlugin, _imaging
import pypdf
import inspect_prepared_bookmark637_render as render
import audit_evidence_io as audit
import metadata_forensic_retention615 as retention

r = render.r
SELF = 'tools/p09/prepare_bookmark638_visual_review.py'
PRIOR = 'implementation/p09/evidence/p09-361-prepared-bookmark637-render003.v1.json'
OUTPUT = 'implementation/p09/evidence/p09-361-prepared-bookmark638-review001.v1.json'
DIRECTORY = 'implementation/p09/evidence/private/p09-361-prepared-bookmark638-review001'


def require(ok, code):
    if not ok:
        raise ValueError('P638_' + code)


def main():
    require(sys.argv[1:] == ['--prepare-lossless-review-only'], 'READONLY_FIXED_MODE')
    require(not (r.c.ROOT/OUTPUT).exists() and not (r.c.ROOT/DIRECTORY).exists(), 'IMMUTABLE_RUN')
    r.tools.select_own_single_cpu()
    r.shared.host.configure_host_policy(r.c)
    guard = r.shared.baseline.guard_type(r.shared.final.guard_type(r.a.Guard))()
    q = external = None
    start = time.monotonic()
    row = dict(state='FAILED638_REVIEW_INPUTS', previews=[], visual_review_performed_by_program=False,
        Native_started=False, PDF_renders_or_old_tests_replayed=False, mask_crop_or_resize=False, P09_complete=False)
    try:
        guard.acquire()
        q = r.a.AcceptanceReader(r.c.ROOT, guard.check)
        q.pin(SELF)
        prior = render.previous.entry.codec.unpack(q.json(PRIOR))
        require(q.snapshots[PRIOR]['sha256'] == '80876d96f410d252977e4035a856f10c8fa1b47ca7c7f55bc605d8372a68e4a6'
            and prior['state'] == 'OBSERVED637_COMPLETE_RENDER_INSPECTION_NOT_FULL_F11'
            and prior['fresh_inputs'] == prior['final_fresh_hashes'] == 41
            and prior['runtime_fresh_inputs'] == prior['runtime_final_fresh_hashes'] == 122
            and prior['cleanup'] is True and prior['accepted_same_media_pairs'] == list(range(1, 9))
            and prior['mismatched_or_blank_cases'] == [], 'EXACT_COMPLETE_PRIOR')
        oldpins = {p['path']: p for p in prior['source_pins']}
        require(q.pin(render.SELF) == oldpins[render.SELF], 'COMPARISON_SOURCE_UNCHANGED')
        python_root = Path(sys.executable).parent
        external = audit.AuditEvidenceReader(python_root, guard.check)
        modules = [Image, BmpImagePlugin, PngImagePlugin, _imaging, pypdf]
        paths = [Path(sys.executable), *(Path(m.__file__) for m in modules)]
        for path in paths:
            render.direct(path)
            external.pin(path.relative_to(python_root).as_posix())
        row['review_runtime'] = dict(pillow_version=PIL.__version__, pypdf_version=pypdf.__version__,
            python_version=list(sys.version_info[:3]), pins=list(external.snapshots.values()))
        output = r.c.ROOT/DIRECTORY
        render.direct(output.parent)
        output.mkdir()
        for case in prior['cases']:
            index = case['case_index']
            if index <= 2:
                for label in ('initial', 'reopened'):
                    matches = [p for p in prior['derived_images'] if p['path'].endswith(f'c{index:02}-{label}-p001-192.png')]
                    require(len(matches) == 1, 'EXACT_EXISTING_PDF_PREVIEW')
                    pin = matches[0]
                    with render.image(render.read(q, pin), 'PNG') as im:
                        require(hashlib.sha256(im.tobytes()).hexdigest() == case['pages'][0]['profiles'][1][label.replace('initial', 'left').replace('reopened', 'right')+'_rgb_sha256'], 'EXISTING_PDF_PIXELS')
                    row['previews'].append(dict(case_index=index, stage=label, media='existing_PDF_192dpi', pin=pin))
            else:
                require(len(case['pages']) == 1 and case['pages'][0]['accepted_pair'] is True, 'EXACT_SINGLE_NATIVE_PAGE_PROFILE')
                for label in ('initial', 'reopened'):
                    matches = [p for p in case['source_pins'] if p['path'].endswith(f'{label}-page-001.bmp')]
                    require(len(matches) == 1, 'EXACT_NATIVE_PREVIEW_SOURCE')
                    pin = matches[0]
                    with render.image(render.read(q, pin), 'BMP') as im:
                        rgb_sha = hashlib.sha256(im.tobytes()).hexdigest()
                        side = 'left' if label == 'initial' else 'right'
                        require(rgb_sha == case['pages'][0][side+'_rgb_sha256'], 'ACTUAL_NATIVE_PIXEL_HASH')
                        path = output/f'c{index:02}-{label}-p001.png'
                        require(not path.exists(), 'NEW_PREVIEW_ONLY')
                        im.save(path, format='PNG', dpi=(96, 96))
                        newpin = q.pin(path.relative_to(q.root).as_posix())
                        with render.image(render.read(q, newpin), 'PNG', list(im.size)) as decoded:
                            require(hashlib.sha256(decoded.tobytes()).hexdigest() == rgb_sha, 'LOSSLESS_PIXELS_AND_GEOMETRY')
                    row['previews'].append(dict(case_index=index, stage=label, media='Native_BMP_lossless_PNG_96dpi',
                        source_pin=pin, pin=newpin, rgb_sha256=rgb_sha))
            guard.check(force=True)
        q.finish()
        external.finish()
        guard.check(force=True)
        row.update(state='OBSERVED638_CURRENT8_LOSSLESS_REVIEW_INPUTS_NOT_AUTOMATIC_VISUAL_ACCEPTANCE',
            cases=8, review_images=16, newly_converted_BMP_images=12, PDF_images_reused=4)
    except (ValueError, OSError, KeyError, TypeError, AttributeError, KeyboardInterrupt) as error:
        row.update(**render.previous.runtime.io.safe_failure(error))
        if isinstance(error, ValueError) and re.fullmatch(r'P638_[A-Z0-9_]{1,100}', str(error)):
            row['error_code'] = str(error)
        trace = error.__traceback__
        while trace is not None:
            if Path(trace.tb_frame.f_globals.get('__file__', '')).name == Path(SELF).name:
                row['local_error_site'] = dict(function=trace.tb_frame.f_code.co_name, line=trace.tb_lineno)
            trace = trace.tb_next
    finally:
        guard.close()
        row.update(cleanup=guard.cleanup, source_pins=[] if q is None else list(q.snapshots.values()),
            fresh_inputs=0 if q is None else len(q.snapshots), final_fresh_hashes=0 if q is None else q.final_fresh_hashes,
            runtime_fresh_inputs=0 if external is None else len(external.snapshots),
            runtime_final_fresh_hashes=0 if external is None else external.final_fresh_hashes,
            elapsed_seconds=round(time.monotonic()-start, 3),
            system_CPU_max=max((s['system_cpu_percent'] for s in guard.samples), default=None),
            available_RAM_min_percent=min((s['available_ram_percent'] for s in guard.samples), default=None))
        row, retained = retention.retain(r.c.ROOT, DIRECTORY+'-forensic', row)
        pin = render.previous.entry.publish(OUTPUT, row)
        print(json.dumps({**{k: row.get(k) for k in ('state', 'error_code', 'cleanup', 'review_images', 'fresh_inputs',
            'final_fresh_hashes', 'elapsed_seconds', 'system_CPU_max', 'available_RAM_min_percent')}, 'receipt': pin}), flush=True)
    return 0 if row['state'].startswith('OBSERVED638_') and row['cleanup'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
