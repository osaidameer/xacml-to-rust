#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, Default)]
#[serde(default)]
pub struct Inputs {
    pub action_action_id: String,
    pub action_qos: String,
}

impl Inputs {
    pub fn new(action_action_id: String, action_qos: String) -> Self {
        Self {
            action_action_id,
            action_qos,
        }
    }
}
