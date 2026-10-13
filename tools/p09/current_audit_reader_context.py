"""Restore only the already-declared current_r4 branch for legacy IO AST oracle."""
import ast
import base64
import hashlib
import json
from unittest.mock import patch
import xml_initial_capacity_binding as b

SELF='tools/p09/current_audit_reader_context.py'
SOURCE='tools/p09/verify_formula_issuer_authority_current.py'
ARCHIVE='implementation/p09/source-archive/p09-149-pre-current-authority-receipt-contract/source-preimages.v1.json'
OLD_SIGNATURE='def validate_case(run, build, manifest, case, mode, outcome):\n'
NEW_SIGNATURE='def validate_case(run, build, manifest, case, mode, outcome, *, scheme="legacy"):\n    require(scheme in {"legacy", "current_r4"}, "authority_build_scheme_invalid")\n'
OLD_POLICY='    policy = run["resource_policy"]\n'
NEW_POLICY=OLD_POLICY+'    if scheme == "current_r4":\n        from current_authority_sql_receipts import validate_current_resources\n        validate_current_resources(run, build)\n        return\n'

def restore(current,old):
    current=current.replace('\r\n','\n');old=old.replace('\r\n','\n')
    for new,original in ((NEW_SIGNATURE,OLD_SIGNATURE),(NEW_POLICY,OLD_POLICY)):
        b.require(current.count(new)==1,'CURRENT_R4_EXACT_ONE_EXTENSION');current=current.replace(new,original,1)
    b.require(current==old,'CURRENT_R4_WHOLE_OLD_VALIDATOR_EXACT');return current

def original_io_oracle_with_current_context(case):
    # Actual source and full archived preimage, not a synthetic passing source.
    rows=json.loads((b.c.ROOT/ARCHIVE).read_text(encoding='utf-8'))['files']
    selected=[r for r in rows if r['path']==SOURCE];b.require(len(selected)==1,'CURRENT_R4_ONE_SOURCE')
    row=selected[0];raw=base64.b64decode(''.join(row['base64_chunks']),validate=True)
    b.require(len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256'],'CURRENT_R4_WHOLE_PREIMAGE')
    current=(b.c.ROOT/SOURCE).read_text(encoding='utf-8');restored=restore(current,raw.decode('utf-8'))
    parse=ast.parse
    def contextual_parse(source,*args,**kwargs):
        return parse(restored if source==current else source,*args,**kwargs)
    from tests.test_audit_evidence_io import AuditEvidenceIOTests
    with patch.object(ast,'parse',contextual_parse):
        ORIGINAL_IO_ORACLE(case)

# Capture once before the fixture method is patched; never bypass original assertions.
from tests.test_audit_evidence_io import AuditEvidenceIOTests
ORIGINAL_IO_ORACLE=AuditEvidenceIOTests.test_current_auditor_keeps_all_non_io_authority_checks_unchanged
