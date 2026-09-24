# SecretPic

Aplikasi web akademik untuk demonstrasi kombinasi enkripsi pesan dan steganografi LSB.

## Fitur
- Enkripsi pesan AES-256-GCM.
- Derivasi kunci dengan PBKDF2-HMAC-SHA256 + salt acak.
- Nonce acak untuk setiap enkripsi.
- LSB embedding pada PNG/BMP.
- PRNG deterministik berbasis stego-key untuk pengacakan posisi channel.
- Header magic + panjang payload.
- Ekstraksi dan dekripsi.
- Perhitungan MSE dan PSNR.
- Fondasi pengujian 1-bit dan 2-bit LSB.

## Instalasi

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
python app.py
```

Buka `http://127.0.0.1:5000`.

## Test

```bash
pytest -q
```

## Catatan keamanan
Kode ini dibuat untuk proyek pembelajaran. Secret key Flask di `app.py` harus dipindahkan ke environment variable untuk deployment nyata. Jangan memasukkan password/kunci nyata ke repository.

## Struktur
- `crypto/` enkripsi dan key derivation
- `steganography/` LSB embedding/extraction
- `analysis/` metrik citra
- `templates/` halaman web
- `static/` CSS
- `tests/` unit test
