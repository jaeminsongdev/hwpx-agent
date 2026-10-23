"""Preserve133; qualify the static lowercase patch-code domain without source/log text."""
import re
import inspect_text_style_failure as base
base.OUTPUT='implementation/p09/evidence/p09-361-text-style-patch-code134.v1.json'
original_snapshot=base.snapshot


def snapshot(capture,expected):
    result=original_snapshot(capture,expected)
    with capture.lock:
        raw=(bytes(capture.buffers['stdout'])+bytes(capture.buffers['stderr'])).decode('utf-8','replace')
    codes=re.findall(r'Error: Compile\(Patch\("([a-z0-9_]{1,96})"\)\)',raw)
    # All values below are static IdIndexError codes, not input-controlled messages.
    allowed={'id_index_unknown_id_like_attribute','id_index_dangling_reference','id_index_duplicate_declaration',
        'id_index_invalid_value','id_index_invalid_profile','patch_selector_stale','patch_conflict','patch_limit_exceeded'}
    result['closed_patch_codes']=[code for code in codes if code in allowed]
    return result


base.snapshot=snapshot
if __name__=='__main__':raise SystemExit(base.main())
