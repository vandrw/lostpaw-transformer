use std::collections::HashMap;

use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct GeoFeatureCollection {
    #[serde(rename = "type")]
    _type: &'static str,
    pub features: Vec<Feature>,
}

impl Default for GeoFeatureCollection {
    fn default() -> Self {
        Self {
            _type: "FeatureCollection",
            features: Vec::new(),
        }
    }
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct Feature {
    #[serde(rename = "type")]
    _type: &'static str,
    pub geometry: Geometry,
    pub properties: HashMap<String, serde_json::Value>,
}

impl From<Geometry> for Feature {
    fn from(geometry: Geometry) -> Self {
        Self {
            _type: "Feature",
            geometry,
            properties: HashMap::new(),
        }
    }
}

#[derive(Debug, Serialize, Deserialize, Clone)]
#[serde(tag = "type")]
pub enum Geometry {
    Point { coordinates: [f64; 2] },
    LineString { coordinates: Vec<[f64; 2]> },
    MultiPoint { coordinates: Vec<[f64; 2]> },
    MultiLineString { coordinates: Vec<Vec<[f64; 2]>> },
    MultiPolygon { coordinates: Vec<Vec<Vec<[f64; 2]>>> },
}
