#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, Default)]
#[serde(default)]
pub struct Inputs {
    pub access_subject_test_attr: NaiveDate,
}

impl Inputs {
    pub fn new(access_subject_test_attr: NaiveDate) -> Self {
        Self {
            access_subject_test_attr,
        }
    }
}
