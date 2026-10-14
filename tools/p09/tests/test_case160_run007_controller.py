"""Reuse all 27 whole contracts with only explicit run007 metadata projection."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import case160_run007_controller as controller

MODULE, SOURCE_PROOF = controller.inherited_tests()


class Tests(MODULE.Tests):
    def test_preflight_selection_is_closed_and_does_not_retry(self):
        current = controller.initialize()
        for value in (True, 1, 9, 2.0, "2"):
            with self.assertRaises(ValueError): controller.select_preflight(current, value)
        self.assertEqual(current.PREFLIGHT, controller.PREFLIGHT)

    def test_preflight_selection_keeps_all_body_code_and_binding_identity(self):
        current = controller.initialize()
        before = current._env["preflight_projection"]
        binding = current.binding
        selected = controller.select_preflight(current, 3)
        self.assertTrue(selected.endswith("preflight047.v1.json"))
        self.assertIs(current.binding, binding)
        self.assertEqual(current.binding.__globals__["PREFLIGHT"], selected)
        self.assertEqual(current.M.PREFLIGHT, selected)
        self.assertIs(current.M.preflight_projection, current._env["preflight_projection"])
        inverse = controller.projected(current.M.preflight_projection, current._env,
            {"-envelope-controller-preflight047.v1.json":"-envelope-controller-preflight046.v1.json"})
        self.assertEqual(inverse.__code__, before.__code__)
        self.assertEqual(inverse.__defaults__, before.__defaults__)
        self.assertEqual(inverse.__closure__, before.__closure__)

    def test_qualification_selection_rejects_nonclosed_attempts(self):
        current = controller.initialize()
        for value in (False, 0, 9, 1.0, "1"):
            with self.assertRaises(ValueError): controller.select_qualification(current, value)
        self.assertEqual(current.QUAL, controller.QUAL)
        self.assertEqual(current.DATA, controller.DATA)

    def test_qualification_selection_keeps_actual_function_environments(self):
        current = controller.initialize()
        qualify, binding, api = current.qualify, current.binding, current.API
        qual, data = controller.select_qualification(current, 2)
        self.assertTrue(qual.endswith("r390-run002.v1.json"))
        self.assertTrue(data.endswith("data048.v1.json"))
        self.assertIs(current.qualify, qualify)
        self.assertIs(current.binding, binding)
        self.assertIs(current.API, api)
        self.assertEqual(current.qualify.__globals__["QUAL"], qual)
        self.assertEqual(current.binding.__globals__["DATA"], data)
        self.assertEqual(current.M.DATA, data)
        self.assertEqual(current.API.QUAL_PATH, qual)
        self.assertEqual(current._api_env["QUAL_PATH"], qual)


if __name__ == "__main__": unittest.main()
