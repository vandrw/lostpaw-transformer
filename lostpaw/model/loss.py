from typing import Optional
import torch
import torch.nn as nn
from torch import Tensor

class PetContrastiveLoss(nn.Module):
    def __init__(self, margin=1.25, eps=1e-8):
        super(PetContrastiveLoss, self).__init__()
        self.margin = margin
        self.eps = eps

    def forward(self, features: Tensor, labels: Tensor, distance: Optional[Tensor] = None) -> Tensor:
        """
        Takes as input a set feature vectors obtained by encoding two images,
        and a label that denotes whether the two images represent the same
        pet or not. Returns the contrastive loss for the two images.


        The contrastive loss is defined as follows:

        L(W, Y, X_1, X_2) = (1 - Y) * 1/2 * (D_W)^2 + (Y) * 1/2 {max(0, m - D_W )}^2

        where m > 0 is a margin (defines a radius around G_W), D_W is the euclidean
        distance between the two feature vectors, and Y is the label that denotes whether
        the two images are of the same pet or not.


        Based on the paper:
         Raia Hadsell, Sumit Chopra, and Yann LeCun. Dimensionality
         reduction by learning an invariant mapping. In CVPR, 2006

         https://ieeexplore.ieee.org/abstract/document/1640964

        Args:
            features: A tensor of shape (N, 2, D) where N is the batch size,
                      and D is the feature dimension.
            labels: A tensor of shape (N, 1) that denotes whether the two
                      images represent the same pet or not (N batches).
        """

        # Get the euclidean distance between the two feature vectors
        euclidean_distance = self.euclidean_distance(features) if distance is None else distance

        diff_pet = (1 - labels) * torch.pow(
            torch.clamp(self.margin - euclidean_distance, min=0.0), 2
        )
        same_pet = (labels) * torch.pow(euclidean_distance, 2)

        # Get the contrastive loss
        contrastive_loss = torch.mean(0.5 * (same_pet + diff_pet))

        return contrastive_loss

    def euclidean_distance(self, features: Tensor):
        """
        Computes the euclidean distance between the two feature vectors
        in the batch.

        Args:
            features: A tensor of shape (N, 2, D) where N is the batch size,
                      and D is the feature dimension.
        """

        # Get the first feature vector
        feature1 = features[:, 0, :]

        # Get the second feature vector
        feature2 = features[:, 1, :]

        # Compute the euclidean distance between the two feature vectors
        euclidean_distance = torch.sqrt(
            torch.sum(torch.pow(feature1 - feature2, 2), 1) + self.eps
        )

        return euclidean_distance
