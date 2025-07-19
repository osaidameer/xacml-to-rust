#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, Default)]
#[serde(default)]
pub struct Inputs {
    pub access_subject_subject_id: String,
    pub resource_simple_file_name: String,
    pub action_action_id: String,
}

impl Inputs {
    pub fn new(access_subject_subject_id: String, resource_simple_file_name: String, action_action_id: String) -> Self {
        Self {
            access_subject_subject_id,
            resource_simple_file_name,
            action_action_id,
        }
    }
}
