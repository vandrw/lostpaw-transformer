use pyo3::{
    types::{PyByteArray, PyModule},
    Python,
};
use tokio::{
    sync::{mpsc, oneshot},
    task::spawn_blocking,
};

pub struct ImageFeatureExtractor {
    sender: mpsc::Sender<(Vec<u8>, oneshot::Sender<Option<Vec<f32>>>)>,
}

impl ImageFeatureExtractor {
    pub fn launch() -> ImageFeatureExtractor {
        let (sender, mut receiver) = mpsc::channel::<(Vec<u8>, oneshot::Sender<Option<Vec<f32>>>)>(20);
        spawn_blocking(move || {
            Python::with_gil(move |py| {
                // Load the module from file
                let module = PyModule::from_code(py, include_str!("ml.py"), "ml.py", "ml")
                    .map_err(|e| format!("{:?} {}", &e, e.traceback(py).unwrap().format().unwrap()))
                    .unwrap();

                // Call a function in the module
                let func = module.getattr("create_latent_space").unwrap();

                while let Some((image_bytes, answer)) = receiver.blocking_recv() {
                    let bytes = PyByteArray::new(py, &image_bytes);
                    if let Ok(result) = func.call((bytes,), None) {
                        let features: &numpy::PyArray1<f32> = result.downcast().unwrap();
                        let features = features.to_vec().unwrap();
                        if features.len() == 512 {
                            let _ = answer.send(Some(features));
                        } else {
                            let _ = answer.send(None);
                        }
                    };
                }
            });
        });

        ImageFeatureExtractor { sender }
    }

    pub async fn extract(&self, bytes: Vec<u8>) -> Option<Vec<f32>> {
        let (ret_send, ret_recv) = oneshot::channel();
        self.sender.send((bytes, ret_send)).await.ok()?;

        ret_recv.await.ok()?
    }
}
