#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, Default)]
#[serde(default)]
pub struct Inputs {
    pub access_subject_test_attr: Vec<Vec<u8>>,
}

impl Inputs {
    pub fn new(access_subject_test_attr: Vec<Vec<u8>>) -> Self {
        Self {
            access_subject_test_attr,
        }
    }
}
