"""Lossless bounded JSON layout only. No compression, external carrier, trust or status promotion."""
import hashlib,json
PROFILE='hwpx-agent.lossless-compact-json-receipt/v1'
MAXIMUM=262144


def raw(value):return json.dumps(value,ensure_ascii=True,allow_nan=False,separators=(',',':')).encode('ascii')


def unique(pairs):
    result={}
    for key,value in pairs:
        if key in result:raise ValueError('COMPACT_RECEIPT_DUPLICATE_KEY')
        result[key]=value
    return result


def unpack(packet):
    if type(packet)is not dict or set(packet)!={'schema_version','state','payload_utf8_bytes','payload_sha256','payload_json'}:
        raise ValueError('COMPACT_RECEIPT_ENVELOPE')
    text=packet['payload_json'];length=packet['payload_utf8_bytes']
    if packet['schema_version']!=PROFILE or type(packet['state'])is not str or type(text)is not str or type(length)is not int or not 0<length<=MAXIMUM or len(text)>MAXIMUM:
        raise ValueError('COMPACT_RECEIPT_LIMIT_OR_PROFILE')
    data=text.encode('ascii')
    if len(data)!=length or hashlib.sha256(data).hexdigest()!=packet['payload_sha256']:raise ValueError('COMPACT_RECEIPT_INTEGRITY')
    value=json.loads(text,object_pairs_hook=unique,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('COMPACT_RECEIPT_NONFINITE')))
    if type(value)is not dict or value.get('state')!=packet['state'] or raw(value)!=data:raise ValueError('COMPACT_RECEIPT_STATE_OR_CANONICAL_LAYOUT')
    return value


def pack(value):
    if type(value)is not dict or type(value.get('state'))is not str:raise ValueError('COMPACT_RECEIPT_STATE_REQUIRED')
    data=raw(value)
    if not 0<len(data)<=MAXIMUM:raise ValueError('COMPACT_RECEIPT_PAYLOAD_LIMIT')
    packet=dict(schema_version=PROFILE,state=value['state'],payload_utf8_bytes=len(data),payload_sha256=hashlib.sha256(data).hexdigest(),payload_json=data.decode('ascii'))
    if raw(unpack(packet))!=data:raise ValueError('COMPACT_RECEIPT_LOSSLESS_ROUNDTRIP')
    # The unchanged original writer formats the envelope this way and enforces the same byte cap.
    published=(json.dumps(packet,ensure_ascii=True,allow_nan=False,indent=2)+'\n').encode('utf-8')
    if len(published)>MAXIMUM:raise ValueError('COMPACT_RECEIPT_OUTER_LIMIT')
    return packet
