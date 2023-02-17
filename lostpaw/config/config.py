from typing import Tuple
from dataclasses import dataclass


@dataclass
class OptimizerConfig:
    lr: float = 1e-3
    betas: Tuple[float, float] = (0.9, 0.999)
    weight_decay: float = 0.0
    dampening: float = 0.0
    momentum: float = 0.0
    eps: float = 1e-8
    amsgrad: bool = False
    nesterov: bool = False

    def get_dict(self, optimizer):
        if optimizer == "adam" or optimizer == "adamw":
            return {
                k: v
                for k, v in self.__dict__.items()
                if k not in ["nesterov", "dampening", "momentum"]
            }
        elif optimizer == "sgd":
            return {
                k: v
                for k, v in self.__dict__.items()
                if k not in ["betas", "amsgrad", "eps"]
            }


@dataclass
class TrainConfig:
    info_path: str
    model_path: str
    run_name: str
    optimizer: str
    optimizer_params: dict
    similarity_probability: float = 0.5
    cross_validiton_k_fold: int = 1
    batches_per_epoch: int = 128
    epochs: int = 100
    batch_size: int = 16
    test_batch_size: int = 16
    test_batch_count: int = 8
    save_model_every: int = 10
    early_stopping_epochs: int = 15
    contrastive_margin: float = 1.25
    contrastive_epsilon: float = 1e-8
    use_wandb: bool = False
    use_tqdm: bool = False
    latent_space_size: int = 1024
