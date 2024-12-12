# C:\attendance_system\script backup\absensi_app\app\routes\admin_routes.py

import datetime
from datetime import datetime, time
import re
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app.models import User, Attendance, Employee, LocationSetting
from flask_bcrypt import Bcrypt
from app import db
import uuid
from werkzeug.utils import secure_filename



admin_bp = Blueprint('admin_bp', __name__)
bcrypt = Bcrypt()

@admin_bp.route('/admin_dashboard')
@login_required
def admin_dashboard():
    # Logika untuk menampilkan dashboard admin
    return render_template('admin/dashboard.html')

@admin_bp.route('/admin/add_employee', methods=['GET', 'POST'])
@login_required
def add_employee():
    if request.method == 'POST':
        # Ambil data dari form
        name = request.form.get('name')
        gender = request.form.get('gender')
        email = request.form.get('email')
        phone_number = request.form.get('phone')
        password = request.form.get('password')
        photo = request.files.get('photo_profile')  # Pastikan ini sesuai dengan nama input

        # Validasi input
        if not name or not email or not password or not phone_number:
            flash('All fields are required!', 'danger')
            return redirect(url_for('admin_bp.add_employee'))

        # Cek apakah email sudah ada di tabel users
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already exists in users table!', 'danger')
            return redirect(url_for('admin_bp.add_employee'))

        # Cek apakah email sudah ada di tabel employees
        existing_employee = Employee.query.filter_by(email=email).first()
        if existing_employee:
            flash('Email already exists in employees table!', 'danger')
            return redirect(url_for('admin_bp.add_employee'))

        # Hash password
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Simpan nama file foto jika ada
        photo_filename = None
        if photo:
            photo_filename = secure_filename(photo.filename)
            # Simpan foto ke folder static/uploads
            photo.save(os.path.join(current_app.root_path, 'static', 'uploads', photo_filename))

        # Simpan data ke database
        new_user = User(email=email, password=hashed_password, status=0)
        db.session.add(new_user)
        db.session.commit()

        new_employee = Employee(
            name=name,
            gender=gender,
            email=email,
            phone_number=phone_number,
            password=hashed_password,
            photo_profile=photo_filename,  # Simpan nama file foto
            user_id=new_user.id
        )
        db.session.add(new_employee)
        db.session.commit()

        flash('Employee added successfully!', 'success')
        return redirect(url_for('admin_bp.list_employee'))

    return render_template('admin/add_employee.html')



@admin_bp.route('/edit_employee/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_employee(id):
    employee = Employee.query.get_or_404(id)  # Ambil data pegawai berdasarkan ID
    if request.method == 'POST':
        # Update data pegawai
        employee.name = request.form['name']
        employee.email = request.form['email']
        db.session.commit()
        flash('Employee updated successfully!', 'success')
        return redirect(url_for('admin_bp.list_employee'))
    return render_template('admin/edit_employee.html', employee=employee)  # Kembali ke halaman daftar pegawai

@admin_bp.route('/delete_employee/<int:id>', methods=['POST'])
@login_required
def delete_employee(id):
    employee = Employee.query.get_or_404(id)
    try:
        db.session.delete(employee)
        db.session.commit()
        flash('Employee deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting employee: {e}', 'danger')
    return redirect(url_for('admin_bp.list_employee'))

@admin_bp.route('/list_employees')
@login_required
def list_employee():
    employees = Employee.query.all()  # Ambil semua pegawai dari tabel Employee
    return render_template('admin/list_employees.html', employees=employees)

from app.models import AttendanceStatus

@admin_bp.route('/attendance_report')
@login_required
def attendance_report():
    if current_user.status != 1:  # Pastikan hanya admin yang bisa mengakses
        flash('Akses ditolak! Halaman ini hanya untuk admin.', 'danger')
        return redirect(url_for('auth_bp.login'))

    # Ambil semua catatan absensi dengan relasi ke Employee
    attendance_records = Attendance.query.options(db.joinedload(Attendance.employee)).all()
    return render_template('admin/attendance_report.html', attendance_records=attendance_records)



@admin_bp.route('/location_settings', methods=['GET', 'POST'])
@login_required
def location_settings():
    if request.method == 'POST':
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        radius = request.form.get('radius')
        date_str = request.form.get('date')  # Get the date as a string
        clock_in_str = request.form.get('clock_in')
        clock_out_str = request.form.get('clock_out')

        # Convert the date string to a datetime.date object
        date = datetime.strptime(date_str, '%Y-%m-%d').date()

        # Convert clock_in and clock_out strings to time objects
        clock_in = datetime.strptime(clock_in_str, '%H:%M').time()
        clock_out = datetime.strptime(clock_out_str, '%H:%M').time()

        # Save data to the database
        new_setting = LocationSetting(
            latitude=latitude,
            longitude=longitude,
            radius=radius,
            date=date,  # Use the converted date object
            clock_in=clock_in,  # Use the converted time object
            clock_out=clock_out  # Use the converted time object
        )
        db.session.add(new_setting)
        db.session.commit()
        flash('Pengaturan lokasi berhasil disimpan!', 'success')
        return redirect(url_for('admin_bp.location_settings'))

    return render_template('admin/location_settings.html')
