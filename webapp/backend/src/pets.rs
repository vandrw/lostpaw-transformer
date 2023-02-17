use std::path::Path;

use crate::{
    geojson::{Feature, GeoFeatureCollection, Geometry},
    ml::ImageFeatureExtractor,
};
use rand::{thread_rng, Rng};
use rand_distr::StandardNormal;
use serde::Serialize;
use tracing::info;

pub struct PetDatabase {
    pets: Vec<Pet>,
}

impl PetDatabase {
    pub async fn new(
        folder_path: impl AsRef<Path>,
        extractor: &ImageFeatureExtractor,
    ) -> PetDatabase {
        let mut thread_rng = thread_rng();
        let mut pets: Vec<Pet> = folder_path
            .as_ref()
            .read_dir()
            .unwrap()
            .map(|e| e.unwrap())
            .filter(|e| e.path().is_file())
            .filter(|e| e.path().extension().and_then(|e| e.to_str()) == Some("jpg"))
            .map(|e| {
                let name = e
                    .file_name()
                    .to_string_lossy()
                    .trim_end_matches(".jpg")
                    .to_string();
                Pet {
                    image: std::fs::read(e.path()).unwrap(),
                    name,
                    feature_vector: Vec::new(),
                    longitude: 6.566044 + 0.03 * thread_rng.sample::<f64, _>(StandardNormal),
                    latitude: 53.217641 + 0.01 * thread_rng.sample::<f64, _>(StandardNormal),
                }
            })
            .collect();

        for pet in &mut pets {
            pet.feature_vector = extractor.extract(pet.image.clone()).await.expect("non pet image in database");
        }

        PetDatabase { pets }
    }

    pub fn to_geo_json(&self) -> GeoFeatureCollection {
        let mut features = GeoFeatureCollection::default();
        for pet in &self.pets {
            let mut feature = Feature::from(Geometry::Point {
                coordinates: [pet.longitude, pet.latitude],
            });

            feature.properties.insert(
                "image-url".to_string(),
                format!("/api/v1/pets/{}.jpg", pet.name).into(),
            );
            feature
                .properties
                .insert("name".to_string(), pet.name.clone().into());
            features.features.push(feature);
        }
        features
    }

    pub fn get_image(&self, path: &str) -> Option<Vec<u8>> {
        let name = path.trim_end_matches(".jpg").to_string();
        info!("image pet name: {name}");
        Some(self.pets.iter().find(|p| p.name == name)?.image.clone())
    }

    pub fn compare_features(
        &self,
        features: &[f32],
        cutoff_distance: f32,
        limit: usize,
    ) -> Vec<CompareResult> {
        let mut all: Vec<_> = self
            .pets
            .iter()
            .map(|p| CompareResult {
                name: p.name.clone(),
                image_url: format!("/api/v1/pets/{}.jpg", p.name),
                distance: p
                    .feature_vector
                    .iter()
                    .zip(features)
                    .map(|(a, b)| (a - b) * (a - b))
                    .sum::<f32>()
                    .sqrt(),
            })
            .filter(|cr| cr.distance < cutoff_distance)
            .take(limit)
            .collect();
        all.sort_by(|a, b| a.distance.partial_cmp(&b.distance).unwrap());
        all
    }
}

pub struct Pet {
    image: Vec<u8>,
    name: String,
    feature_vector: Vec<f32>,
    latitude: f64,
    longitude: f64,
}

#[derive(Debug, Clone, Serialize)]
pub struct CompareResult {
    name: String,
    image_url: String,
    distance: f32,
}
