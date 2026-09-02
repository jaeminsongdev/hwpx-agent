use std::error::Error;
use std::io::{Cursor, Read};

use hwpx_package::{Hancom2020Vs0Builder, Hancom2020Vs0Error};
use zip::{CompressionMethod, ZipArchive};

#[test]
fn builds_deterministic_graph_validated_hancom_2020_vs0() -> Result<(), Box<dyn Error>> {
    let first = Hancom2020Vs0Builder::build("HWPX Agent VS-0 한글 2020")?;
    let second = Hancom2020Vs0Builder::build("HWPX Agent VS-0 한글 2020")?;
    assert_eq!(first.sha256(), second.sha256());
    assert_eq!(first.size_bytes(), second.size_bytes());
    assert_eq!(first.part_count(), 11);
    first.verify()?;
    first.with_verified_bytes(|left| {
        second.with_verified_bytes(|right| assert_eq!(left, right))
    })??;
    Ok(())
}

#[test]
fn package_is_one_a4_paragraph_without_personal_metadata() -> Result<(), Box<dyn Error>> {
    let artifact = Hancom2020Vs0Builder::build("<&> \'\" 한글")?;
    artifact.with_verified_bytes(|bytes| -> Result<(), Box<dyn Error>> {
        let mut zip = ZipArchive::new(Cursor::new(bytes))?;
        assert_eq!(zip.len(), 11);
        assert_eq!(
            zip.file_names().collect::<Vec<_>>(),
            vec![
                "mimetype",
                "version.xml",
                "Contents/header.xml",
                "Contents/section0.xml",
                "Preview/PrvText.txt",
                "settings.xml",
                "Preview/PrvImage.png",
                "META-INF/container.rdf",
                "Contents/content.hpf",
                "META-INF/container.xml",
                "META-INF/manifest.xml",
            ]
        );
        assert_eq!(
            zip.by_name("mimetype")?.compression(),
            CompressionMethod::Stored
        );
        assert_eq!(
            zip.by_name("version.xml")?.compression(),
            CompressionMethod::Stored
        );
        assert!(zip.by_name("META-INF/container.rdf").is_ok());
        assert!(zip.by_name("META-INF/manifest.xml").is_ok());
        assert!(zip.by_name("Preview/PrvImage.png").is_ok());
        let mut section = String::new();
        zip.by_name("Contents/section0.xml")?
            .read_to_string(&mut section)?;
        assert_eq!(section.matches("<hp:p ").count(), 1);
        assert!(section.contains(r#"width="59528" height="84186""#));
        assert!(section.contains("&lt;&amp;&gt; &apos;&quot; 한글"));
        assert!(!section.contains("Users\\"));
        drop(section);
        let mut content = String::new();
        zip.by_name("Contents/content.hpf")?
            .read_to_string(&mut content)?;
        assert!(!content.contains("creator"));
        assert!(!content.contains("lastsaveby"));
        assert!(!content.contains("CreatedDate"));
        Ok(())
    })??;
    Ok(())
}

#[test]
fn rejects_empty_multiline_control_noncharacter_and_oversized_text() {
    for invalid in ["", "line1\nline2", "a\tb", "\u{ffff}"] {
        assert_eq!(
            Hancom2020Vs0Builder::build(invalid).err(),
            Some(Hancom2020Vs0Error::InvalidText)
        );
    }
    let oversized = "a".repeat(4097);
    assert_eq!(
        Hancom2020Vs0Builder::build(&oversized).err(),
        Some(Hancom2020Vs0Error::InvalidText)
    );
}
