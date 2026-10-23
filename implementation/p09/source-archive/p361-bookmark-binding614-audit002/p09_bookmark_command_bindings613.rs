//! Fixed read-only product test of existing010 outputs. No Native or general path CLI.
use domain_ir::{DocumentId, ReferenceAuxiliaryLimitConfig, ReferenceAuxiliaryLimits};
use hwpx_agent_cli::reference_validation_product::ReferenceValidationProductOperation as Product;
#[cfg(test)]
use hwpx_agent_cli::reference_validation_product::source_crossref::bookmark_bindings::SourceBookmarkCrossReferenceProductError as ProductError;
#[cfg(test)]
use hwpx_package::cross_reference_sdk::{
    SdkCrossReferenceCandidate, SdkCrossReferenceDisplay as Display, SdkCrossReferenceTarget,
};
use hwpx_package::document_import::{
    SourceImportLimits,
    fields::bookmark_crossref::{
        BookmarkCrossReferenceDisplay, SourceBookmarkCrossReferenceBindings,
        SourceBookmarkResolution,
    },
};
use std::{
    error::Error,
    fs::{File, OpenOptions},
    io::Read,
    path::{Path, PathBuf},
    time::{Duration, Instant},
};
#[cfg(test)]
#[path = "../../hwpx-package/tests/support/document_import_field_fixture.rs"]
#[allow(dead_code)]
mod base;
#[cfg(test)]
#[path = "../../hwpx-package/tests/support/document_import_bookmark_fixture.rs"]
#[allow(dead_code)]
mod fixture;
use serde_json::{Value, json};
use sha2::{Digest as _, Sha256};
type Result<T> = std::result::Result<T, Box<dyn Error>>;
const CORPUS: &str = include_str!(
    "../../../implementation/p09/evidence/p09-361-capture010-bookmark-binding-corpus613.v1.json"
);
const CORPUS_SHA: &str = "9e033d551a968c46d982a3a46f5faf6cf96fc99f29b6c9ac6393bff88e9f4e3f";
fn require(ok: bool) -> Result<()> {
    if !ok {
        return Err("BOOKMARK_BINDING613_REJECTED".into());
    }
    Ok(())
}
fn limits() -> Result<ReferenceAuxiliaryLimits> {
    Ok(ReferenceAuxiliaryLimits::new(
        ReferenceAuxiliaryLimitConfig {
            items_per_kind: 256,
            ..Default::default()
        },
    )?)
}
fn bind(bytes: &[u8]) -> Result<SourceBookmarkCrossReferenceBindings> {
    Ok(Product::read_source_bookmark_crossrefs(
        bytes,
        DocumentId::parse("p09-captured-bookmark-bindings")?,
        Sha256::digest(bytes).into(),
        SourceImportLimits::default(),
        limits()?,
    )?)
}
fn root() -> Result<PathBuf> {
    Ok(Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .and_then(Path::parent)
        .ok_or("BOOKMARK_BINDING613_ROOT")?
        .to_owned())
}
fn direct(meta: &std::fs::Metadata) -> Result<()> {
    require(!meta.file_type().is_symlink())?;
    #[cfg(windows)]
    {
        use std::os::windows::fs::MetadataExt as _;
        require(meta.file_attributes() & 0x400 == 0)?;
    }
    Ok(())
}
fn read_pin(pin: &Value) -> Result<Vec<u8>> {
    let name = pin["path"].as_str().ok_or("BOOKMARK_BINDING613_PATH")?;
    require(
        !name.contains('\\')
            && !name.starts_with('/')
            && !name.split('/').any(|v| v == ".." || v.is_empty()),
    )?;
    let path = root()?.join(name);
    for parent in path.ancestors().skip(1) {
        let m = parent.symlink_metadata()?;
        direct(&m)?;
        require(m.is_dir())?;
    }
    let meta = path.symlink_metadata()?;
    direct(&meta)?;
    let size = pin["bytes"].as_u64().ok_or("BOOKMARK_BINDING613_SIZE")?;
    require(meta.is_file() && 0 < size && size <= 4194304 && meta.len() == size)?;
    std::thread::sleep(Duration::from_millis(50));
    let mut options = OpenOptions::new();
    options.read(true);
    #[cfg(windows)]
    {
        use std::os::windows::fs::OpenOptionsExt as _;
        options.share_mode(1);
    }
    let mut file: File = options.open(path)?;
    let mut bytes = Vec::new();
    let mut buffer = [0; 65536];
    let watch = Instant::now();
    loop {
        let n = file.read(&mut buffer)?;
        if n == 0 {
            break;
        }
        require(bytes.len().checked_add(n).is_some_and(|v| v <= 4194304))?;
        bytes.try_reserve(n)?;
        bytes.extend_from_slice(&buffer[..n]);
        let duration = Duration::from_secs_f64(bytes.len() as f64 / 2097152.);
        if let Some(delay) = duration.checked_sub(watch.elapsed()) {
            std::thread::sleep(delay);
        }
    }
    require(
        bytes.len() as u64 == size
            && hex::encode(Sha256::digest(&bytes))
                == pin["sha256"].as_str().ok_or("BOOKMARK_BINDING613_SHA")?,
    )?;
    Ok(bytes)
}
fn fixed_captured_results() -> Result<Value> {
    require(hex::encode(Sha256::digest(CORPUS.as_bytes())) == CORPUS_SHA)?;
    let corpus: Value = serde_json::from_str(CORPUS)?;
    require(
        corpus["native_execution_authorized"] == false
            && corpus["cases"].as_array().is_some_and(|v| v.len() == 8),
    )?;
    let source = read_pin(&corpus["source"])?;
    require(bind(&source)?.bindings().is_empty())?;
    let mut rows = Vec::new();
    for (index, case) in corpus["cases"]
        .as_array()
        .ok_or("BOOKMARK_BINDING613_CASES")?
        .iter()
        .enumerate()
    {
        require(case["case_index"] == index + 1)?;
        let expected = match index / 2 {
            0 => BookmarkCrossReferenceDisplay::Page,
            1 => BookmarkCrossReferenceDisplay::BookmarkName,
            2 => BookmarkCrossReferenceDisplay::Content,
            _ => BookmarkCrossReferenceDisplay::RelativePosition,
        };
        for stage in ["opened", "saved", "reopened"] {
            let pin = &case["artifacts"][stage];
            let path = format!(
                "implementation/p09/evidence/private/p09-361-crossref-bookmark-native-20261023-g010-c{:02}-attempt01/{stage}.hwpx",
                index + 1
            );
            require(pin["path"] == path)?;
            let bytes = read_pin(pin)?;
            let result = bind(&bytes)?;
            let report = result.canonical_json(limits()?)?;
            let json: Value = serde_json::from_slice(&report)?;
            for key in [
                "native_execution_attested",
                "native_target_resolution_qualified",
                "complete_reference_validation_qualified",
            ] {
                require(json[key] == false)?;
            }
            if stage == "opened" {
                require(result.bindings().is_empty())?;
            } else {
                require(result.bindings().len() == 1)?;
                let row = &result.bindings()[0];
                require(
                    row.display == expected
                        && row.hyperlink == (index % 2 == 1)
                        && matches!(row.target, SourceBookmarkResolution::Bound { .. }),
                )?;
                require(
                    hex::encode(row.command_sha256)
                        == case["command_sha256"]
                            .as_str()
                            .ok_or("BOOKMARK_BINDING613_COMMAND_HASH")?,
                )?;
            }
            rows.push(json!({"case_index":index+1,"stage":stage,"source_sha256":pin["sha256"],"bindings":result.bindings(),
                "canonical_report_bytes":report.len(),"canonical_report_sha256":hex::encode(Sha256::digest(&report)),
                "native_target_resolution_qualified":false,"complete_reference_validation_qualified":false}));
            require(read_pin(pin)? == bytes)?;
        }
    }
    require(read_pin(&corpus["source"])? == source)?;
    Ok(
        json!({"state":"source_bookmark_bindings_derived_from_fixed010_not_native_or_gate","observations":rows,
        "actual_native_started":false,"existing_native_replayed":false,"native_target_resolution_qualified":false,"p09_complete":false}),
    )
}
fn main() {
    let result = (|| -> Result<()> {
        require(std::env::args().skip(1).collect::<Vec<_>>() == ["--fixed-captured-readonly"])?;
        let bytes = serde_json::to_vec(&fixed_captured_results()?)?;
        require(bytes.len() <= 65536)?;
        println!("{}", String::from_utf8(bytes)?);
        Ok(())
    })();
    if result.is_err() {
        eprintln!("BOOKMARK_BINDING613_READONLY_PRODUCT_FAILED");
        std::process::exit(2);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    fn escape(text: &str) -> String {
        text.replace('&', "&amp;").replace('<', "&lt;")
    }
    fn command(display: Display, hyperlink: bool) -> Result<String> {
        Ok(SdkCrossReferenceCandidate::build(
            SdkCrossReferenceTarget::Bookmark {
                exact_source_name: "private & target",
            },
            display,
            hyperlink,
        )?
        .command_for_discovery()
        .to_owned())
    }
    fn field(children: &str, count: usize) -> String {
        format!(
            "<hp:ctrl><hp:fieldBegin id='1' type='CROSSREF'><hp:parameters cnt='{count}'>{children}</hp:parameters></hp:fieldBegin></hp:ctrl><hp:t>untrusted cache</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='1'/></hp:ctrl>"
        )
    }
    fn leaf(key: &str, text: &str) -> String {
        format!(
            "<hp:stringParam name='{key}'>{}</hp:stringParam>",
            escape(text)
        )
    }
    fn package(body: &str) -> Result<Vec<u8>> {
        base::package(&fixture::paragraph(body))
    }
    fn one(children: &str, count: usize) -> Result<Vec<u8>> {
        package(&format!(
            "{}{}",
            fixture::marker("private &amp; target"),
            field(children, count)
        ))
    }
    #[test]
    fn eight_display_hyperlink_variants_bind_to_actual_source_bookmark() -> Result<()> {
        for display in [
            Display::Page,
            Display::BookmarkName,
            Display::Content,
            Display::RelativePosition,
        ] {
            for hyperlink in [false, true] {
                let bytes = one(&leaf("Command", &command(display, hyperlink)?), 1)?;
                let result = bind(&bytes)?;
                require(
                    result.bindings().len() == 1
                        && result.bindings()[0].hyperlink == hyperlink
                        && matches!(
                            result.bindings()[0].target,
                            SourceBookmarkResolution::Bound { .. }
                        ),
                )?;
                let json = String::from_utf8(result.canonical_json(limits()?)?)?;
                require(!json.contains("private") && !format!("{result:?}").contains("private"))?;
            }
        }
        Ok(())
    }
    #[test]
    fn arbitrary_parameter_key_does_not_become_command_semantics() -> Result<()> {
        let bytes = one(&leaf("unknown-key", &command(Display::Page, false)?), 1)?;
        require(bind(&bytes).is_err())
    }
    #[test]
    fn duplicate_command_even_with_equal_values_is_rejected() -> Result<()> {
        let c = leaf("Command", &command(Display::Page, false)?);
        require(bind(&one(&(c.clone() + &c), 2)?).is_err())
    }
    #[test]
    fn wrong_type_namespace_nested_or_comment_commands_are_rejected() -> Result<()> {
        let c = escape(&command(Display::Page, false)?);
        for child in [
            format!("<hp:integerParam name='Command'>{c}</hp:integerParam>"),
            format!("<u:stringParam name='Command'>{c}</u:stringParam>"),
            format!("<hp:stringParam name='Command'><hp:t>{c}</hp:t></hp:stringParam>"),
            format!(
                "<hp:stringParam name='Command'>?<!--x-->{}</hp:stringParam>",
                &c[1..]
            ),
        ] {
            require(bind(&one(&child, 1)?).is_err())?;
        }
        Ok(())
    }
    #[test]
    fn missing_and_ambiguous_names_are_not_first_match_success() -> Result<()> {
        let c = field(&leaf("Command", &command(Display::Page, false)?), 1);
        let missing = bind(&package(&c)?)?;
        require(matches!(
            missing.bindings()[0].target,
            SourceBookmarkResolution::Missing
        ))?;
        let marker = fixture::marker("private &amp; target");
        let ambiguous = bind(&package(&(marker.clone() + &marker + &c))?)?;
        require(matches!(
            ambiguous.bindings()[0].target,
            SourceBookmarkResolution::Ambiguous
        ))
    }
    #[test]
    fn malformed_and_foreign_command_syntax_are_not_normalized() -> Result<()> {
        for value in [
            "?private & target;6;00;0;0",
            "?private & target;6;0;2;0",
            "?private & target;6;0;0;1",
            "?other/path;6;0;0;0",
            "?private & target;6;0;0;0;extra",
        ] {
            require(bind(&one(&leaf("Command", value), 1)?).is_err())?;
        }
        Ok(())
    }
    #[test]
    fn object_note_kind_mapping_remains_unqualified() -> Result<()> {
        for kind in [0, 1, 2, 3, 4, 5] {
            let value = format!("?#1;{kind};0;0;0");
            let bytes = one(&leaf("Command", &value), 1)?;
            require(matches!(
                Product::read_source_bookmark_crossrefs(
                    &bytes,
                    DocumentId::parse("invalid-kind")?,
                    Sha256::digest(&bytes).into(),
                    SourceImportLimits::default(),
                    limits()?
                ),
                Err(ProductError::UnqualifiedKind)
            ))?;
        }
        Ok(())
    }
    #[test]
    fn wrong_sha_and_tiny_output_budget_are_rejected() -> Result<()> {
        let bytes = one(&leaf("Command", &command(Display::Page, false)?), 1)?;
        let before = bytes.clone();
        require(matches!(
            Product::read_source_bookmark_crossrefs(
                &bytes,
                DocumentId::parse("wrong-sha")?,
                [0; 32],
                SourceImportLimits::default(),
                limits()?
            ),
            Err(ProductError::Binding)
        ))?;
        let tiny = ReferenceAuxiliaryLimits::new(ReferenceAuxiliaryLimitConfig {
            output_bytes: 128,
            ..Default::default()
        })?;
        require(
            Product::read_source_bookmark_crossrefs(
                &bytes,
                DocumentId::parse("small")?,
                Sha256::digest(&bytes).into(),
                SourceImportLimits::default(),
                tiny,
            )
            .is_err(),
        )?;
        require(before == bytes)
    }
    #[test]
    fn empty_crossref_set_is_not_native_or_complete_validation() -> Result<()> {
        let bytes = package(&fixture::marker("private &amp; target"))?;
        let result = bind(&bytes)?;
        require(result.bindings().is_empty())?;
        let json: Value = serde_json::from_slice(&result.canonical_json(limits()?)?)?;
        require(
            json["complete_reference_validation_qualified"] == false
                && json["native_target_resolution_qualified"] == false,
        )
    }
    #[test]
    fn exact_captured010_all24_outputs_use_public_product_path() -> Result<()> {
        let result = fixed_captured_results()?;
        require(
            result["observations"]
                .as_array()
                .is_some_and(|rows| rows.len() == 24)
                && result["p09_complete"] == false,
        )
    }
}
