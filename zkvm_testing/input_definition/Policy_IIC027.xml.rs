

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, Default)]
#[serde(default)]
pub struct Inputs {
    pub environment_bart_simpson_age: f64,
    pub access_subject_age: f64,
}

impl Inputs {
    pub fn new(environment_bart_simpson_age: f64, access_subject_age: f64) -> Self {
        Self {
            environment_bart_simpson_age,
            access_subject_age,
        }
    }
}