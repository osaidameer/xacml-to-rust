
use iso8601_duration::Duration as IsoDuration;

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