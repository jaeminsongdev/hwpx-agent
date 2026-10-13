"""Live SQL paced full-byte IO; fresh at every original pin and again at finish."""
import math
from pathlib import Path
import time

from conservative_maintenance import ROOT, require
from audit_evidence_io import AuditEvidenceReader, CHUNK_BYTES, MAX_PARSE_BYTES, READ_BYTES_PER_SECOND

MAX_SCOPE_SECONDS = 600


class LiveSQLReader:
    def __init__(self, resources, clock=time.monotonic):
        self.resources, self.clock = resources, clock
        self.started, self.finished = clock(), False
        require(type(self.started) in (int, float) and math.isfinite(self.started), "sql_io_clock_invalid")
        self.reader = AuditEvidenceReader(ROOT, self.checkpoint)

    def checkpoint(self):
        require(not self.finished, "sql_io_already_finished")
        now = self.clock()
        require(type(now) in (int, float) and math.isfinite(now) and now >= self.started, "sql_io_clock_invalid")
        require(now-self.started <= MAX_SCOPE_SECONDS, "STOP_SQL_IO_SCOPE_TIME")
        self.resources.checkpoint_io()

    def name(self, path):
        require(isinstance(path, (str, Path)), "sql_io_path_scope")
        source = ROOT/path
        require(source.resolve().is_relative_to(ROOT.resolve()), "sql_io_path_outside_root")
        return source.relative_to(ROOT).as_posix() if Path(path).is_absolute() else str(path)

    def pin(self, path):
        return self.reader.fresh_pin(self.name(path))

    def json(self, path):
        return self.reader.json(self.name(path))

    def text(self, path):
        return self.reader.text(self.name(path))

    def finish(self):
        self.checkpoint()
        self.reader.finish()
        self.finished = True

    def summary(self):
        return {"read_passes": self.reader.read_passes, "bytes_read": self.reader.bytes_read,
            "bound_inputs": len(self.reader.snapshots), "final_fresh_hashes": self.reader.final_fresh_hashes,
            "finished": self.finished, "chunk_bytes": CHUNK_BYTES, "parse_budget_bytes": MAX_PARSE_BYTES,
            "read_bytes_per_second": READ_BYTES_PER_SECOND, "maximum_scope_seconds": MAX_SCOPE_SECONDS}
