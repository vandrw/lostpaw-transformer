use std::{error::Error, path::PathBuf};

use serde::{Deserialize, Serialize};

pub type Result<T> = std::result::Result<T, Box<dyn Error + Send + Sync>>;

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct Pet {
    pub pet_id: i32,
    pub pet_species_id: i32,
    pub pet_age: Option<String>,
    pub pet_breed: Option<String>,
    pub pet_photos: Vec<PetPhoto>,
    pub pet_attributes: Vec<PetAttribute>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, PartialOrd, Ord)]
#[serde(rename_all = "camelCase")]
pub struct PetPhoto {
    pub display_photo_url: String,
    pub saved_path: Option<PathBuf>,
    pub pet_id: Option<i32>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct PetAttribute {
    pub label: String,
    pub content: Option<String>,
}
