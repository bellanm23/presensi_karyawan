# C:\attendance_system\script backup\absensi_app\app\routes\attendance_routes.py

import os
from flask import Blueprint, render_template, request, session, redirect, url_for, flash, current_app
from app import db
from app.models import Attendance, AttendanceStatus
from datetime import datetime
from werkzeug.utils import secure_filename


attendance_bp = Blueprint('attendance', __name__)

from flask import current_app
from werkzeug.utils import secure_filename
import os

@attendance_bp.route('/record', methods=['GET', 'POST'])
def record_attendance():
    if request.method == 'POST':
        photo = request.files['photo']  # Ambil file foto dari form
        if photo:
            photo_filename = secure_filename(photo.filename)
            # Tentukan path untuk menyimpan foto ke dalam folder absensi
            upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'absensi')
            # Pastikan folder absensi ada
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            # Simpan foto ke folder absensi
            photo.save(os.path.join(upload_folder, photo_filename))

        # Simpan data absensi ke database
        attendance = Attendance(
            employee_id=session['user_id'],
            status=AttendanceStatus.CLOCK_IN,
            date=datetime.today().date(),
            time=datetime.now().time(),
            photo=photo_filename,  # Simpan nama file foto
        )
        db.session.add(attendance)
        db.session.commit()
        flash('Absensi berhasil!')

    return render_template('employee/attendance.html')