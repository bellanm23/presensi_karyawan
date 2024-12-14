import logging, os, base64
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Attendance, AttendanceStatus, Employee
from werkzeug.utils import secure_filename
from datetime import datetime
import pytz

# Konfigurasi Logging
logging.basicConfig(level=logging.INFO,  # Atur level log yang diinginkan (INFO, ERROR, DEBUG, dsb)
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.StreamHandler(),  # Output log ke konsol
                        logging.FileHandler('app.log')  # Simpan log ke file app.log
                    ])

user_bp = Blueprint('user_bp', __name__)

@user_bp.route('/user_dashboard', methods=['GET'])
@login_required
def user_dashboard():
    employee = Employee.query.filter_by(user_id=current_user.id).first()
    attendances = Attendance.query.filter_by(employee_id=current_user.id).all()

    logging.info(f"User {current_user.id} accessed their dashboard.")  # Logging saat pengguna mengakses dashboard

    # Cek apakah permintaan menginginkan JSON
    if request.accept_mimetypes.best_match(['application/json', 'text/html']) == 'application/json':
        attendance_data = [
            {
                'date': attendance.date.strftime('%Y-%m-%d'),
                'status': attendance.status.value,  # Menggunakan .value untuk mendapatkan string dari enum
                'time': attendance.time.strftime('%H:%M:%S'),
                'time_out': attendance.time_out.strftime('%H:%M:%S') if attendance.time_out else 'Belum Clock Out',
                'reason': attendance.reason if attendance.reason else 'N/A',
                'photo': attendance.photo if attendance.photo else 'Tidak ada foto yang diunggah.'
            }
            for attendance in attendances
        ]
        response_data = {
            'employee': {
                'id': employee.id,
                'name': employee.name,
                'gender': employee.gender,
                'email': employee.email,
                'phone_number': employee.phone_number,
                'photo_profile': employee.photo_profile if employee.photo_profile else 'Tidak ada foto profil'
            },
            'attendances': attendance_data
        }
        return jsonify(response_data), 200

    # Jika permintaan bukan JSON, render halaman dashboard
    return render_template('employee/user_dashboard.html', attendances=attendances, employee=employee)


@user_bp.route('/clock_in', methods=['GET', 'POST'])
@login_required
def clock_in():
    if request.method == 'POST':
        data = request.get_json()  # Mengambil data JSON dari request (jika ada)
        photo = request.files.get('photo')  # Mengambil file foto dari request
        lat = data.get('lat')
        long = data.get('long')

        if not photo:
            flash('Foto tidak ditemukan. Silakan coba lagi.', 'danger')
            logging.warning(f"User {current_user.id} failed clock-in: Photo not provided.")  # Logging jika foto tidak ada
            return jsonify({"status": "error", "message": "Foto tidak ditemukan. Silakan coba lagi."}), 400

        # Validasi latitude dan longitude
        if not lat or not long:
            flash('Latitude dan Longitude harus diisi!', 'danger')
            logging.warning(f"User {current_user.id} failed clock-in: Latitude or Longitude missing.")  # Logging jika lat/long tidak ada
            return jsonify({"status": "error", "message": "Latitude dan Longitude harus diisi!"}), 400

        # Simpan foto ke folder static/uploads
        photo_filename = secure_filename(photo.filename)
        photo_path = os.path.join(current_app.root_path, 'static', 'uploads', photo_filename)
        photo.save(photo_path)

        # Simpan data absensi ke database
        attendance = Attendance(
            employee_id=current_user.id,  # Menggunakan ID karyawan yang sedang login
            status=AttendanceStatus.CLOCK_IN,
            date=datetime.today().date(),
            time=datetime.now(),
            photo=photo_filename,  # Simpan nama file foto
            latitude=float(lat),  # Konversi lat dan long ke float
            longitude=float(long)
        )
        db.session.add(attendance)
        db.session.commit()
        flash('Clock In berhasil!', 'success')
        logging.info(f"User {current_user.id} successfully clocked in at {lat}, {long} with photo {photo_filename}.")  # Logging jika clock-in berhasil

        # Kembalikan respons JSON jika berhasil
        return jsonify({"status": "success", "message": "Clock In berhasil!"}), 200

    # Jika metode GET, render halaman clock in
    return render_template('employee/clock_in.html')



@user_bp.route('/clock_out', methods=['GET', 'POST'])
@login_required
def clock_out():
    if request.method == 'POST':
        # Cari data clock-in terakhir
        attendance = Attendance.query.filter_by(
            employee_id=current_user.id,
            status=AttendanceStatus.CLOCK_IN
        ).order_by(Attendance.id.desc()).first()

        if not attendance:
            flash('Tidak ada data Clock In sebelumnya untuk Clock Out!', 'danger')
            logging.warning(f"User {current_user.id} attempted to clock out without clocking in.")  # Logging jika tidak ada clock-in sebelumnya
            return jsonify({"status": "error", "message": "Tidak ada data Clock In sebelumnya untuk Clock Out!"}), 400

        # Update data clock-out
        attendance.time_out = datetime.now()  # Simpan waktu clock out
        attendance.status = AttendanceStatus.CLOCK_OUT
        db.session.commit()
        flash('Clock Out berhasil!', 'success')
        logging.info(f"User {current_user.id} successfully clocked out.")  # Logging jika clock-out berhasil
        
        # Jika permintaan meminta JSON, kembalikan respons JSON
        if request.accept_mimetypes.best_match(['application/json', 'text/html']) == 'application/json':
            return jsonify({"status": "success", "message": "Clock Out berhasil!"}), 200

    # Jika metode GET, render halaman clock out
    return render_template('employee/clock_out.html')


@user_bp.route('/recap', methods=['GET'])
@login_required
def recap():
    # Ambil semua catatan absensi untuk karyawan yang sedang login
    attendance_records = Attendance.query.filter_by(employee_id=current_user.id).all()
    logging.info(f"User {current_user.id} accessed their attendance recap. Found {len(attendance_records)} records.")  # Logging saat mengakses recap

    # Memeriksa apakah permintaan menginginkan JSON
    if request.accept_mimetypes.best_match(['application/json', 'text/html']) == 'application/json':
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
    return render_template('employee/recap.html', attendance_records=attendance_records, AttendanceStatus=AttendanceStatus)


@user_bp.route('/leave', methods=['GET', 'POST'])
@login_required
def leave():
    if request.method == 'POST':
        # Ambil data JSON dari request body
        data = request.get_json()

        reason = data.get('reason')
        date = data.get('date')
        photo = data.get('photo')  # Foto dalam format base64

        # Validasi alasan dan tanggal
        if not reason or not date:
            flash('Alasan dan tanggal harus diisi!', 'danger')
            logging.warning(f"User {current_user.id} failed leave request: Reason or date not provided.")  # Logging jika alasan atau tanggal tidak diisi
            return jsonify({"status": "error", "message": "Alasan dan tanggal harus diisi!"}), 400

        # Simpan foto jika ada
        photo_filename = None
        if photo:
            try:
                # Mengonversi foto dari base64 ke file
                photo_data = base64.b64decode(photo.split(',')[1])  # Menghilangkan prefix data:image/jpeg;base64,
                photo_filename = secure_filename(f'{current_user.id}_leave.jpg')
                photo_path = os.path.join(current_app.root_path, 'static', 'uploads', photo_filename)
                with open(photo_path, 'wb') as f:
                    f.write(photo_data)
                logging.info(f"User {current_user.id} uploaded a leave photo: {photo_filename}")  # Logging saat foto diunggah
            except Exception as e:
                logging.error(f"Error saving the photo for user {current_user.id}: {e}")
                return jsonify({"status": "error", "message": "Gagal menyimpan foto!"}), 500

        # Simpan pengajuan izin ke database
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
        logging.info(f"User {current_user.id} successfully submitted a leave request for {date}.")  # Logging pengajuan izin berhasil

        # Memeriksa apakah permintaan menginginkan JSON
        if request.accept_mimetypes.best_match(['application/json', 'text/html']) == 'application/json':
            # Kembalikan respons JSON jika berhasil
            return jsonify({"status": "success", "message": "Pengajuan izin berhasil!"}), 200

    # Jika metode GET, render halaman pengajuan izin
    return render_template('employee/leave.html')
