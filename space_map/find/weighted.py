"""Multi-channel weighted finder for affine-matrix selection.

Feature extraction / matching runs on the *density* channel only (unchanged).
When ranking candidate affine matrices, however, we score the alignment across
density **and** the auxiliary point-cloud channels (expanded cell types, genes),
combining their per-channel overlap with cell-count-based weights.

The density channel carries a fixed base weight; the remaining weight budget is
split among the auxiliary channels in proportion to their product counts.
"""
from __future__ import annotations

import numpy as np
import space_map


class WeightedFinder(space_map.AffineFinder):
    def __init__(self, base_finder=None, aux_pairs=None,
                 density_base_weight=0.5):
        """
        base_finder: per-channel scorer (defaults to the Dice finder). Its
            ``err`` convention is preserved (lower = better; Dice finders return
            the negated overlap).
        aux_pairs: list of ``(imgI_k, imgJ_raw_k, n_points_k)`` for each auxiliary
            channel. ``imgJ_raw_k`` is the *unwarped* moving image; it is warped
            by the current candidate transform at score time.
        density_base_weight: fixed weight given to the density channel; the rest
            (``1 - w``) is distributed across aux channels by product count.
        """
        super().__init__("WeightedFinder")
        self.base = base_finder if base_finder is not None else space_map.find.default()
        self.aux_pairs = aux_pairs or []
        self.density_base_weight = float(density_base_weight)
        self._H = np.eye(3)
        self._weights = self._compute_weights()

    def _compute_weights(self):
        """Density fixed base weight; aux channels share (1 - base) by count."""
        wd = self.density_base_weight
        total = float(sum(max(0, n) for _, _, n in self.aux_pairs))
        weights = []
        for _, _, n in self.aux_pairs:
            if total > 0:
                weights.append((1.0 - wd) * (max(0, n) / total))
            else:
                weights.append(0.0)
        return weights

    def set_transform(self, H):
        """Record the cumulative candidate transform used to warp aux J images."""
        self._H = np.eye(3) if H is None else np.asarray(H, dtype=np.float64)

    def err(self, imgI, imgJ):
        # Density term: score the (already-warped) density images directly.
        score = self.density_base_weight * self.base.err(imgI, imgJ)
        # Auxiliary terms: warp each moving aux image by the current transform.
        for (auxI, auxJ_raw, _), w in zip(self.aux_pairs, self._weights):
            if w <= 0:
                continue
            auxJ = space_map.he_img.rotate_imgH(auxJ_raw, self._H)
            score += w * self.base.err(auxI, auxJ)
        return score

    def copy(self):
        f = WeightedFinder(self.base, self.aux_pairs, self.density_base_weight)
        f.set_transform(self._H)
        return f
