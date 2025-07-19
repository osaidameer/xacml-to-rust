#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, Default)]
#[serde(default)]
pub struct Inputs {
    pub access_subject_licensed_on: String,
}

impl Inputs {
    pub fn new(access_subject_licensed_on: String) -> Self {
        Self {
            access_subject_licensed_on,
        }
    }
}
