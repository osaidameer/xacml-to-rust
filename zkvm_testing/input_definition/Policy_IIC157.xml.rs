#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, Default)]
#[serde(default)]
use iso8601_duration::Duration as IsoDuration;

pub struct Inputs {
    pub access_subject_test_attr: String,
}

impl Inputs {
    pub fn new(access_subject_test_attr: String) -> Self {
        Self {
            access_subject_test_attr,
        }
    }
}