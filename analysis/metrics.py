import io
import math
import numpy as np
from PIL import Image

def _array(data: bytes):
    return np.asarray(Image.open(io.BytesIO(data)).convert("RGB"), dtype=np.float64)

def mse(original: bytes, modified: bytes) -> float:
    a = _array(original)
    b = _array(modified)
    return float(np.mean((a - b) ** 2))

def psnr(original: bytes, modified: bytes) -> float:
    value = mse(original, modified)
    if value == 0:
        return float("inf")
    return float(10 * math.log10((255 ** 2) / value))
