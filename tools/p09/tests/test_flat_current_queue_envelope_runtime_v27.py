"""All original controller14 tests with exact metadata-only source binding."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import flat_current_queue_envelope_runtime_v27 as controller
MODULE,AST_PROOFS=controller.test_namespace()
Tests=MODULE.Tests
