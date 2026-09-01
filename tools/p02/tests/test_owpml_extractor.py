from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tools.p02.extract_owpml import (
    ExtractionConfig,
    ExtractionError,
    build_records,
    decode_machine_standard,
    load_source_entry,
    parse_package_parts,
    parse_schema_sections,
    run,
    serialize_records,
)
from tools.p02.verify_owpml_output import verify


def schema(namespace_suffix: str, body: str) -> str:
    return (
        "<div><table><tr><td><?xml version=\"1.0\" encoding=\"UTF-8\"?><br/>"
        f"<xs:schema xmlns:xs=\"http://www.w3.org/2001/XMLSchema\" "
        f"targetNamespace=\"http://www.owpml.org/owpml/2024/{namespace_suffix}\"><br/>"
        f"{body}<br/></xs:schema></td></tr></table></div>"
    )


def machine_document() -> dict:
    package = (
        "<table><tr><td><br/>* ZIP Container<br/>mimetype<br/>version.xml<br/>"
        "META-INF/<br/>container.xml<br/>[manifest.xml]<br/>Contents/<br/>"
        "header.xml<br/>section0.xml<br/>XMLTemplate/<br/>TemplateSchema.xsd"
        "</td><td>descriptions</td></tr></table>"
    )
    titles = [{"NUMBERING": "8.2", "TITLEINDEX": "8.2 OCF OWPML 프로파일"}]
    contents = [{"NUMBERING": "8.2", "TITLE_NUMBERING": "8.2", "CONTENT": package}]
    names = {
        "B": "version",
        "C": "head",
        "D": "section",
        "E": "paragraph",
        "F": "core",
        "G": "master-page",
        "H": "history",
    }
    for appendix, namespace_suffix in names.items():
        element_name = f"{namespace_suffix}Root"
        if appendix == "C":
            element_name = (
                "<div class='jb-container'><div class='jb-title'>HWP</div>"
                "<div class='jb-text'>glossary definition</div></div>MLHead"
            )
        body = (
            f'<xs:element name="{element_name}"><xs:annotation>'
            f"<xs:documentation>{appendix} 설명</xs:documentation></xs:annotation>"
            "<xs:complexType><xs:attribute name=\"id\" type=\"xs:string\"/>"
            "</xs:complexType></xs:element>"
        )
        if appendix == "C":
            body = (
                '<xs:import namespace="http://www.owpml.org/owpml/2024/core" '
                'schemaLocation="HWPMLCoreSchema.xsd"/><br/>' + body
            )
        titles.append(
            {"NUMBERING": appendix, "TITLEINDEX": f"{appendix} Synthetic XML 스키마"}
        )
        contents.append(
            {
                "NUMBERING": appendix,
                "TITLE_NUMBERING": appendix,
                "CONTENT": schema(namespace_suffix, body),
            }
        )
    return {
        "info": {
            "ksCode": "KSX6101",
            "tmprKsNo": "KSX6101",
            "reformNo": "03",
            "activeYn": "Y",
            "operationDate": "2024년 10월 30일",
        },
        "title": titles,
        "content": contents,
    }


class OwpmlExtractorTests(unittest.TestCase):
    def write_source(self, root: Path, license_state: str = "public_reference") -> tuple[Path, Path]:
        source = root / "machine.json"
        content = (json.dumps(machine_document(), ensure_ascii=False) + "\n").encode("utf-8")
        source.write_bytes(content)
        source_lock = root / "source-lock.json"
        source_lock.write_text(
            json.dumps(
                {
                    "schema_version": "hwpx-agent.source-lock/v2",
                    "source_lock_id": "synthetic-owpml-lock",
                    "sources": [
                        {
                            "source_id": "synthetic-ksx6101",
                            "kind": "machine_readable_standard",
                            "license_state": license_state,
                            "sha256": hashlib.sha256(content).hexdigest(),
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        return source, source_lock

    def config(self, root: Path, source: Path, source_lock: Path) -> ExtractionConfig:
        return ExtractionConfig(
            source_lock=source_lock,
            source_id="synthetic-ksx6101",
            input_path=source,
            output_root=root,
            output_relative="records/owpml.json",
        )

    def test_builds_deterministic_schema_and_package_coverage(self) -> None:
        document = decode_machine_standard(
            (json.dumps(machine_document(), ensure_ascii=False) + "\n").encode("utf-8")
        )
        first, coverage = build_records("lock", "synthetic-ksx6101", "a" * 64, document)
        second, _ = build_records("lock", "synthetic-ksx6101", "a" * 64, document)
        self.assertEqual(serialize_records(first), serialize_records(second))
        self.assertEqual(coverage["appendices"], list("BCDEFGH"))
        self.assertEqual(coverage["namespace_versions"], ["2024"])
        self.assertEqual(coverage["glossary_replacement_count"], 1)
        self.assertEqual(coverage["component_counts"]["schema"], 7)
        self.assertEqual(coverage["component_counts"]["element"], 7)
        self.assertEqual(coverage["component_counts"]["attribute"], 7)
        self.assertIn("HWPMLHead", [record["original_name"] for record in first])
        self.assertNotIn("<?xml", serialize_records(first).decode("utf-8"))

    def test_publishes_no_overwrite_and_verifies_independently(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "records").mkdir()
            source, source_lock = self.write_source(root)
            config = self.config(root, source, source_lock)
            receipt = run(config)
            output = root / "records" / "owpml.json"
            result = verify(output, source_lock, "synthetic-ksx6101", source)
            self.assertEqual(result["errors"], [])
            self.assertEqual(receipt["output_sha256"], hashlib.sha256(output.read_bytes()).hexdigest())
            with self.assertRaisesRegex(ExtractionError, "already exists"):
                run(config)

    def test_rejects_tamper_and_wrong_source_kind(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "records").mkdir()
            source, source_lock = self.write_source(root)
            source.write_bytes(source.read_bytes() + b" ")
            with self.assertRaisesRegex(ExtractionError, "SHA-256 mismatch"):
                run(self.config(root, source, source_lock))
            lock = json.loads(source_lock.read_text(encoding="utf-8"))
            lock["sources"][0]["kind"] = "web_help"
            source_lock.write_text(json.dumps(lock), encoding="utf-8")
            with self.assertRaisesRegex(ExtractionError, "not machine_readable_standard"):
                load_source_entry(source_lock, "synthetic-ksx6101")

    def test_rejects_missing_or_duplicate_schema_authority(self) -> None:
        document = machine_document()
        document["title"] = document["title"][:-1]
        document["content"] = document["content"][:-1]
        with self.assertRaisesRegex(ExtractionError, "appendix H must occur exactly once"):
            parse_schema_sections(document)
        document = machine_document()
        document["content"][-1]["CONTENT"] = document["content"][-2]["CONTENT"]
        with self.assertRaisesRegex(ExtractionError, "duplicate targetNamespace"):
            parse_schema_sections(document)

    def test_rejects_entities_residual_markup_and_excessive_depth(self) -> None:
        document = machine_document()
        document["content"][1]["CONTENT"] = document["content"][1]["CONTENT"].replace(
            "<?xml", "<!DOCTYPE x [<!ENTITY y 'z'>]><?xml"
        )
        with self.assertRaisesRegex(ExtractionError, "prohibited XML declaration"):
            parse_schema_sections(document)
        document = machine_document()
        document["content"][1]["CONTENT"] = document["content"][1]["CONTENT"].replace(
            "</xs:schema>", "<div>unexpected</div></xs:schema>"
        )
        with self.assertRaisesRegex(ExtractionError, "residual viewer markup"):
            parse_schema_sections(document)
        document = machine_document()
        nested = "<xs:annotation>" * 65 + "<xs:documentation>x</xs:documentation>" + "</xs:annotation>" * 65
        document["content"][1]["CONTENT"] = schema("version", nested)
        with self.assertRaisesRegex(ExtractionError, "depth limit"):
            parse_schema_sections(document)

    def test_rejects_package_traversal_and_restricted_output_escape(self) -> None:
        document = machine_document()
        document["content"][0]["CONTENT"] = document["content"][0]["CONTENT"].replace(
            "header.xml", "../header.xml"
        )
        with self.assertRaisesRegex(ExtractionError, "unsupported package part token"):
            parse_package_parts(document)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "records").mkdir()
            source, source_lock = self.write_source(root, license_state="restricted")
            with self.assertRaisesRegex(ExtractionError, "implementation/p02/evidence"):
                run(self.config(root, source, source_lock))

    def test_rejects_output_traversal_before_publication(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, source_lock = self.write_source(root)
            config = replace(
                self.config(root, source, source_lock), output_relative="../escape.json"
            )
            with self.assertRaisesRegex(ExtractionError, "normal repository-style"):
                run(config)


if __name__ == "__main__":
    unittest.main()
