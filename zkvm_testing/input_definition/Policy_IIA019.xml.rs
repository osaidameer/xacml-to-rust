#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, Default)]
#[serde(default)]
pub struct Inputs {
    pub environment_current_date: Vec<String>,
}

impl Inputs {
    pub fn new(environment_current_date: Vec<String>) -> Self {
        Self {
            environment_current_date,
        }
    }
}
