"""Explicit lossless XZ publication recovery for the consumed631 metadata ONLY.

No Native entry, retry, old codec mutation, data omission or acceptance upgrade.
Preserves old4MiB/tree/depth/180000-compressed/256KiB-publication bounds.
"""
import base64
import hashlib
import json
from pathlib import Path

import compact_receipt_json as compact
import crossref_lossless_receipt610 as legacy
import receipt_xz_envelope_v1 as xz
import crossref_generation010_publication as files

PROFILE = 'hwpx-agent.prepared631-lossless-xz-publication-recovery/v1'
SPOOL = 'implementation/p09/evidence/private/p09-361-prepared-bookmark631-native001-forensic'
MANIFEST_SHA = 'add83a105a27be7b738a814dd2cace669de4b70eecaffa8765575ead9c57387e'
RAW_BYTES = 875415


def require(ok, code):
    if not ok:
        raise ValueError('P632_RECEIPT_'+code)


def retained(reader):
    files.directory(reader.root/SPOOL, reader.root)
    manifest = reader.json(SPOOL+'/manifest.v1.json')
    require(type(manifest) is dict and set(manifest) == {'state', 'profile', 'bytes', 'sha256', 'parts'}
            and manifest['state'] == 'RAW_METADATA_RETAINED_NOT_ACCEPTANCE_OR_NATIVE_PERMIT'
            and manifest['profile'] == 'hwpx-agent.private.canonical-metadata-retention/v1'
            and type(manifest['bytes']) is int and manifest['bytes'] == RAW_BYTES
            and manifest['sha256'] == MANIFEST_SHA and type(manifest['parts']) is list
            and len(manifest['parts']) == 14, 'EXACT631_RETAINED_METADATA')
    data = bytearray()
    for index, pin in enumerate(manifest['parts']):
        name = f'part-{index:04}.bin'
        require(type(pin) is dict and set(pin) == {'path', 'bytes', 'sha256'} and pin['path'] == name
                and type(pin['bytes']) is int and 0 < pin['bytes'] <= 65536, 'FIXED_PART_NO_PATH_INJECTION')
        path = SPOOL+'/'+name
        expected = dict(pin, path=path)
        require(reader.pin(path) == expected, 'PART_INTEGRITY')
        reader.checkpoint()
        chunk = files.read_bound(reader.root/path, 65536)
        require(len(chunk) == pin['bytes'] and hashlib.sha256(chunk).hexdigest() == pin['sha256'], 'HELD_PART_INTEGRITY')
        require(len(data)+len(chunk) <= RAW_BYTES, 'TOTAL_RAW_BOUND')
        data.extend(chunk)
    raw = bytes(data)
    require(len(raw) == RAW_BYTES and hashlib.sha256(raw).hexdigest() == MANIFEST_SHA, 'WHOLE_ORIGINAL_HASH')
    value = json.loads(raw, object_pairs_hook=compact.unique)
    legacy.validate_tree(value, reader.checkpoint)
    require(compact.raw(value) == raw, 'CANONICAL_ORIGINAL_UNCHANGED')
    return value, raw


def pack(row, checkpoint):
    legacy.validate_tree(row, checkpoint)
    raw = compact.raw(row)
    require(type(row) is dict and type(row.get('state')) is str and 0 < len(raw) <= legacy.MAX_INPUT_BYTES,
            'RAW4M_AND_STATE')
    encoded = xz.encode(raw, checkpoint)
    packet = json.loads(encoded, object_pairs_hook=compact.unique)
    require(len(base64.b64decode(packet['payload'], validate=True)) <= legacy.MAX_COMPRESSED_BYTES,
            'ORIGINAL_COMPRESSED180K_LIMIT')
    value = dict(state=row['state'], profile=PROFILE, xz=packet)
    result = compact.pack(value)
    require(compact.raw(unpack(result, checkpoint)) == raw, 'EXACT_WHOLE_ROUND_TRIP')
    return result


def unpack(value, checkpoint):
    packet = compact.unpack(value)
    require(type(packet) is dict and set(packet) == {'state', 'profile', 'xz'}
            and packet['profile'] == PROFILE and type(packet['state']) is str, 'EXPLICIT_NEW_PROFILE_ONLY')
    payload = packet['xz']
    require(type(payload) is dict and type(payload.get('original_bytes')) is int
            and 0 < payload['original_bytes'] <= legacy.MAX_INPUT_BYTES
            and type(payload.get('payload')) is str
            and len(payload['payload']) <= 4*((legacy.MAX_COMPRESSED_BYTES+2)//3), 'PREDECODE_ORIGINAL_BOUNDS')
    raw = xz.decode(compact.raw(payload), checkpoint)
    value = json.loads(raw, object_pairs_hook=compact.unique)
    legacy.validate_tree(value, checkpoint)
    require(type(value) is dict and value.get('state') == packet['state'] and compact.raw(value) == raw,
            'UNCHANGED_STATE_AND_CANONICAL_JSON')
    return value
