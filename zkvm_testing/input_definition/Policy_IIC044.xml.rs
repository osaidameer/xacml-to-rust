#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, Default)]
#[serde(default)]
use chrono::{NaiveDate, DateTime, FixedOffset};

pub struct Inputs {
    pub access_subject_started_work: String,
}

impl Inputs {
    pub fn new(access_subject_started_work: String) -> Self {
        Self {
            access_subject_started_work,
        }
    }
}