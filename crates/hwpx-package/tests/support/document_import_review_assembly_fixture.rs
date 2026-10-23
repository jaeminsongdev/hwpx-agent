// Synthetic in-memory derivative of the ORIGINAL native package builder.
// Nothing is written to a captured source or user document.
use hwpx_package::{BoundedZipReader, Hancom2020Vs0Builder, PackageLimits, PreservingXmlDocument};
use std::{
    error::Error,
    io::{Cursor, Write},
};
use zip::{CompressionMethod, ZipWriter, write::SimpleFileOptions};
pub fn markers(text: &str) -> String {
    format!(
        "<hp:ctrl><hp:fieldBegin id='42' type='MEMO'><hp:parameters cnt='0'/><hp:subList><hp:p id='101' styleIDRef='0' paraPrIDRef='0'><hp:run charPrIDRef='0'><hp:t>{text}</hp:t></hp:run></hp:p></hp:subList></hp:fieldBegin></hp:ctrl><hp:t>VISIBLE-CACHE</hp:t><hp:ctrl><hp:fieldEnd beginIDRef='42'/></hp:ctrl><hp:hiddenComment><hp:subList><hp:p id='102' styleIDRef='0' paraPrIDRef='0'><hp:run charPrIDRef='0'><hp:t>HIDDEN-REVIEW</hp:t></hp:run></hp:p></hp:subList></hp:hiddenComment>"
    )
}
pub fn package(markers: &str) -> Result<Vec<u8>, Box<dyn Error>> {
    let base = Hancom2020Vs0Builder::build("MAIN")?.with_verified_bytes(<[u8]>::to_vec)?;
    let mut reader = BoundedZipReader::open(Cursor::new(&base), PackageLimits::default())?;
    let names: Vec<_> = reader
        .entries()
        .iter()
        .map(|e| e.path.as_str().to_owned())
        .collect();
    let mut writer = ZipWriter::new(Cursor::new(Vec::new()));
    for (index, name) in names.into_iter().enumerate() {
        let bytes = reader.read_entry(index)?;
        let changed = if name == "Contents/section0.xml" {
            let xml = PreservingXmlDocument::parse(&bytes)?;
            let run = xml
                .elements()
                .iter()
                .find(|e| {
                    e.name().namespace() == Some("http://www.hancom.co.kr/hwpml/2011/paragraph")
                        && e.name().local_name() == "run"
                })
                .ok_or("fixture run")?;
            let at = run.content_span().ok_or("fixture run span")?.end();
            let mut result = std::str::from_utf8(&bytes)?.to_owned();
            result.insert_str(at, markers);
            result.into_bytes()
        } else {
            bytes.clone()
        };
        if name != "Contents/section0.xml" {
            assert_eq!(changed, bytes);
        }
        writer.start_file(
            name,
            SimpleFileOptions::default().compression_method(CompressionMethod::Stored),
        )?;
        writer.write_all(&changed)?;
    }
    Ok(writer.finish()?.into_inner())
}
