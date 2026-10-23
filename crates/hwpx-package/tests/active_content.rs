use std::error::Error;
use std::io::{Cursor, Write};

use hwpx_package::{
    ActivationKind, ActiveContentControlKind, ActiveContentDisposition, ActiveContentError,
    ActiveContentInventory, ActiveContentLimitConfig, ActiveContentLimits,
    ActiveContentResourceKind, ActiveContentSignature, BoundedZipReader, PackageGraph,
    PackageGraphLimits, PackageLimits,
};
use zip::write::SimpleFileOptions;
use zip::{CompressionMethod, ZipWriter};

type TestResult = Result<(), Box<dyn Error>>;
type TestReader = BoundedZipReader<Cursor<Vec<u8>>>;

const CONTAINER: &str = r#"<?xml version="1.0" encoding="UTF-8"?>
<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0">
  <rootfiles><rootfile full-path="Contents/content.hpf" media-type="application/oebps-package+xml"/></rootfiles>
</container>"#;
const SECTION_PREFIX: &str =
    r#"<hp:section xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph">"#;

#[test]
fn embedded_ole_is_relationship_bound_opaque_and_never_activatable() -> TestResult {
    let section =
        section(r#"<hp:ole objectType="EMBEDDED" binaryItemIDRef="ole1" hasMoniker="0"/>"#);
    let bytes = archive_with(
        &section,
        &[Resource::new(
            "ole1",
            "../BinData/object.bin",
            "BinData/object.bin",
            "application/octet-stream",
            cfb(),
        )],
    )?;
    let (mut reader, graph) = open_graph(bytes)?;
    let inventory = ActiveContentInventory::scan(
        &mut reader,
        &graph,
        PackageGraphLimits::default(),
        ActiveContentLimits::default(),
    )?;

    assert_eq!(inventory.resources().len(), 1);
    let resource = &inventory.resources()[0];
    assert_eq!(resource.kind(), ActiveContentResourceKind::OpaqueOle);
    assert_eq!(
        resource.disposition(),
        ActiveContentDisposition::PreserveBlocked
    );
    assert_eq!(resource.signature(), ActiveContentSignature::Verified);
    assert_eq!(resource.relationship_ids(), &["ole1"]);
    assert_eq!(inventory.controls().len(), 1);
    assert_eq!(
        inventory.controls()[0].kind(),
        ActiveContentControlKind::Ole
    );
    assert!(!inventory.controls()[0].external());
    assert!(!inventory.activation_allowed());
    for action in [
        ActivationKind::Ole,
        ActivationKind::Multimedia,
        ActivationKind::EmbeddedExecutable,
        ActivationKind::ScriptMacro,
        ActivationKind::FormCommand,
        ActivationKind::ExternalLink,
    ] {
        assert_eq!(
            active_error(inventory.authorize(action)).code(),
            "active_content_activation_denied"
        );
    }
    Ok(())
}

#[test]
fn local_video_and_unreferenced_audio_are_complete_and_signature_checked() -> TestResult {
    let section = section(r#"<hp:video videotype="Local" fileIDRef="video1"/>"#);
    let bytes = archive_with(
        &section,
        &[
            Resource::new(
                "video1",
                "../BinData/movie.mp4",
                "BinData/movie.mp4",
                "video/mp4",
                mp4(),
            ),
            Resource::new(
                "audio1",
                "../BinData/sound.wav",
                "BinData/sound.wav",
                "audio/wav",
                wav(),
            ),
        ],
    )?;
    let inventory = scan(bytes)?;

    assert_eq!(inventory.resources().len(), 2);
    assert!(inventory.resources().iter().all(|resource| {
        resource.disposition() == ActiveContentDisposition::PreservePassive
            && resource.signature() == ActiveContentSignature::Verified
    }));
    assert!(
        inventory
            .resources()
            .iter()
            .any(|resource| resource.kind() == ActiveContentResourceKind::Audio)
    );
    assert!(
        inventory
            .resources()
            .iter()
            .any(|resource| resource.kind() == ActiveContentResourceKind::Video)
    );
    assert_eq!(inventory.counts().resources, 2);
    assert_eq!(inventory.counts().controls, 1);
    Ok(())
}

#[test]
fn external_ole_web_video_and_form_commands_are_quarantined_without_value_leak() -> TestResult {
    let section = section(
        r#"<hp:ole objectType="LINK" binaryItemIDRef="ole1" hasMoniker="1"/>
<hp:video videotype="Web" tag="https://secret.example/private"/>
<hp:btn command="TOP-SECRET-COMMAND"/>
<hp:comboBox command=""/><hp:listBox/><hp:edit/>"#,
    );
    let bytes = archive_with(
        &section,
        &[Resource::new(
            "ole1",
            "../BinData/link.bin",
            "BinData/link.bin",
            "application/octet-stream",
            cfb(),
        )],
    )?;
    let inventory = scan(bytes)?;

    assert_eq!(inventory.controls().len(), 6);
    assert_eq!(inventory.counts().quarantined, 3);
    assert!(
        inventory.controls()[0..2]
            .iter()
            .all(hwpx_package::ActiveContentControl::external)
    );
    let Some(button) = inventory
        .controls()
        .iter()
        .find(|control| control.kind() == ActiveContentControlKind::FormButton)
    else {
        return Err(std::io::Error::other("button missing").into());
    };
    assert!(button.command_present());
    assert_eq!(button.element_sha256().len(), 64);

    let debug = format!("{inventory:?}");
    assert!(!debug.contains("TOP-SECRET"));
    assert!(!debug.contains("secret.example"));
    assert!(!debug.contains("BinData/link.bin"));
    let json = String::from_utf8(inventory.canonical_json(ActiveContentLimits::default())?)?;
    assert!(!json.contains("TOP-SECRET"));
    assert!(!json.contains("secret.example"));
    Ok(())
}

#[test]
fn executable_and_script_payloads_are_quarantined_even_when_media_is_generic() -> TestResult {
    let bytes = archive_with(
        &section(""),
        &[
            Resource::new(
                "exe1",
                "../BinData/tool.bin",
                "BinData/tool.bin",
                "application/octet-stream",
                b"MZpayload",
            ),
            Resource::new(
                "script1",
                "../Scripts/action.js",
                "Scripts/action.js",
                "application/javascript",
                b"doSecretThing()",
            ),
        ],
    )?;
    let inventory = scan(bytes)?;

    assert_eq!(inventory.resources().len(), 2);
    assert!(
        inventory
            .resources()
            .iter()
            .all(|resource| { resource.disposition() == ActiveContentDisposition::Quarantine })
    );
    assert!(
        inventory
            .resources()
            .iter()
            .any(|resource| resource.kind() == ActiveContentResourceKind::Executable)
    );
    assert!(
        inventory
            .resources()
            .iter()
            .any(|resource| resource.kind() == ActiveContentResourceKind::ScriptMacro)
    );
    assert!(!format!("{inventory:?}").contains("doSecretThing"));
    Ok(())
}

#[test]
fn equation_script_is_not_misclassified_but_out_of_equation_script_is_quarantined() -> TestResult {
    let section = section(
        r"<hp:equation><hp:script>{x}+{1}</hp:script></hp:equation>
<hp:script>active-command</hp:script>",
    );
    let inventory = scan(archive_with(&section, &[])?)?;

    assert_eq!(inventory.controls().len(), 1);
    assert_eq!(
        inventory.controls()[0].kind(),
        ActiveContentControlKind::ScriptMacro
    );
    assert_eq!(
        inventory.controls()[0].disposition(),
        ActiveContentDisposition::Quarantine
    );
    assert!(!format!("{inventory:?}").contains("active-command"));
    Ok(())
}

#[test]
fn namespace_spoof_dangling_reference_and_bad_enum_fail_closed() -> TestResult {
    let cases = [
        (
            section(r#"<x:ole xmlns:x="urn:spoof" objectType="EMBEDDED" binaryItemIDRef="ole1"/>"#),
            vec![Resource::new(
                "ole1",
                "../BinData/object.bin",
                "BinData/object.bin",
                "application/octet-stream",
                cfb(),
            )],
            "active_content_namespace_spoof",
        ),
        (
            section(r#"<hp:ole objectType="EMBEDDED" binaryItemIDRef="missing"/>"#),
            vec![],
            "active_content_dangling_reference",
        ),
        (
            section(r#"<hp:video videotype="Remote" tag="x"/>"#),
            vec![],
            "active_content_invalid_attribute",
        ),
        (
            section(r#"<hp:video videotype="Local" fileIDRef="image1"/>"#),
            vec![Resource::new(
                "image1",
                "../BinData/poster.png",
                "BinData/poster.png",
                "image/png",
                png(),
            )],
            "active_content_conflicting_resource_role",
        ),
    ];
    for (section, resources, expected) in cases {
        let bytes = archive_with(&section, &resources)?;
        let (mut reader, graph) = open_graph(bytes)?;
        let error = active_error(ActiveContentInventory::scan(
            &mut reader,
            &graph,
            PackageGraphLimits::default(),
            ActiveContentLimits::default(),
        ));
        assert_eq!(error.code(), expected);
    }
    Ok(())
}

#[test]
fn known_multimedia_signature_mismatch_is_not_downgraded_to_opaque() -> TestResult {
    let bytes = archive_with(
        &section(r#"<hp:video videotype="Local" fileIDRef="video1"/>"#),
        &[Resource::new(
            "video1",
            "../BinData/movie.mp4",
            "BinData/movie.mp4",
            "video/mp4",
            b"not-an-mp4",
        )],
    )?;
    let (mut reader, graph) = open_graph(bytes)?;
    let error = active_error(ActiveContentInventory::scan(
        &mut reader,
        &graph,
        PackageGraphLimits::default(),
        ActiveContentLimits::default(),
    ));
    assert_eq!(error.code(), "active_content_signature_mismatch");
    Ok(())
}

#[test]
fn supplied_graph_drift_is_rejected_before_inventory_publication() -> TestResult {
    let bytes = archive_with(&section(""), &[])?;
    let (mut reader, mut graph) = open_graph(bytes)?;
    graph.parts[0].raw_sha256 = [0; 32];
    let error = active_error(ActiveContentInventory::scan(
        &mut reader,
        &graph,
        PackageGraphLimits::default(),
        ActiveContentLimits::default(),
    ));
    assert_eq!(error.code(), "active_content_source_graph_drift");
    Ok(())
}

#[test]
fn preservation_allows_unrelated_xml_shift_but_rejects_payload_or_control_tamper() -> TestResult {
    let ole = r#"<hp:ole objectType="EMBEDDED" binaryItemIDRef="ole1" hasMoniker="0"/>"#;
    let source = scan(archive_with(
        &section(ole),
        &[Resource::new(
            "ole1",
            "../BinData/object.bin",
            "BinData/object.bin",
            "application/octet-stream",
            cfb(),
        )],
    )?)?;
    let shifted = scan(archive_with(
        &section(&format!("<hp:p/>{ole}")),
        &[Resource::new(
            "ole1",
            "../BinData/object.bin",
            "BinData/object.bin",
            "application/octet-stream",
            cfb(),
        )],
    )?)?;
    let receipt = source.verify_preserved(&shifted)?;
    assert_eq!(receipt.byte_exact_resources, 1);
    assert!(!receipt.activation_allowed);

    let mut changed = cfb().to_vec();
    changed.push(9);
    let payload_tamper = scan(archive_with(
        &section(ole),
        &[Resource::new(
            "ole1",
            "../BinData/object.bin",
            "BinData/object.bin",
            "application/octet-stream",
            &changed,
        )],
    )?)?;
    assert_eq!(
        active_error(source.verify_preserved(&payload_tamper)).code(),
        "active_content_state_drift"
    );

    let control_tamper = scan(archive_with(
        &section(r#"<hp:ole objectType="STATIC" binaryItemIDRef="ole1" hasMoniker="0"/>"#),
        &[Resource::new(
            "ole1",
            "../BinData/object.bin",
            "BinData/object.bin",
            "application/octet-stream",
            cfb(),
        )],
    )?)?;
    assert_eq!(
        active_error(source.verify_preserved(&control_tamper)).code(),
        "active_content_state_drift"
    );
    Ok(())
}

#[test]
fn limits_and_json_are_finite_deterministic_and_redacted() -> TestResult {
    assert_eq!(
        active_error(ActiveContentLimits::new(ActiveContentLimitConfig {
            max_inventory_items: 0,
            ..ActiveContentLimitConfig::default()
        }))
        .code(),
        "active_content_invalid_limit"
    );
    let bytes = archive_with(
        &section(r#"<hp:btn command="SECRET-A"/><hp:edit command="SECRET-B"/>"#),
        &[],
    )?;
    let (mut reader, graph) = open_graph(bytes.clone())?;
    let tight = ActiveContentLimits::new(ActiveContentLimitConfig {
        max_inventory_items: 1,
        ..ActiveContentLimitConfig::default()
    })?;
    assert_eq!(
        active_error(ActiveContentInventory::scan(
            &mut reader,
            &graph,
            PackageGraphLimits::default(),
            tight,
        ))
        .code(),
        "active_content_inventory_limit"
    );

    let total_bound_bytes = archive_with(
        &section(r"<hp:btn/><hp:edit/>"),
        &[Resource::new(
            "opaque1",
            "../BinData/opaque.bin",
            "BinData/opaque.bin",
            "application/octet-stream",
            b"opaque",
        )],
    )?;
    let (mut total_reader, total_graph) = open_graph(total_bound_bytes)?;
    let total_limit = ActiveContentLimits::new(ActiveContentLimitConfig {
        max_inventory_items: 2,
        ..ActiveContentLimitConfig::default()
    })?;
    assert_eq!(
        active_error(ActiveContentInventory::scan(
            &mut total_reader,
            &total_graph,
            PackageGraphLimits::default(),
            total_limit,
        ))
        .code(),
        "active_content_inventory_limit"
    );

    let first = scan(bytes.clone())?;
    let second = scan(bytes)?;
    assert_eq!(first, second);
    assert_eq!(
        first.canonical_json(ActiveContentLimits::default())?,
        second.canonical_json(ActiveContentLimits::default())?
    );
    let tiny_json = ActiveContentLimits::new(ActiveContentLimitConfig {
        max_json_bytes: 1,
        ..ActiveContentLimitConfig::default()
    })?;
    assert_eq!(
        active_error(first.canonical_json(tiny_json)).code(),
        "active_content_output_limit"
    );
    let debug = format!("{first:?}");
    assert!(!debug.contains("SECRET-A"));
    assert!(!debug.contains("SECRET-B"));
    Ok(())
}

#[test]
fn streamed_canonical_and_scan_budget_match_legacy_bytes_at_exact_boundaries() -> TestResult {
    let body = r#"<hp:btn command="PRIVATE-NEVER-EXECUTED"/>"#.repeat(256);
    let bytes = archive_with(&section(&body), &[])?;
    let inventory = scan(bytes.clone())?;
    let legacy = serde_json::to_vec(&inventory)?;
    assert!(legacy.len() > 8192);
    let exact = ActiveContentLimits::new(ActiveContentLimitConfig {
        max_json_bytes: legacy.len(), ..Default::default()
    })?;
    assert!(inventory.canonical_json(exact)? == legacy);
    let (mut reader, graph) = open_graph(bytes.clone())?;
    let same = ActiveContentInventory::scan(&mut reader, &graph, PackageGraphLimits::default(), exact)?;
    assert_eq!(same, inventory);
    for maximum in [1, legacy.len() - 1] {
        let tight = ActiveContentLimits::new(ActiveContentLimitConfig {
            max_json_bytes: maximum, ..Default::default()
        })?;
        assert_eq!(active_error(inventory.canonical_json(tight)).code(), "active_content_output_limit");
        let (mut reader, graph) = open_graph(bytes.clone())?;
        assert_eq!(active_error(ActiveContentInventory::scan(&mut reader, &graph,
            PackageGraphLimits::default(), tight)).code(), "active_content_output_limit");
    }
    Ok(())
}

#[test]
fn streamed_inventory_state_hash_matches_exact_legacy_projection() -> TestResult {
    use serde::Serialize;
    use sha2::{Digest as _, Sha256};
    #[derive(Eq, Ord, PartialEq, PartialOrd, Serialize)]
    struct LegacyControl<'a> {
        document_part: &'a str,
        kind: ActiveContentControlKind,
        disposition: ActiveContentDisposition,
        relationship_id: Option<&'a str>,
        resource_path: Option<&'a str>,
        external: bool,
        command_present: bool,
        element_sha256: &'a str,
    }
    #[derive(Serialize)]
    struct LegacyState<'a> {
        schema_version: &'static str,
        profile_id: &'static str,
        resources: &'a [hwpx_package::ActiveContentResource],
        controls: Vec<LegacyControl<'a>>,
    }
    let inputs = [
        archive_with(&section(""), &[])?,
        archive_with(&section(r#"<hp:script>PRIVATE</hp:script><hp:video videotype="Web" tag="https://fixture.invalid/private"/><hp:btn command="PRIVATE"/>"#), &[])?,
        archive_with(&section(r#"<hp:btn/><hp:ole objectType="EMBEDDED" binaryItemIDRef="ole1" hasMoniker="0"/>"#),
            &[Resource::new("ole1", "../BinData/object.bin", "BinData/object.bin", "application/octet-stream", cfb())])?,
    ];
    for bytes in inputs {
        let inventory = scan(bytes)?;
        let mut controls: Vec<_> = inventory.controls().iter().map(|control| LegacyControl {
            document_part: control.document_part(), kind: control.kind(), disposition: control.disposition(),
            relationship_id: control.relationship_id(), resource_path: control.resource_path(),
            external: control.external(), command_present: control.command_present(),
            element_sha256: control.element_sha256(),
        }).collect();
        controls.sort_unstable();
        let legacy = serde_json::to_vec(&LegacyState {
            schema_version: hwpx_package::ACTIVE_CONTENT_SCHEMA_VERSION,
            profile_id: hwpx_package::ACTIVE_CONTENT_PROFILE_ID,
            resources: inventory.resources(), controls,
        })?;
        assert_eq!(inventory.state_sha256(), hex::encode(Sha256::digest(&legacy)));
        assert!(inventory.canonical_json(ActiveContentLimits::default())? == serde_json::to_vec(&inventory)?);
    }
    Ok(())
}

#[test]
fn streamed_state_digest_preserves_unrelated_xml_shift_semantics() -> TestResult {
    let controls = r#"<hp:script>PRIVATE</hp:script><hp:btn command="PRIVATE"/>"#;
    let first = scan(archive_with(&section(controls), &[])?)?;
    let shifted = scan(archive_with(&section(&format!("<hp:p/>{controls}")), &[])?)?;
    assert_eq!(first.state_sha256(), shifted.state_sha256());
    assert_ne!(first.source_graph_sha256(), shifted.source_graph_sha256());
    assert!(first.verify_preserved(&shifted).is_ok());
    Ok(())
}

fn scan(bytes: Vec<u8>) -> Result<ActiveContentInventory, Box<dyn Error>> {
    let (mut reader, graph) = open_graph(bytes)?;
    Ok(ActiveContentInventory::scan(
        &mut reader,
        &graph,
        PackageGraphLimits::default(),
        ActiveContentLimits::default(),
    )?)
}

fn section(body: &str) -> String {
    format!("{SECTION_PREFIX}{body}</hp:section>")
}

struct Resource<'a> {
    id: &'a str,
    href: &'a str,
    entry: &'a str,
    media_type: &'a str,
    bytes: &'a [u8],
}

impl<'a> Resource<'a> {
    const fn new(
        id: &'a str,
        href: &'a str,
        entry: &'a str,
        media_type: &'a str,
        bytes: &'a [u8],
    ) -> Self {
        Self {
            id,
            href,
            entry,
            media_type,
            bytes,
        }
    }
}

fn archive_with(
    section: &str,
    resources: &[Resource<'_>],
) -> Result<Vec<u8>, zip::result::ZipError> {
    let mut resource_manifest = String::new();
    for resource in resources {
        resource_manifest.push_str(r#"<opf:item id=""#);
        resource_manifest.push_str(resource.id);
        resource_manifest.push_str(r#"" href=""#);
        resource_manifest.push_str(resource.href);
        resource_manifest.push_str(r#"" media-type=""#);
        resource_manifest.push_str(resource.media_type);
        resource_manifest.push_str(r#""/>"#);
    }
    let opf = format!(
        r#"<?xml version="1.0" encoding="UTF-8"?>
<opf:package xmlns:opf="http://www.idpf.org/2007/opf" version="2.0">
  <opf:manifest>
    <opf:item id="header" href="header.xml" media-type="application/xml"/>
    <opf:item id="section0" href="section0.xml" media-type="application/xml"/>
    {resource_manifest}
  </opf:manifest>
  <opf:spine><opf:itemref idref="section0" linear="yes"/></opf:spine>
</opf:package>"#
    );
    let mut entries = vec![
        entry(
            "mimetype",
            b"application/hwp+zip",
            CompressionMethod::Stored,
        ),
        entry("version.xml", b"<version/>", CompressionMethod::Stored),
        entry(
            "META-INF/container.xml",
            CONTAINER.as_bytes(),
            CompressionMethod::Deflated,
        ),
        entry(
            "Contents/content.hpf",
            opf.as_bytes(),
            CompressionMethod::Deflated,
        ),
        entry(
            "Contents/header.xml",
            b"<header/>",
            CompressionMethod::Deflated,
        ),
        entry(
            "Contents/section0.xml",
            section.as_bytes(),
            CompressionMethod::Deflated,
        ),
    ];
    entries.extend(
        resources
            .iter()
            .map(|resource| entry(resource.entry, resource.bytes, CompressionMethod::Stored)),
    );
    archive(entries)
}

fn entry(
    name: &str,
    bytes: &[u8],
    method: CompressionMethod,
) -> (String, Vec<u8>, CompressionMethod) {
    (name.to_owned(), bytes.to_vec(), method)
}

fn archive(
    entries: Vec<(String, Vec<u8>, CompressionMethod)>,
) -> Result<Vec<u8>, zip::result::ZipError> {
    let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
    for (name, bytes, method) in entries {
        writer.start_file(
            name,
            SimpleFileOptions::default().compression_method(method),
        )?;
        writer.write_all(&bytes)?;
    }
    Ok(writer.finish()?.into_inner())
}

fn open_graph(bytes: Vec<u8>) -> Result<(TestReader, PackageGraph), Box<dyn Error>> {
    let mut reader = BoundedZipReader::open(Cursor::new(bytes), PackageLimits::default())?;
    let graph = PackageGraph::build(&mut reader, PackageGraphLimits::default())?;
    Ok((reader, graph))
}

fn active_error<T>(result: Result<T, ActiveContentError>) -> ActiveContentError {
    let Err(error) = result else {
        panic!("expected active-content failure");
    };
    error
}

fn cfb() -> &'static [u8] {
    b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1opaque-ole"
}

fn mp4() -> &'static [u8] {
    b"\x00\x00\x00\x18ftypisomfixture"
}

fn wav() -> &'static [u8] {
    b"RIFF\x04\x00\x00\x00WAVEfixture"
}

fn png() -> &'static [u8] {
    b"\x89PNG\r\n\x1a\nfixture"
}
