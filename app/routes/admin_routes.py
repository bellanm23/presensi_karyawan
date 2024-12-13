import logging
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

# Konfigurasi Logging
logging.basicConfig(level=logging.INFO,  # Atur level log yang diinginkan (INFO, ERROR, DEBUG, dsb)
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.StreamHandler(),  # Output log ke konsol
                        logging.FileHandler('app.log')  # Simpan log ke file app.log
                    ])

admin_bp = Blueprint('admin_bp', __name__)
bcrypt = Bcrypt()

@admin_bp.route('/dashboard')
@login_required
def admin_dashboard():
    # Logika untuk menampilkan dashboard admin
    logging.info(f'User {current_user.email} accessed the dashboard.')
    return render_template('admin/dashboard.html')

@admin_bp.route('/add_employee', methods=['GET', 'POST'])
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
            logging.warning(f'Missing required fields while adding employee for email: {email}')
            return redirect(url_for('admin_bp.add_employee'))

        # Cek apakah email sudah ada di tabel users
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already exists in users table!', 'danger')
            logging.warning(f'Email {email} already exists in users table.')
            return redirect(url_for('admin_bp.add_employee'))

        # Cek apakah email sudah ada di tabel employees
        existing_employee = Employee.query.filter_by(email=email).first()
        if existing_employee:
            flash('Email already exists in employees table!', 'danger')
            logging.warning(f'Email {email} already exists in employees table.')
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
        logging.info(f'New user added with email {email}.')

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
        logging.info(f'New employee added with email {email}.')

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
        logging.info(f'Employee with ID {id} updated.')
        flash('Employee updated successfully!', 'success')
        return redirect(url_for('admin_bp.list_employee'))
    return render_template('admin/edit_employee.html', employee=employee)  # Kembali ke halaman daftar pegawai

@admin_bp.route('/delete_employee/<int:id>', methods=['POST'])
@login_required
def delete_employee(id):
    user = User.query.get_or_404(id)  # Mengambil user berdasarkan ID
    try:
        db.session.delete(user)  # Menghapus user
        db.session.commit()
        logging.info(f'User with ID {id} and all related records deleted successfully.')
        flash('User and all related employees and attendance records deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        logging.error(f'Error deleting user with ID {id}: {e}')
        flash(f'Error deleting user: {e}', 'danger')

    return redirect(url_for('admin_bp.list_employee'))

@admin_bp.route('/list_employees')
@login_required
def list_employee():
    employees = Employee.query.all()  # Ambil semua pegawai dari tabel Employee
    logging.info(f'{len(employees)} employees listed.')
    return render_template('admin/list_employees.html', employees=employees)

from app.models import AttendanceStatus

@admin_bp.route('/attendance_report')
@login_required
def attendance_report():
    if current_user.status != 1:  # Pastikan hanya admin yang bisa mengakses
        flash('Akses ditolak! Halaman ini hanya untuk admin.', 'danger')
        logging.warning(f'Access denied for user {current_user.email} to attendance report.')
        return redirect(url_for('auth_bp.login'))

    # Ambil semua catatan absensi dengan relasi ke Employee
    attendance_records = Attendance.query.options(db.joinedload(Attendance.employee)).all()
    logging.info(f'{len(attendance_records)} attendance records fetched for report.')
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
        logging.info('New location setting added successfully.')
        flash('Pengaturan lokasi berhasil disimpan!', 'success')
        return redirect(url_for('admin_bp.location_settings'))

    return render_template('admin/location_settings.html')