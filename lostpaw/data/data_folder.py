from pathlib import Path
from pprint import pprint
import shutil
from typing import Any, Dict, Iterator, List, Optional, Tuple, Union
from PIL import Image
from PIL.Image import Image as ImageT
import pandas as pd
import numpy as np

from lostpaw.data.extract_pets import lookup_next_image_name


class PetImagesFolder:
    sources: List[str] = []
    paths: List[List[str]] = []
    pet_ids: List[int] = []
    folder: Path
    info_file: Path

    def __init__(self, folder: Path, info_file_name: str = "train.data"):
        self.folder = folder
        self.info_file = folder / info_file_name

        self.folder.mkdir(exist_ok=True)
        self.info_file.touch(exist_ok=True)
        df = pd.read_json(self.info_file, lines=True)

        if len(df) > 0:
            self.sources = df["source"].tolist()
            self.paths = df["paths"].tolist()
            self.pet_ids = df["pet_id"].tolist()

    def __len__(self) -> int:
        id_len = len(self.pet_ids)
        assert len(self.sources) == len(self.paths) == id_len
        return id_len

    def __getitem__(self, idx) -> Tuple[List[Tuple[ImageT, Path]], int]:
        paths, pet_id, source = self.get_record(idx)
        images = []
        for image_path in paths:
            image = Image.open(image_path).convert("RGB")
            images.append((image, image_path))

        return images, pet_id

    def data_frame(self) -> pd.DataFrame:
        data = dict(source=self.sources, paths=self.paths, pet_id=self.pet_ids)
        return pd.DataFrame(data)

    def save_info(self):
        df = self.data_frame()
        df.to_json(self.info_file, orient="records", lines=True, default_handler=str)

    def get_record(self, idx: int) -> Tuple[List[Path], int, str]:
        return (
            [
                Path(p) if Path(p).is_absolute else self.image_folder / Path(p)
                for p in self.paths[idx]
            ],
            int(self.pet_ids[idx]),
            str(self.sources[idx]),
        )

    def add_record(
        self, images: List[Union[ImageT, Path]], pet_id: int, source: str = ""
    ):
        pet_folder = self.folder / str(pet_id)
        pet_folder.mkdir(exist_ok=True)
        paths = []
        for image in images:
            image_path = lookup_next_image_name(pet_folder)
            if isinstance(image, ImageT):
                image.save(image_path)
            elif isinstance(image, Path):
                shutil.copy(image, image_path)
            else:
                raise ValueError(f"invalid image type given: {type(image)}")
            paths.append(str(image_path))

        self.sources.append(source)
        self.paths.append(paths)
        self.pet_ids.append(pet_id)

    def describe(self, print=False, drop_duplicates=True) -> Dict[str, Any]:
        df = self.data_frame()

        if drop_duplicates:
            df.drop_duplicates(subset=["source"], inplace=True)

        grouped = df.groupby("pet_id")["paths"]
        sizes = grouped.apply(lambda x: len(x))

        info = {
            "average images per pet": grouped.count().mean(),
            # "average images per pet >1": filtered_grouped.count().mean(),
            "sizes": np.bincount(sizes, minlength=6)[1:6].tolist(),
        }

        if print:
            pprint(info)

        return info
