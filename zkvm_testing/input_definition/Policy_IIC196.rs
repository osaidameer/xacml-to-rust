
use chrono::{NaiveDate, DateTime, FixedOffset};

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, Default)]
#[serde(default)]
pub struct Inputs {
    pub access_subject_test_attr: Vec<String>,
}

impl Inputs {
    pub fn new(access_subject_test_attr: Vec<String>) -> Self {
        Self {
            access_subject_test_attr,
        }
    }
}