#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct Inputs {
    pub subject_id: String,
    pub NaN: f64,
    pub INF: f64,
    pub NegativeINF: f64,
}

impl Inputs {
    pub fn new(subject_id: String, NaN: f64, INF: f64, NegativeINF: f64) -> Self {
        Self {
            subject_id,
            NaN,
            INF,
            NegativeINF,
        }
    }
}
