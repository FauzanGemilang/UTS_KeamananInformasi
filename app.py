from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename
from pathlib import Path
import io
import base64

from crypto.encryption import encrypt_message, decrypt_message
from steganography.lsb import embed_payload, extract_payload, capacity_bytes
from analysis.metrics import mse, psnr

app = Flask(__name__)
app.secret_key = "CHANGE_THIS_IN_PRODUCTION"

ALLOWED = {"png", "bmp"}
MAX_UPLOAD_MB = 20

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/hide", methods=["GET", "POST"])
def hide():
    result = None
    if request.method == "POST":
        image = request.files.get("image")
        message = request.form.get("message", "")
        key = request.form.get("key", "")

        if not image or not image.filename:
            flash("Pilih gambar PNG atau BMP.", "error")
            return redirect(url_for("hide"))
        if not allowed_file(image.filename):
            flash("Format gambar harus PNG atau BMP.", "error")
            return redirect(url_for("hide"))
        if not message.strip() or not key:
            flash("Pesan dan stego-key wajib diisi.", "error")
            return redirect(url_for("hide"))

        try:
            original = image.read()
            encrypted = encrypt_message(message, key)
            stego = embed_payload(original, encrypted, key)

            original_mse = mse(original, stego)
            original_psnr = psnr(original, stego)
            cap = capacity_bytes(original)

            result = {
                "image_b64": base64.b64encode(stego).decode(),
                "filename": secure_filename(image.filename.rsplit(".", 1)[0]) + "_stego.png",
                "mse": original_mse,
                "psnr": original_psnr,
                "capacity": cap,
                "message_size": len(encrypted),
            }
        except ValueError as exc:
            flash(str(exc), "error")
        except Exception:
            flash("Terjadi kesalahan saat proses penyisipan.", "error")

    return render_template("hide.html", result=result)

@app.route("/download-stego", methods=["POST"])
def download_stego():
    data = request.form.get("data", "")
    filename = secure_filename(request.form.get("filename", "stego.png"))
    if not data:
        flash("Data stego tidak tersedia.", "error")
        return redirect(url_for("hide"))
    try:
        raw = base64.b64decode(data)
        return send_file(io.BytesIO(raw), mimetype="image/png", as_attachment=True, download_name=filename)
    except Exception:
        flash("File stego tidak valid.", "error")
        return redirect(url_for("hide"))

@app.route("/extract", methods=["GET", "POST"])
def extract():
    extracted = None
    if request.method == "POST":
        image = request.files.get("image")
        key = request.form.get("key", "")

        if not image or not image.filename:
            flash("Pilih gambar stego.", "error")
            return redirect(url_for("extract"))
        if not allowed_file(image.filename):
            flash("Format gambar harus PNG atau BMP.", "error")
            return redirect(url_for("extract"))
        if not key:
            flash("Stego-key wajib diisi.", "error")
            return redirect(url_for("extract"))

        try:
            image_bytes = image.read()
            encrypted = extract_payload(image_bytes, key)
            extracted = decrypt_message(encrypted, key)
        except ValueError as exc:
            flash(str(exc), "error")
        except Exception:
            flash("Ekstraksi gagal. Periksa gambar dan stego-key.", "error")

    return render_template("extract.html", extracted=extracted)

@app.route("/analysis")
def analysis():
    return render_template("analysis.html")

@app.route("/about")
def about():
    return render_template("about.html")

if __name__ == "__main__":
    app.run(debug=True)
