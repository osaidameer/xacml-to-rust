#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct Inputs {
    pub subject_id: String,
}

impl Inputs {
    pub fn new(subject_id: String) -> Self {
        Self {
            subject_id,
        }
    }
}
