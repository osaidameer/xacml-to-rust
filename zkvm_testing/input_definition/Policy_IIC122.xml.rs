#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, Default)]
#[serde(default)]
pub struct Inputs {
    pub access_subject_test_attr: bool,
}

impl Inputs {
    pub fn new(access_subject_test_attr: bool) -> Self {
        Self {
            access_subject_test_attr,
        }
    }
}
