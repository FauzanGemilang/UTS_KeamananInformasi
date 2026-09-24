# Arsitektur Sistem SecretPic

## 1. Gambaran Arsitektur

SecretPic merupakan aplikasi web berbasis Flask yang menggabungkan modul
kriptografi, steganografi, dan analisis kualitas citra.

Arsitektur sistem terdiri dari beberapa komponen utama:

```text
                    USER / BROWSER
                         |
                         v
                +------------------+
                |   Flask Web App  |
                +--------+---------+
                         |
          +--------------+--------------+
          |              |              |
          v              v              v
   +-------------+ +-------------+ +-------------+
   | Crypto      | | Steganography| | Analysis   |
   | Module      | | Module       | | Module     |
   +-------------+ +-------------+ +-------------+
   | PBKDF2      | | Header       | | MSE         |
   | AES-GCM     | | PRNG         | | PSNR        |
   | Encryption  | | LSB Embed    | |             |
   | Decryption  | | LSB Extract  | |             |
   +-------------+ +-------------+ +-------------+
          |              |              |
          +--------------+--------------+
                         |
                         v
                +------------------+
                |   Result / UI    |
                +------------------+
                         |
                         v
                  USER / BROWSER