"""Bounded, embedded-font, full-page PDF comparisons. Never activates Hangul."""
import hashlib
import io
import math
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

import PIL
from PIL import Image, ImageChops
import pypdf
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
DPIS = (96, 192)
MAX_BYTES = 32 * 1024 * 1024
MAX_PAGES = 32
MAX_PAGE_PIXELS = 8_000_000
MAX_TOTAL_PIXELS = 128_000_000


def require(condition, code):
    if not condition:
        raise ValueError(code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def resolved(value):
    return value.get_object() if hasattr(value, 'get_object') else value


def unlinked(path):
    path = Path(path).absolute()
    for part in (path, *path.parents):
        require(not part.is_symlink() and not (part.exists() and part.is_junction()), 'p57_linked_path')
    return path


def bounded(path, expected=None, limit=MAX_BYTES):
    path = unlinked(path)
    before = path.stat()
    require(path.is_file() and 0 < before.st_size <= limit, 'p57_file_boundary')
    with path.open('rb') as stream:
        raw = stream.read(limit + 1)
    after = path.stat()
    require(before.st_size == after.st_size == len(raw) and before.st_mtime_ns == after.st_mtime_ns,
            'p57_file_changed')
    require(expected is None or sha(raw) == expected, 'p57_input_sha256')
    return raw


def font_scope(resources, seen=None, depth=0):
    """No fallback to unbound Windows/fontconfig fonts. Type3 glyph programs are internal."""
    require(depth <= 16, 'p57_resource_depth')
    seen = set() if seen is None else seen
    resources = resolved(resources)
    marker = id(resources)
    if marker in seen:
        return
    seen.add(marker)
    require(len(seen) <= 1024, 'p57_resource_count')
    require(not resources.get('/Pattern'), 'p57_pattern_resources_unsupported')
    for value in resources.get('/ExtGState', {}).values():
        require(not resolved(value).get('/Font'), 'p57_graphics_state_font_unsupported')
    fonts = resolved(resources.get('/Font', {}))
    require(len(fonts) <= 128, 'p57_font_count')
    for value in fonts.values():
        font = resolved(value)
        if font.get('/Subtype') == '/Type3':
            require(bool(font.get('/CharProcs')), 'p57_type3_glyphs_absent')
            font_scope(font.get('/Resources', {}), seen, depth + 1)
            continue
        for child in font.get('/DescendantFonts', [font]):
            child = resolved(child)
            descriptor = child.get('/FontDescriptor')
            require(descriptor is not None, 'p57_external_font_rejected')
            descriptor = resolved(descriptor)
            require(any(descriptor.get(key) is not None for key in ('/FontFile', '/FontFile2', '/FontFile3')),
                    'p57_external_font_rejected')
    objects = resolved(resources.get('/XObject', {}))
    require(len(objects) <= 1024, 'p57_resource_count')
    for value in objects.values():
        obj = resolved(value)
        if obj.get('/Subtype') == '/Form' and '/Resources' in obj:
            font_scope(obj['/Resources'], seen, depth + 1)


def geometry(raw):
    require(type(raw) is bytes and 0 < len(raw) <= MAX_BYTES and raw.startswith(b'%PDF-'),
            'p57_pdf_boundary')
    reader = PdfReader(io.BytesIO(raw), strict=True)
    require(not reader.is_encrypted, 'p57_encrypted_pdf')
    require(not reader.trailer['/Root'].get('/AcroForm'), 'p57_interactive_pdf_unsupported')
    require(0 < len(reader.pages) <= MAX_PAGES, 'p57_page_count')
    pages = []
    total = 0
    for page in reader.pages:
        media = [float(v) for v in page.mediabox]
        crop = [float(v) for v in page.cropbox]
        require(all(math.isfinite(v) and abs(v) <= 14400 for v in media + crop), 'p57_page_geometry')
        require(media[0] <= crop[0] < crop[2] <= media[2] and media[1] <= crop[1] < crop[3] <= media[3],
                'p57_page_geometry')
        rotation = page.get('/Rotate', 0)
        require(type(rotation) is not bool and float(rotation).is_integer() and int(rotation) in (0, 90, 180, 270),
                'p57_page_rotation')
        # Poppler/pypdf UserUnit handling is not assumed equivalent; unsupported values reject.
        require(float(page.get('/UserUnit', 1)) == 1, 'p57_user_unit_unsupported')
        font_scope(page.get('/Resources', {}))
        require(not page.get('/Annots'), 'p57_annotation_appearance_unsupported')
        width, height = media[2] - media[0], media[3] - media[1]
        if int(rotation) in (90, 270):
            width, height = height, width
        sizes = {}
        for dpi in DPIS:
            size = [math.ceil(width * dpi / 72), math.ceil(height * dpi / 72)]
            require(0 < size[0] * size[1] <= MAX_PAGE_PIXELS, 'p57_page_pixel_boundary')
            total += size[0] * size[1]
            sizes[str(dpi)] = size
        pages.append({'media_box': media, 'crop_box': crop, 'rotation': int(rotation), 'user_unit': 1,
                      'raster_sizes': sizes})
    require(total <= MAX_TOTAL_PIXELS, 'p57_total_pixel_boundary')
    return pages


def pixels(left, right):
    require(left.mode == right.mode == 'RGB', 'p57_rgb_required')
    if left.size != right.size:
        return {'state': 'dimension_mismatch', 'left_size': list(left.size), 'right_size': list(right.size)}
    diff = ImageChops.difference(left, right)
    red, green, blue = diff.split()
    mask = ImageChops.lighter(ImageChops.lighter(red, green), blue)
    changed = sum(mask.histogram()[1:])
    delta = sum(i * count for band in (red, green, blue) for i, count in enumerate(band.histogram()))
    white = Image.new('RGB', left.size, 'white')
    return {'state': 'exact_pixels' if changed == 0 else 'pixel_mismatch', 'size': list(left.size),
            'changed_pixels': changed, 'rgb_delta_sum': delta,
            'difference_bbox': list(diff.getbbox()) if diff.getbbox() else None,
            'left_nonwhite_bbox': list(ImageChops.difference(left, white).getbbox())
                if ImageChops.difference(left, white).getbbox() else None,
            'right_nonwhite_bbox': list(ImageChops.difference(right, white).getbbox())
                if ImageChops.difference(right, white).getbbox() else None,
            'left_rgb_sha256': sha(left.tobytes()), 'right_rgb_sha256': sha(right.tobytes())}


class Renderer:
    def __init__(self):
        executable = shutil.which('pdftoppm')
        require(executable is not None, 'p57_poppler_absent')
        self.executable = unlinked(executable)
        self.identity = self.runtime_identity()

    def runtime_identity(self):
        files = sorted([self.executable, *self.executable.parent.glob('*.dll')], key=lambda p: p.name.lower())
        require(1 < len(files) <= 256, 'p57_renderer_runtime_inventory')
        inventory = [{'name': p.name.lower(), 'bytes': p.stat().st_size,
                      'sha256': sha(bounded(p, limit=128 * 1024 * 1024))} for p in files]
        require(sum(row['bytes'] for row in inventory) <= 1024 * 1024 * 1024, 'p57_renderer_runtime_boundary')
        # The receipt binds the actually loaded parser/raster extension and version, not arbitrary Python provenance.
        from PIL import _imaging
        return {'poppler_files': inventory, 'pypdf_version': pypdf.__version__, 'pillow_version': PIL.__version__,
                'pypdf_entry_sha256': sha(bounded(pypdf.__file__, limit=4 * 1024 * 1024)),
                'pillow_raster_extension_sha256': sha(bounded(_imaging.__file__, limit=32 * 1024 * 1024)),
                'python_version': list(__import__('sys').version_info[:3]), 'dpi_profiles': list(DPIS),
                'font_policy': 'embedded_only', 'mask_crop_tolerance_or_normalization': False}

    def scratch(self):
        parent = unlinked(ROOT / 'tmp/pdfs')
        parent.mkdir(parents=True, exist_ok=True)
        return tempfile.TemporaryDirectory(prefix='p09-57-', dir=parent)

    def render_page(self, pdf, directory, page, dpi, size):
        require(unlinked(directory).parent.parent == unlinked(ROOT / 'tmp/pdfs')
                and directory.parent.name.startswith('p09-57-') and pdf.parent == directory,
                'p57_scratch_scope')
        prefix = directory / f'page-{page}-{dpi}'
        require(not prefix.with_suffix('.png').exists(), 'p57_scratch_output_exists')
        command = [str(self.executable), '-f', str(page), '-l', str(page), '-singlefile',
                   '-r', str(dpi), '-freetype', 'yes', '-aa', 'yes', '-aaVector', 'yes',
                   '-thinlinemode', 'none', '-png', str(pdf), str(prefix)]
        env = dict(os.environ)
        for key in tuple(env):
            if key.upper().startswith(('FONTCONFIG_', 'FREETYPE_')):
                env.pop(key)
        result = subprocess.run(command, capture_output=True, timeout=30, env=env,
                                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        require(result.returncode == 0 and not result.stderr, 'p57_renderer_error')
        path = prefix.with_suffix('.png')
        require(path.stat().st_size <= MAX_PAGE_PIXELS * 4 + 65536, 'p57_png_boundary')
        with Image.open(path) as image:
            require(image.size == tuple(size), 'p57_observed_raster_geometry')
            require(image.mode == 'RGB', 'p57_observed_raster_mode')
            image.load()
            copied = image.copy()
        path.unlink()  # Only this exclusive scratch render, never source/native evidence.
        return copied

    def compare(self, left, right):
        before = self.runtime_identity()
        require(before == self.identity, 'p57_renderer_runtime_changed')
        a, b = geometry(left), geometry(right)
        rows = []
        with self.scratch() as temporary:
            base = Path(temporary)
            dirs = [base / 'left', base / 'right']
            for directory, raw in zip(dirs, (left, right), strict=True):
                directory.mkdir()
                with (directory / 'snapshot.pdf').open('xb') as stream:
                    stream.write(raw)  # Exact byte copy for analysis, never PdfWriter/re-export.
            for index in range(max(len(a), len(b))):
                if index >= min(len(a), len(b)):
                    rows.append({'page': index + 1, 'state': 'missing_right_page' if index >= len(b)
                                 else 'missing_left_page'})
                    continue
                row = {'page': index + 1, 'geometry_exact': a[index] == b[index], 'profiles': []}
                for dpi in DPIS:
                    images = [self.render_page(d / 'snapshot.pdf', d, index + 1, dpi, meta[index]['raster_sizes'][str(dpi)])
                              for d, meta in zip(dirs, (a, b), strict=True)]
                    try:
                        row['profiles'].append({'dpi': dpi, **pixels(*images)})
                    finally:
                        for image in images:
                            image.close()
                row['state'] = 'exact_full_page' if row['geometry_exact'] and all(
                    r['state'] == 'exact_pixels' for r in row['profiles']) else 'mismatch'
                rows.append(row)
        require(self.identity == self.runtime_identity(), 'p57_renderer_runtime_changed')
        return {'state': 'exact_full_document' if all(r['state'] == 'exact_full_page' for r in rows) else 'mismatch',
                'left_pdf_sha256': sha(left), 'right_pdf_sha256': sha(right),
                'left_pages': a, 'right_pages': b, 'pages': rows, 'dpi_profiles': list(DPIS),
                'all_pages_accounted_for': True, 'every_corresponding_page_rendered_at_both_dpis': True,
                'unpaired_pages': abs(len(a) - len(b)), 'mask_tolerance_or_normalization': False,
                'native_semantics_direct_baseline_or_product_qualified': False}
