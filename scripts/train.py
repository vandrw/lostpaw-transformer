from lostpaw.config.args import get_args
from lostpaw.model.trainer import Trainer, TrainConfig

def main(args):
    config = TrainConfig(**vars(args))

    k_folds = max(config.cross_validiton_k_fold, 1)
    pet_data = None

    for _ in range(k_folds):
        trainer = Trainer(config, pet_data)
        pet_data = trainer.pet_data

        trainer.train()
        
        pet_data.next_fold()

if __name__ == "__main__":
    args = get_args()

    main(args)