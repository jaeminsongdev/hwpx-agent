from __future__ import annotations

import tempfile
import unittest
import warnings
import zipfile
from pathlib import Path
from xml.etree import ElementTree

from PIL import Image

from tools.p08 import object_target_oracle as oracle


def common(
    tag: str = "rect",
    *,
    native_id: int = 8101,
    instid: int = 18101,
    group_level: int = 0,
    z_order: int = 0,
    body: str = "",
) -> str:
    return (
        f'<{tag} id="{native_id}" zOrder="{z_order}" textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES" '
        f'lock="0" groupLevel="{group_level}" instid="{instid}">'
        '<offset x="0" y="0"/><orgSz width="100" height="80"/>'
        '<sz width="100" height="80"/><pos x="0" y="0"/>'
        f'<outMargin left="0" right="0" top="0" bottom="0"/>{body}</{tag}>'
    )


def xml(value: str) -> ElementTree.Element:
    return ElementTree.fromstring(value)


class ObjectTargetOracleTests(unittest.TestCase):
    def test_duplicate_zip_member_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / "duplicate.hwpx"
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                with zipfile.ZipFile(package, "w") as archive:
                    archive.writestr("Contents/section0.xml", b"<sec/>")
                    archive.writestr("Contents/section0.xml", b"<sec/>")
            with self.assertRaisesRegex(oracle.OracleError, "duplicate_zip_member"):
                with oracle.SafeZip(package):
                    pass

    def test_windows_alias_zip_members_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / "aliases.hwpx"
            with zipfile.ZipFile(package, "w") as archive:
                archive.writestr("Contents/section0.xml", b"<sec/>")
                archive.writestr("contents/SECTION0.xml", b"<sec/>")
            with self.assertRaisesRegex(oracle.OracleError, "ambiguous_zip_member"):
                with oracle.SafeZip(package):
                    pass

    def test_resource_ids_may_remap_but_payload_and_embedding_must_not(self) -> None:
        payload = b"bounded-image"
        source = (
            xml(
                '<sec xmlns:hc="http://www.hancom.co.kr/hwpml/2011/core">'
                '<pic><hc:img binaryItemIDRef="source-id"/></pic></sec>'
            ),
            {"BinData/image.png": payload},
            xml(
                '<opf:package xmlns:opf="http://www.idpf.org/2007/opf/">'
                '<opf:manifest><opf:item id="source-id" href="BinData/image.png" '
                'media-type="image/png" isEmbeded="1"/></opf:manifest></opf:package>'
            ),
        )
        target = (
            xml(
                '<sec xmlns:hc="http://www.hancom.co.kr/hwpml/2011/core">'
                '<pic><hc:img binaryItemIDRef="image1"/></pic></sec>'
            ),
            {"BinData/image.png": payload},
            xml(
                '<opf:package xmlns:opf="http://www.idpf.org/2007/opf/">'
                '<opf:manifest><opf:item id="image1" href="BinData/image.png" '
                'media-type="image/png" isEmbeded="1"/></opf:manifest></opf:package>'
            ),
        )
        self.assertEqual(oracle.validate_resources(True, source, target), 1)
        target_item = next(element for element in target[2].iter() if oracle.local_name(element.tag) == "item")
        target_item.set("isEmbeded", "0")
        with self.assertRaisesRegex(oracle.OracleError, "resource_not_embedded"):
            oracle.validate_resources(True, source, target)

    def test_resource_path_and_inventory_drift_are_rejected(self) -> None:
        payload = b"bounded-image"

        def package(item_id: str, href: str) -> tuple[ElementTree.Element, dict[str, bytes], ElementTree.Element]:
            return (
                xml(
                    '<sec xmlns:hc="http://www.hancom.co.kr/hwpml/2011/core">'
                    f'<hc:img binaryItemIDRef="{item_id}"/></sec>'
                ),
                {href: payload},
                xml(
                    '<opf:package xmlns:opf="http://www.idpf.org/2007/opf/">'
                    '<opf:manifest>'
                    f'<opf:item id="{item_id}" href="{href}" media-type="image/png" isEmbeded="1"/>'
                    '</opf:manifest></opf:package>'
                ),
            )

        source = package("source-id", "BinData/image.png")
        remapped_path = package("target-id", "BinData/remapped.png")
        with self.assertRaisesRegex(oracle.OracleError, "resource_projection_mismatch"):
            oracle.validate_resources(True, source, remapped_path)

        orphaned = package("source-id", "BinData/image.png")
        orphaned[1]["BinData/orphan.png"] = b"orphan"
        with self.assertRaisesRegex(oracle.OracleError, "resource_inventory_mismatch"):
            oracle.validate_resources(True, source, orphaned)

    def test_exact_hancom_2020_resource_canonicalization_is_accepted(self) -> None:
        payload = b"bounded-image"
        digest = oracle.sha256_bytes(payload)

        def package(item_id: str, href: str) -> tuple[ElementTree.Element, dict[str, bytes], ElementTree.Element]:
            return (
                xml(
                    '<sec xmlns:hc="http://www.hancom.co.kr/hwpml/2011/core">'
                    f'<hc:img binaryItemIDRef="{item_id}"/></sec>'
                ),
                {href: payload},
                xml(
                    '<opf:package xmlns:opf="http://www.idpf.org/2007/opf/">'
                    '<opf:manifest>'
                    f'<opf:item id="{item_id}" href="{href}" media-type="image/png" isEmbeded="1"/>'
                    '</opf:manifest></opf:package>'
                ),
            )

        source = package("source-id", f"BinData/p08-{digest}.png")
        target = package("image1", "BinData/image1.png")
        self.assertEqual(oracle.validate_resources(True, source, target), 1)

        wrong_target = package("image2", "BinData/image2.png")
        with self.assertRaisesRegex(oracle.OracleError, "resource_projection_mismatch"):
            oracle.validate_resources(True, source, wrong_target)

    def test_core_alpha_and_connector_subject_loss_are_rejected(self) -> None:
        source = xml(f"<sec>{common(body='<lineShape alpha=\"51\"/>')}</sec>")
        target = xml(f"<sec>{common(body='<lineShape alpha=\"0\"/>')}</sec>")
        with self.assertRaisesRegex(oracle.OracleError, "semantic_subtree_mismatch:lineShape"):
            oracle.validate_semantics("OBJ-020", 18101, source, target)

        connector = (
            '<startPt x="0" y="0" subjectIDRef="1" subjectIdx="1"/>'
            '<endPt x="100" y="80" subjectIDRef="2" subjectIdx="2"/>'
            '<controlPoints/>'
        )
        disconnected = connector.replace('subjectIDRef="1" subjectIdx="1"', 'subjectIDRef="0" subjectIdx="0"').replace(
            'subjectIDRef="2" subjectIdx="2"', 'subjectIDRef="0" subjectIdx="0"'
        )
        source = xml(f"<sec>{common('connectLine', instid=18330, body=connector)}</sec>")
        target = xml(f"<sec>{common('connectLine', instid=18330, body=disconnected)}</sec>")
        with self.assertRaisesRegex(oracle.OracleError, "semantic_subtree_mismatch:startPt"):
            oracle.validate_semantics("OBJ-041", 18330, source, target)

    def test_only_reviewed_nested_group_common_child_normalization_is_allowed(self) -> None:
        source_object = common(
            "pic",
            instid=18251,
            group_level=1,
            body='<imgClip left="1" right="2" top="3" bottom="4"/>',
        )
        target_object = source_object.replace('<sz width="100" height="80"/>', "").replace(
            '<pos x="0" y="0"/>', ""
        ).replace('<outMargin left="0" right="0" top="0" bottom="0"/>', "")
        oracle.validate_semantics(
            "OBJ-031",
            18251,
            xml(f"<sec>{source_object}</sec>"),
            xml(f"<sec>{target_object}</sec>"),
        )

    def test_nested_zorder_and_id_normalization_preserve_instance_tree_order(self) -> None:
        first = common("pic", instid=18251, group_level=1, z_order=1)
        second = common("rect", instid=18252, group_level=1, z_order=2)
        source_group = common("container", instid=18250, body=first + second)
        target_group = common(
            "container",
            instid=18250,
            body=first.replace('zOrder="1"', 'zOrder="0"')
            + second.replace('zOrder="2"', 'zOrder="0"'),
        )
        oracle.validate_semantics(
            "OBJ-031",
            18251,
            xml(f"<sec>{source_group}</sec>"),
            xml(f"<sec>{target_group}</sec>"),
        )
        with self.assertRaisesRegex(oracle.OracleError, "object_structure_mismatch"):
            oracle.validate_semantics(
                "OBJ-031",
                18251,
                xml(f"<sec>{source_group}</sec>"),
                xml(f"<sec>{target_group.replace(first.replace('zOrder=\"1\"', 'zOrder=\"0\"') + second.replace('zOrder=\"2\"', 'zOrder=\"0\"'), second.replace('zOrder=\"2\"', 'zOrder=\"0\"') + first.replace('zOrder=\"1\"', 'zOrder=\"0\"'))}</sec>"),
            )

    def test_top_level_native_id_drift_and_non_numeric_identity_are_rejected(self) -> None:
        source = xml(f"<sec>{common()}</sec>")
        target = xml(f"<sec>{common()}</sec>")
        source[0].set("id", "8101")
        target[0].set("id", "8102")
        with self.assertRaisesRegex(oracle.OracleError, "object_attribute_mismatch:id"):
            oracle.validate_semantics("OBJ-020", 18101, source, target)
        target[0].set("id", "not-a-number")
        with self.assertRaisesRegex(oracle.OracleError, "invalid_native_attribute:id"):
            oracle.validate_semantics("OBJ-020", 18101, source, target)

    def test_root_attribute_namespace_and_form_identity_drift_are_rejected(self) -> None:
        source = xml(f"<sec>{common()}</sec>")
        target = xml(f"<sec>{common()}</sec>")
        target[0].set("ratio", "1")
        with self.assertRaisesRegex(oracle.OracleError, "object_attribute_mismatch:root"):
            oracle.validate_semantics("OBJ-001", 18101, source, target)

        namespaced_source = xml(
            '<sec xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph">'
            + common("hp:rect")
            + "</sec>"
        )
        wrong_namespace = xml(
            '<sec xmlns:evil="urn:wrong">' + common("evil:rect") + "</sec>"
        )
        with self.assertRaisesRegex(oracle.OracleError, "object_tag_mismatch"):
            oracle.validate_semantics("OBJ-001", 18101, namespaced_source, wrong_namespace)

        form = (
            '<edit id="8146" zOrder="0" groupLevel="0" instid="18146" name="p08field" '
            'printable="0"><sz width="100" height="80"/></edit>'
        )
        changed = form.replace('instid="18146"', 'instid="18147"')
        with self.assertRaisesRegex(oracle.OracleError, "form_attribute_mismatch:root"):
            oracle.validate_semantics(
                "OBJ-046", 18146, xml(f"<sec>{form}</sec>"), xml(f"<sec>{changed}</sec>")
            )
        with self.assertRaisesRegex(oracle.OracleError, "semantic_target_missing"):
            oracle.validate_semantics(
                "OBJ-046", 18146, xml(f"<sec>{changed}</sec>"), xml(f"<sec>{changed}</sec>")
            )

    def test_exact_hancom_form_canonicalization_preserves_stable_properties(self) -> None:
        source = xml(
            '<sec><edit id="8146" zOrder="0" numberingType="NONE" '
            'textWrap="TOP_AND_BOTTOM" textFlow="BOTH_SIDES" lock="0" '
            'dropcapstyle="None" href="" groupLevel="0" instid="18146" '
            'name="p08field" printable="0" tabOrder="0">'
            '<sz width="100" height="80"/><pos x="0" y="0"/>'
            '<outMargin left="0" right="0" top="0" bottom="0"/>'
            '<formCharPr charPrIDRef="0"/><text>value</text></edit></sec>'
        )
        target = xml(
            '<sec><edit name="p08field" printable="0" tabOrder="1">'
            '<formCharPr charPrIDRef="0"/><text>value</text>'
            '<sz width="100" height="80"/><pos x="0" y="0"/>'
            '<outMargin left="0" right="0" top="0" bottom="0"/>'
            '</edit></sec>'
        )
        oracle.validate_semantics("OBJ-046", 18146, source, target)
        next(element for element in target.iter() if oracle.local_name(element.tag) == "edit").set(
            "printable", "1"
        )
        with self.assertRaisesRegex(oracle.OracleError, "form_attribute_mismatch:root"):
            oracle.validate_semantics("OBJ-046", 18146, source, target)

    def test_exact_hancom_hyperlink_suffix_is_accepted(self) -> None:
        source = xml(
            f'<sec>{common().replace("instid=\"18101\"", "instid=\"18101\" href=\"https://example.test/p08\"")}</sec>'
        )
        target = xml(
            f'<sec>{common().replace("instid=\"18101\"", "instid=\"18101\" href=\"https://example.test/p08;0;0;0;\"")}</sec>'
        )
        oracle.validate_semantics("OBJ-048", 18101, source, target)
        target[0].set("href", "https://example.test/p08;0;0;1;")
        with self.assertRaisesRegex(oracle.OracleError, "object_attribute_mismatch:href"):
            oracle.validate_semantics("OBJ-048", 18101, source, target)

    def test_empty_connector_controls_may_be_omitted_but_nonempty_controls_may_not(self) -> None:
        endpoints = (
            '<startPt x="0" y="0" subjectIDRef="101" subjectIdx="1"/>'
            '<endPt x="100" y="80" subjectIDRef="102" subjectIdx="2"/>'
        )
        source = xml(
            f"<sec>{common('connectLine', instid=18330, body=endpoints + '<controlPoints/>')}</sec>"
        )
        target = xml(f"<sec>{common('connectLine', instid=18330, body=endpoints)}</sec>")
        oracle.validate_semantics("OBJ-041", 18330, source, target)
        canonical = xml(
            f"<sec>{common('connectLine', instid=18330, body=endpoints + '<controlPoints><point x=\"7200\" y=\"-12600\" type=\"3\"/><point x=\"3600\" y=\"-7200\" type=\"26\"/></controlPoints>')}</sec>"
        )
        oracle.validate_semantics("OBJ-041", 18330, target, canonical)
        nonempty = xml(
            f"<sec>{common('connectLine', instid=18330, body=endpoints + '<controlPoints><point x=\"1\" y=\"2\" type=\"3\"/></controlPoints>')}</sec>"
        )
        with self.assertRaisesRegex(oracle.OracleError, "semantic_subtree_mismatch:controlPoints"):
            oracle.validate_semantics("OBJ-041", 18330, nonempty, target)

    def test_render_comparison_is_exact_and_rejects_empty_pages(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "first.png"
            same = root / "same.png"
            changed = root / "changed.png"
            empty = root / "empty.png"
            image = Image.new("RGB", (20, 20), "white")
            image.putpixel((10, 10), (0, 0, 0))
            image.save(first)
            image.save(same)
            changed_image = image.copy()
            changed_image.putpixel((10, 10), (1, 1, 1))
            changed_image.save(changed)
            Image.new("RGB", (20, 20), "white").save(empty)
            self.assertEqual(
                oracle.compare_image_files(first, same)["nonwhite_bbox"],
                [10, 10, 11, 11],
            )
            with self.assertRaisesRegex(oracle.OracleError, "render_pixel_mismatch"):
                oracle.compare_image_files(first, changed)
            with self.assertRaisesRegex(oracle.OracleError, "render_empty_page"):
                oracle.compare_image_files(empty, empty)

    def test_calibrated_render_change_is_bounded_to_affected_region(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "first.png"
            accepted = root / "accepted.png"
            outside = root / "outside.png"
            image = Image.new("RGB", (794, 1122), "white")
            image.putpixel((113, 133), (0, 0, 0))
            image.putpixel((276, 241), (0, 0, 0))
            image.putpixel((135, 166), (20, 60, 160))
            image.save(first)
            accepted_image = image.copy()
            accepted_image.putpixel((135, 166), (21, 60, 160))
            accepted_image.save(accepted)
            outside_image = accepted_image.copy()
            outside_image.putpixel((134, 165), (254, 254, 254))
            outside_image.save(outside)
            result = oracle.compare_image_files(first, accepted, "OBJ-020")
            self.assertEqual(result["changed_pixels"], 1)
            with self.assertRaisesRegex(oracle.OracleError, "render_calibration_exceeded"):
                oracle.compare_image_files(first, outside, "OBJ-020")


if __name__ == "__main__":
    unittest.main()
