

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, Default)]
#[serde(default)]
pub struct Inputs {
    pub environment_bart_simpson_age: i32,
    pub access_subject_age: i32,
}

impl Inputs {
    pub fn new(environment_bart_simpson_age: i32, access_subject_age: i32) -> Self {
        Self {
            environment_bart_simpson_age,
            access_subject_age,
        }
    }
}