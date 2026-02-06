

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, Default)]
#[serde(default)]
pub struct Inputs {
    pub access_subject_key: String,
}

impl Inputs {
    pub fn new(access_subject_key: String) -> Self {
        Self {
            access_subject_key,
        }
    }
}