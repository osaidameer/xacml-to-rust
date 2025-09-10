
use chrono::{NaiveDate, DateTime, FixedOffset};

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, Default)]
#[serde(default)]
pub struct Inputs {
    pub access_subject_test_attr: DateTime<FixedOffset>,
}

impl Inputs {
    pub fn new(access_subject_test_attr: DateTime<FixedOffset>) -> Self {
        Self {
            access_subject_test_attr,
        }
    }
}