import os
import logging
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, jsonify
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

@home_bp.route('/', methods=['GET'])
def home():
    # Logic for the home page
    user_status = 'Active'
    logging.info(f"Home page accessed by user: {current_user.id if current_user.is_authenticated else 'Guest'}")  # Logging siapa yang mengakses halaman home

    # Jika permintaan adalah JSON, kembalikan data dalam format JSON
    if request.is_json:
        response_data = {
            'status': 'success',
            'message': 'Welcome to the Home Page!',
            'user_status': 'Admin' if current_user.is_authenticated and current_user.status == 1 else 'User ' if current_user.is_authenticated else 'Guest'
        }
        return jsonify(response_data), 200

    # Jika permintaan bukan JSON, render halaman home
    return render_template('home.html', user_status=user_status)

employee_bp = Blueprint('employee', __name__)

@employee_bp.route('/profile', methods=['GET'])
@login_required
def profile():
    logging.info(f"Profile page accessed by user: {current_user.id}")  # Logging saat mengakses halaman profil
    employee = Employee.query.filter_by(user_id=current_user.id).first()

    # Jika permintaan adalah JSON, kembalikan data dalam format JSON
    if request.is_json:
        if employee:
            employee_data = {
                'id': employee.id,
                'name': employee.name,
                'gender': employee.gender,
                'email': employee.email,
                'phone_number': employee.phone_number,
                'photo_profile': employee.photo_profile if employee.photo_profile else 'Tidak ada foto profil'
            }
            return jsonify(employee_data), 200
        else:
            return jsonify({"status": "error", "message": "Employee not found."}), 404

    # Jika permintaan bukan JSON, render halaman profil
    return render_template('employee/profile.html', employee=employee)

@employee_bp.route('/recap', methods=['GET'])
@login_required
def recap():
    # Ambil semua catatan absensi untuk karyawan yang sedang login
    attendance_records = Attendance.query.filter_by(employee_id=current_user.id).all()
    logging.info(f"Recap page accessed by user: {current_user.id}, Found {len(attendance_records)} attendance records")  # Logging saat mengakses rekapan absensi

    # Jika permintaan adalah JSON, kembalikan data dalam format JSON
    if request.is_json:
        records_data = [
            {
                'date': record.date.strftime('%Y-%m-%d'),
                'status': record.status.value,  # Menggunakan .value untuk mendapatkan string dari enum
                'reason': record.reason if record.reason else 'N/A',
                'photo': record.photo if record.photo else 'Tidak ada foto yang diunggah.',
                'time': record.time.strftime('%H:%M:%S'),
                'time_out': record.time_out.strftime('%H:%M:%S') if record.time_out else 'Belum Clock Out',
                'latitude': record.latitude,
                'longitude': record.longitude
            }
            for record in attendance_records
        ]
        return jsonify(records_data), 200

    # Jika permintaan bukan JSON, render halaman rekap absensi
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
            return jsonify({"status": "error", "message": "Alasan dan tanggal harus diisi!"}), 400

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
            
            # Kembalikan respons JSON jika berhasil
            return jsonify({"status": "success", "message": "Pengajuan izin berhasil!"}), 200
        except Exception as e:
            db.session.rollback()  # Rollback jika terjadi kesalahan saat menyimpan pengajuan izin
            logging.error(f"Error while submitting leave request for user {current_user.id}: {e}")  # Logging kesalahan saat menyimpan pengajuan izin
            return jsonify({"status": "error", "message": "Terjadi kesalahan saat mengajukan izin. Silakan coba lagi."}), 500

    # Jika metode GET, render halaman pengajuan izin
    return render_template('employee/leave.html')
