use axum::{
    body::{Body, Bytes},
    extract::{Path as PathExtractor, Query, State},
    http::{Response, StatusCode},
    routing::{get, post},
    Json, Router,
};
use axum_sessions::{
    async_session::MemoryStore,
    extractors::{ReadableSession, WritableSession},
    SessionLayer,
};
use geojson::GeoFeatureCollection;
use pets::{CompareResult, PetDatabase};
use rand::prelude::*;
use serde::{Deserialize, Serialize};
use std::{net::SocketAddr, ops::Not, path::Path, sync::Arc};
use tower_http::{
    cors::{AllowHeaders, AllowOrigin, CorsLayer},
    trace::TraceLayer,
};
use tracing::debug;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

use crate::login::UserAuthenticator;
use crate::ml::ImageFeatureExtractor;

pub mod geojson;
pub mod login;
pub mod ml;
pub mod pets;

struct AppState {
    auth: UserAuthenticator,
    extractor: ImageFeatureExtractor,
    pets: PetDatabase,
}

impl AppState {
    pub async fn new(pet_image_folder: impl AsRef<Path>) -> Self {
        let extractor = ImageFeatureExtractor::launch();
        Self {
            auth: UserAuthenticator::new().await.unwrap(),
            pets: PetDatabase::new(pet_image_folder, &extractor).await,
            extractor,
        }
    }
}

#[tokio::main]
async fn main() {
    tracing_subscriber::registry()
        .with(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "lostpaw_backend=debug,tower_http=debug".into()),
        )
        .with(tracing_subscriber::fmt::layer())
        .init();

    let state = Arc::new(AppState::new("example_pets").await);

    let mut secret = [0; 64];
    secret[0..32].copy_from_slice(&random::<[u8; 32]>());
    secret[32..64].copy_from_slice(&random::<[u8; 32]>());
    let store = MemoryStore::new();
    let session_layer = SessionLayer::new(store, &secret);

    let cors = CorsLayer::new()
        .allow_origin(AllowOrigin::any())
        .allow_headers(AllowHeaders::any());

    let api_v1 = Router::new()
        .route("/login", post(login))
        .route("/login/confirm", get(confirm_login))
        .route("/pet-spotted", post(pet_spotted))
        .route("/pets/:name", get(pet_image))
        .route("/pets", get(pets));

    // build our application with a route
    let app = Router::new()
        .nest("/api/v1", api_v1)
        .with_state(state)
        .layer(TraceLayer::new_for_http())
        .layer(cors)
        .layer(session_layer);

    // run it
    let addr = SocketAddr::from(([127, 0, 0, 1], 3000));
    tracing::debug!("listening on {}", addr);
    axum::Server::bind(&addr)
        .serve(app.into_make_service())
        .await
        .unwrap();
}

#[axum_macros::debug_handler]
async fn pets(state: State<Arc<AppState>>) -> Json<GeoFeatureCollection> {
    Json(state.pets.to_geo_json())
}

#[axum_macros::debug_handler]
async fn pet_image(
    name: PathExtractor<String>,
    state: State<Arc<AppState>>,
) -> Result<Response<Body>, StatusCode> {
    let image = state
        .pets
        .get_image(name.as_str())
        .ok_or(StatusCode::NOT_FOUND)?;
    Ok(Response::builder()
        .header("Content-Type", "image/jpeg")
        .body(Body::from(image))
        .unwrap())
}

#[axum_macros::debug_handler]
#[tracing::instrument(skip(payload, state))]
async fn pet_spotted(
    session: WritableSession,
    query: Query<PetSpottedQuery>,
    state: State<Arc<AppState>>,
    payload: Bytes,
) -> Result<Json<Vec<CompareResult>>, (StatusCode, String)> {
    let features = state
        .extractor
        .extract(payload.to_vec())
        .await
        .ok_or_else(|| {
            (
                StatusCode::NOT_ACCEPTABLE,
                "No dog found in image".to_string(),
            )
        })?;

    let result = state.pets.compare_features(&features, 1.66, 5);

    Ok(Json(result))
}

#[derive(Default, Debug, Clone, Serialize, Deserialize)]
pub struct PetSpottedQuery {
    lat: f64,
    lon: f64,
}

#[axum_macros::debug_handler]
async fn login(session: ReadableSession, state: State<Arc<AppState>>) -> Json<LoginResult> {
    debug!("session {:?}", session);
    let user = session.get::<User>("user");
    if let Some(user) = user {
        if session.is_expired().not() {
            return Json(LoginResult::Done { user });
        }
    }
    let url = state.auth.init_login().unwrap().as_str().to_owned();
    Json(LoginResult::Redirect { url })
}

#[derive(Serialize, Deserialize)]
struct LoginQuery {
    user: Option<String>,
    password: Option<String>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "camelCase", tag = "action")]
enum LoginResult {
    Done { user: User },
    Redirect { url: String },
    ProvideCredentials,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct User {
    email: String,
}

#[axum_macros::debug_handler]
async fn confirm_login(
    query: Query<ConfirmLoginQuery>,
    mut session: WritableSession,
    state: State<Arc<AppState>>,
) -> Json<User> {
    let email = state.auth.login(&query.state, &query.code).await.unwrap();

    let user = User { email };
    session.insert("user", &user).unwrap();
    Json(user)
}

#[derive(Serialize, Deserialize)]
struct ConfirmLoginQuery {
    state: String,
    code: String,
}
