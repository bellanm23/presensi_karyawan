import random, string
import logging
from flask import Blueprint, render_template, request, flash, redirect, url_for
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
        email = request.form.get('email')
        password = request.form.get('password')

        logging.info(f"Attempting to login with email: {email}")  # Logging attempt login

        if not email or not password:
            flash('Email dan password harus diisi!', 'danger')
            logging.warning(f'Failed login attempt. Missing email or password for email: {email}')
            return redirect(url_for('auth_bp.login'))

        user = User.query.filter_by(email=email).first()
        if user:
            logging.info(f"User found: {user.email}, Status: {user.status}")  # Logging user found
            if bcrypt.check_password_hash(user.password, password):
                login_user(user)
                flash('Login berhasil!', 'success')
                logging.info(f'User {user.email} successfully logged in.')
                if user.status == 1:  # Admin
                    return redirect(url_for('admin_bp.admin_dashboard'))
                else:  # Karyawan biasa
                    return redirect(url_for('user_bp.user_dashboard'))
            else:
                flash('Password salah!', 'danger')
                logging.warning(f'Failed login attempt. Incorrect password for user: {email}')
        else:
            flash('Email tidak ditemukan!', 'danger')
            logging.warning(f'Failed login attempt. Email {email} not found in database.')

        return redirect(url_for('auth_bp.login'))

    return render_template('auth/login.html')

# Logout
@auth_bp.route('/logout')
def logout():
    logging.info(f'User {current_user.email} logged out.')  # Logging user logout
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
            logging.info(f'Password reset token generated for email: {email}')
            return redirect(url_for('auth_bp.login'))
        else:
            flash('Email tidak ditemukan.', 'danger')
            logging.warning(f'Failed password reset request. Email {email} not found.')

    return render_template('auth/forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user_id = verify_reset_token(token)
    if user_id is None:
        flash('Token tidak valid atau telah kedaluwarsa.', 'danger')
        logging.warning(f'Invalid or expired reset token: {token}')
        return redirect(url_for('auth_bp.login'))

    user = User.query.get(user_id)
    if request.method == 'POST':
        new_password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
        user.password = hashed_password
        
        try:
            db.session.commit()  # Commit perubahan
            flash('Kata sandi Anda telah diperbarui!', 'success')
            logging.info(f'Password updated for user with ID {user.id}.')
            return redirect(url_for('auth_bp.login'))
        except Exception as e:
            db.session.rollback()  # Rollback jika terjadi kesalahan
            flash('Terjadi kesalahan saat memperbarui kata sandi. Silakan coba lagi.', 'danger')
            logging.error(f"Error updating password for user ID {user.id}: {e}")

    return render_template('auth/reset_password.html', token=token)
