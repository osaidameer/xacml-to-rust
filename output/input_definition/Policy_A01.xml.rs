#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct Inputs {
    pub subject_id: String,
    pub resource_id: String,
    pub action_id: String,
}

impl Inputs {
    pub fn new(subject_id: String, resource_id: String, action_id: String) -> Self {
        Self {
            subject_id,
            resource_id,
            action_id,
        }
    }
}
