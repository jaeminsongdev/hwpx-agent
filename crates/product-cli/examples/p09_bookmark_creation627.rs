//! Fixed local candidate observation; does not launch or authorize Native.
use hwpx_agent_cli::reference_validation_product::ReferenceValidationProductOperation as Product;
use hwpx_package::{
    WriterLimits,
    document_import::{SourceImportLimits, fields::bookmark_insertion::SourceBookmarkInsertion},
};
use sha2::{Digest as _, Sha256};
#[path = "../../hwpx-package/tests/bookmark_source_creation627.rs"]
#[allow(dead_code, unused_imports)]
mod fixed;
fn main() {
    let result = (|| -> fixed::Result {
        fixed::require(
            std::env::args().skip(1).collect::<Vec<_>>() == ["--fixed-first-insertion-readonly"],
        )?;
        let value = fixed::fixed_observations(|bytes, run, target, display, hyperlink| {
            Ok(Product::prepare_source_bookmark_reference_insertion(
                bytes,
                domain_ir::DocumentId::parse(fixed::DOC)?,
                Sha256::digest(bytes).into(),
                SourceImportLimits::default(),
                fixed::limits()?,
                SourceBookmarkInsertion {
                    run,
                    target_id: target,
                    display,
                    hyperlink,
                },
                WriterLimits::default(),
            )?)
        })?;
        let output = serde_json::to_vec(&value)?;
        fixed::require(output.len() <= 32768)?;
        println!("{}", std::str::from_utf8(&output)?);
        Ok(())
    })();
    if result.is_err() {
        eprintln!("P627_FIXED_FIRST_INSERTION_REJECTED_NO_RAW_VALUES");
        std::process::exit(2);
    }
}
