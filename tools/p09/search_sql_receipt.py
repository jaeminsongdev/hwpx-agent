"""Task-local lossless column dictionaries; original 256KiB envelope cap, no external carrier."""
import json,os
import character_detail_receipt as pins
import resource_sample_table as samples
import compact_receipt_json as compact
PROFILE='hwpx-agent.search-sql-inline-resource-columns/v1'

def require(ok):
    if not ok:raise ValueError('SEARCH_SQL_RECEIPT_COLUMNS_INVALID')

def scalar(value):
    return value is None or type(value)in(bool,int,float)or(type(value)is str and len(value)<=128)

def canonical(value):return json.dumps(value,ensure_ascii=True,allow_nan=False,sort_keys=True,separators=(',',':'))

def encode(row):
    value=pins.encode(samples.encode(row));table=value[samples.KEY];columns=table['columns'];rows=table['rows'];n=len(rows)
    require(n<=4096 and len(columns)<=64);series=[]
    for i in range(len(columns)):
        values=[r[i]for r in rows];require(all(scalar(v)for v in values))
        choices=[dict(kind='raw',values=values)];unique=[];indices=[];seen={}
        for v in values:
            key=compact.raw(v)
            if key not in seen:seen[key]=len(unique);unique.append(v)
            indices.append(seen[key])
        choices.append(dict(kind='dictionary',values=unique,indices=indices))
        if values and all(type(v)is str for v in values):
            prefix=os.path.commonprefix(values)
            choices.append(dict(kind='prefix',prefix=prefix,suffixes=[v[len(prefix):]for v in values]))
        series.append(min(choices,key=lambda c:len(compact.raw(c))))
    value[samples.KEY]=dict(profile=PROFILE,columns=columns,sample_count=n,series=series)
    require(canonical(decode(value))==canonical(row));return value

def decode(value):
    value=json.loads(compact.raw(value));table=value.get(samples.KEY)
    require(type(table)is dict and set(table)=={'profile','columns','sample_count','series'}and table['profile']==PROFILE)
    columns,n,series=table['columns'],table['sample_count'],table['series']
    require(type(n)is int and 0<=n<=4096 and type(columns)is list and len(columns)<=64 and all(type(k)is str for k in columns)
        and len(set(columns))==len(columns)and type(series)is list and len(series)==len(columns))
    decoded=[]
    for column in series:
        require(type(column)is dict);kind=column.get('kind')
        if kind=='raw':
            require(set(column)=={'kind','values'}and type(column['values'])is list);values=column['values']
        elif kind=='dictionary':
            require(set(column)=={'kind','values','indices'}and type(column['values'])is list and type(column['indices'])is list)
            require(len(column['values'])<=n and len(column['indices'])==n and all(type(i)is int and 0<=i<len(column['values'])for i in column['indices']))
            values=[column['values'][i]for i in column['indices']]
        elif kind=='prefix':
            require(set(column)=={'kind','prefix','suffixes'}and type(column['prefix'])is str and len(column['prefix'])<=128
                and type(column['suffixes'])is list and len(column['suffixes'])==n and all(type(s)is str and len(s)<=128 for s in column['suffixes']))
            values=[column['prefix']+s for s in column['suffixes']]
        else:raise ValueError('SEARCH_SQL_RECEIPT_COLUMNS_INVALID')
        require(len(values)==n and all(scalar(v)for v in values));decoded.append(values)
    value[samples.KEY]=dict(profile=samples.PROFILE,columns=columns,rows=[[c[i]for c in decoded]for i in range(n)])
    return samples.decode(pins.decode(value))

def pack(row):return compact.pack(encode(row))
def unpack(packet):return decode(compact.unpack(packet))
