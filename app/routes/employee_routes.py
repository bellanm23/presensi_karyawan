import os
import logging
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from app import db
from app.models import Attendance, AttendanceStatus, Employee
from werkzeug.utils import secure_filename
from datetime import datetime

# Konfigurasi Logging
logging.basicConfig(level=logging.INFO,  # Atur level log yang diinginkan (INFO, ERROR, DEBUG, dsb)
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.StreamHandler(),  # Output log ke konsol
                        logging.FileHandler('app.log')  # Simpan log ke file app.log
                    ])

home_bp = Blueprint('home', __name__)
@home_bp.route('/')
def home():
    # Logic for the home page
    user_status = 'Active'
    logging.info(f"Home page accessed by user: {current_user.id if current_user.is_authenticated else 'Guest'}")  # Logging siapa yang mengakses halaman home
    return render_template('home.html', user_status=user_status)

employee_bp = Blueprint('employee', __name__)

@employee_bp.route('/profile')
@login_required
def profile():
    logging.info(f"Profile page accessed by user: {current_user.id}")  # Logging saat mengakses halaman profil
    print(f"Current User ID: {current_user.id}")  # Debug print
    employee = Employee.query.filter_by(user_id=current_user.id).first()
    return render_template('employee/profile.html', employee=employee)

@employee_bp.route('/recap')
@login_required
def recap():
    # Ambil semua catatan absensi untuk karyawan yang sedang login
    attendance_records = Attendance.query.filter_by(employee_id=current_user.id).all()
    logging.info(f"Recap page accessed by user: {current_user.id}, Found {len(attendance_records)} attendance records")  # Logging saat mengakses rekapan absensi
    return render_template('employee/recap.html', attendance_records=attendance_records)

@employee_bp.route('/leave', methods=['GET', 'POST'])
@login_required
def leave():
    if request.method == 'POST':
        reason = request.form.get('reason')
        photo = request.files.get('photo')  # Ambil file foto dari form
        date = request.form.get('date')

        if not reason or not date:
            flash('Alasan dan tanggal harus diisi!', 'danger')
            logging.warning(f"Leave request failed for user {current_user.id}: Reason or date not provided")  # Logging jika pengajuan izin gagal
            return redirect(url_for('employee.leave'))

        # Simpan foto jika ada
        photo_filename = None
        if photo:
            photo_filename = secure_filename(photo.filename)
            photo.save(os.path.join(current_app.root_path, 'static', 'uploads', photo_filename))
            logging.info(f"Leave photo uploaded for user {current_user.id}: {photo_filename}")  # Logging saat foto diunggah

        # Simpan pengajuan izin ke database
        try:
            attendance = Attendance(
                employee_id=current_user.id,
                status=AttendanceStatus.IJIN,
                date=datetime.strptime(date, '%Y-%m-%d'),  # Mengonversi string ke objek datetime
                time=datetime.now(),
                reason=reason,
                photo=photo_filename  # Simpan nama file foto
            )
            db.session.add(attendance)
            db.session.commit()
            flash('Pengajuan izin berhasil!', 'success')
            logging.info(f"Leave request successfully submitted for user {current_user.id} on {date}")  # Logging pengajuan izin berhasil
        except Exception as e:
            db.session.rollback()  # Rollback jika terjadi kesalahan saat menyimpan pengajuan izin
            logging.error(f"Error while submitting leave request for user {current_user.id}: {e}")  # Logging kesalahan saat menyimpan pengajuan izin
            flash('Terjadi kesalahan saat mengajukan izin. Silakan coba lagi.', 'danger')

        return redirect(url_for('user_bp.user_dashboard'))

    return render_template('employee/leave.html')
