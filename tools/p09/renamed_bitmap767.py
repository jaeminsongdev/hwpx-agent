"""Describe bounded 24-bit BMP pixels separately from immutable file/header bytes."""
import hashlib,struct

def require(ok,code):
    if not ok:raise ValueError('XREF_BITMAP767_'+code)

def describe(data,checkpoint):
    require(type(data)is bytes and 54<=len(data)<=16*1024*1024,'BYTE_BOUND')
    checkpoint()
    require(data[:2]==b'BM'and struct.unpack_from('<I',data,2)[0]==len(data),'FILE_HEADER')
    offset=struct.unpack_from('<I',data,10)[0];dib,width,height,planes,depth,compression=struct.unpack_from('<IiiHHI',data,14)
    require(dib==40 and offset==54 and planes==1 and depth==24 and compression==0,'FIXED_RGB24_PROFILE')
    require(0<width<=4096 and 0<height<=4096 and width*height<=4*1024*1024,'FIXED_BOTTOM_UP_DIMENSIONS')
    visible=width*3;stride=(visible+3)//4*4
    require(offset+stride*height==len(data),'COMPLETE_ROWS_ONLY')
    pixels=hashlib.sha256(struct.pack('<II',width,height));padding=hashlib.sha256();nonwhite=0;ink_rows=[]
    # Canonical top-to-bottom BGR row bytes; row padding is retained separately.
    for row in range(height-1,-1,-1):
        if row%64==0:checkpoint()
        start=offset+row*stride;line=data[start:start+visible]
        pixels.update(line);padding.update(data[start+visible:start+stride]);count=len(line)-line.count(255);nonwhite+=count
        if count:ink_rows.append(height-1-row)
    checkpoint()
    return dict(profile='hwpx-agent.fixed-rgb24-visible-pixel767/v1',bytes=len(data),file_sha256=hashlib.sha256(data).hexdigest(),
        width=width,height=height,pixel_sha256=pixels.hexdigest(),header_sha256=hashlib.sha256(data[:offset]).hexdigest(),row_padding_sha256=padding.hexdigest(),
        bitmap_pixels_per_meter=list(struct.unpack_from('<ii',data,38)),nonwhite_color_channels=nonwhite,nonwhite_rows=len(ink_rows),
        first_nonwhite_row=None if not ink_rows else ink_rows[0],last_nonwhite_row=None if not ink_rows else ink_rows[-1],native_producer_attested_by_parser=False,
        source_bytes_rewritten=False,semantic_or_OCR_acceptance=False)
