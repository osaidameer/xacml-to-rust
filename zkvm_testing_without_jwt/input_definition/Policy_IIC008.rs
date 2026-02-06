

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, Default)]
#[serde(default)]
pub struct Inputs {
    pub access_subject_group: Vec<String>,
}

impl Inputs {
    pub fn new(access_subject_group: Vec<String>) -> Self {
        Self {
            access_subject_group,
        }
    }
}