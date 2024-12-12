# C:\attendance_system\script backup\absensi_app\app\routes\employee_routes.py

import os
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from app import db
from app.models import Attendance, AttendanceStatus, Employee
from werkzeug.utils import secure_filename
from datetime import datetime
# from app.models import Attendance

home_bp = Blueprint('home', __name__)
@home_bp.route('/')
def home():
    # Logic for the home page
    user_status = 'Active'
    return render_template('home.html', user_status=user_status)

employee_bp = Blueprint('employee', __name__)

# Di dalam file app/routes/employee_routes.py
@employee_bp.route('/profile')
@login_required
def profile():
    print(f"Current User ID: {current_user.id}")  # Debug print
    employee = Employee.query.filter_by(user_id=current_user.id).first()
    return render_template('employee/profile.html', employee=employee)

@employee_bp.route('/recap')
@login_required
def recap():
    # Ambil semua catatan absensi untuk karyawan yang sedang login
    attendance_records = Attendance.query.filter_by(employee_id=current_user.id).all()
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
            return redirect(url_for('employee.leave'))

        # Simpan foto jika ada
        photo_filename = None
        if photo:
            photo_filename = secure_filename(photo.filename)
            photo.save(os.path.join(current_app.root_path, 'static', 'uploads', photo_filename))

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
        return redirect(url_for('user_bp.user_dashboard'))

    return render_template('employee/leave.html')



