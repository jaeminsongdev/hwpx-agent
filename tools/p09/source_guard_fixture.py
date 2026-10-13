"""Class-local immutable source text; fresh byte binding and final rehash, no cross-run cache."""
from pathlib import PurePosixPath

from audit_evidence_io import AuditEvidenceReader, require
from conservative_maintenance import ROOT


class SourceGuardFixture:
    # Used only for source-only tests. Not a JSON/receipt cache or runtime acceptance.
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        require("_source_reader" not in cls.__dict__, "source_fixture_lifecycle_overlap")
        files = cls.SOURCE_FILES
        require(isinstance(files, tuple) and len(files) == 2
            and all(isinstance(pair, tuple) and len(pair) == 2 for pair in files)
            and tuple(pair[0] for pair in files) == ("source", "driver"), "source_fixture_config_scope")
        for _, name in files:
            require(isinstance(name, str) and name and not PurePosixPath(name).is_absolute()
                and ".." not in PurePosixPath(name).parts and ":" not in name and "\\" not in name,
                "source_fixture_path_scope")
        require(isinstance(cls.SOURCE_SLICE, tuple) and len(cls.SOURCE_SLICE) == 2
            and all(isinstance(marker, str) and marker for marker in cls.SOURCE_SLICE),
            "source_fixture_slice_scope")
        cls._source_reader = AuditEvidenceReader(ROOT, lambda: None)
        try:
            for attribute, name in files:
                setattr(cls, attribute, cls._source_reader.text(name))
            begin, end = (cls.source.index(marker) for marker in cls.SOURCE_SLICE)
            require(begin < end, "source_fixture_slice_scope")
            cls.live = cls.source[begin:end]
        except (OSError, ValueError):
            cls._release_source_fixture()
            raise

    @classmethod
    def _release_source_fixture(cls):
        for name in ("source", "driver", "live", "_source_reader"):
            if name in cls.__dict__:
                delattr(cls, name)

    @classmethod
    def tearDownClass(cls):
        try:
            # Every byte is freshly re-read even though all test instances shared text.
            cls._source_reader.finish()
        finally:
            cls._release_source_fixture()
            super().tearDownClass()
