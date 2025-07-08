#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct Inputs {
    pub test_attr: String,
}

impl Inputs {
    pub fn new(test_attr: String) -> Self {
        Self {
            test_attr,
        }
    }
}
