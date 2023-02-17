from argparse import ArgumentParser, Namespace
from glob import glob
import json
import logging
from pathlib import Path
from typing import Any, List, Set, Tuple
from lostpaw.data import PetImagesDataset, DetrPetExtractor
from lostpaw.data.auto_augment import DataAugmenter
from multiprocessing import Process
from PIL.Image import Image

from lostpaw.data.extract_pets import lookup_next_image_name

def extract_images(data: PetImagesDataset, output_dir: Path, model_path: Path, batch_size: int = 4):
    logging.basicConfig(
        format="[%(levelname)s] %(message)s", level=logging.INFO)

    pet_extractor = DetrPetExtractor(model_path)
    pet_augment = DataAugmenter()

    with open(output_dir / "processed.txt", "at") as processed_file:
        with open(output_dir / "train.data", "at") as resulting_file:
            for batch in data.get_batches(batch_size=batch_size):
                input_images = batch["images"]
                input_labels = [str(l) for l in batch["labels"]]
                input_paths = batch["paths"]
                labels = zip(input_labels, input_paths)

                cropped: List[Tuple[Image, Tuple[str, Any]]] = pet_extractor.extract(
                    input_images, labels, output_size=(384, 384))

                for image, (label, path) in cropped:
                    augmented = pet_augment.get_transforms(image, 2)
                    augmented.insert(0, image)

                    paths = [save_image(image, label, output_dir)
                             for image in augmented]

                    processed_file.write(f"{path}\n")
                    resulting_file.write(json.dumps(
                        dict(source_path=path, pet_id=label, augmented=paths)))
                    resulting_file.write("\n")

                processed_file.flush()
                resulting_file.flush()


def save_image(image, label, output_dir):
    folder_path = Path(output_dir, str(label))
    if not folder_path.exists():
        folder_path.mkdir(parents=True, exist_ok=True)

    path = lookup_next_image_name(folder_path);

    image.save(path)
    return str(path.resolve())


def main(args: Namespace):
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    processed_file_paths = glob(
        str(output_dir / "**" / "processed.txt"), recursive=True)
    ignore: Set[str] = set()
    for processed_file_path in processed_file_paths:
        with open(processed_file_path, "rt") as processed_file:
            ignore.union(l.strip() for l in processed_file.readlines())

    pet_data = PetImagesDataset.load_from_file(Path(args.info_file), ignore=ignore)

    processes: List[Process] = []
    for i, data_subset in enumerate(pet_data.split(args.threads)):
        sub_out_path = output_dir / f"thread_{i}"
        sub_out_path.mkdir(exist_ok=True)
        process = Process(target=extract_images, args=[data_subset, sub_out_path, args.model_path])
        process.start()
        processes.append(process)

    for process in processes:
        process.join()

if __name__ == "__main__":
    parser = ArgumentParser()

    parser.add_argument("--info_file", type=str, required=True)
    parser.add_argument("--model_path", type=str, required=True)
    parser.add_argument("--output_dir", type=str, required=True)
    parser.add_argument("--threads", type=int, default=4)
    parser.add_argument("--batch_size", type=int, default=4)

    args = parser.parse_args()

    logging.basicConfig(
        format="[%(levelname)s] %(message)s", level=logging.INFO)

    main(args)
