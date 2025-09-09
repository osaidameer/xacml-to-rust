#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, Default)]
#[serde(default)]

pub struct Inputs {
    pub access_subject_test_attr: i32,
}

impl Inputs {
    pub fn new(access_subject_test_attr: i32) -> Self {
        Self {
            access_subject_test_attr,
        }
    }
}