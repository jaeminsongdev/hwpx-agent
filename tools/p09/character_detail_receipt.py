"""Lossless inline directory-indexed pin rows. Original 256KiB cap; no compression or external carrier."""
import json,posixpath
import resource_sample_table as samples
import compact_receipt_json as compact
KEY='source_pin_table'
PROFILE='hwpx-agent.inline-directory-source-pin-table/v1'

def require(ok):
    if not ok:raise ValueError('CHARACTER_DETAIL_PIN_TABLE_INVALID')

def encode(value):
    require(type(value)is dict and KEY not in value and type(value.get('source_pins'))is list)
    original=value;value=json.loads(compact.raw(value));pins=value['source_pins'];directories=[];indices={};rows=[]
    for pin in pins:
        require(type(pin)is dict and set(pin)=={'path','bytes','sha256'}and type(pin['path'])is str)
        directory,name=posixpath.split(pin['path']);require(bool(name)and directory+'/'+name==pin['path']if directory else bool(name)and name==pin['path'])
        if directory not in indices:indices[directory]=len(directories);directories.append(directory)
        rows.append([indices[directory],name,pin['bytes'],pin['sha256']])
    table=dict(profile=PROFILE,directories=directories,rows=rows)
    encoded={(KEY if key=='source_pins'else key):(table if key=='source_pins'else item)for key,item in value.items()}
    require(compact.raw(decode(encoded))==compact.raw(original));return encoded

def decode(value):
    require(type(value)is dict and 'source_pins'not in value and KEY in value)
    value=json.loads(compact.raw(value));table=value[KEY]
    require(type(table)is dict and set(table)=={'profile','directories','rows'}and table['profile']==PROFILE)
    directories,rows=table['directories'],table['rows'];require(type(directories)is list and all(type(d)is str for d in directories)
        and len(directories)==len(set(directories))and type(rows)is list)
    pins=[]
    for row in rows:
        require(type(row)is list and len(row)==4 and type(row[0])is int and 0<=row[0]<len(directories)and type(row[1])is str and row[1]and '/'not in row[1])
        directory=directories[row[0]];pins.append(dict(path=(directory+'/'if directory else'')+row[1],bytes=row[2],sha256=row[3]))
    return {('source_pins'if key==KEY else key):(pins if key==KEY else item)for key,item in value.items()}

def pack(row):return compact.pack(encode(samples.encode(row)))
def unpack(packet):return samples.decode(decode(compact.unpack(packet)))
