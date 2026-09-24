# Flowchart SecretPic

## 1. Hide Message

```mermaid
flowchart TD

A([Start])
--> B[Select Image]

B
--> C{Format Valid?}

C -- No -->
D[Show Error]

D
--> Z([End])

C -- Yes -->
E[Validate Image Data]

E
--> F{Image Can Be Read?}

F -- No -->
G[Show Invalid Image Error]

G
--> Z

F -- Yes -->
H[Input Secret Message]

H
--> I[Input Stego-Key]

I
--> J[Encrypt Message with AES-GCM]

J
--> K[Calculate Image Capacity]

K
--> L{Payload <= Capacity?}

L -- No -->
M[Reject Payload]

M
--> Z

L -- Yes -->
N[Generate Pixel Positions from Stego-Key]

N
--> O[Build Header + Encrypted Payload]

O
--> P[Embed Payload using LSB]

P
--> Q[Generate Stego Image as PNG]

Q
--> R[Calculate MSE and PSNR]

R
--> S[Convert Stego Image to Base64]

S
--> T[Display Stego Image and Metrics]

T
--> U[Download Stego Image]

U
--> Z([End])
```

## 2. Extract Message

```mermaid
flowchart TD

A([Start])
--> B[Select Stego Image]

B
--> C{Format Valid?}

C -- No -->
D[Show Error]

D
--> Z([End])

C -- Yes -->
E[Validate Image Data]

E
--> F{Image Can Be Read?}

F -- No -->
G[Show Invalid Image Error]

G
--> Z

F -- Yes -->
H[Input Stego-Key]

H
--> I[Generate Same Pixel Positions]

I
--> J[Extract LSB Payload]

J
--> K[Read Payload Header]

K
--> L{Header Valid?}

L -- No -->
M[Extraction Failed]

M
--> Z

L -- Yes -->
N[Get Encrypted Payload]

N
--> O[AES-GCM Decryption]

O
--> P{Authentication Valid?}

P -- No -->
Q[Wrong Key or Modified Payload]

Q
--> Z

P -- Yes -->
R[Display Original Secret Message]

R
--> Z([End])
```

## 3. Alur Pengujian

```mermaid
flowchart TD

A([Start Testing])
--> B[Prepare Test Images]

B
--> C[Select Message Size]

C
--> D[Hide Message]

D
--> E[Generate Stego PNG]

E
--> F[Calculate MSE]

F
--> G[Calculate PSNR]

G
--> H[Compare Cover and Stego]

H
--> I[Extract Message]

I
--> J{Extraction Successful?}

J -- Yes -->
K[Record Successful Result]

J -- No -->
L[Record Failed Result]

K
--> M[Test Wrong Stego-Key]

L
--> M

M
--> N[Test JPEG Re-save]

N
--> O[Compare Histogram]

O
--> P[Test Enhanced LSB]

P
--> Q[Test 1-bit vs 2-bit LSB]

Q
--> R{All Test Cases Complete?}

R -- No -->
C

R -- Yes -->
S[Analyze Results]

S
--> T([End])
```

## 4. Format Gambar yang Didukung

SecretPic menerima file dengan ekstensi:

- `.png`
- `.bmp`
- `.jpg`
- `.jpeg`
- `.img`

### Catatan penting tentang `.img`

Ekstensi `.img` dapat digunakan oleh berbagai jenis file dan tidak selalu merupakan file gambar yang dapat dibaca oleh Pillow. Oleh karena itu, aplikasi harus melakukan validasi isi file, bukan hanya memeriksa ekstensi.

File akan diproses hanya jika Pillow berhasil membacanya sebagai citra.

## 5. Perubahan pada `app.py`

Gunakan daftar ekstensi berikut:

```python
ALLOWED = {"png", "bmp", "jpg", "jpeg", "img"}
```

Fungsi validasi ekstensi:

```python
def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED
    )
```

Karena `.img` tidak selalu merupakan format gambar standar, tambahkan validasi isi:

```python
from PIL import Image
import io

def valid_image_content(file_bytes):
    try:
        with Image.open(io.BytesIO(file_bytes)) as img:
            img.verify()
        return True
    except Exception:
        return False
```

Setelah file dibaca:

```python
original = image.read()

if not valid_image_content(original):
    flash(
        "File bukan gambar yang valid atau format gambar tidak didukung.",
        "error"
    )
    return redirect(url_for("hide"))
```

Lakukan validasi yang sama pada halaman `extract`.

## 6. Perubahan pada `hide.html`

Gunakan:

```html
<input
    type="file"
    name="image"
    accept=".png,.bmp,.jpg,.jpeg,.img"
    required
>
```

Keterangan:

```html
<p class="muted">
    Format yang didukung: PNG, BMP, JPG, JPEG, dan IMG.
    Hasil steganografi disimpan sebagai PNG agar data LSB tetap terjaga.
</p>
```

## 7. Perubahan pada `extract.html`

Gunakan:

```html
<input
    type="file"
    name="image"
    accept=".png,.bmp,.jpg,.jpeg,.img"
    required
>
```

Keterangan:

```html
<p class="muted">
    Format input yang diterima: PNG, BMP, JPG, JPEG, dan IMG.
    Stego image hasil proses utama disimpan sebagai PNG.
</p>
```

## 8. Konversi dan Output Stego

Input:

```text
PNG
BMP
JPG
JPEG
IMG (jika dapat dibaca sebagai citra)
```

Diproses menjadi:

```text
RGB Image
   |
   v
AES-GCM Encryption
   |
   v
LSB Embedding
   |
   v
Stego PNG
```

Output utama tetap **PNG** agar bit LSB tidak berubah akibat kompresi lossy seperti JPEG.

## 9. Ringkasan

Alur utama aplikasi:

```text
Upload Image
     |
     v
Validate Extension
     |
     v
Validate Image Content
     |
     v
Encrypt Secret Message
     |
     v
Check Capacity
     |
     v
Generate Pixel Positions
     |
     v
LSB Embedding
     |
     v
Stego PNG
     |
     +----> MSE
     |
     +----> PSNR
     |
     v
Preview + Download
```
