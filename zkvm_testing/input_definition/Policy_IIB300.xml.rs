#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, Default)]
#[serde(default)]
pub struct Inputs {
    pub action_action_id: String,
    pub access_subject_role: String,
    pub resource_resource_type: String,
}

impl Inputs {
    pub fn new(action_action_id: String, access_subject_role: String, resource_resource_type: String) -> Self {
        Self {
            action_action_id,
            access_subject_role,
            resource_resource_type,
        }
    }
}
