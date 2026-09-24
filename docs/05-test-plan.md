# Rencana Pengujian SecretPic

## 1. Tujuan Pengujian

Pengujian dilakukan untuk memastikan:
- fungsi enkripsi dan dekripsi berjalan dengan benar,
- pesan dapat disisipkan dan diekstraksi,
- stego-key yang benar dapat menghasilkan pesan asli,
- stego-key yang salah menyebabkan kegagalan,
- kualitas citra tetap terjaga setelah penyisipan,
- perubahan citra dapat diukur secara kuantitatif.

## 2. Dataset

Gunakan minimal 5 citra PNG atau BMP.

Contoh:

| No | Nama Citra | Format |
|---|---|---|
| 1 | image01 | PNG |
| 2 | image02 | PNG |
| 3 | image03 | PNG |
| 4 | image04 | BMP |
| 5 | image05 | PNG |

Gunakan citra yang dapat digunakan secara sah untuk eksperimen.

## 3. Variasi Ukuran Pesan

Minimal digunakan 3 ukuran pesan:

| Kategori | Ukuran |
|---|---:|
| Kecil | 1 KB |
| Sedang | 5 KB |
| Besar | 10 KB |

Dengan 5 citra dan 3 ukuran pesan diperoleh minimal:

5 x 3 = 15 kombinasi pengujian.

## 4. Pengujian Fungsional

### 4.1 Hide Message

Input:
- citra PNG/BMP,
- pesan rahasia,
- stego-key.

Expected result:
- proses berhasil,
- stego image terbentuk,
- MSE dan PSNR ditampilkan.

### 4.2 Extract Message

Input:
- stego image,
- stego-key yang benar.

Expected result:
- pesan asli berhasil dikembalikan.

### 4.3 Wrong Key

Input:
- stego image,
- stego-key yang salah.

Expected result:
- ekstraksi/dekripsi gagal.

### 4.4 Modified Payload

Payload atau isi stego image diubah.

Expected result:
- verifikasi AES-GCM gagal atau pesan tidak dapat
  didekripsi dengan benar.

## 5. Pengujian MSE

Mean Squared Error digunakan untuk mengukur rata-rata kuadrat
perbedaan antara citra asli dan citra stego.

Catat nilai MSE untuk setiap kombinasi citra dan ukuran pesan.

## 6. Pengujian PSNR

Peak Signal-to-Noise Ratio digunakan untuk mengukur kualitas citra
hasil steganografi.

Catat nilai PSNR untuk setiap kombinasi citra dan ukuran pesan.

## 7. Pengujian Histogram

Bandingkan histogram:
- citra cover,
- citra stego.

Tujuannya mengamati perubahan distribusi pixel setelah proses
penyisipan.

## 8. Pengujian Enhanced LSB

Tampilkan bidang LSB dari citra cover dan citra stego untuk
mengamati perubahan bit least significant bit.

## 9. Pengujian JPEG

Langkah:
1. Buat stego image dari PNG.
2. Simpan ulang atau konversi stego image menjadi JPEG.
3. Coba lakukan ekstraksi pesan.

Expected result:
- data LSB dapat mengalami perubahan,
- ekstraksi dapat gagal atau payload tidak lagi valid.

## 10. Perbandingan 1-bit dan 2-bit LSB

Bandingkan:
- kapasitas pesan,
- MSE,
- PSNR,
- keberhasilan ekstraksi.

Contoh tabel:

| Metode | Kapasitas | MSE | PSNR | Extraction |
|---|---:|---:|---:|---|
| 1-bit LSB | ... | ... | ... | ... |
| 2-bit LSB | ... | ... | ... | ... |

Data pada tabel harus diisi berdasarkan hasil eksperimen aktual.

## 11. Unit Test

Minimal mencakup:
- encryption/decryption,
- wrong key,
- LSB embedding/extraction,
- capacity,
- MSE/PSNR.

Jangan mengisi hasil test secara manual. Jalankan test dan catat
hasil aktual.

## 12. Format Data Pengujian

Gunakan tabel XLSX dengan kolom:

| Image | Width | Height | Message Size | Bits/Channel | MSE | PSNR | Extraction | JPEG Test |
|---|---:|---:|---:|---:|---:|---:|---|---|
| ... | ... | ... | ... | ... | ... | ... | ... | ... |

## 13. Kriteria Keberhasilan

Pengujian dinyatakan berhasil apabila:
1. pesan dapat disisipkan dengan benar,
2. pesan dapat diekstraksi kembali dengan key yang benar,
3. key yang salah ditolak,
4. perubahan kualitas citra dapat diukur,
5. seluruh pengujian wajib terdokumentasi,
6. hasil analisis berasal dari eksperimen aktual.