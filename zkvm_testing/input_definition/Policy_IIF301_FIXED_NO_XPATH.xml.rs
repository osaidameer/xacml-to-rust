#[derive(Debug, Clone, serde::Serialize, serde::Deserialize, Default)]
#[serde(default)]

pub struct Inputs {
    pub OurTown_theHospitalWebSite: String,
}

impl Inputs {
    pub fn new(OurTown_theHospitalWebSite: String) -> Self {
        Self {
            OurTown_theHospitalWebSite,
        }
    }
}