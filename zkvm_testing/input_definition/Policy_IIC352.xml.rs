#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, Default)]
#[serde(default)]
pub struct Inputs {
    pub access_subject_age: f64,
}

impl Inputs {
    pub fn new(access_subject_age: f64) -> Self {
        Self {
            access_subject_age,
        }
    }
}
