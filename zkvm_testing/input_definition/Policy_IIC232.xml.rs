#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, Default)]
#[serde(default)]
pub struct Inputs {
    pub access_subject_auth_duration: String,
}

impl Inputs {
    pub fn new(access_subject_auth_duration: String) -> Self {
        Self {
            access_subject_auth_duration,
        }
    }
}
