

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, Default)]
#[serde(default)]
pub struct Inputs {
    pub action_action_id: String,
}

impl Inputs {
    pub fn new(action_action_id: String) -> Self {
        Self {
            action_action_id,
        }
    }
}