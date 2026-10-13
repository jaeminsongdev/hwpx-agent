"""Opt-in 64KiB readinto workspace; not a product/Native qualification.

Only the frozen leaf reader's chunk allocation changes. The original MRO,
stream opening/identity, every checkpoint/reservation/refund, parse budget,
hashing, binding and complete closing freshness reads remain. One workspace
belongs to one serial reader; it never supplies unread/cached source bytes.
No default/global reader mutation, subprocess, sampler or retry is added.
"""
import ast
import copy
from contextlib import contextmanager
import hashlib
import threading

import audit_evidence_io as original

SELF = "tools/p09/reusable_audit_chunk_v1.py"
TEST = "tools/p09/tests/test_reusable_audit_chunk_v1.py"
ORIGINAL_PIN = dict(path="tools/p09/audit_evidence_io.py", bytes=5653,
    sha256="84b7dae287ac01c7ec308ca302762ec283406fca3fa43bc469882a3913578a8f")
ATTRIBUTE = "_p09_reusable_chunk_workspace_v1"


def require(ok, code):
    if not ok:
        raise ValueError("REUSABLE_CHUNK_" + code)


class Workspace:
    """A scratch area, NOT a file-content cache or a replacement stream."""
    def __init__(self, reader):
        self.reader = reader
        self.owner = threading.get_ident()
        self.storage = bytearray(original.CHUNK_BYTES)
        self.window = memoryview(self.storage)
        self.active = False
        self.leases = self.returns = self.readinto_attempts = 0
        self.readinto_completed = self.returned_bytes = self.invalid_returns = 0

    def owner_check(self):
        require(threading.get_ident() == self.owner, "SERIAL_OWNER")
        require(getattr(self.reader, ATTRIBUTE, None) is self, "EXACT_READER_BINDING")

    @contextmanager
    def lease(self):
        self.owner_check()
        require(not self.active, "REENTRANT_READ")
        self.active = True
        self.leases += 1
        try:
            yield self
        finally:
            self.active = False
            self.returns += 1

    def summary(self):
        self.owner_check()
        return dict(workspace_allocations=1, workspace_bytes=len(self.storage),
            active_lease=self.active, leases=self.leases, lease_returns=self.returns,
            readinto_attempts=self.readinto_attempts,
            readinto_completed=self.readinto_completed, returned_bytes=self.returned_bytes,
            invalid_readinto_returns=self.invalid_returns,
            fresh_stream_read_before_every_exposed_chunk=True,
            unread_tail_exposed=False, file_bytes_or_hash_or_JSON_cache=False,
            original_MRO_wrappers_preserved=True,
            original_stream_open_and_identity_binding_preserved=True,
            original_checkpoints_pacing_parse_budget_and_final_hashes_preserved=True,
            added_sampler_query_thread_or_process=False,
            actual_whole_Native_or_product_connection_qualified=False,
            PC_freeze_resolved=False)


def _workspace_for(reader):
    workspace = getattr(reader, ATTRIBUTE, None)
    if workspace is None:
        workspace = Workspace(reader)
        setattr(reader, ATTRIBUTE, workspace)
    require(type(workspace) is Workspace and workspace.reader is reader, "WORKSPACE_TYPE")
    workspace.owner_check()
    return workspace


def _read_chunk(stream, workspace):
    workspace.owner_check()
    require(workspace.active, "LIVE_LEASE_REQUIRED")
    workspace.readinto_attempts += 1
    # readinto is a fresh call on the SAME stream. No fallback/second open or
    # reuse of a previous count after an exception, None or invalid return.
    count = stream.readinto(workspace.window)
    if type(count) is not int or not 0 <= count <= original.CHUNK_BYTES:
        workspace.invalid_returns += 1
        raise ValueError("REUSABLE_CHUNK_INVALID_READINTO_COUNT")
    workspace.readinto_completed += 1
    workspace.returned_bytes += count
    return workspace.window[:count]


def project_read(raw):
    require(type(raw) is bytes and len(raw) == ORIGINAL_PIN["bytes"]
        and hashlib.sha256(raw).hexdigest() == ORIGINAL_PIN["sha256"], "EXACT_FROZEN_SOURCE")
    classes = [n for n in ast.parse(raw.decode("utf-8")).body
               if isinstance(n, ast.ClassDef) and n.name == "AuditEvidenceReader"]
    require(len(classes) == 1, "ONE_READER_CLASS")
    methods = [n for n in classes[0].body if isinstance(n, ast.FunctionDef) and n.name == "_read"]
    require(len(methods) == 1, "ONE_LEAF_READ")
    node = copy.deepcopy(methods[0])
    before = ast.dump(node, include_attributes=False)
    read_changes = lease_changes = 0

    class Project(ast.NodeTransformer):
        def visit_Assign(self, n):
            nonlocal read_changes
            expected = ast.parse("chunk = stream.read(CHUNK_BYTES)").body[0]
            if ast.dump(n, include_attributes=False) == ast.dump(expected, include_attributes=False):
                read_changes += 1
                replacement = ast.parse("chunk = _read_chunk(stream, _chunk_workspace)").body[0]
                replacement._original_chunk_read = copy.deepcopy(n)
                return replacement
            return self.generic_visit(n)

        def visit_With(self, n):
            nonlocal lease_changes
            expected = ast.parse('with self._source(name).open("rb") as stream: pass').body[0].items
            if ast.dump(ast.With(items=n.items, body=[], type_comment=None), include_attributes=False) == \
                    ast.dump(ast.With(items=expected, body=[], type_comment=None), include_attributes=False):
                lease_changes += 1
                self.generic_visit(n)
                wrapper = ast.parse("with _workspace_for(self).lease() as _chunk_workspace: pass").body[0]
                wrapper.body = n.body
                wrapper._original_body_wrapper = True
                n.body = [wrapper]
                return n
            return self.generic_visit(n)

    node = Project().visit(node)
    require((read_changes, lease_changes) == (1, 1), "ONLY_ONE_CHUNK_AND_LEASE")

    class Undo(ast.NodeTransformer):
        def visit(self, n):
            if hasattr(n, "_original_chunk_read"):
                return copy.deepcopy(n._original_chunk_read)
            return super().visit(n)

        def visit_With(self, n):
            self.generic_visit(n)
            if hasattr(n, "_original_body_wrapper"):
                return n.body
            return n

    require(ast.dump(Undo().visit(copy.deepcopy(node)), include_attributes=False) == before,
            "ALL_ORIGINAL_LEAF_READ_STATEMENTS_RETAINED")
    environment = dict(vars(original), _workspace_for=_workspace_for, _read_chunk=_read_chunk)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])),
                 ORIGINAL_PIN["path"], "exec"), environment)
    return environment["_read"], dict(original_leaf_read_AST_restored_exactly=True,
        chunk_read_allocation_operations_changed=1, scratch_lease_wrappers_added=1,
        original_checkpoints_hash_parse_pacing_and_stream_statements_removed=0,
        original_chunk_bytes=original.CHUNK_BYTES, default_reader_mutated=False,
        runtime_or_freeze_resolution_qualified=False)


def reader_type(base, raw):
    require(isinstance(base, type) and base is not original.AuditEvidenceReader
        and original.AuditEvidenceReader in base.__mro__, "DERIVED_READER_REQUIRED")
    projected, proof = project_read(raw)

    class ChunkLeaf(original.AuditEvidenceReader):
        _read = projected

    class ReusableReader(base, ChunkLeaf):
        pass

    # Insert ONLY the projected leaf before the original leaf. All original
    # open20/owned weighted1/2MiB super() wrappers keep their original order.
    expected = list(base.__mro__)
    expected.insert(expected.index(original.AuditEvidenceReader), ChunkLeaf)
    require(list(ReusableReader.__mro__[1:]) == expected, "EXACT_ORIGINAL_MRO_WITH_ONE_LEAF")
    return ReusableReader, dict(proof, original_MRO_preserved_with_one_leaf_insert=True)


def summary(reader):
    workspace = getattr(reader, ATTRIBUTE, None)
    require(type(workspace) is Workspace, "ACTUAL_WORKSPACE_REQUIRED")
    return workspace.summary()
