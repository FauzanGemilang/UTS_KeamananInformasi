from flask import Flask, render_template, request, flash, redirect, url_for
from werkzeug.utils import secure_filename
import base64
import os

from crypto.encryption import encrypt_message, decrypt_message
from steganography.lsb import embed_payload, extract_payload, capacity_bytes
from analysis.metrics import mse, psnr


# =========================================================
# FLASK CONFIGURATION
# =========================================================

app = Flask(
    __name__,
    static_folder="public",
    static_url_path=""
)

# saat deployment, akan gunakan environment variable.
# Saat lokal, akan memakai fallback ini.
app.secret_key = os.environ.get(
    "SECRET_KEY",
    "secretpic-development-key"
)

# Format gambar yang diperbolehkan
ALLOWED = {"png", "bmp"}

# Batas upload untuk menghindari request terlalu besar.
# Disarankan tetap menggunakan gambar PNG/BMP berukuran wajar
# saat deployment di Vercel.
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024


# =========================================================
# HELPER FUNCTION
# =========================================================

def allowed_file(filename):
    """
    Mengecek apakah file memiliki ekstensi yang diperbolehkan.
    """
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED
    )


# =========================================================
# HOME
# =========================================================

@app.route("/")
def index():
    return render_template("index.html")


# =========================================================
# HIDE MESSAGE
# =========================================================

@app.route("/hide", methods=["GET", "POST"])
def hide():
    result = None

    if request.method == "POST":

        # Ambil data dari form
        image = request.files.get("image")
        message = request.form.get("message", "")
        key = request.form.get("key", "")

        # -------------------------------------------------
        # VALIDATION
        # -------------------------------------------------

        if not image or not image.filename:
            flash(
                "Pilih gambar PNG atau BMP.",
                "error"
            )
            return redirect(url_for("hide"))

        if not allowed_file(image.filename):
            flash(
                "Format gambar harus PNG atau BMP.",
                "error"
            )
            return redirect(url_for("hide"))

        if not message.strip():
            flash(
                "Pesan rahasia wajib diisi.",
                "error"
            )
            return redirect(url_for("hide"))

        if not key:
            flash(
                "Stego-key wajib diisi.",
                "error"
            )
            return redirect(url_for("hide"))

        # -------------------------------------------------
        # PROCESSING
        # -------------------------------------------------

        try:
            # Membaca gambar asli
            original = image.read()

            # Enkripsi pesan
            encrypted = encrypt_message(
                message,
                key
            )

            # Sisipkan payload terenkripsi
            # ke dalam gambar menggunakan LSB
            stego = embed_payload(
                original,
                encrypted,
                key
            )

            # -------------------------------------------------
            # IMAGE QUALITY METRICS
            # -------------------------------------------------

            original_mse = mse(
                original,
                stego
            )

            original_psnr = psnr(
                original,
                stego
            )

            # Kapasitas maksimum gambar
            cap = capacity_bytes(
                original
            )

            # -------------------------------------------------
            # CONVERT STEGO IMAGE TO BASE64
            # -------------------------------------------------

            image_b64 = base64.b64encode(
                stego
            ).decode("utf-8")

            # Nama file hasil
            original_name = image.filename.rsplit(
                ".",
                1
            )[0]

            filename = (
                secure_filename(original_name)
                + "_stego.png"
            )

            # -------------------------------------------------
            # RESULT
            # -------------------------------------------------

            result = {
                "image_b64": image_b64,
                "filename": filename,
                "mse": original_mse,
                "psnr": original_psnr,
                "capacity": cap,
                "message_size": len(encrypted),
            }

        except ValueError as exc:
            flash(
                str(exc),
                "error"
            )

        except Exception as exc:
            print("Hide error:", exc)

            flash(
                "Terjadi kesalahan saat proses penyisipan.",
                "error"
            )

    return render_template(
        "hide.html",
        result=result
    )


# =========================================================
# EXTRACT MESSAGE
# =========================================================

@app.route("/extract", methods=["GET", "POST"])
def extract():
    extracted = None

    if request.method == "POST":

        # Ambil data form
        image = request.files.get("image")
        key = request.form.get("key", "")

        # -------------------------------------------------
        # VALIDATION
        # -------------------------------------------------

        if not image or not image.filename:
            flash(
                "Pilih gambar stego.",
                "error"
            )
            return redirect(url_for("extract"))

        if not allowed_file(image.filename):
            flash(
                "Format gambar harus PNG atau BMP.",
                "error"
            )
            return redirect(url_for("extract"))

        if not key:
            flash(
                "Stego-key wajib diisi.",
                "error"
            )
            return redirect(url_for("extract"))

        # -------------------------------------------------
        # EXTRACTION
        # -------------------------------------------------

        try:

            # Membaca file stego
            image_bytes = image.read()

            # Ekstraksi payload
            encrypted = extract_payload(
                image_bytes,
                key
            )

            # Dekripsi pesan
            extracted = decrypt_message(
                encrypted,
                key
            )

        except ValueError as exc:

            flash(
                str(exc),
                "error"
            )

        except Exception as exc:

            print(
                "Extract error:",
                exc
            )

            flash(
                "Ekstraksi gagal. "
                "Periksa gambar dan stego-key.",
                "error"
            )

    return render_template(
        "extract.html",
        extracted=extracted
    )


# =========================================================
# ANALYSIS PAGE
# =========================================================

@app.route("/analysis")
def analysis():
    return render_template(
        "analysis.html"
    )


# =========================================================
# ABOUT PAGE
# =========================================================

@app.route("/about")
def about():
    return render_template(
        "about.html"
    )


# =========================================================
# RUN LOCAL SERVER
# =========================================================

if __name__ == "__main__":
    app.run(
        debug=True
    )