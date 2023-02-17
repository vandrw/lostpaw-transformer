import argparse
import os
from pathlib import Path

from lostpaw.data.data_folder import PetImagesFolder
from lostpaw.data.dataset import RandomPairDataset

if __name__ == "__main__":

    # Create a parser object
    parser = argparse.ArgumentParser()

    # Add an argument for the folder path
    parser.add_argument('folder', help='The path to the data folder')

    # Parse the arguments
    args = parser.parse_args()

    data_folder = PetImagesFolder(Path(args.folder), "train.data")

    # data_folder.describe(True)

    # exit(0)

    # Dataset
    pet_data = RandomPairDataset(data_folder, 0.5)

    for i, batch in enumerate(pet_data.get_batches(batch_size=3)):
        pet_data.visualize_batch(batch, file_name=f"data_{i}.jpg")
        if i == 2:
            break;

