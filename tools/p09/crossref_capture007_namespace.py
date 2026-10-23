"""Fixed007 output paths only. No Native entry, caller generation selector, approval or retries."""
PREFIX='implementation/p09/evidence/private/p09-361-crossref-bookmark-native-20261022-g007-c'
PROBE='target/debug/examples/p09_crossref_capture007_probe.exe'
FILES=('opened.hwpx','saved.hwpx','reopened.hwpx','target-trace.json','owner-identities.json')

def directory(index):
    if type(index)is not int or not 1<=index<=8:raise ValueError('XREF_CAPTURE007_FIXED_CASE')
    return PREFIX+f'{index:02}-attempt01'

def artifact(index,name):
    if type(name)is not str or name not in FILES:raise ValueError('XREF_CAPTURE007_FIXED_ARTIFACT')
    return directory(index)+'/'+name

def require_absent(root):
    for index in range(1,9):
        path=root/directory(index)
        if path.exists()or path.is_symlink()or path.is_junction():raise ValueError('XREF_CAPTURE007_EXISTING_ATTEMPT_NO_REPLAY')
