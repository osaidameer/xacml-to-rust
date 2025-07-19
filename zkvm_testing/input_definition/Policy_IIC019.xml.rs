#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, Default)]
#[serde(default)]
pub struct Inputs {
    pub access_subject_age: f64,
    pub environment_bart_simpson_age: f64,
}

impl Inputs {
    pub fn new(access_subject_age: f64, environment_bart_simpson_age: f64) -> Self {
        Self {
            access_subject_age,
            environment_bart_simpson_age,
        }
    }
}
