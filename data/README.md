# Data Pengujian SecretPic

Folder `data` digunakan untuk menyimpan data yang diperlukan dalam
pengujian aplikasi **SecretPic — Secure Image Steganography**.

Data pengujian digunakan untuk menguji proses penyisipan dan ekstraksi
pesan, mengukur kualitas citra setelah proses steganografi, serta
menganalisis pengaruh ukuran pesan dan kondisi tertentu terhadap hasil
steganografi.

---

## 1. Tujuan Pengujian

Data pada folder ini digunakan untuk:

- menguji proses penyisipan pesan rahasia ke dalam citra;
- menguji proses ekstraksi pesan dari stego image;
- menguji penggunaan stego-key yang benar;
- menguji penggunaan stego-key yang salah;
- mengukur Mean Squared Error (MSE);
- mengukur Peak Signal-to-Noise Ratio (PSNR);
- membandingkan citra cover dan stego;
- membandingkan histogram citra;
- melakukan analisis enhanced LSB;
- menguji kerapuhan steganografi terhadap penyimpanan ulang JPEG;
- membandingkan metode 1-bit LSB dan 2-bit LSB.

---

## 2. Format Citra yang Digunakan

Aplikasi SecretPic menerima citra dengan format:

- PNG (`.png`)
- BMP (`.bmp`)
- JPG (`.jpg`)
- JPEG (`.jpeg`)

### Catatan

PNG dan BMP digunakan sebagai format utama untuk proses steganografi
LSB karena nilai pixel dapat dipertahankan dengan baik.

JPG dan JPEG dapat digunakan sebagai input serta digunakan dalam
pengujian kerapuhan. Kompresi JPEG dapat mengubah nilai pixel sehingga
dapat memengaruhi payload LSB.

Hasil steganografi utama disimpan dalam format PNG agar data LSB tetap
dapat digunakan untuk proses ekstraksi.

---

## 3. Citra Pengujian

Pengujian menggunakan minimal **5 citra** yang dapat digunakan secara
sah untuk keperluan akademik.

Contoh struktur:

```text
data/
└── images/
    ├── image01.png
    ├── image02.jpg
    ├── image03.bmp
    ├── image04.jpeg
    └── image05.png