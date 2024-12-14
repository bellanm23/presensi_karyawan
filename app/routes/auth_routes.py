import random, string
import logging
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User
from flask_bcrypt import Bcrypt
from flask_mail import Mail, Message  # Pastikan Anda mengimpor Flask-Mail
from app import mail, db
from werkzeug.security import generate_password_hash
from app.utils import generate_reset_token, verify_reset_token

# Konfigurasi Logging
logging.basicConfig(level=logging.INFO,  # Atur level log yang diinginkan (INFO, ERROR, DEBUG, dsb)
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.StreamHandler(),  # Output log ke konsol
                        logging.FileHandler('app.log')  # Simpan log ke file app.log
                    ])

auth_bp = Blueprint('auth_bp', __name__)
bcrypt = Bcrypt()
mail = Mail()  # Inisialisasi Flask-Mail

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Ambil data dari body JSON
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        logging.info(f"Attempting to login with email: {email}")

        if not email or not password:
            # logging.info(f'email = {email}')
            # logging.info(f'password = {password}')
            return jsonify({"code": 400, "status": "Bad Request", "message": "Email dan password harus diisi!"}), 400

        user = User.query.filter_by(email=email).first()
        if user:
            logging.info(f"User found: {user.email}, Status: {user.status}")
            if bcrypt.check_password_hash(user.password, password):
                login_user(user)
                logging.info(f'User {user.email} successfully logged in.')
                return jsonify({
                    "code": 200,
                    "status": "OK",
                    "message": "Login berhasil!",
                    "redirect_url": url_for('admin_bp.admin_dashboard') if user.status == 1 else url_for('user_bp.user_dashboard')
                }), 200
            else:
                logging.warning(f'Failed login attempt. Incorrect password for user: {email}')
                return jsonify({"code": 401, "status": "Unauthorized", "message": "Password salah!"}), 401
        else:
            logging.warning(f'Failed login attempt. Email {email} not found in database.')
            return jsonify({"code": 404, "status": "Not Found", "message": "Email tidak ditemukan!"}), 404

    # Jika metode GET, render halaman login
    return render_template('auth/login.html')


# Logout
@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    if current_user.is_authenticated:
        logging.info(f'User   {current_user.email} logged out.')
        logout_user()
        
        # Jika metode POST, kembalikan respons dalam format JSON
        if request.method == 'POST':
            return jsonify({"code": 200, "status": "OK", "message": "Logout berhasil!"}), 200
        
        # Jika metode GET, render halaman logout
        return render_template('auth/logout.html', message="Logout berhasil!")
    else:
        # Jika metode POST, kembalikan respons kesalahan dalam format JSON
        if request.method == 'POST':
            return jsonify({"code": 401, "status": "Unauthorized", "message": "User  tidak terautentikasi!"}), 401
        
        # Jika metode GET, render halaman dengan pesan kesalahan
        return render_template('auth/logout.html', message="User  tidak terautentikasi!")

# Forgot Password
@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.json.get('email')

        if not email:
            return jsonify({"code": 400, "status": "Bad Request", "message": "Email harus diisi!"}), 400

        user = User.query.filter_by(email=email).first()
        if user:
            token = generate_reset_token(user.id)
            reset_url = url_for('auth_bp.reset_password', token=token, _external=True)

            # Kirim email reset password (implementasi pengiriman email tidak ditampilkan di sini)
            logging.info(f'Password reset email sent to {email}.')
            return jsonify({"code": 200, "status": "OK", "message": "Email reset password telah dikirim!"}), 200
        else:
            logging.warning(f'Email {email} tidak ditemukan.')
            return jsonify({"code": 404, "status": "Not Found", "message": "Email tidak ditemukan!"}), 404

    # Jika metode GET, render halaman forgot password
    return render_template('auth/forgot_password.html')
# Reset Password
@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user_id = verify_reset_token(token)
    if user_id is None:
        return jsonify({"code": 400, "status": "Bad Request", "message": "Token tidak valid atau telah kedaluwarsa."}), 400

    if request.method == 'POST':
        # Ambil data dari body JSON
        data = request.get_json()
        if not data:
            return jsonify({"code": 400, "status": "Bad Request", "message": "Body request kosong!"}), 400

        new_password = data.get('password')  # Ambil password dari JSON body
        if not new_password:
            return jsonify({"code": 400, "status": "Bad Request", "message": "Password baru harus diisi!"}), 400

        user = User.query.get(user_id)
        hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        user.password = hashed_password

        try:
            db.session.commit()
            return jsonify({"code": 200, "status": "OK", "message": "Kata sandi Anda telah diperbarui!"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"code": 500, "status": "Internal Server Error", "message": "Terjadi kesalahan saat memperbarui kata sandi."}), 500

    # Jika metode GET, render halaman reset password
    return render_template('auth/reset_password.html', token=token)
