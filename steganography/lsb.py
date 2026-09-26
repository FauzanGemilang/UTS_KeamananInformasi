import hashlib
import io
import math
import struct

from PIL import Image


# =========================================================
# CONFIGURATION
# =========================================================

MAGIC = b"LSB1"

# 4 byte MAGIC + 4 byte panjang payload
HEADER_SIZE = 8


# =========================================================
# IMAGE HANDLING
# =========================================================

def _image_from_bytes(data: bytes) -> Image.Image:
    """
    Membuka gambar dari bytes dan mengubahnya menjadi RGB.
    """

    try:
        return Image.open(
            io.BytesIO(data)
        ).convert("RGB")

    except Exception as exc:
        raise ValueError(
            "File bukan gambar yang valid "
            "atau format gambar tidak didukung."
        ) from exc


def _image_to_png_bytes(img: Image.Image) -> bytes:
    """
    Mengubah image menjadi bytes PNG.
    """

    output = io.BytesIO()

    img.save(
        output,
        format="PNG"
    )

    return output.getvalue()


def _flattened_channels(img: Image.Image) -> bytearray:
    """
    Mengambil seluruh channel RGB secara langsung sebagai bytearray.

    Karena gambar sudah dipastikan RGB:
        panjang data = width × height × 3

    Pendekatan ini menghindari penggunaan getdata()
    yang deprecated pada Pillow versi baru.
    """

    return bytearray(
        img.tobytes()
    )


# =========================================================
# DETERMINISTIC POSITION GENERATOR
# =========================================================

def _position_parameters(
    total_channels: int,
    key: str
):
    """
    Membuat parameter posisi deterministik
    berdasarkan stego-key.

    Tidak membuat list posisi seluruh gambar.
    """

    if total_channels <= 0:
        raise ValueError(
            "Gambar tidak memiliki channel."
        )

    seed = hashlib.sha256(
        key.encode("utf-8")
    ).digest()

    start = (
        int.from_bytes(
            seed[:8],
            byteorder="big"
        )
        % total_channels
    )

    step = (
        int.from_bytes(
            seed[8:16],
            byteorder="big"
        )
        % total_channels
    )

    if step == 0:
        step = 1

    # Pastikan step relatif prima dengan
    # total channel agar seluruh posisi
    # dapat dilewati tanpa pengulangan.
    while math.gcd(
        step,
        total_channels
    ) != 1:

        step += 1

        if step >= total_channels:
            step = 1

    return start, step


def _position(
    index: int,
    total_channels: int,
    start: int,
    step: int
) -> int:
    """
    Menghasilkan posisi channel.
    """

    return (
        start
        + (index * step)
    ) % total_channels


# =========================================================
# CAPACITY
# =========================================================

def capacity_bytes(
    image_bytes: bytes,
    bits_per_channel: int = 1
) -> int:
    """
    Menghitung kapasitas payload maksimum dalam byte.

    bits_per_channel:
        1 -> satu bit per channel
        2 -> dua bit per channel
    """

    if bits_per_channel not in (1, 2):
        raise ValueError(
            "bits_per_channel harus 1 atau 2."
        )

    img = _image_from_bytes(
        image_bytes
    )

    total_channels = (
        img.width
        * img.height
        * 3
    )

    total_bits = (
        total_channels
        * bits_per_channel
    )

    capacity = (
        total_bits // 8
        - HEADER_SIZE
    )

    return max(
        0,
        capacity
    )


# =========================================================
# BITS <-> BYTES
# =========================================================

def _payload_to_bits(
    payload: bytes
):
    """
    Mengubah bytes menjadi bit.
    """

    for byte in payload:

        for shift in range(
            7,
            -1,
            -1
        ):

            yield (
                byte >> shift
            ) & 1


def _bits_to_bytes(
    bits
) -> bytes:
    """
    Mengubah bit menjadi bytes.
    """

    output = bytearray()

    for i in range(
        0,
        len(bits),
        8
    ):

        byte = 0

        for bit in bits[
            i:i + 8
        ]:

            byte = (
                byte << 1
            ) | bit

        output.append(
            byte
        )

    return bytes(output)


# =========================================================
# EMBED PAYLOAD
# =========================================================

def embed_payload(
    image_bytes: bytes,
    payload: bytes,
    key: str,
    bits_per_channel: int = 1
) -> bytes:
    """
    Menyisipkan payload ke dalam gambar menggunakan LSB.
    """

    if bits_per_channel not in (1, 2):
        raise ValueError(
            "bits_per_channel harus 1 atau 2."
        )

    if not key:
        raise ValueError(
            "Stego-key tidak boleh kosong."
        )

    # -----------------------------------------------------
    # Buka gambar sebagai RGB
    # -----------------------------------------------------

    img = _image_from_bytes(
        image_bytes
    )

    total_channels = (
        img.width
        * img.height
        * 3
    )

    # -----------------------------------------------------
    # Hitung kapasitas
    # -----------------------------------------------------

    max_payload = (
        total_channels
        * bits_per_channel
        // 8
        - HEADER_SIZE
    )

    if len(payload) > max_payload:
        raise ValueError(
            "Pesan terlalu besar. "
            f"Kapasitas maksimum sekitar "
            f"{max_payload} byte."
        )

    # -----------------------------------------------------
    # Header + payload
    # -----------------------------------------------------

    packet = (
        MAGIC
        + struct.pack(
            ">I",
            len(payload)
        )
        + payload
    )

    # -----------------------------------------------------
    # Convert packet -> bits
    # -----------------------------------------------------

    bits = list(
        _payload_to_bits(
            packet
        )
    )

    # -----------------------------------------------------
    # Bentuk unit 1-bit atau 2-bit
    # -----------------------------------------------------

    if bits_per_channel == 1:

        units = bits

    else:

        units = []

        for i in range(
            0,
            len(bits),
            2
        ):

            first = bits[i]

            second = (
                bits[i + 1]
                if i + 1 < len(bits)
                else 0
            )

            value = (
                (first << 1)
                | second
            )

            units.append(
                value
            )

    # -----------------------------------------------------
    # Generate posisi
    # -----------------------------------------------------

    start, step = _position_parameters(
        total_channels,
        key
    )

    # -----------------------------------------------------
    # Ambil data RGB sebagai bytearray
    # -----------------------------------------------------

    flat = _flattened_channels(
        img
    )

    # Pastikan panjang benar
    if len(flat) != total_channels:
        raise ValueError(
            "Ukuran data pixel tidak sesuai "
            "dengan dimensi gambar."
        )

    # -----------------------------------------------------
    # Mask
    # -----------------------------------------------------

    mask = (
        (1 << bits_per_channel)
        - 1
    )

    # -----------------------------------------------------
    # Embed
    # -----------------------------------------------------

    for index, value in enumerate(
        units
    ):

        position = _position(
            index,
            total_channels,
            start,
            step
        )

        flat[position] = (
            (
                flat[position]
                & ~mask
            )
            | value
        )

    # -----------------------------------------------------
    # Build new image
    # -----------------------------------------------------

    output = Image.frombytes(
        "RGB",
        img.size,
        bytes(flat)
    )

    # -----------------------------------------------------
    # Output always PNG
    # -----------------------------------------------------

    return _image_to_png_bytes(
        output
    )


# =========================================================
# EXTRACT BITS
# =========================================================

def _extract_bits(
    flat: bytearray,
    total_channels: int,
    start: int,
    step: int,
    count_units: int,
    bits_per_channel: int
):
    """
    Mengambil unit dari channel yang telah disisipi.
    """

    mask = (
        (1 << bits_per_channel)
        - 1
    )

    bits = []

    for index in range(
        count_units
    ):

        position = _position(
            index,
            total_channels,
            start,
            step
        )

        value = (
            flat[position]
            & mask
        )

        if bits_per_channel == 1:

            bits.append(
                value
            )

        else:

            bits.append(
                (value >> 1) & 1
            )

            bits.append(
                value & 1
            )

    return bits


# =========================================================
# READ HEADER
# =========================================================

def _read_header(
    flat: bytearray,
    total_channels: int,
    start: int,
    step: int,
    bits_per_channel: int
) -> bytes:
    """
    Membaca header:
        MAGIC + payload length
    """

    header_bits = (
        HEADER_SIZE * 8
    )

    if bits_per_channel == 1:

        required_units = header_bits

    else:

        required_units = (
            header_bits // 2
        )

    bits = _extract_bits(
        flat,
        total_channels,
        start,
        step,
        required_units,
        bits_per_channel
    )

    bits = bits[
        :header_bits
    ]

    return _bits_to_bytes(
        bits
    )


# =========================================================
# EXTRACT PAYLOAD
# =========================================================

def extract_payload(
    image_bytes: bytes,
    key: str,
    bits_per_channel: int = 1
) -> bytes:
    """
    Mengekstraksi payload dari stego image.
    """

    if bits_per_channel not in (1, 2):
        raise ValueError(
            "bits_per_channel harus 1 atau 2."
        )

    if not key:
        raise ValueError(
            "Stego-key tidak boleh kosong."
        )

    # -----------------------------------------------------
    # Buka image
    # -----------------------------------------------------

    img = _image_from_bytes(
        image_bytes
    )

    total_channels = (
        img.width
        * img.height
        * 3
    )

    # -----------------------------------------------------
    # Ambil pixel data
    # -----------------------------------------------------

    flat = _flattened_channels(
        img
    )

    if len(flat) != total_channels:
        raise ValueError(
            "Ukuran data pixel tidak sesuai "
            "dengan dimensi gambar."
        )

    # -----------------------------------------------------
    # Generate posisi yang sama
    # -----------------------------------------------------

    start, step = _position_parameters(
        total_channels,
        key
    )

    # -----------------------------------------------------
    # Read header
    # -----------------------------------------------------

    header = _read_header(
        flat,
        total_channels,
        start,
        step,
        bits_per_channel
    )

    if len(header) < HEADER_SIZE:
        raise ValueError(
            "Header payload tidak valid."
        )

    # -----------------------------------------------------
    # Validate MAGIC
    # -----------------------------------------------------

    if header[:4] != MAGIC:

        raise ValueError(
            "Header tidak ditemukan. "
            "Stego-key mungkin salah atau "
            "file bukan stego image."
        )

    # -----------------------------------------------------
    # Payload length
    # -----------------------------------------------------

    payload_length = struct.unpack(
        ">I",
        header[4:8]
    )[0]

    # -----------------------------------------------------
    # Validate payload length
    # -----------------------------------------------------

    max_payload = capacity_bytes(
        image_bytes,
        bits_per_channel
    )

    if payload_length > max_payload:
        raise ValueError(
            "Panjang payload tidak valid."
        )

    # -----------------------------------------------------
    # Total bits
    # -----------------------------------------------------

    total_payload_bytes = (
        HEADER_SIZE
        + payload_length
    )

    total_bits = (
        total_payload_bytes
        * 8
    )

    if bits_per_channel == 1:

        units_needed = total_bits

    else:

        units_needed = (
            total_bits + 1
        ) // 2

    # -----------------------------------------------------
    # Extract
    # -----------------------------------------------------

    bits = _extract_bits(
        flat,
        total_channels,
        start,
        step,
        units_needed,
        bits_per_channel
    )

    bits = bits[
        :total_bits
    ]

    data = _bits_to_bytes(
        bits
    )

    if len(data) < HEADER_SIZE:
        raise ValueError(
            "Payload tidak lengkap."
        )

    return data[
        HEADER_SIZE:
    ]