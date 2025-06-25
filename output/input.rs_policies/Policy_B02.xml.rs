#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct Inputs {
    pub action_id: String,
}

impl Inputs {
    pub fn new(action_id: String) -> Self {
        Self {
            action_id,
        }
    }
}
