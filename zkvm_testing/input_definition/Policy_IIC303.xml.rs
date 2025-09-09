#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, Default)]
#[serde(default)]

pub struct Inputs {
    pub resource_resource_id: String,
}

impl Inputs {
    pub fn new(resource_resource_id: String) -> Self {
        Self {
            resource_resource_id,
        }
    }
}