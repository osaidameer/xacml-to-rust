#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, Default)]
#[serde(default)]
use chrono::{NaiveDate, DateTime, FixedOffset};

pub struct Inputs {
    pub environment_current_dateTime: DateTime<FixedOffset>,
}

impl Inputs {
    pub fn new(environment_current_dateTime: DateTime<FixedOffset>) -> Self {
        Self {
            environment_current_dateTime,
        }
    }
}