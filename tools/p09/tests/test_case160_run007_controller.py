"""Reuse all 27 whole contracts with only explicit run007 metadata projection."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import case160_run007_controller as controller

MODULE, SOURCE_PROOF = controller.inherited_tests()


class Tests(MODULE.Tests):
    pass


if __name__ == "__main__": unittest.main()
