from typing import Any, Iterable, Optional, Union
from lostpaw.data.data_folder import PetImagesFolder
from lostpaw.model import PetViTContrastiveModel, PetContrastiveLoss
from lostpaw.config import TrainConfig, OptimizerConfig
from lostpaw.data import RandomPairDataset
from dataclasses import asdict
from pathlib import Path
from tqdm import tqdm
import logging
import wandb
import torch
from torch.optim import Adam, AdamW, SGD
import numpy as np
from PIL.Image import Image

device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")


class Trainer:
    def __init__(
        self,
        config: TrainConfig,
        data: Optional[RandomPairDataset] = None,
        seed: Optional[int] = None,
    ) -> None:
        logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

        self.config = config
        self.batches_per_epoch = config.batches_per_epoch
        self.model_path = Path(config.model_path)
        self.model_path.mkdir(exist_ok=True, parents=True)
        self.run_name = config.run_name

        if config.cross_validiton_k_fold > 1:
            k = 0 if data is None else data.current_fold
            self.run_name += f" kfold-{k}of{config.cross_validiton_k_fold}"

        self.model_state_path = self.model_path / f"model_{self.run_name}.pt"

        # ViT model
        self.vit_model = PetViTContrastiveModel(
            config.model_path, config.latent_space_size, device=device
        ).to(device)
        self.load_model()

        # Loss function
        self.contrastive_loss = PetContrastiveLoss(
            config.contrastive_margin, config.contrastive_epsilon
        )

        # Dataset
        if data is None:
            info_path = Path(config.info_path)
            data_folder = PetImagesFolder(info_path.parent, info_path.name)
            self.pet_data = RandomPairDataset(
                data_folder,
                config.similarity_probability,
                config.cross_validiton_k_fold,
                seed=seed,
            )
        else:
            self.pet_data = data

        logging.info("Trainer initialized")
        logging.info(f"Using device: {device}")
        logging.info("Train config:")
        logging.info(f"{config}")

        opt_config = OptimizerConfig(**config.optimizer_params)
        self.optimizer: Union[Adam, AdamW, SGD]
        self.load_optimizer(config.optimizer, opt_config)

        self.use_wandb = config.use_wandb
        self.use_tqdm = config.use_tqdm
        if config.use_wandb:
            wandb.init(
                project="lostpaw",
                entity="klotzandrei",
                name=self.run_name,
                config=asdict(config),
                reinit=True,
            )
            wandb.watch(self.vit_model)

    def train(self):
        epochs: int = self.config.epochs
        batch_size: int = self.config.batch_size
        test_batch_size: int = self.config.test_batch_size
        test_batch_count: int = self.config.test_batch_count
        self.vit_model.train()

        progress_tqdm = None

        data = self.pet_data.get_batches(batch_size)

        if test_batch_size != 0 and test_batch_count != 0:
            if self.pet_data.fold_count is not None and self.pet_data.fold_count > 1:
                test_data = self.pet_data.get_batches(test_batch_size, test=True)
            else:
                # For now just use the same data for testing, as long as the
                # test_batch_size is small we should have old data generally. 
                test_data = self.pet_data.get_batches(test_batch_size)

        bad_epochs = 0
        best_accuracy = 0

        for epoch in range(epochs):
            # Get the batches
            progress: Iterable[Any] = enumerate(data)
            if self.use_tqdm:
                progress = progress_tqdm = tqdm(
                    progress,
                    total=self.batches_per_epoch,
                )

            total_loss = 0.0
            total_acc = 0.0
            total_metric = np.zeros([4])

            for idx, (imgs1, imgs2, given_labels) in progress:
                if idx >= self.batches_per_epoch:
                    break

                self.optimizer.zero_grad()

                # Get the features
                features1 = self.vit_model(imgs1)
                features2 = self.vit_model(imgs2)

                # Merge the images for the contrastive loss
                # fatures: [batch_size, 2, output_dim]
                # labels: [batch_size]
                features = torch.stack([features1, features2], dim=1).to(device)
                labels = torch.tensor(given_labels, dtype=torch.float32).to(device)
                distance = self.contrastive_loss.euclidean_distance(features)

                # Compute the loss
                loss: torch.Tensor = self.contrastive_loss(features, labels, distance)

                # Backpropagate
                loss.backward()

                # Update the weights
                self.optimizer.step()

                total_metric += self.compute_metrics(labels, distance, batch_size)

                total_loss += loss.item()

                # Log the accuracy and loss
                if progress_tqdm:
                    (m_different, m_err1, m_err2, m_same) = total_metric / (idx + 1)
                    progress_tqdm.set_postfix(
                        {
                            "epoch": epoch,
                            "loss": total_loss / (idx + 1),
                            # "acc": total_acc / (idx + 1),
                            "diff": m_different,
                            "err1": m_err1,
                            "err2": m_err2,
                            "same": m_same,
                        }
                    )

            total_loss /= self.batches_per_epoch
            total_metric /= self.batches_per_epoch
            metric_different, metric_err1, metric_err2, metric_same = total_metric
            total_acc = 1 - (metric_err1 + metric_err2)

            test_dict = dict()
            if test_batch_size != 0:
                test_dict = dict(
                    test_accuracy=0,
                    test_diff=0,
                    test_same=0,
                    test_err1=0,
                    test_err2=0,
                )
                for _ in range(test_batch_count):
                    test_imgs1, test_imgs2, test_labels = next(test_data)
                    test_metric = self.test_batch(
                        test_imgs1, test_imgs2, test_labels, test_batch_size
                    )

                    tm_different, tm_err1, tm_err2, tm_same = test_metric
                    test_acc = 1 - (tm_err1 + tm_err2)
                    test_dict["test_accuracy"] += test_acc
                    test_dict["test_diff"] += tm_different
                    test_dict["test_same"] += tm_same
                    test_dict["test_err1"] += tm_err1
                    test_dict["test_err2"] += tm_err2
                
                test_dict["test_accuracy"] /= test_batch_count
                test_dict["test_diff"] /= test_batch_count
                test_dict["test_same"] /= test_batch_count
                test_dict["test_err1"] /= test_batch_count
                test_dict["test_err2"] /= test_batch_count

            if epoch > 50:
                if test_dict["test_accuracy"] <= best_accuracy:
                    bad_epochs += 1
                else:
                    bad_epochs = 0
                    best_accuracy = test_dict["test_accuracy"]


            logging.info(
                f"Epoch {epoch} - Avg. Loss: {total_loss:.3f} - Avg. Accuracy: {total_acc:.3f}"
            )
            if self.use_wandb:
                wandb.log(
                    dict(
                        loss=total_loss,
                        accuracy=total_acc,
                        diff=metric_different,
                        same=metric_same,
                        err1=metric_err1,
                        err2=metric_err2,
                        **test_dict
                    ),
                    step=epoch,
                )

            if (epoch % self.config.save_model_every == 0) or (epoch == epochs - 1) or (bad_epochs > self.config.early_stopping_epochs):
                self.save_model()

            if bad_epochs > self.config.early_stopping_epochs:
                logging.info("Early stopping!")
                break

    def compute_metrics(self, labels, distances, batch_size) -> np.array:
        labels_u8 = labels.to(dtype=torch.int8)
        values_u8 = (distances <= self.contrastive_loss.margin).to(dtype=torch.int8)

        metrics = (2 * labels_u8 + values_u8).bincount(minlength=4) / batch_size
        return metrics.cpu().numpy()

    def test_batch(self, imgs1, imgs2, labels, batch_size):
        with torch.no_grad():
            features1 = self.vit_model(imgs1)
            features2 = self.vit_model(imgs2)

            features = torch.stack([features1, features2], dim=1).to(device)
            labels = torch.tensor(labels, dtype=torch.float32).to(device)
            distance = self.contrastive_loss.euclidean_distance(features)
            return self.compute_metrics(labels, distance, batch_size)

    def save_model(self):
        logging.info("Saving model...")
        self.vit_model.save_model(self.model_state_path)

    def load_model(self):
        if self.model_state_path.exists():
            logging.info("Found previous model. Continuing training...")
            self.vit_model.load_model(self.model_state_path)
            return True
        else:
            logging.info("No model to load. Training from scratch.")
            return False

    def load_optimizer(self, optimizer: str, config: OptimizerConfig):
        logging.info("Optimizer config:")
        optimizer = optimizer.lower()
        if optimizer == "adam":
            self.optimizer = Adam(
                self.vit_model.parameters(),
                config.lr,
                config.betas,
                config.eps,
                config.weight_decay,
                config.amsgrad,
            )
        elif optimizer == "adamw":
            if config.weight_decay == 0.0:
                logging.warn(
                    "AdamW requires a weight decay. Setting it to default 1e-2."
                )
                config.weight_decay = 1e-2

            self.optimizer = AdamW(
                self.vit_model.parameters(),
                config.lr,
                config.betas,
                config.eps,
                config.weight_decay,
                config.amsgrad,
            )
        elif optimizer == "sgd":
            self.optimizer = SGD(
                self.vit_model.parameters(),
                config.lr,
                config.momentum,
                config.dampening,
                config.weight_decay,
                config.nesterov,
            )
        else:
            raise ValueError(f"Optimizer {optimizer} not supported")

        logging.info(f"{optimizer}: {config.get_dict(optimizer)}")
