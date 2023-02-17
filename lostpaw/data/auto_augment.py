# https://pytorch.org/vision/master/auto_examples/plot_transforms.html#sphx-glr-auto-examples-plot-transforms-py
# https://github.com/GuillaumeErhard/Supervised_contrastive_loss_pytorch/blob/main/data_augmentation/auto_augment.py

from typing import List, Optional
import torchvision.transforms as T
from PIL.Image import Image

class DataAugmenter:
    def __init__(self, policies: Optional[List[T.AutoAugmentPolicy]] = None) -> None:
        policies = policies or [
            T.AutoAugmentPolicy.CIFAR10,
            T.AutoAugmentPolicy.IMAGENET,
            T.AutoAugmentPolicy.SVHN,
        ]
        self.augmenters = [T.AutoAugment(policy) for policy in policies]

    def get_transforms(self, orig_img: Image, count=4):
        imgs = [
            augmenter(orig_img) for _ in range(count) for augmenter in self.augmenters
        ]
        # row_title = [str(policy).split('.')[-1] for policy in policies]
        # plot(imgs, row_title=row_title)

        return imgs
