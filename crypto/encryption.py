import base64
import hashlib
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

SALT_SIZE = 16
NONCE_SIZE = 12
KEY_SIZE = 32
ITERATIONS = 600_000
MAGIC = b"SP01"

def derive_key(password: str, salt: bytes) -> bytes:
    if not password:
        raise ValueError("Password/key tidak boleh kosong.")
    return hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        ITERATIONS,
        dklen=KEY_SIZE,
    )

def encrypt_message(message: str, password: str) -> bytes:
    if not message:
        raise ValueError("Pesan tidak boleh kosong.")
    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)
    key = derive_key(password, salt)
    ciphertext = AESGCM(key).encrypt(nonce, message.encode("utf-8"), None)
    return MAGIC + salt + nonce + ciphertext

def decrypt_message(payload: bytes, password: str) -> str:
    if len(payload) < len(MAGIC) + SALT_SIZE + NONCE_SIZE + 16:
        raise ValueError("Payload tidak valid.")
    if payload[:len(MAGIC)] != MAGIC:
        raise ValueError("Format payload tidak dikenali.")
    offset = len(MAGIC)
    salt = payload[offset:offset+SALT_SIZE]
    offset += SALT_SIZE
    nonce = payload[offset:offset+NONCE_SIZE]
    offset += NONCE_SIZE
    ciphertext = payload[offset:]
    key = derive_key(password, salt)
    try:
        plaintext = AESGCM(key).decrypt(nonce, ciphertext, None)
    except Exception as exc:
        raise ValueError("Stego-key salah atau payload telah diubah.") from exc
    return plaintext.decode("utf-8")
