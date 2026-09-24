import hashlib
import struct
from PIL import Image
import io

MAGIC = b"LSB1"
HEADER_SIZE = 8  # magic (4) + payload length (4)

def _image_from_bytes(data: bytes):
    return Image.open(io.BytesIO(data)).convert("RGB")

def _image_to_png_bytes(img: Image.Image) -> bytes:
    out = io.BytesIO()
    img.save(out, format="PNG")
    return out.getvalue()

def _positions(total_channels: int, key: str):
    # Deterministic Fisher-Yates shuffle using SHA-256 based PRNG.
    # This is intended for an academic demonstration, not production cryptography.
    seed = hashlib.sha256(key.encode("utf-8")).digest()
    state = int.from_bytes(seed, "big")
    positions = list(range(total_channels))
    for i in range(total_channels - 1, 0, -1):
        state = (1103515245 * state + 12345) & ((1 << 256) - 1)
        j = state % (i + 1)
        positions[i], positions[j] = positions[j], positions[i]
    return positions

def capacity_bytes(image_bytes: bytes, bits_per_channel: int = 1) -> int:
    if bits_per_channel not in (1, 2):
        raise ValueError("bits_per_channel harus 1 atau 2.")
    img = _image_from_bytes(image_bytes)
    channels = img.width * img.height * 3
    total_bits = channels * bits_per_channel
    return max(0, total_bits // 8 - HEADER_SIZE)

def _payload_to_bits(payload: bytes):
    for byte in payload:
        for shift in range(7, -1, -1):
            yield (byte >> shift) & 1

def embed_payload(image_bytes: bytes, payload: bytes, key: str, bits_per_channel: int = 1) -> bytes:
    if bits_per_channel not in (1, 2):
        raise ValueError("bits_per_channel harus 1 atau 2.")
    img = _image_from_bytes(image_bytes)
    pixels = list(img.getdata())
    channels = len(pixels) * 3
    max_payload = channels * bits_per_channel // 8 - HEADER_SIZE
    if len(payload) > max_payload:
        raise ValueError(f"Pesan terlalu besar. Kapasitas maksimum sekitar {max_payload} byte.")

    packet = MAGIC + struct.pack(">I", len(payload)) + payload
    bits = list(_payload_to_bits(packet))
    if bits_per_channel == 2:
        # Pack bits into 2-bit chunks for higher capacity.
        values = []
        for i in range(0, len(bits), 2):
            a = bits[i]
            b = bits[i+1] if i+1 < len(bits) else 0
            values.append((a << 1) | b)
        units = values
    else:
        units = bits

    flat = [c for p in pixels for c in p]
    positions = _positions(channels, key)
    mask = (1 << bits_per_channel) - 1

    for idx, value in enumerate(units):
        pos = positions[idx]
        flat[pos] = (flat[pos] & ~mask) | value

    new_pixels = [tuple(flat[i:i+3]) for i in range(0, len(flat), 3)]
    out = Image.new("RGB", img.size)
    out.putdata(new_pixels)
    return _image_to_png_bytes(out)

def extract_payload(image_bytes: bytes, key: str, bits_per_channel: int = 1) -> bytes:
    if bits_per_channel not in (1, 2):
        raise ValueError("bits_per_channel harus 1 atau 2.")
    img = _image_from_bytes(image_bytes)
    pixels = list(img.getdata())
    channels = len(pixels) * 3
    flat = [c for p in pixels for c in p]
    positions = _positions(channels, key)
    mask = (1 << bits_per_channel) - 1

    # Read enough units for header.
    needed_header_bits = HEADER_SIZE * 8
    if bits_per_channel == 1:
        header_units = needed_header_bits
        units = [(flat[positions[i]] & mask) for i in range(header_units)]
        bits = units
    else:
        header_units = needed_header_bits // 2
        values = [(flat[positions[i]] & mask) for i in range(header_units)]
        bits = []
        for value in values:
            bits.extend([(value >> 1) & 1, value & 1])

    header = bytearray()
    for i in range(0, len(bits), 8):
        byte = 0
        for bit in bits[i:i+8]:
            byte = (byte << 1) | bit
        header.append(byte)

    if bytes(header[:4]) != MAGIC:
        raise ValueError("Header tidak ditemukan. Key mungkin salah atau file bukan stego image.")
    payload_len = struct.unpack(">I", bytes(header[4:8]))[0]
    total_bits = (HEADER_SIZE + payload_len) * 8
    if bits_per_channel == 1:
        units_needed = total_bits
    else:
        units_needed = (total_bits + 1) // 2

    if units_needed > channels:
        raise ValueError("Panjang payload tidak valid.")

    if bits_per_channel == 1:
        all_bits = [(flat[positions[i]] & mask) for i in range(units_needed)]
    else:
        all_bits = []
        for i in range(units_needed):
            value = flat[positions[i]] & mask
            all_bits.extend([(value >> 1) & 1, value & 1])
        all_bits = all_bits[:total_bits]

    data = bytearray()
    for i in range(0, len(all_bits), 8):
        byte = 0
        for bit in all_bits[i:i+8]:
            byte = (byte << 1) | bit
        data.append(byte)

    return bytes(data[HEADER_SIZE:])
