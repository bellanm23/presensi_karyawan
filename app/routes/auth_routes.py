#  C:\attendance_system\script backup\absensi_app\app\routes\auth_routes.py
import random, string
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User
from flask_bcrypt import Bcrypt
from flask_mail import Mail, Message  # Pastikan Anda mengimpor Flask-Mail
from app import mail, db
from werkzeug.security import generate_password_hash
from app.utils import generate_reset_token, verify_reset_token

auth_bp = Blueprint('auth_bp', __name__)
bcrypt = Bcrypt()
mail = Mail()  # Inisialisasi Flask-Mail

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash('Email dan password harus diisi!', 'danger')
            return redirect(url_for('auth_bp.login'))

        user = User.query.filter_by(email=email).first()
        if user:
            if bcrypt.check_password_hash(user.password, password):
                login_user(user)
                flash('Login berhasil!', 'success')
                # print(user)
                # Arahkan pengguna berdasarkan status
                if user.status == 1:  # Admin
                    return redirect(url_for('admin_bp.admin_dashboard'))  # Pastikan ini sesuai dengan nama blueprint dan rute
                else:  # Karyawan biasa
                    return redirect(url_for('user_bp.user_dashboard'))  # Pastikan ini sesuai dengan nama blueprint dan rute
            else:
                flash('Password salah!', 'danger')
        else:
            flash('Email tidak ditemukan!', 'danger')

        return redirect(url_for('auth_bp.login'))

    return render_template('auth/login.html')

# Logout
@auth_bp.route('/logout')
def logout():
    logout_user()
    flash('Anda berhasil logout.', 'info')
    return redirect(url_for('auth_bp.login'))


# Halaman forgot password (jika diperlukan)
@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if user:
            token = generate_reset_token(user.id)  # Menggunakan fungsi dari utils
            reset_url = url_for('auth_bp.reset_password', token=token, _external=True)
            flash(f'Token reset password Anda: {reset_url}', 'info')  # Tampilkan token di flash message
            return redirect(url_for('auth_bp.login'))
        else:
            flash('Email tidak ditemukan.', 'danger')
    return render_template('auth/forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user_id = verify_reset_token(token)
    if user_id is None:
        flash('Token tidak valid atau telah kedaluwarsa.', 'danger')
        return redirect(url_for('auth_bp.login'))

    user = User.query.get(user_id)
    if request.method == 'POST':
        new_password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        user.password = hashed_password
        
        try:
            db.session.commit()  # Commit perubahan
            flash('Kata sandi Anda telah diperbarui!', 'success')
            return redirect(url_for('auth_bp.login'))
        except Exception as e:
            db.session.rollback()  # Rollback jika terjadi kesalahan
            flash('Terjadi kesalahan saat memperbarui kata sandi. Silakan coba lagi.', 'danger')
            print(f"Error: {e}")

    return render_template('auth/reset_password.html', token=token)