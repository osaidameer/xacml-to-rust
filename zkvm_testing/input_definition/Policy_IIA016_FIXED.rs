
use chrono::{NaiveDate, DateTime, FixedOffset};

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, Default)]
#[serde(default)]
pub struct Inputs {
    pub environment_current_time: String,
}

impl Inputs {
    pub fn new(environment_current_time: String) -> Self {
        Self {
            environment_current_time,
        }
    }
}