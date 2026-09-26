from flask import (
    Flask,
    render_template,
    request,
    flash,
    redirect,
    url_for
)

from werkzeug.utils import secure_filename

from PIL import Image, UnidentifiedImageError

import base64
import io
import os


# =========================================================
# APPLICATION MODULES
# =========================================================

from crypto.encryption import (
    encrypt_message,
    decrypt_message
)

from steganography.lsb import (
    embed_payload,
    extract_payload,
    capacity_bytes
)

from analysis.metrics import (
    mse,
    psnr
)


# =========================================================
# FLASK CONFIGURATION
# =========================================================

app = Flask(
    __name__,
    static_folder="public",
    static_url_path=""
)


# =========================================================
# SECRET KEY
# =========================================================
#
# Untuk deployment Vercel:
# buat Environment Variable dengan nama:
#
# SECRET_KEY
#
# Jangan menulis secret key produksi secara langsung
# di source code atau mengunggahnya ke GitHub.
#

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "secretpic-development-key"
)


# =========================================================
# SUPPORTED IMAGE FORMATS
# =========================================================

ALLOWED = {
    "png",
    "bmp",
    "jpg",
    "jpeg"
}


# =========================================================
# UPLOAD CONFIGURATION
# =========================================================
#
# Vercel memiliki batas request payload.
# Untuk deployment, gunakan ukuran file yang relatif kecil.
#
# Default: 3 MB
#
# Jika diperlukan saat lokal, nilainya dapat diubah
# melalui environment variable MAX_UPLOAD_MB.
#

try:
    MAX_UPLOAD_MB = int(
        os.environ.get(
            "MAX_UPLOAD_MB",
            "3"
        )
    )
except ValueError:
    MAX_UPLOAD_MB = 3


app.config["MAX_CONTENT_LENGTH"] = (
    MAX_UPLOAD_MB * 1024 * 1024
)


# =========================================================
# IMAGE RESOLUTION LIMIT
# =========================================================
#
# Maksimal sekitar 12 megapixel.
#
# Tujuannya agar proses LSB tidak terlalu berat,
# terutama saat aplikasi dijalankan sebagai serverless
# function di Vercel.
#

MAX_IMAGE_PIXELS = 12_000_000


# =========================================================
# HELPER FUNCTION
# =========================================================

def allowed_file(filename):
    """
    Mengecek apakah ekstensi file didukung.
    """

    return (
        "." in filename
        and filename.rsplit(
            ".",
            1
        )[1].lower() in ALLOWED
    )


def validate_image(image_bytes):
    """
    Memastikan file benar-benar merupakan gambar yang
    dapat dibaca oleh Pillow dan tidak melebihi resolusi
    maksimum.
    """

    try:

        with Image.open(
            io.BytesIO(image_bytes)
        ) as img:

            width, height = img.size

            total_pixels = (
                width * height
            )

            if total_pixels > MAX_IMAGE_PIXELS:

                return (
                    False,
                    "Resolusi gambar terlalu besar. "
                    f"Maksimal sekitar "
                    f"{MAX_IMAGE_PIXELS:,} pixel."
                )

            # Memastikan image dapat diverifikasi
            img.verify()

        return (
            True,
            None
        )

    except UnidentifiedImageError:

        return (
            False,
            "File bukan gambar yang valid."
        )

    except Exception as exc:

        print(
            "Image validation error:",
            exc
        )

        return (
            False,
            "Gambar tidak dapat diproses."
        )


def get_original_name(filename):
    """
    Mengambil nama file tanpa extension
    dan membersihkannya agar aman.
    """

    name = filename.rsplit(
        ".",
        1
    )[0]

    name = secure_filename(
        name
    )

    if not name:

        name = "image"

    return name


# =========================================================
# ERROR HANDLER — FILE TERLALU BESAR
# =========================================================

@app.errorhandler(413)
def request_entity_too_large(error):

    flash(
        "Ukuran file terlalu besar. "
        f"Maksimal upload sekitar "
        f"{MAX_UPLOAD_MB} MB.",
        "error"
    )

    return redirect(
        request.referrer or
        url_for("hide")
    )


# =========================================================
# HOME
# =========================================================

@app.route("/")
def index():

    return render_template(
        "index.html"
    )


# =========================================================
# HIDE MESSAGE
# =========================================================

@app.route(
    "/hide",
    methods=["GET", "POST"]
)
def hide():

    result = None

    if request.method == "POST":

        # -------------------------------------------------
        # GET FORM DATA
        # -------------------------------------------------

        image = request.files.get(
            "image"
        )

        message = request.form.get(
            "message",
            ""
        )

        key = request.form.get(
            "key",
            ""
        )


        # -------------------------------------------------
        # VALIDATE FILE
        # -------------------------------------------------

        if (
            not image
            or not image.filename
        ):

            flash(
                "Pilih gambar terlebih dahulu.",
                "error"
            )

            return redirect(
                url_for("hide")
            )


        # -------------------------------------------------
        # VALIDATE EXTENSION
        # -------------------------------------------------

        if not allowed_file(
            image.filename
        ):

            flash(
                "Format gambar yang didukung: "
                "PNG, BMP, JPG, dan JPEG.",
                "error"
            )

            return redirect(
                url_for("hide")
            )


        # -------------------------------------------------
        # VALIDATE MESSAGE
        # -------------------------------------------------

        if not message.strip():

            flash(
                "Pesan rahasia wajib diisi.",
                "error"
            )

            return redirect(
                url_for("hide")
            )


        # -------------------------------------------------
        # VALIDATE STEGO KEY
        # -------------------------------------------------

        if not key:

            flash(
                "Stego-key wajib diisi.",
                "error"
            )

            return redirect(
                url_for("hide")
            )


        # =================================================
        # PROCESSING
        # =================================================

        try:

            # -------------------------------------------------
            # READ ORIGINAL IMAGE
            # -------------------------------------------------

            original = image.read()


            if not original:

                flash(
                    "File gambar kosong.",
                    "error"
                )

                return redirect(
                    url_for("hide")
                )


            # -------------------------------------------------
            # VALIDATE IMAGE CONTENT
            # -------------------------------------------------

            is_valid, validation_message = (
                validate_image(
                    original
                )
            )


            if not is_valid:

                flash(
                    validation_message,
                    "error"
                )

                return redirect(
                    url_for("hide")
                )


            # -------------------------------------------------
            # ENCRYPT SECRET MESSAGE
            # -------------------------------------------------

            encrypted = encrypt_message(
                message,
                key
            )


            # -------------------------------------------------
            # CHECK IMAGE CAPACITY
            # -------------------------------------------------

            cap = capacity_bytes(
                original
            )


            if len(encrypted) > cap:

                flash(
                    "Pesan terlalu besar untuk gambar ini. "
                    f"Kapasitas maksimum sekitar "
                    f"{cap} byte.",
                    "error"
                )

                return redirect(
                    url_for("hide")
                )


            # -------------------------------------------------
            # LSB EMBEDDING
            # -------------------------------------------------

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


            # -------------------------------------------------
            # CONVERT STEGO TO BASE64
            # -------------------------------------------------

            image_b64 = base64.b64encode(
                stego
            ).decode(
                "utf-8"
            )


            # -------------------------------------------------
            # GENERATE OUTPUT FILENAME
            # -------------------------------------------------

            original_name = get_original_name(
                image.filename
            )

            filename = (
                original_name
                + "_stego.png"
            )


            # -------------------------------------------------
            # RESULT DATA
            # -------------------------------------------------

            result = {

                "image_b64": image_b64,

                "filename": filename,

                "mse": original_mse,

                "psnr": original_psnr,

                "capacity": cap,

                "message_size": len(
                    encrypted
                )

            }


        # =================================================
        # EXPECTED APPLICATION ERROR
        # =================================================

        except ValueError as exc:

            flash(
                str(exc),
                "error"
            )


        # =================================================
        # UNEXPECTED ERROR
        # =================================================

        except Exception as exc:

            print(
                "Hide error:",
                repr(exc)
            )

            flash(
                "Terjadi kesalahan saat "
                "proses penyisipan.",
                "error"
            )


    # -----------------------------------------------------
    # RENDER PAGE
    # -----------------------------------------------------

    return render_template(
        "hide.html",
        result=result
    )


# =========================================================
# EXTRACT MESSAGE
# =========================================================

@app.route(
    "/extract",
    methods=["GET", "POST"]
)
def extract():

    extracted = None

    if request.method == "POST":

        # -------------------------------------------------
        # GET FORM DATA
        # -------------------------------------------------

        image = request.files.get(
            "image"
        )

        key = request.form.get(
            "key",
            ""
        )


        # -------------------------------------------------
        # VALIDATE FILE
        # -------------------------------------------------

        if (
            not image
            or not image.filename
        ):

            flash(
                "Pilih gambar stego terlebih dahulu.",
                "error"
            )

            return redirect(
                url_for("extract")
            )


        # -------------------------------------------------
        # VALIDATE EXTENSION
        # -------------------------------------------------

        if not allowed_file(
            image.filename
        ):

            flash(
                "Format gambar yang didukung: "
                "PNG, BMP, JPG, dan JPEG.",
                "error"
            )

            return redirect(
                url_for("extract")
            )


        # -------------------------------------------------
        # VALIDATE KEY
        # -------------------------------------------------

        if not key:

            flash(
                "Stego-key wajib diisi.",
                "error"
            )

            return redirect(
                url_for("extract")
            )


        # =================================================
        # EXTRACTION
        # =================================================

        try:

            # -------------------------------------------------
            # READ STEGO IMAGE
            # -------------------------------------------------

            image_bytes = image.read()


            if not image_bytes:

                flash(
                    "File gambar kosong.",
                    "error"
                )

                return redirect(
                    url_for("extract")
                )


            # -------------------------------------------------
            # VALIDATE IMAGE CONTENT
            # -------------------------------------------------

            is_valid, validation_message = (
                validate_image(
                    image_bytes
                )
            )


            if not is_valid:

                flash(
                    validation_message,
                    "error"
                )

                return redirect(
                    url_for("extract")
                )


            # -------------------------------------------------
            # EXTRACT ENCRYPTED PAYLOAD
            # -------------------------------------------------

            encrypted = extract_payload(
                image_bytes,
                key
            )


            # -------------------------------------------------
            # DECRYPT MESSAGE
            # -------------------------------------------------

            extracted = decrypt_message(
                encrypted,
                key
            )


        # =================================================
        # EXPECTED ERROR
        # =================================================

        except ValueError as exc:

            flash(
                str(exc),
                "error"
            )


        # =================================================
        # UNEXPECTED ERROR
        # =================================================

        except Exception as exc:

            print(
                "Extract error:",
                repr(exc)
            )

            flash(
                "Ekstraksi gagal. "
                "Periksa gambar dan stego-key.",
                "error"
            )


    # -----------------------------------------------------
    # RENDER PAGE
    # -----------------------------------------------------

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
# LOCAL DEVELOPMENT SERVER
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )