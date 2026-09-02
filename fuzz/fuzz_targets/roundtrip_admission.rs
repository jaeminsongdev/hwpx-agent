#![no_main]

use std::io::Cursor;

use hwpx_package::{RoundTripLimits, RoundTripVerifier};
use libfuzzer_sys::fuzz_target;

const MAX_FUZZ_INPUT_BYTES: usize = 1024 * 1024;

fuzz_target!(|data: &[u8]| {
    if data.len() > MAX_FUZZ_INPUT_BYTES {
        return;
    }
    if let Err(error) = RoundTripVerifier::verify(Cursor::new(data), RoundTripLimits::default()) {
        let diagnostic = error.diagnostic();
        let _ = (
            diagnostic.code(),
            diagnostic.layer(),
            diagnostic.repairability(),
            diagnostic.action(),
        );
    }
});
