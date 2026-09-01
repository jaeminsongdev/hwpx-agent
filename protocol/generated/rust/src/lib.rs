#![forbid(unsafe_code)]
#![allow(clippy::doc_markdown)]
#![allow(clippy::must_use_candidate)]

pub mod foundation {
    pub mod v1 {
        include!("hwpx_agent.foundation.v1.rs");
    }
}

pub mod schema_models;

#[cfg(test)]
mod tests {
    use super::schema_models::SourceRecordV1;

    #[test]
    fn source_record_sample_deserializes_into_generated_model() {
        let source = include_str!("../../../../fixtures/synthetic/p02-source-records/help.json");
        let record: SourceRecordV1 = serde_json::from_str(source).unwrap_or_else(|error| {
            panic!("generated SourceRecordV1 rejected the schema-valid sample: {error}")
        });
        assert_eq!(record.schema_version, "hwpx-agent.source-record/v1");
        assert_eq!(record.source_kind, "help");
    }
}
