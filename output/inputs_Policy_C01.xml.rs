#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct Inputs {
    pub age: i32,
    pub bart_simpson_age: i32,
}

impl Inputs {
    pub fn new(age: i32, bart_simpson_age: i32) -> Self {
        Self {
            age,
            bart_simpson_age,
        }
    }
}
