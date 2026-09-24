from PIL import Image
import io
from crypto.encryption import encrypt_message, decrypt_message
from steganography.lsb import embed_payload, extract_payload, capacity_bytes

def image_bytes(size=(64, 64)):
    img = Image.new("RGB", size, (120, 130, 140))
    out = io.BytesIO()
    img.save(out, format="PNG")
    return out.getvalue()

def test_lsb_embed_extract():
    original = image_bytes()
    payload = encrypt_message("hello world", "secret")
    stego = embed_payload(original, payload, "secret")
    extracted = extract_payload(stego, "secret")
    assert decrypt_message(extracted, "secret") == "hello world"

def test_capacity_positive():
    assert capacity_bytes(image_bytes()) > 0

def test_wrong_stego_key():
    original = image_bytes()
    payload = encrypt_message("hello", "secret")
    stego = embed_payload(original, payload, "secret")
    try:
        extract_payload(stego, "wrong")
        assert False
    except ValueError:
        assert True
