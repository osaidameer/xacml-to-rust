#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, Default)]
#[serde(default)]
pub struct Inputs {
    pub action_action_approved_by: String,
}

impl Inputs {
    pub fn new(action_action_approved_by: String) -> Self {
        Self {
            action_action_approved_by,
        }
    }
}
