use std::error::Error;
use std::io::{Cursor, Write};

use hwpx_agent_foundation::workdir::WorkspaceError;
use hwpx_package::{
    DiagnosticLayer, RecommendedAction, Repairability, RoundTripError, RoundTripLimits,
    RoundTripVerifier, WriterError,
};
use sha2::{Digest as _, Sha256};
use zip::write::SimpleFileOptions;
use zip::{CompressionMethod, ZipWriter};

type TestResult = Result<(), Box<dyn Error>>;

const CORPUS_SIZE: usize = 128;
const CONTAINER_NS: &str = "urn:oasis:names:tc:opendocument:xmlns:container";
const OPF_NS: &str = "http://www.idpf.org/2007/opf/";
const PARAGRAPH_NS: &str = "http://www.hancom.co.kr/hwpml/2011/paragraph";

#[test]
fn deterministic_128_fixture_roundtrip_has_zero_untouched_violations() -> TestResult {
    let mut corpus_aggregate = Sha256::new();
    let mut writer_aggregate = Sha256::new();
    for seed in 0..CORPUS_SIZE {
        let fixture = valid_archive(seed)?;
        let evidence =
            RoundTripVerifier::verify(Cursor::new(&fixture.archive), RoundTripLimits::default())?;
        assert_eq!(evidence.source_parts(), 5);
        assert_eq!(evidence.writer_entries(), 5);
        assert_eq!(evidence.untouched_policy_violations(), 0);
        assert!(evidence.preserving_deterministic());
        assert!(evidence.normalized_deterministic());
        corpus_aggregate.update(u64::try_from(seed)?.to_le_bytes());
        corpus_aggregate.update(Sha256::digest(&fixture.semantic_descriptor));
        corpus_aggregate.update(u64::try_from(evidence.source_parts())?.to_le_bytes());
        corpus_aggregate.update(u64::try_from(evidence.writer_entries())?.to_le_bytes());
        corpus_aggregate
            .update(u64::try_from(evidence.untouched_policy_violations())?.to_le_bytes());
        writer_aggregate.update(u64::try_from(seed)?.to_le_bytes());
        writer_aggregate.update(evidence.preserving_sha256());
        writer_aggregate.update(evidence.normalized_sha256());
    }
    assert_eq!(
        hex::encode(corpus_aggregate.finalize()),
        "b0f187093072a78bc50e12de31f6d30c88d679fb35c8a7ab309203937ba06823"
    );
    assert_eq!(
        hex::encode(writer_aggregate.finalize()),
        "d5492303a282c3fe4b00b7fa9b0cfd8a8528f7f2b060ffc24b086341e06d0224"
    );
    Ok(())
}

#[test]
fn bounded_mutation_and_truncation_replay_never_returns_partial_evidence() -> TestResult {
    let baseline = valid_archive(97)?.archive;
    for seed in 0..CORPUS_SIZE {
        let mut mutated = baseline.clone();
        let offset = seed.checked_mul(7_919).ok_or("mutation offset overflow")? % mutated.len();
        mutated[offset] ^= u8::try_from((seed % 251) + 1)?;
        assert_stable_result(&mutated);
    }
    for seed in 0..CORPUS_SIZE {
        let keep = seed
            .checked_mul(baseline.len())
            .ok_or("truncation size overflow")?
            / CORPUS_SIZE;
        assert_stable_result(&baseline[..keep]);
    }
    Ok(())
}

#[test]
fn repair_diagnostics_are_stable_non_mutating_and_actionable() {
    let corrupt = RoundTripVerifier::verify(Cursor::new(b"not-a-zip"), RoundTripLimits::default());
    let Err(error) = corrupt else {
        panic!("corrupt input unexpectedly passed");
    };
    let diagnostic = error.diagnostic();
    assert_eq!(diagnostic.code(), error.code());
    assert_eq!(diagnostic.layer(), DiagnosticLayer::Archive);
    assert_eq!(
        diagnostic.repairability(),
        Repairability::NotRepairableAutomatically
    );
    assert_eq!(
        diagnostic.action(),
        RecommendedAction::ReplaceOrRestoreSource
    );

    let output_exists =
        RoundTripError::Writer(WriterError::Workspace(WorkspaceError::ArtifactExists)).diagnostic();
    assert_eq!(output_exists.code(), "writer_output_exists");
    assert_eq!(output_exists.repairability(), Repairability::SafeRetry);
    assert_eq!(output_exists.action(), RecommendedAction::UseNewDestination);

    let output_limit = RoundTripError::Writer(WriterError::OutputLimitExceeded).diagnostic();
    assert_eq!(output_limit.code(), "writer_output_limit_exceeded");
    assert_eq!(output_limit.layer(), DiagnosticLayer::Publication);
    assert_eq!(output_limit.repairability(), Repairability::SafeRetry);
    assert_eq!(output_limit.action(), RecommendedAction::ReviewFiniteLimits);

    let invalid_writer_limit = RoundTripError::Writer(WriterError::InvalidLimit {
        field: "max_output_bytes",
        value: 0,
        ceiling: 1,
    })
    .diagnostic();
    assert_eq!(invalid_writer_limit.code(), "writer_invalid_limit");
    assert_eq!(
        invalid_writer_limit.repairability(),
        Repairability::SafeRetry
    );
    assert_eq!(
        invalid_writer_limit.action(),
        RecommendedAction::ReviewFiniteLimits
    );

    let published = RoundTripError::Writer(WriterError::PublishedIncomplete).diagnostic();
    assert_eq!(published.code(), "writer_published_incomplete");
    assert_eq!(
        published.repairability(),
        Repairability::NotRepairableAutomatically
    );
    assert_eq!(
        published.action(),
        RecommendedAction::InspectPublishedArtifact
    );
}

fn assert_stable_result(bytes: &[u8]) {
    let first = RoundTripVerifier::verify(Cursor::new(bytes), RoundTripLimits::default());
    let second = RoundTripVerifier::verify(Cursor::new(bytes), RoundTripLimits::default());
    match (first, second) {
        (Ok(left), Ok(right)) => {
            assert_eq!(left, right);
            assert_eq!(left.untouched_policy_violations(), 0);
        }
        (Err(left), Err(right)) => {
            assert_eq!(left.code(), right.code());
            assert_eq!(left.diagnostic(), right.diagnostic());
        }
        _ => panic!("identical fuzz input produced different admission states"),
    }
}

struct CorpusFixture {
    archive: Vec<u8>,
    semantic_descriptor: Vec<u8>,
}

fn append_descriptor(descriptor: &mut Vec<u8>, value: &[u8]) {
    descriptor.extend_from_slice(&u64::try_from(value.len()).unwrap_or(u64::MAX).to_le_bytes());
    descriptor.extend_from_slice(value);
}

fn valid_archive(seed: usize) -> Result<CorpusFixture, zip::result::ZipError> {
    let container = format!(
        r#"<?xml version="1.0" encoding="UTF-8"?>
<container xmlns="{CONTAINER_NS}" version="1.0">
  <rootfiles><rootfile full-path="Contents/content.hpf" media-type="application/oebps-package+xml"/></rootfiles>
  <!--seed-{seed}-->
</container>"#
    );
    let opf = format!(
        r#"<?xml version="1.0" encoding="UTF-8"?>
<o:package xmlns:o="{OPF_NS}" id="pkg" version="2.0">
  <o:manifest><o:item id="section0" href="section0.xml" media-type="application/xml"/></o:manifest>
  <o:spine><o:itemref idref="section0" linear="{}"/></o:spine>
  <!--seed-{seed}-->
</o:package>"#,
        if seed.is_multiple_of(2) { "yes" } else { "no" }
    );
    let section = format!(r#"<q:section xmlns:q="{PARAGRAPH_NS}"><!--seed-{seed}--></q:section>"#);
    let entries = [
        ("META-INF/container.xml", container.into_bytes()),
        ("Contents/content.hpf", opf.into_bytes()),
        ("Contents/section0.xml", section.into_bytes()),
    ];
    let permutations = [
        [0, 1, 2],
        [0, 2, 1],
        [1, 0, 2],
        [1, 2, 0],
        [2, 0, 1],
        [2, 1, 0],
    ];
    let cursor = Cursor::new(Vec::new());
    let mut writer = ZipWriter::new(cursor);
    let mut semantic_descriptor = Vec::new();
    append_descriptor(&mut semantic_descriptor, b"mimetype");
    append_descriptor(&mut semantic_descriptor, b"stored");
    append_descriptor(&mut semantic_descriptor, b"application/hwp+zip");
    writer.start_file(
        "mimetype",
        SimpleFileOptions::default().compression_method(CompressionMethod::Stored),
    )?;
    writer.write_all(b"application/hwp+zip")?;
    append_descriptor(&mut semantic_descriptor, b"version.xml");
    append_descriptor(&mut semantic_descriptor, b"stored");
    append_descriptor(&mut semantic_descriptor, b"<version/>");
    writer.start_file(
        "version.xml",
        SimpleFileOptions::default().compression_method(if seed.is_multiple_of(2) {
            CompressionMethod::Stored
        } else {
            CompressionMethod::Deflated
        }),
    )?;
    writer.write_all(b"<version/>")?;
    for (ordinal, entry_index) in permutations[seed % permutations.len()].iter().enumerate() {
        let (path, bytes) = &entries[*entry_index];
        let method = if ((seed >> ordinal) & 1) == 0 {
            CompressionMethod::Stored
        } else {
            CompressionMethod::Deflated
        };
        append_descriptor(&mut semantic_descriptor, path.as_bytes());
        append_descriptor(
            &mut semantic_descriptor,
            if method == CompressionMethod::Stored {
                b"stored"
            } else {
                b"deflated"
            },
        );
        append_descriptor(&mut semantic_descriptor, bytes);
        writer.start_file(
            *path,
            SimpleFileOptions::default()
                .compression_method(method)
                .compression_level((method == CompressionMethod::Deflated).then_some(6)),
        )?;
        writer.write_all(bytes)?;
    }
    writer.finish().map(|cursor| CorpusFixture {
        archive: cursor.into_inner(),
        semantic_descriptor,
    })
}
