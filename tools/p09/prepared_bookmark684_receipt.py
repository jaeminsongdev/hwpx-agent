"""Whole new684 metadata, losslessly packed with existing bounded XZ.

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

PROFILE = 'hwpx-agent.prepared684-lossless-xz-publication/v1'


def require(ok, code):
    if not ok:
        raise ValueError('XREF_PREPARED684_RECEIPT_'+code)


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
