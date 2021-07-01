from typing import Tuple

import numpy as np


class Mask:
    def __init__(self, string: str):
        split = [int(s) for s in string.split(",")]
        if len(split) != 4:
            raise ValueError("Mask expects a comma-separated list for 4 integers")

        self.x1 = min(split[:2])
        self.x2 = max(split[:2])
        self.y1 = min(split[2:])
        self.y2 = max(split[2:])

    def as_array(self, shape: Tuple[int, int]) -> np.ndarray:
        mask = np.zeros(shape, np.uint8)
        mask.fill(255)
        mask[self.y1 : self.y2, self.x1 : self.x2] = 0
        return mask

    def __str__(self):
        return f"Mask(x=[{self.x1}, {self.x2}], y=[{self.y1}, {self.y2}])"

    def __repr__(self):
        return self.__str__()
