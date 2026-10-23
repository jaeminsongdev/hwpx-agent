//! Creates only fixed new private evidence copies, not a product revision.
#[path = "../tests/stored_bookmark_insertion628.rs"]
#[allow(dead_code, unused_imports)]
mod fixed;
fn main() {
    let result = (|| -> fixed::Result {
        let args: Vec<_> = std::env::args().skip(1).collect();
        fixed::require(
            args.len() == 2 && args[0] == "--fixed-private-output-generation" && args[1].len() <= 3,
        )?;
        let generation = args[1].parse::<u16>()?;
        let output = serde_json::to_vec(&fixed::fixed_output_batch(generation)?)?;
        fixed::require(output.len() <= 32768)?;
        println!("{}", std::str::from_utf8(&output)?);
        Ok(())
    })();
    if result.is_err() {
        eprintln!("P628_FIXED_STORED_OUTPUT_BATCH_REJECTED_NO_RAW_VALUES");
        std::process::exit(2);
    }
}
