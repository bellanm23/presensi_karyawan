import os
import logging
from flask import Blueprint, request, session, jsonify, current_app
from app import db
from app.models import Attendance, AttendanceStatus
from datetime import datetime
from werkzeug.utils import secure_filename

# Konfigurasi Logging
logging.basicConfig(level=logging.INFO,  # Atur level log yang diinginkan (INFO, ERROR, DEBUG, dsb)
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.StreamHandler(),  # Output log ke konsol
                        logging.FileHandler('app.log')  # Simpan log ke file app.log
                    ])

attendance_bp = Blueprint('attendance', __name__)

@attendance_bp.route('/record', methods=['GET', 'POST'])
def record_attendance():
    if request.method == 'POST':
        photo = request.files.get('photo')  # Ambil file foto dari form
        photo_filename = None
        
        if photo:
            try:
                photo_filename = secure_filename(photo.filename)
                # Tentukan path untuk menyimpan foto ke dalam folder absensi
                upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'absensi')
                # Pastikan folder absensi ada
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)
                # Simpan foto ke folder absensi
                photo.save(os.path.join(upload_folder, photo_filename))

                logging.info(f"Photo uploaded successfully: {photo_filename}")  # Logging saat foto berhasil diupload

            except Exception as e:
                logging.error(f"Error while uploading photo: {e}")  # Logging jika terjadi kesalahan saat upload foto
                return jsonify({'message': 'Terjadi kesalahan saat mengunggah foto. Silakan coba lagi.'}), 500

        # Simpan data absensi ke database
        try:
            attendance = Attendance(
                employee_id=session['user_id'],
                status=AttendanceStatus.CLOCK_IN,
                date=datetime.today().date(),
                time=datetime.now().time(),
                photo=photo_filename,  # Simpan nama file foto
            )
            db.session.add(attendance)
            db.session.commit()
            logging.info(f"Attendance recorded for employee ID {session['user_id']} on {datetime.today().date()} at {datetime.now().time()}")  # Logging absensi yang berhasil

            # Kembalikan respons dalam format JSON
            return jsonify({'message': 'Absensi berhasil!', 'attendance': {
                'employee_id': session['user_id'],
                'status': AttendanceStatus.CLOCK_IN,
                'date': datetime.today().date().strftime('%Y-%m-%d'),
                'time': datetime.now().time().strftime('%H:%M:%S'),
                'photo': photo_filename
            }}), 201

        except Exception as e:
            db.session.rollback()  # Rollback jika terjadi kesalahan saat menyimpan absensi
            logging.error(f"Error while recording attendance for employee ID {session['user_id']}: {e}")  # Logging error saat menyimpan absensi
            return jsonify({'message': 'Terjadi kesalahan saat mencatat absensi. Silakan coba lagi.'}), 500

    # Jika metode GET, kembalikan respons JSON atau informasi lain yang diperlukan
    return jsonify({'message': 'GET request received. Please send POST request to record attendance.'}), 200
