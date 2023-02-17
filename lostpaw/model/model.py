from transformers import ViTFeatureExtractor, ViTModel
import torch
import torch.nn as nn
from torch import Tensor
from pathlib import Path


class PetViTContrastiveModel(nn.Module):
    def __init__(
        self,
        model_path: Path,
        output_dim: int = 1024,  # Output dimension of the model, latent space size
        device="cpu",
    ):
        super(PetViTContrastiveModel, self).__init__()
        self.vit_encoder = None
        self.vit_model = None
        self.model_path = Path(model_path)
        self.fetch_vit()

        self.device = device

        self.latent_space = nn.Sequential(
            # 577 = 384 / 16 * 384 / 16 + 1 (cls token)
            nn.Linear(self.vit_model.config.hidden_size * 577, 2 * output_dim),
            nn.ELU(),
            nn.Linear(2 * output_dim, 2 * output_dim),
            nn.ELU(),
            nn.Linear(2 * output_dim, output_dim),
        )

    def forward(self, x: Tensor):
        x = self.vit_encoder(x, return_tensors="pt").to(self.device)
        x = self.vit_model(**x)[0]
        x = x.flatten(1)
        x = self.latent_space(x)
        return x

    def train(self, train=True):
        super().train(train)
        self.vit_model.train(False)

    def fetch_vit(self):
        model_path = self.model_path / "model"
        encoder_path = self.model_path / "encoder"

        if model_path.exists() and encoder_path.exists():
            self.vit_encoder = ViTFeatureExtractor.from_pretrained(
                encoder_path, local_files_only=True
            )
            self.vit_model = ViTModel.from_pretrained(model_path, local_files_only=True)
        else:
            self.vit_model = ViTModel.from_pretrained("google/vit-base-patch16-384")
            self.vit_encoder: ViTFeatureExtractor = ViTFeatureExtractor.from_pretrained(
                "google/vit-base-patch16-384"
            )
            model_path.mkdir(exist_ok=True, parents=True)
            encoder_path.mkdir(exist_ok=True, parents=True)
            self.vit_model.save_pretrained(model_path)
            self.vit_encoder.save_pretrained(encoder_path)


    def load_model(self, path: Path):
        state = torch.load(path)
        self.load_state_dict(state)

    def save_model(self, path: Path):
        state = self.state_dict()
        torch.save(state, path)
