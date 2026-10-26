use domain_ir::ReferenceAuxiliaryLimits;
use hwpx_package::cross_reference_sdk::SdkCrossReferenceDisplay as D;
use hwpx_package::document_import::fields::{
    ImportedDocumentFields,
    block_bookmarks::ImportedBlockBookmarks,
    bookmark_crossref::{
        BookmarkCrossReferenceDisplay, SourceBookmarkCrossReferenceBindings,
        SourceBookmarkResolution,
    },
    bookmark_insertion::{SourceBookmarkInsertion as Request, SourceBookmarkInsertionError as E},
    semantics::{
        ImportedFieldMeaning,
        source_index::{SourceFieldMeaningIndex, bookmark_updates::SourceBookmarkCommandChange},
    },
};
use hwpx_package::{
    BoundedZipReader, IdIndex, IdIndexError, IdIndexLimits, IdRuleProfile, PackageGraph,
    PackageGraphLimits, PackageLimits, WriterLimits,
};
use std::{error::Error, io::Cursor};
#[path = "support/document_import_field_fixture.rs"]
#[allow(dead_code)]
mod fixture;
#[path = "support/block_bookmark679_fixture.rs"]
mod native;
type Result = std::result::Result<(), Box<dyn Error>>;
fn limits() -> ReferenceAuxiliaryLimits {
    ReferenceAuxiliaryLimits::new(Default::default()).expect("finite limits")
}
fn index(raw: &[u8], profile: IdRuleProfile) -> std::result::Result<IdIndex, Box<dyn Error>> {
    let mut reader = BoundedZipReader::open(Cursor::new(raw), PackageLimits::default())?;
    let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
    Ok(IdIndex::build(&mut reader, &graph, profile, IdIndexLimits::default())?)
}
fn block(id: u32, field: u32, prop: &str) -> String {
    format!(
        "<hp:ctrl><hp:fieldBegin id='{id}' type='BOOKMARK' name='b{id}' fieldid='{field}'><hp:parameters cnt='1' name=''><hp:integerParam name='Prop'>{prop}</hp:integerParam></hp:parameters></hp:fieldBegin></hp:ctrl><hp:t>text</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='{id}' fieldid='{field}'/></hp:ctrl>"
    )
}
fn sample(body: &str) -> std::result::Result<Vec<u8>, Box<dyn Error>> {
    fixture::package(&format!("<hp:p id='1'><hp:run>{body}</hp:run></hp:p>"))
}
fn output(raw: &[u8], display: D, link: bool) -> std::result::Result<Vec<u8>, Box<dyn Error>> {
    let forms = fixture::forms(raw, "block679")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let (run, target) = native::select(&forms)?;
    let proof = forms.reconstruct_source_for_verification(raw)?;
    Ok(fields
        .create_bookmark_reference(
            &proof,
            Request {
                run: &run,
                target_id: &target,
                display,
                hyperlink: link,
            },
            limits(),
            WriterLimits::default(),
        )?
        .with_verified_bytes(|v| v.to_vec())?)
}
#[test]
fn native_shared_scalars_require_the_new_profile_and_keep_begin_ids() -> Result {
    let raw = native::native_source()?;
    assert!(index(&raw, IdRuleProfile::hwpml_2011_shape_v6()).is_err());
    let current = index(&raw, IdRuleProfile::hancom_2020_block_bookmark_v12())?;
    assert_eq!(
        current
            .declarations()
            .iter()
            .filter(|v| v.kind() == hwpx_package::IdKind::FieldBegin)
            .count(),
        8
    );
    Ok(())
}
#[test]
fn mismatched_end_scalar_rejects_instead_of_ignoring_the_attribute() -> Result {
    let raw = sample(&block(1, 777, "2").replace(
        "beginIDRef='1' fieldid='777'",
        "beginIDRef='1' fieldid='778'",
    ))?;
    assert!(matches!(
        index(&raw, IdRuleProfile::hancom_2020_block_bookmark_v12()),
        Err(ref e) if matches!(e.downcast_ref::<IdIndexError>(),Some(IdIndexError::BlockBookmarkProfileRejected))
    ));
    Ok(())
}
#[test]
fn duplicate_begin_identity_is_still_rejected() -> Result {
    let raw = sample(&(block(1, 777, "2") + &block(1, 777, "2")))?;
    assert!(index(&raw, IdRuleProfile::hancom_2020_block_bookmark_v12()).is_err());
    Ok(())
}
#[test]
fn unsupported_prop_cannot_use_scalar_classification() -> Result {
    let raw = sample(&block(1, 777, "1"))?;
    assert!(matches!(
        index(&raw, IdRuleProfile::hancom_2020_block_bookmark_v12()),
        Err(ref e) if matches!(e.downcast_ref::<IdIndexError>(),Some(IdIndexError::BlockBookmarkProfileRejected))
    ));
    Ok(())
}
#[test]
fn same_paragraph_pairing_is_required_by_the_observed_profile() -> Result {
    let body = block(1, 777, "2").replace(
        "<hp:ctrl><hp:fieldEnd",
        "</hp:run></hp:p><hp:p id='2'><hp:run><hp:ctrl><hp:fieldEnd",
    );
    let raw = sample(&body)?;
    assert!(index(&raw, IdRuleProfile::hancom_2020_block_bookmark_v12()).is_err());
    Ok(())
}
#[test]
fn duplicate_instance_ids_of_other_field_kinds_keep_legacy_rejection() -> Result {
    let field = "<hp:ctrl><hp:fieldBegin id='1' type='FORMULA' fieldid='777'/></hp:ctrl><hp:t>x</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='1' fieldid='777'/></hp:ctrl>";
    let raw = sample(
        &(field.to_owned()
            + &field
                .replace("id='1'", "id='2'")
                .replace("beginIDRef='1'", "beginIDRef='2'")),
    )?;
    assert!(index(&raw, IdRuleProfile::hancom_2020_block_bookmark_v12()).is_err());
    Ok(())
}
#[test]
fn actual_derived_source_creates_content_fields_and_preserves_all_eight_blocks() -> Result {
    let raw = native::derived_source()?;
    let original = fixture::forms(&raw, "block679")?;
    let old_fields = ImportedDocumentFields::import(&original)?;
    let old = ImportedBlockBookmarks::import(&old_fields, limits())?;
    for link in [false, true] {
        let out = output(&raw, D::Content, link)?;
        let forms = fixture::forms(&out, "block679")?;
        let fields = ImportedDocumentFields::import(&forms)?;
        let blocks = ImportedBlockBookmarks::import(&fields, limits())?;
        assert_eq!(fields.fields().len(), 9);
        assert_eq!(blocks.observations().len(), 8);
        for (a, b) in old.observations().iter().zip(blocks.observations()) {
            assert_eq!(a.name(), b.name());
            assert_eq!(a.selected_source(), b.selected_source());
        }
        let binding = SourceBookmarkCrossReferenceBindings::import(&fields, limits())?;
        assert_eq!(binding.bindings().len(), 1);
        let b = &binding.bindings()[0];
        assert_eq!(b.display, BookmarkCrossReferenceDisplay::Content);
        assert_eq!(b.hyperlink, link);
        assert!(
            matches!(&b.target,SourceBookmarkResolution::Bound{logical_target_id,..}if logical_target_id==blocks.observations()[0].field_reference_id())
        );
        index(&out, IdRuleProfile::hancom_2020_block_bookmark_v12())?;
    }
    Ok(())
}
#[test]
fn plain_run_requirement_still_rejects_native_mixed_runs() -> Result {
    let raw = native::native_source()?;
    let forms = fixture::forms(&raw, "mixed679")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let blocks = ImportedBlockBookmarks::import(&fields, limits())?;
    let p = forms
        .source()
        .parts()
        .iter()
        .find(|p| p.path().as_str() == "Contents/section0.xml")
        .ok_or("section")?;
    let xml = p.xml().ok_or("xml")?;
    let run = xml
        .elements()
        .iter()
        .position(|e| e.name().local_name() == "run")
        .ok_or("run")?;
    let proof = forms.reconstruct_source_for_verification(&raw)?;
    assert!(matches!(
        fields.create_bookmark_reference(
            &proof,
            Request {
                run: p.element_anchor(run).ok_or("anchor")?,
                target_id: blocks.observations()[0].field_reference_id(),
                display: D::Content,
                hyperlink: false
            },
            limits(),
            WriterLimits::default()
        ),
        Err(E::Selection)
    ));
    Ok(())
}
#[test]
fn core_point_content_remains_denied_without_a_block_flag() -> Result {
    let raw = fixture::package(
        "<hp:p id='1'><hp:run><hp:ctrl><hp:bookmark name='point'/></hp:ctrl></hp:run></hp:p><hp:p id='2'><hp:run><hp:t>display</hp:t></hp:run></hp:p>",
    )?;
    let forms = fixture::forms(&raw, "point679")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let p = forms
        .source()
        .parts()
        .iter()
        .find(|p| p.path().as_str() == "Contents/section0.xml")
        .ok_or("section")?;
    let run = p
        .xml()
        .ok_or("xml")?
        .elements()
        .iter()
        .enumerate()
        .filter(|(_, e)| e.name().local_name() == "run")
        .last()
        .ok_or("run")?
        .0;
    let proof = forms.reconstruct_source_for_verification(&raw)?;
    assert!(matches!(
        fields.create_bookmark_reference(
            &proof,
            Request {
                run: p.element_anchor(run).ok_or("anchor")?,
                target_id: &forms.body_structure().bookmarks()[0].reference_id,
                display: D::Content,
                hyperlink: false
            },
            limits(),
            WriterLimits::default()
        ),
        Err(E::ContentRequiresBlockBookmark)
    ));
    Ok(())
}
#[test]
fn block_command_edit_uses_shared_resolution_without_refreshing_cached_text() -> Result {
    let raw = output(&native::derived_source()?, D::Page, false)?;
    let forms = fixture::forms(&raw, "block679")?;
    let fields = ImportedDocumentFields::import(&forms)?;
    let index = SourceFieldMeaningIndex::import(&fields, limits())?;
    let (i, f) = fields
        .fields()
        .iter()
        .enumerate()
        .find(|(_, f)| f.native_kind == "CROSSREF")
        .ok_or("crossref")?;
    let target = ImportedBlockBookmarks::import(&fields, limits())?.observations()[0]
        .field_reference_id()
        .clone();
    let proof = forms.reconstruct_source_for_verification(&raw)?;
    let candidate = index.lower_bookmark_command_changes(
        &proof,
        &[SourceBookmarkCommandChange {
            reference_id: &f.reference_id,
            expected_source_field_sha256: f.begin_anchor.fingerprint_sha256,
            expected_meaning_sha256: index.meaning_sha256(i)?,
            target_id: &target,
            display: D::Content,
            hyperlink: true,
        }],
        WriterLimits::default(),
    )?;
    assert!(candidate.receipt().cached_values_preserved_not_refreshed);
    let out = candidate.with_verified_bytes(|v| v.to_vec())?;
    let after = fixture::forms(&out, "block679")?;
    let after_fields = ImportedDocumentFields::import(&after)?;
    let meanings = SourceFieldMeaningIndex::import(&after_fields, limits())?;
    assert!(meanings.observations().iter().any(|v|matches!(&v.meaning,ImportedFieldMeaning::BookmarkCrossReference{command}if command.display==BookmarkCrossReferenceDisplay::Content&&command.hyperlink&&matches!(command.target,SourceBookmarkResolution::Bound{..}))));
    Ok(())
}
