#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, Default)]
#[serde(default)]
use chrono::{NaiveDate, DateTime, FixedOffset};
use iso8601_duration::Duration as IsoDuration;

pub struct Inputs {
    pub access_subject_auth_duration: String,
}

impl Inputs {
    pub fn new(access_subject_auth_duration: String) -> Self {
        Self {
            access_subject_auth_duration,
        }
    }
}