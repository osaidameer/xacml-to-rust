

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, Default)]
#[serde(default)]
pub struct Inputs {
    pub intermediary_subject_age: i32,
}

impl Inputs {
    pub fn new(intermediary_subject_age: i32) -> Self {
        Self {
            intermediary_subject_age,
        }
    }
}