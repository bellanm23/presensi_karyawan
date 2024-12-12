import sys
import os

# Tambahkan path ke folder aplikasi Anda
path = '/home/bellanm123/absensi_app'  # Ganti 'username' dengan nama pengguna PythonAnywhere Anda

if path not in sys.path:
    sys.path.append(path)

# Impor aplikasi Flask dari file yang sesuai
from app import create_app  # Mengimpor fungsi create_app dari __init__.py

# Buat instance aplikasi
application = create_app()  # Memanggil fungsi create_app untuk membuat instance aplikasi