#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct Inputs {
    pub subject_id: String,
    pub bogus: String,
    pub age: i32,
    pub bart_simpson_age: i32,
}

impl Inputs {
    pub fn new(subject_id: String, bogus: String, age: i32, bart_simpson_age: i32) -> Self {
        Self {
            subject_id,
            bogus,
            age,
            bart_simpson_age,
        }
    }
}
