from __future__ import annotations

import io
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "tools/p17"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import codex_bundle  # noqa: E402


class CodexBundleTests(unittest.TestCase):
    def test_source_and_composed_bundle_are_exact(self) -> None:
        source, source_errors = codex_bundle.read_codex_entries()
        entries, errors = codex_bundle.compose_entries()
        self.assertEqual(source_errors, [])
        self.assertEqual(errors, [])
        self.assertEqual(set(source), set(codex_bundle.CODEX_FILES))
        self.assertEqual(len(entries), 19)

    def test_composition_is_deterministic(self) -> None:
        first, first_errors = codex_bundle.compose_entries()
        second, second_errors = codex_bundle.compose_entries()
        self.assertEqual(first_errors + second_errors, [])
        self.assertEqual(codex_bundle.deterministic_zip_bytes(first), codex_bundle.deterministic_zip_bytes(second))

    def test_manifest_adds_skills_but_no_unqualified_connection(self) -> None:
        entries, errors = codex_bundle.compose_entries()
        self.assertEqual(errors, [])
        manifest, parse_errors = codex_bundle.universal.load_json_bytes(
            entries[".codex-plugin/plugin.json"], "manifest"
        )
        self.assertEqual(parse_errors, [])
        self.assertIsNotNone(manifest)
        assert manifest is not None
        self.assertEqual(manifest["skills"], "./skills/")
        self.assertNotIn("apps", manifest)
        self.assertNotIn("mcpServers", manifest)

    def test_command_drift_and_forbidden_content_fail(self) -> None:
        entries, errors = codex_bundle.read_codex_entries()
        self.assertEqual(errors, [])
        entries["commands/create.md"] = b"# Command\n\nUse HAction.Run.\n"
        result = codex_bundle.validate_codex_entries(entries)
        self.assertIn("command.contract:commands/create.md", result)
        self.assertIn("source.forbidden:commands/create.md", result)

    def test_invalid_agent_frontmatter_fails(self) -> None:
        entries, errors = codex_bundle.read_codex_entries()
        self.assertEqual(errors, [])
        entries["agents/hancom-document-engineer.md"] = b"# missing frontmatter\n"
        self.assertIn("agent.contract", codex_bundle.validate_codex_entries(entries))

    def test_archive_traversal_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            archive_path = Path(directory) / "bad.zip"
            output = io.BytesIO()
            with zipfile.ZipFile(output, "w") as archive:
                archive.writestr("../escape", b"x")
                archive.writestr("..\\windows-escape", b"x")
            archive_path.write_bytes(output.getvalue())
            self.assertIn("archive.entry_path", codex_bundle.validate_archive(archive_path))

    def test_publish_is_no_overwrite_and_validates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "bundle.zip"
            result, errors = codex_bundle.publish_archive(output)
            self.assertEqual(errors, [])
            self.assertIsNotNone(result)
            self.assertEqual(codex_bundle.validate_archive(output), [])
            second, second_errors = codex_bundle.publish_archive(output)
            self.assertIsNone(second)
            self.assertEqual(second_errors, ["output.exists"])


if __name__ == "__main__":
    unittest.main()
