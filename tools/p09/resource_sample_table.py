"""Lossless inline sample-column layout, retaining the original 256KiB compact receipt cap."""
import json
import compact_receipt_json as compact
PROFILE='hwpx-agent.inline-resource-sample-table/v1'
KEY='resource_sample_table'


def encode(row):
    if type(row)is not dict or KEY in row or type(row.get('resource_samples'))is not list:
        raise ValueError('RESOURCE_TABLE_INPUT')
    value=json.loads(compact.raw(row));samples=value.pop('resource_samples')
    columns=list(samples[0])if samples else []
    if any(type(s)is not dict or list(s)!=columns for s in samples):raise ValueError('RESOURCE_TABLE_COLUMNS')
    value[KEY]=dict(profile=PROFILE,columns=columns,rows=[[s[k]for k in columns]for s in samples])
    if json.dumps(decode(value),sort_keys=True,allow_nan=False)!=json.dumps(row,sort_keys=True,allow_nan=False):
        raise ValueError('RESOURCE_TABLE_ROUNDTRIP')
    return value


def decode(value):
    if type(value)is not dict or 'resource_samples'in value or KEY not in value:raise ValueError('RESOURCE_TABLE_ENVELOPE')
    value=json.loads(compact.raw(value));table=value.pop(KEY)
    if type(table)is not dict or set(table)!={'profile','columns','rows'}or table['profile']!=PROFILE:
        raise ValueError('RESOURCE_TABLE_PROFILE')
    columns,rows=table['columns'],table['rows']
    if type(columns)is not list or any(type(k)is not str for k in columns)or len(set(columns))!=len(columns)or type(rows)is not list:
        raise ValueError('RESOURCE_TABLE_COLUMNS')
    if any(type(row)is not list or len(row)!=len(columns)for row in rows):raise ValueError('RESOURCE_TABLE_ROW')
    value['resource_samples']=[dict(zip(columns,row,strict=True))for row in rows]
    return value


def pack(row):return compact.pack(encode(row))
def unpack(packet):return decode(compact.unpack(packet))
