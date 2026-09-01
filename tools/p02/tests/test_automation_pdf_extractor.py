from __future__ import annotations

import json
import hashlib
from pathlib import Path
import tempfile
import unittest

from tools.p02.extract_automation_pdfs import (
    ExtractionConfig,
    ExtractionError,
    HorizontalLine,
    PageLayout,
    ParsedItem,
    SourceInput,
    TextLine,
    parse_action_table,
    parse_automation_events,
    parse_automation_objects,
    parse_manual_event_summary,
    parse_parameter_table,
    record_id,
    run,
    serialize_records,
    source_record,
)
from tools.p02.verify_automation_output import verify

ROOT = Path(__file__).resolve().parents[3]
FIXTURE = ROOT / "fixtures" / "synthetic" / "p02-automation-pdf" / "negative-layouts.json"
SHA256 = "a" * 64


def text_line(x: float, y: float, text: str) -> TextLine:
    return TextLine(x, y, x + max(10, len(text) * 5), y + 10, text)


def page_layout(
    number: int,
    lines: list[tuple[float, float, str]],
    boundaries: list[tuple[float, float, float]],
) -> PageLayout:
    return PageLayout(
        number=number,
        width=842,
        height=595,
        text_lines=tuple(text_line(*line) for line in lines),
        horizontal_lines=tuple(HorizontalLine(*line) for line in boundaries),
    )


def source(kind: str) -> SourceInput:
    return SourceInput(
        source_kind=kind,
        source_id=f"synthetic-{kind}",
        path=Path("unused.pdf"),
        source_entry={"sha256": SHA256, "license_state": "public_reference"},
        content=b"unused",
    )


class AutomationPdfExtractorTests(unittest.TestCase):
    def test_action_table_preserves_wrapped_id_and_parameter_set(self) -> None:
        layout = page_layout(
            2,
            [
                (92, 550, "Action ID"),
                (92, 520, "LongActionNam"),
                (92, 505, "e"),
                (264, 520, "SampleSet*"),
                (393, 520, "합성 설명"),
            ],
            [(86, 532, 756), (86, 490, 756)],
        )
        items = parse_action_table(source("action_table"), [layout])
        self.assertEqual(items[0].name, "LongActionName")
        self.assertEqual(items[0].parameters[0]["original_name"], "SampleSet*")

    def test_parameter_table_keeps_type_subtype_and_explicit_missing_type(self) -> None:
        layout = page_layout(
            5,
            [
                (90, 570, "5) SampleSet : 합성 파라미터셋"),
                (152, 550, "Item ID"),
                (260, 550, "Type"),
                (350, 550, "SubType"),
                (433, 550, "Description"),
                (121, 515, "ArrayItem"),
                (245, 515, "PIT_ARRAY"),
                (319, 515, "PIT_UI2"),
                (433, 515, "배열"),
                (121, 475, "MissingType"),
                (319, 475, "PIT_UI1"),
                (433, 475, "원문 Type 공란"),
            ],
            [(116, 532, 757), (116, 495, 757), (116, 455, 757)],
        )
        items = parse_parameter_table(source("parameter_table"), [layout])
        self.assertEqual(items[0].parameters[0]["declared_type"], "PIT_ARRAY [SubType=PIT_UI2]")
        self.assertEqual(
            items[1].parameters[0]["declared_type"],
            "[Type missing] [SubType=PIT_UI1]",
        )

    def test_object_declaration_parses_optional_parameter_after_row_assembly(self) -> None:
        layout = page_layout(
            12,
            [
                (94, 570, "ISampleObject : 합성 객체"),
                (145, 550, "Item Name"),
                (372, 550, "Description"),
                (100, 520, "Open(Method)"),
                (248, 530, "Description"),
                (248, 518, "문서를 연다."),
                (248, 506, "Declaration"),
                (248, 494, "Open(BSTR path, [VARIANT format])"),
                (248, 482, "Parameters"),
                (248, 470, "path : 경로"),
                (248, 458, "format : 형식"),
            ],
            [(93, 540, 547), (93, 450, 547)],
        )
        item = parse_automation_objects(source("automation_object"), [layout])[0]
        self.assertEqual([parameter["original_name"] for parameter in item.parameters], ["path", "format"])
        self.assertIsNone(item.parameters[0]["required"])
        self.assertFalse(item.parameters[1]["required"])

    def test_manual_and_code_event_sources_remain_separate(self) -> None:
        manual = page_layout(
            46,
            [
                (96, 570, "IHwpObjectEvents(_DIHwpObjectEvents) : 이벤트"),
                (135, 550, "Item Name"),
                (236, 550, "Return"),
                (389, 550, "Description"),
                (101, 510, "DocumentChange"),
                (227, 510, "long"),
                (285, 510, "문서 변경"),
            ],
            [(95, 560, 546), (95, 540, 546), (95, 490, 546)],
        )
        code = page_layout(
            3,
            [(90, 500, "STDMETHOD(DocumentChange)(long newVal)")],
            [],
        )
        summary_item = parse_manual_event_summary(source("automation_object"), [manual])[0]
        code_item = parse_automation_events(source("automation_event"), [code])[0]
        self.assertEqual(summary_item.parameters[0]["original_name"], "Return")
        self.assertEqual(code_item.parameters[0]["original_name"], "newVal")
        self.assertNotEqual(summary_item.source_id, code_item.source_id)

    def test_negative_layout_fixtures_fail_closed(self) -> None:
        fixtures = json.loads(FIXTURE.read_text(encoding="utf-8"))

        def layout(name: str) -> PageLayout:
            case = fixtures[name]
            return page_layout(case["page"], case["text_lines"], case["horizontal_lines"])

        with self.assertRaisesRegex(ExtractionError, "no preceding item"):
            parse_action_table(source("action_table"), [layout("action_continuation_without_item")])
        with self.assertRaisesRegex(ExtractionError, "multiple declared types"):
            parse_parameter_table(source("parameter_table"), [layout("parameter_multiple_types")])
        with self.assertRaisesRegex(ExtractionError, "ambiguous automation item"):
            parse_automation_objects(
                source("automation_object"), [layout("automation_item_without_marker")]
            )
        with self.assertRaisesRegex(ExtractionError, "ambiguous STDMETHOD"):
            parse_automation_events(
                source("automation_event"), [layout("malformed_event_signature")]
            )

    def test_record_identity_and_serialization_are_deterministic(self) -> None:
        item = ParsedItem(
            source_kind="automation_event",
            source_id="synthetic-event",
            source_sha256=SHA256,
            page_start=3,
            page_end=4,
            section="synthetic",
            name="DocumentChange",
            description=None,
        )
        self.assertEqual(record_id(item), record_id(item))
        record = source_record(item, "synthetic-source-lock", 0)
        self.assertEqual(serialize_records([record]), serialize_records([record]))
        self.assertEqual(record["locator"]["value"], "automation_event/p000003-p000004")

    def test_restricted_sources_reject_non_private_output_before_pdf_read(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            lock = root / "source-lock.json"
            sources = []
            ids = {}
            for kind in ("action", "parameter", "automation", "event"):
                source_id = f"synthetic-{kind}"
                ids[kind] = source_id
                sources.append(
                    {
                        "source_id": source_id,
                        "kind": "pdf_manual",
                        "sha256": SHA256,
                        "license_state": "restricted",
                    }
                )
            lock.write_text(
                json.dumps({"source_lock_id": "synthetic-lock", "sources": sources}),
                encoding="utf-8",
            )
            config = ExtractionConfig(
                source_lock=lock,
                action_source_id=ids["action"],
                action_input=root / "missing-action.pdf",
                parameter_source_id=ids["parameter"],
                parameter_input=root / "missing-parameter.pdf",
                automation_source_id=ids["automation"],
                automation_input=root / "missing-automation.pdf",
                event_source_id=ids["event"],
                event_input=root / "missing-event.pdf",
                output_root=root,
                output_relative="records.json",
            )
            with self.assertRaisesRegex(ExtractionError, "implementation/p02/evidence"):
                run(config)

    def test_independent_verifier_binds_every_input_source(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            role_to_kind = {
                "action_table": "action_table",
                "parameter_table": "parameter_table",
                "automation_object": "automation_object",
                "automation_event": "automation_event",
            }
            source_ids: dict[str, str] = {}
            source_inputs: dict[str, Path] = {}
            lock_entries = []
            records = []
            for ordinal, (role, record_kind) in enumerate(role_to_kind.items()):
                source_id = f"synthetic-{role}"
                content = f"synthetic-pdf-{role}".encode()
                digest = hashlib.sha256(content).hexdigest()
                path = root / f"{role}.pdf"
                path.write_bytes(content)
                source_ids[role] = source_id
                source_inputs[role] = path
                lock_entries.append(
                    {
                        "source_id": source_id,
                        "kind": "pdf_manual",
                        "sha256": digest,
                        "license_state": "public_reference",
                    }
                )
                parameters = []
                if record_kind == "parameter_table":
                    parameters = [
                        {
                            "ordinal": 0,
                            "original_name": "SyntheticItem",
                            "declared_type": "PIT_UI1",
                            "direction": "unknown",
                            "required": None,
                            "description_ko": None,
                        }
                    ]
                item = ParsedItem(
                    source_kind=record_kind,
                    source_id=source_id,
                    source_sha256=digest,
                    page_start=ordinal + 1,
                    page_end=ordinal + 1,
                    section=f"section-{role}",
                    name=f"Item{ordinal}",
                    description=None,
                    parameters=parameters,
                )
                records.append(source_record(item, "synthetic-lock", ordinal))
            lock = root / "source-lock.json"
            lock.write_text(
                json.dumps({"source_lock_id": "synthetic-lock", "sources": lock_entries}),
                encoding="utf-8",
            )
            output = root / "records.json"
            output.write_bytes(serialize_records(records))
            result = verify(output, lock, source_ids, source_inputs)
            self.assertEqual(result["errors"], [])
            self.assertEqual(result["record_count"], 4)


if __name__ == "__main__":
    unittest.main()
