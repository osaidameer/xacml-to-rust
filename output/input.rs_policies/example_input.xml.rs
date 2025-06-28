#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct Inputs {
    pub role: String,
    pub ipAddress: String,
}

impl Inputs {
    pub fn new(role: String, ipAddress: String) -> Self {
        Self {
            role,
            ipAddress,
        }
    }
}
