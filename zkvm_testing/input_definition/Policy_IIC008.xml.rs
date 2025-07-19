#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, Default)]
#[serde(default)]
pub struct Inputs {
    pub access_subject_group: String,
}

impl Inputs {
    pub fn new(access_subject_group: String) -> Self {
        Self {
            access_subject_group,
        }
    }
}
