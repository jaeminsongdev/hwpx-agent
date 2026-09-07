use std::{env, fs, path::PathBuf, process::ExitCode};

use hwpx_package::{CurrentFontMetricLimits, CurrentFontMetricReceipt, FontMetricReceiptError};

fn main() -> ExitCode {
    match verify() {
        Ok(summary) => {
            println!("{summary}");
            ExitCode::SUCCESS
        }
        Err(code) => {
            eprintln!("{code}");
            ExitCode::from(1)
        }
    }
}

fn verify() -> Result<String, &'static str> {
    let mut arguments = env::args().skip(1);
    let run_id = arguments.next().ok_or("font_metric_run_id_required")?;
    if arguments.next().is_some()
        || run_id.len() != 32
        || !run_id
            .bytes()
            .all(|byte| byte.is_ascii_hexdigit() && !byte.is_ascii_uppercase())
    {
        return Err("font_metric_run_id_invalid");
    }

    let repository_root = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .canonicalize()
        .map_err(|_| "repository_root_unavailable")?;
    let run_root = repository_root.join("artifacts/p06/font-metric-runs");
    let run_directory = run_root.join(&run_id);
    for directory in [&run_root, &run_directory] {
        let metadata =
            fs::symlink_metadata(directory).map_err(|_| "font_metric_receipt_path_invalid")?;
        if metadata.file_type().is_symlink() || !metadata.is_dir() {
            return Err("font_metric_receipt_boundary_invalid");
        }
    }
    let receipt_path = run_directory.join("receipt.json");
    let metadata =
        fs::symlink_metadata(&receipt_path).map_err(|_| "font_metric_receipt_missing")?;
    if metadata.file_type().is_symlink()
        || !metadata.is_file()
        || metadata.len() == 0
        || metadata.len() > 256 * 1024
    {
        return Err("font_metric_receipt_path_invalid");
    }
    let canonical_parent = receipt_path
        .parent()
        .ok_or("font_metric_receipt_path_invalid")?
        .canonicalize()
        .map_err(|_| "font_metric_receipt_path_invalid")?;
    let expected_parent = run_root
        .join(&run_id)
        .canonicalize()
        .map_err(|_| "font_metric_receipt_path_invalid")?;
    if canonical_parent != expected_parent {
        return Err("font_metric_receipt_boundary_invalid");
    }

    let source = fs::read(&receipt_path).map_err(|_| "font_metric_receipt_read_failed")?;
    let receipt = CurrentFontMetricReceipt::parse(&source, CurrentFontMetricLimits::default())
        .map_err(FontMetricReceiptError::code)?;
    Ok(format!(
        concat!(
            "{{\"schema_version\":\"hwpx-agent.p06-05-current-font-metric-rust-verification/v1\",",
            "\"state\":\"pass\",\"run_id\":\"{}\",\"receipt_sha256\":\"{}\",",
            "\"measurement_set_sha256\":\"{}\",\"cell_count\":{},",
            "\"actual_hangul_renderer\":false,\"product_complete\":false}}"
        ),
        run_id,
        receipt.receipt_sha256(),
        receipt.measurement_set_sha256(),
        receipt.cells().len(),
    ))
}
