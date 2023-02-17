from argparse import ArgumentParser
from pathlib import Path
from shutil import copy, copyfileobj

from lostpaw.data.extract_pets import lookup_next_image_name
from lostpaw.data.data_folder import PetImagesFolder

if __name__ == "__main__":
    parser = ArgumentParser()

    parser.add_argument("src", nargs="+", type=Path)
    parser.add_argument("target", type=Path)

    args = parser.parse_args()
    target_path = Path(args.target)
    target_folder = PetImagesFolder(target_path)
    target_path_processed = target_path / "processed.txt"
    target_path_processed.touch(exist_ok=True)

    for source in args.src:
        source_folder = PetImagesFolder(source)

        with open(target_path_processed, "at") as processed:
            processed_path = source / "processed.txt"
            with open(processed_path, "rt") as src_processed:
                copyfileobj(src_processed, processed)

        for idx in range(len(source_folder)):
            images, pet_id, source = source_folder.get_record(idx)
            target_folder.add_record(images, pet_id, source)

        target_folder.save_info()
