#![forbid(unsafe_code)]
#![allow(clippy::doc_markdown)]
#![allow(clippy::must_use_candidate)]

pub mod foundation {
    pub mod v1 {
        include!("hwpx_agent.foundation.v1.rs");
    }
}
