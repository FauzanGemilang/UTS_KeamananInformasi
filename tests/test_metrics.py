from PIL import Image
import io
from analysis.metrics import mse, psnr

def image_bytes(color):
    img = Image.new("RGB", (8, 8), color)
    out = io.BytesIO()
    img.save(out, format="PNG")
    return out.getvalue()

def test_metrics_identical():
    a = image_bytes((10, 20, 30))
    assert mse(a, a) == 0
    assert psnr(a, a) == float("inf")
