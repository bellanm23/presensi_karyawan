import os
import base64

# Menghasilkan SECRET_KEY dari Base64
secret_key = base64.b64encode(os.urandom(24)).decode('utf-8')

class Config:
    # Koneksi ke database SQLite
    SECRET_KEY = secret_key
    SQLALCHEMY_DATABASE_URI = 'sqlite:///attendance_system.db?timeout=60'
    SQLALCHEMY_POOL_RECYCLE = 3600
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Menambahkan batas ukuran upload
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB

    # Tentukan lokasi folder untuk menyimpan foto
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'static', 'uploads')

    # Pastikan folder ada
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)


    smtp_server = 'smtp.gmail.com'
    smtp_port = 587