from transformers import DetrFeatureExtractor, DetrForObjectDetection
from typing import Iterable, List, Optional, Sequence, Sized, Tuple, TypeVar
from pathlib import Path
from PIL.Image import Image, new as newImage
import logging
import torch

L = TypeVar('L') 

class DetrPetExtractor:
    def __init__(self, path: Path):
        self.feature_extractor: DetrFeatureExtractor = None
        self.model: DetrForObjectDetection = None
        self.load_extractor(path)

    def extract(
        self,
        images: Sequence[Image],
        labels: Iterable[L],
        threshold: float = 0.9,
        output_size: Optional[tuple] = None,
    ) -> List[Tuple[Image, L]]:
        """
        Extract pets from images.

        Args:
            images: List of images to extract pets from.
            labels: List of labels for each image. If provided, the output will be a list of tuples (image, (label, pet)).
            threshold: Threshold for the model to consider a prediction as valid.
            output_size: Size of the output images. If None, the output images will have the same size as the input images.

        Returns:
            List of images or List of tuples (image, (label, pet)).
        """

        inputs = self.feature_extractor(images=images, return_tensors="pt")
        outputs = self.model(**inputs)

        # Get the predicted bounding boxes and labels
        target_sizes = torch.tensor([i.size[::-1] for i in images])
        results = self.feature_extractor.post_process_object_detection(
            outputs, target_sizes=target_sizes
        )

        cropped_images = []

        for result, image, pet_label in zip(results, images, labels):
            imgs = self.parse_result(result, image, threshold, output_size)
            imgs_with_labels = [(img, pet_label) for img in imgs]
            cropped_images.extend(imgs_with_labels)

        logging.info(f"Found {len(cropped_images)} pets in {len(images)} images.")
        return cropped_images

    def parse_result(
        self,
        result,
        image: Image,
        threshold: float = 0.9,
        output_size: Optional[tuple] = None,
    ):
        imgs = []
        for score, label, box in zip(
            result["scores"], result["labels"], result["boxes"]
        ):
            box = [int(x) for x in box]

            if score > threshold:
                # Save only if the label is "cat" or "dog"
                if (label == 17) or (label == 18):
                    img_crop = image.crop(box)
                    if output_size:
                        img_crop = self.resize(img_crop, output_size)

                    imgs.append(img_crop)

        return imgs

    def resize(self, image: Image, size):
        # Resize the image to the size of the model
        # Keep the aspect ratio
        width, height = image.size
        if width > height:
            new_width = size[0]
            new_height = int(height * size[0] / width)
        else:
            new_width = int(width * size[1] / height)
            new_height = size[1]

        # Fill the rest with black
        new_image = newImage("RGB", size, (0, 0, 0))
        # Paste the resized image in the center
        new_image.paste(
            image.resize((new_width, new_height)),
            (int((size[0] - new_width) / 2), int((size[1] - new_height) / 2)),
        )

        return new_image

    def load_extractor(self, path: Path):
        model_path = Path(path) / "extractor_model"
        feature_path = Path(path) / "extractor_feature"
        if model_path.exists():
            self.model = DetrForObjectDetection.from_pretrained(
                model_path, local_files_only=True
            )
            self.feature_extractor = DetrFeatureExtractor.from_pretrained(
                feature_path, local_files_only=True
            )
        else:
            Path(path).mkdir(parents=True, exist_ok=True)
            self.feature_extractor = DetrFeatureExtractor.from_pretrained(
                "facebook/detr-resnet-50"
            )
            self.model = DetrForObjectDetection.from_pretrained(
                "facebook/detr-resnet-50"
            )
            self.save_extractor(path)

    def save_extractor(self, path: Path):
        if not Path(path).exists():
            Path(path).mkdir(parents=True, exist_ok=True)

        model_path = Path(path) / "extractor_model"
        feature_path = Path(path) / "extractor_feature"

        self.model.save_pretrained(str(model_path))
        self.feature_extractor.save_pretrained(str(feature_path))


def lookup_next_image_name(folder_path: Path) -> Path:
    i = len(list(folder_path.glob("*.jpg")))

    while (folder_path / f"{i}.jpg").exists():
        i += 1

    return folder_path / f"{i}.jpg"
