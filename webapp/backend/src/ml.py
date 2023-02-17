from io import BytesIO
from lostpaw.config.config import TrainConfig
from lostpaw.data.extract_pets import DetrPetExtractor
from lostpaw.model import PetViTContrastiveModel
from PIL import Image
from torch import Tensor
import yaml
import numpy as np

from lostpaw.model.trainer import Trainer

with open("lostpaw/configs/container.yaml", "r") as f:
    config = TrainConfig(**yaml.safe_load(f))
    print(config)

trainer = Trainer(config)
model = trainer.vit_model
model.train(False)

extractor = DetrPetExtractor(config.model_path)


def create_latent_space(buffer):
    bytes = BytesIO(buffer)
    # print(len(bytes))
    bytes.seek(0)
    image = Image.open(bytes, formats=["JPEG", "PNG"])
    image.load()
    image = image.convert("RGB")
    print(np.array(image).shape)
    extracted_pets = extractor.extract([image], [0], output_size=(384, 384))
    if len(extracted_pets) == 0:
        return np.array([], dtype=np.float32)
    feature_tensor: Tensor = model(extracted_pets[0][0])
    return np.reshape(feature_tensor.detach().to(device="cpu").numpy(), -1)