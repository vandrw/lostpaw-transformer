from math import ceil
from torch.utils.data import Dataset
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from PIL.Image import Image as ImageT
import pandas as pd
from typing import Any, Dict, Iterator, List, Optional, Set, Tuple
from sys import maxsize
import random
import numpy as np

from lostpaw.data.data_folder import PetImagesFolder


class PetImageDataset(Dataset):
    @classmethod
    def load_from_file(
        cls, info_file: Path, ignore: Set[str] = set()
    ) -> "PetImageDataset":
        image_root = info_file.parent
        try:
            imgs_and_labels = pd.read_json(info_file, lines=True)
            imgs_and_labels["isProcessed"] = imgs_and_labels["savedPath"].map(
                lambda p: p not in ignore
            )
            imgs_and_labels_filtered = imgs_and_labels[imgs_and_labels["isProcessed"]]
            img_paths = imgs_and_labels_filtered["savedPath"]
            img_labels = imgs_and_labels_filtered["petId"]
            return PetImageDataset(image_root, img_paths, img_labels)

        except ValueError:
            print(
                "[ERROR] The provided info_file does not exist or is not a valid JSON file."
            )
            exit()

    def __init__(
        self, image_root: Path, image_paths: pd.Series, image_labels: pd.Series
    ):
        self.image_root = image_root
        self.image_paths = image_paths
        self.image_labels = image_labels

    def __len__(self) -> int:
        return len(self.image_paths)

    def __iter__(self) -> Iterator[Tuple[Image.Image, str]]:
        for idx in range(len(self)):
            yield self.__getitem__(idx)

    def iter_with_path(self) -> Iterator[Tuple[Image.Image, str, str]]:
        for idx in range(len(self)):
            i, l = self.__getitem__(idx)
            yield i, l, self.image_paths[idx]

    def __getitem__(self, idx) -> Tuple[Image.Image, str]:
        img_path = self.image_root / self.image_paths[idx]
        image = Image.open(img_path).convert("RGB")
        label = self.image_labels[idx]

        return image, label

    def get_batches(self, batch_size=32) -> Iterator[Dict[str, Any]]:
        images, labels, paths = [], [], []

        for img, label, path in self.iter_with_path():
            images.append(img)
            labels.append(label)
            paths.append(path)

            if len(images) == batch_size:
                yield dict(images=images, labels=labels, paths=paths)
                images, labels, paths = [], [], []

    def split(self, count: int) -> Iterator["PetImageDataset"]:
        chunk_length = ceil(len(self) / count)
        for i in range(count):
            start = i * chunk_length
            end = start + chunk_length
            end = end if end < len(self) else len(self)
            paths = self.image_paths[start:end].reset_index(drop=True)
            labels = self.image_labels[start:end].reset_index(drop=True)
            yield PetImageDataset(self.image_root, paths, labels)


class RandomPairDataset(Dataset):
    def __init__(
        self,
        folder: PetImagesFolder,
        same_probability=0.5,
        fold_count: Optional[int] = None,
        seed: Optional[int] = None,
    ):
        self.seed = seed or random.randint(0, maxsize)
        self.folder = folder
        self.same_probability = same_probability
        df = folder.data_frame()
        self.pets = df.groupby("pet_id").agg(dict(paths=list))
        self.pets = self.pets[self.pets["paths"].map(lambda p: len(p) > 1)]
        self.fold_count = fold_count
        self.current_fold = 0 if fold_count is not None else None

    def __len__(self) -> int:
        return maxsize

    def __iter__(self) -> Iterator[Tuple[ImageT, ImageT, int]]:
        for idx in range(len(self)):
            yield self.__getitem__(idx)

    def iter_test_items(self) -> Iterator[Tuple[ImageT, ImageT, int]]:
        for idx in range(len(self)):
            yield self.get_test_item(idx)

    def _get_item(self, idx: int) -> Tuple[ImageT, ImageT, int]:
        rand_state = random.getstate()
        random.seed(idx ^ self.seed)
        data_length = len(self.pets)
        idx = random.randint(0, data_length - 1)
        is_same = random.random() < self.same_probability

        img_path1 = None
        img_path2 = None
        img_list1: List[str]
        img_list2: List[str]
        image_paths_of_pet: List[List[str]] = self.pets.iloc[idx]["paths"]
        if is_same:
            if len(image_paths_of_pet) == 1:
                raise RuntimeError("Should never happen, filtered out by robin.")
                # idx_1, idx_2 = random.sample(range(len(image_paths_of_pet[0])), 2)
                # img_path1 = image_paths_of_pet[0][idx_1]
                # img_path2 = image_paths_of_pet[0][idx_2]
            else:
                img_list1, img_list2 = random.sample(image_paths_of_pet, 2)

                img_path1 = random.choice(img_list1)
                img_path2 = random.choice(img_list2)

        else:
            img_list1 = random.choice(image_paths_of_pet)

            idx2 = random.randint(0, data_length - 1)
            while idx2 == idx:
                idx2 = random.randint(0, data_length - 1)

            img_list2 = random.choice(self.pets.iloc[idx2]["paths"])

            img_path1 = random.choice(img_list1)
            img_path2 = random.choice(img_list2)

        img1 = Image.open(img_path1).convert("RGB")
        img2 = Image.open(img_path2).convert("RGB")

        random.setstate(rand_state)

        return img1, img2, is_same

    def __getitem__(self, idx: int) -> Tuple[ImageT, ImageT, int]:
        # To implement K-fold validation, we simply skip every Kth index.
        if self.fold_count is not None and self.fold_count > 1:
            fold_number = self.fold_count - 1
            idx = idx + int(idx % fold_number >= self.current_fold) + idx // fold_number

        return self._get_item(idx)

    def get_test_item(self, idx: int) -> Tuple[ImageT, ImageT, int]:
        if self.fold_count is None or self.fold_count <= 1:
            raise RuntimeError("no test items in dataset, specify k-fold")

        idx = self.current_fold + idx * self.fold_count

        return self._get_item(idx)

    def next_fold(self):
        self.current_fold = (self.current_fold + 1) % self.fold_count

    def visualize_batch(
        self,
        batch: Tuple[List[ImageT], List[ImageT], List[int]],
        image_size=100,
        file_name: str = "result.jpg",
    ):
        # Create a new image with a white background
        length = len(batch[0])
        height = image_size + 36

        result = Image.new(
            "RGB",
            (image_size * 2, height * length),
            "white",
        )
        for i, image1, image2, is_same in zip(range(length), *batch):
            result.paste(image1.resize((image_size, image_size)), (0, i * height))
            result.paste(
                image2.resize((image_size, image_size)), (image_size, i * height)
            )

            font = ImageFont.truetype("fonts/Helvetica.ttf", size=25)
            # Create a draw object
            draw = ImageDraw.Draw(result)

            # Draw some text below the images
            fill = "green" if is_same else "red"
            text_width, text_height = (100, 10)
            x = image_size
            y = i * height + image_size + 3
            draw.text((x, y), "same" if is_same else "different", "black", font=font, anchor="mt")
            # draw.rectangle((x, y, x + text_width, y + text_height), fill)

        result.save(file_name)

    def get_batches(
        self,
        batch_size=8,
        test=False,
    ) -> Iterator[Tuple[List[ImageT], List[ImageT], List[int]]]:
        img0s, img1s, labels = [], [], []

        source = self.iter_test_items() if test else self

        for img0, img1, label in source:
            img0s.append(img0)
            img1s.append(img1)
            labels.append(label)

            if len(img0s) == batch_size:
                yield img0s, img1s, labels
                img0s, img1s, labels = [], [], []
