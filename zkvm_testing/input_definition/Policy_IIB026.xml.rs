#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, Default)]
#[serde(default)]
pub struct Inputs {
    pub access_subject_subject_id: String,
    pub access_subject_request_time: String,
    pub resource_resource_id: String,
    pub action_action_id: String,
}

impl Inputs {
    pub fn new(access_subject_subject_id: String, access_subject_request_time: String, resource_resource_id: String, action_action_id: String) -> Self {
        Self {
            access_subject_subject_id,
            access_subject_request_time,
            resource_resource_id,
            action_action_id,
        }
    }
}
