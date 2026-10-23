"""Fixed003 path inventory only. No execution entry, permit, mutable selector or retries."""

PREFIX='implementation/p09/evidence/private/p09-361-crossref-bookmark-native-20261021-g003-c'
PROBE='target/debug/examples/p09_crossref_capture003_probe.exe'
FILES=('opened.hwpx','saved.hwpx','reopened.hwpx','target-trace.json','owner-identities.json')

def directory(index):
    if type(index)is not int or not 1<=index<=8:raise ValueError('XREF_CAPTURE003_FIXED_CASE')
    return PREFIX+f'{index:02}-attempt01'

def artifact(index,name):
    if type(name)is not str or name not in FILES:raise ValueError('XREF_CAPTURE003_FIXED_ARTIFACT')
    return directory(index)+'/'+name

def require_absent(root):
    # Inspection only: old attempts must never be moved, deleted or reused.
    for index in range(1,9):
        path=root/directory(index)
        if path.exists()or path.is_symlink()or path.is_junction():
            raise ValueError('XREF_CAPTURE003_EXISTING_ATTEMPT_NO_REPLAY')
