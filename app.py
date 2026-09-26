import os
import base64
import io

from flask import (
    Flask,
    render_template,
    request,
    flash,
    redirect,
    url_for,
)
from werkzeug.utils import secure_filename
from PIL import Image, UnidentifiedImageError

from crypto.encryption import encrypt_message, decrypt_message
from steganography.lsb import (
    embed_payload,
    extract_payload,
    capacity_bytes,
)
from analysis.metrics import mse, psnr


app = Flask(__name__, static_folder="public", static_url_path="")

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "secretpic-development-key"
)

MAX_UPLOAD_MB = int(os.environ.get("MAX_UPLOAD_MB", "3"))
MAX_IMAGE_PIXELS = 12_000_000

app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024

ALLOWED_EXTENSIONS = {"png", "bmp", "jpg", "jpeg"}


def allowed_file(filename):
    """Memeriksa ekstensi file."""
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def validate_image(image_bytes):
    """Memvalidasi gambar berdasarkan isi file."""
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            if img.format not in {"PNG", "BMP", "JPEG"}:
                raise ValueError("Format gambar tidak didukung.")

            width, height = img.size

            if width * height > MAX_IMAGE_PIXELS:
                raise ValueError(
                    "Resolusi gambar terlalu besar. "
                    "Silakan gunakan gambar dengan resolusi lebih kecil."
                )

            img.load()
            return img.copy()

    except (UnidentifiedImageError, OSError):
        raise ValueError(
            "File yang diunggah bukan gambar yang valid."
        )


def get_original_name(filename):
    """Membersihkan nama file."""
    safe_name = secure_filename(filename)

    if not safe_name:
        return "image"

    return os.path.splitext(safe_name)[0]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/hide", methods=["GET", "POST"])
def hide():
    result = None

    if request.method == "POST":
        uploaded_file = request.files.get("image")
        message = request.form.get("message", "")
        key = request.form.get("key", "")

        if not uploaded_file or not uploaded_file.filename:
            flash("Silakan pilih gambar terlebih dahulu.", "error")
            return redirect(url_for("hide"))

        if not allowed_file(uploaded_file.filename):
            flash(
                "Format gambar harus PNG, BMP, JPG, atau JPEG.",
                "error"
            )
            return redirect(url_for("hide"))

        if not message.strip():
            flash("Pesan rahasia tidak boleh kosong.", "error")
            return redirect(url_for("hide"))

        if not key:
            flash("Stego-key tidak boleh kosong.", "error")
            return redirect(url_for("hide"))

        try:
            original_bytes = uploaded_file.read()

            if not original_bytes:
                raise ValueError("File gambar yang diunggah kosong.")

            validate_image(original_bytes)

            # Enkripsi pesan dengan AES-GCM.
            encrypted = encrypt_message(message, key)

            # Kapasitas LSB sudah memperhitungkan header 8 byte.
            capacity = capacity_bytes(original_bytes)

            if len(encrypted) > capacity:
                raise ValueError(
                    "Pesan terlalu besar untuk gambar yang dipilih. "
                    f"Kapasitas payload: {capacity} byte, "
                    f"ukuran payload: {len(encrypted)} byte."
                )

            # Sisipkan payload terenkripsi.
            stego_bytes = embed_payload(
                original_bytes,
                encrypted,
                key
            )

            # Pastikan hasil benar-benar gambar yang valid.
            validate_image(stego_bytes)

            # Hitung kualitas gambar.
            mse_value = mse(original_bytes, stego_bytes)
            psnr_value = psnr(original_bytes, stego_bytes)

            filename = (
                f"{get_original_name(uploaded_file.filename)}_stego.png"
            )

            result = {
                "image_b64": base64.b64encode(
                    stego_bytes
                ).decode("utf-8"),
                "filename": filename,
                "mse": mse_value,
                "psnr": psnr_value,
                "capacity": capacity,
                "message_size": len(encrypted),
            }

        except ValueError as error:
            flash(str(error), "error")

        except Exception:
            app.logger.exception(
                "Terjadi kesalahan saat menyisipkan pesan."
            )
            flash(
                "Terjadi kesalahan saat memproses gambar. "
                "Periksa kembali gambar dan stego-key.",
                "error"
            )

    return render_template("hide.html", result=result)


@app.route("/extract", methods=["GET", "POST"])
def extract():
    extracted_message = None

    if request.method == "POST":
        uploaded_file = request.files.get("image")
        key = request.form.get("key", "")

        if not uploaded_file or not uploaded_file.filename:
            flash("Silakan pilih gambar stego.", "error")
            return redirect(url_for("extract"))

        if not allowed_file(uploaded_file.filename):
            flash(
                "Format gambar harus PNG, BMP, JPG, atau JPEG.",
                "error"
            )
            return redirect(url_for("extract"))

        if not key:
            flash("Stego-key tidak boleh kosong.", "error")
            return redirect(url_for("extract"))

        try:
            image_bytes = uploaded_file.read()

            if not image_bytes:
                raise ValueError("File gambar yang diunggah kosong.")

            validate_image(image_bytes)

            # Ekstraksi payload LSB.
            encrypted = extract_payload(image_bytes, key)

            # Dekripsi payload AES-GCM.
            extracted_message = decrypt_message(encrypted, key)

        except ValueError as error:
            flash(str(error), "error")

        except Exception:
            app.logger.exception(
                "Terjadi kesalahan saat ekstraksi pesan."
            )
            flash(
                "Pesan tidak dapat diekstrak. "
                "Pastikan gambar dan stego-key benar.",
                "error"
            )

    return render_template(
        "extract.html",
        extracted_message=extracted_message
    )


@app.route("/analysis")
def analysis():
    return render_template("analysis.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.errorhandler(413)
def request_entity_too_large(error):
    flash(
        f"Ukuran unggahan melebihi batas {MAX_UPLOAD_MB} MB.",
        "error"
    )
    return redirect(url_for("hide"))


if __name__ == "__main__":
    app.run(debug=True)