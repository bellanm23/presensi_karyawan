import logging
import datetime
from datetime import datetime, time
import re
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
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

@admin_bp.route('/dashboard', methods=['GET'])
@login_required
def admin_dashboard():
    # Logika untuk menampilkan dashboard admin
    logging.info(f'User  {current_user.email} accessed the dashboard.')

    # Ambil data untuk dashboard
    dashboard_data = {
        'message': 'Welcome to the Admin Dashboard!',
        'user_email': current_user.email,
        'user_status': current_user.status,
        'total_employees': Employee.query.count(),  # Menghitung total karyawan
        'total_attendance_records': Attendance.query.count()  # Menghitung total catatan absensi
    }

    # Jika ingin mengembalikan data dalam format JSON
    if request.args.get('format') == 'json':
        return jsonify(dashboard_data), 200

    # Jika metode GET, render halaman dashboard
    return render_template('admin/dashboard.html', dashboard_data=dashboard_data)

@admin_bp.route('/add_employee', methods=['GET', 'POST'])
@login_required
def add_employee():
    if request.method == 'POST':
        # Ambil data JSON
        data = request.get_json()
        if not data:
            return jsonify({'message': 'Body request kosong atau tidak valid!'}), 400

        name = data.get('name')
        gender = data.get('gender')
        email = data.get('email')
        phone_number = data.get('phone')
        password = data.get('password')

        # Ambil file dari request
        photo = request.files.get('photo_profile')  # Pastikan file tetap dikirim sebagai multipart/form-data

        # Validasi input
        if not name or not email or not password or not phone_number:
            return jsonify({'message': 'All fields are required!'}), 400

        # Cek apakah email sudah ada di tabel users
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({'message': 'Email already exists in users table!'}), 400

        # Cek apakah email sudah ada di tabel employees
        existing_employee = Employee.query.filter_by(email=email).first()
        if existing_employee:
            return jsonify({'message': 'Email already exists in employees table!'}), 400

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

        logging.info(f'New employee added with email {email}.')
        return jsonify({'message': 'Employee added successfully!'}), 201

    # Jika metode GET, render halaman untuk menambahkan pegawai
    return render_template('admin/add_employee.html')


@admin_bp.route('/edit_employee/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_employee(id):
    employee = Employee.query.get_or_404(id)  # Ambil data pegawai berdasarkan ID

    if request.method == 'POST':
        # Ambil data JSON dari request
        data = request.get_json()
        if not data:
            return jsonify({'message': 'Body request kosong atau tidak valid!'}), 400

        # Update data pegawai berdasarkan input JSON
        name = data.get('name')
        email = data.get('email')

        # Validasi input
        if not name or not email:
            return jsonify({'message': 'Name dan email harus diisi!'}), 400

        # Update data pegawai
        employee.name = name
        employee.email = email

        # Simpan perubahan ke database
        try:
            db.session.commit()
            logging.info(f'Employee with ID {id} updated.')
            return jsonify({'message': 'Employee updated successfully!', 'employee': {
                'id': employee.id,
                'name': employee.name,
                'email': employee.email
            }}), 200
        except Exception as e:
            db.session.rollback()
            logging.error(f'Error updating employee with ID {id}: {e}')
            return jsonify({'message': 'Terjadi kesalahan saat memperbarui data!'}), 500

    # Jika metode GET, render halaman edit
    return render_template('admin/edit_employee.html', employee=employee)


@admin_bp.route('/delete_employee/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_employee(id):
    user = User.query.get_or_404(id)  # Mengambil user berdasarkan ID

    if request.method == 'POST':
        try:
            db.session.delete(user)  # Menghapus user
            db.session.commit()
            logging.info(f'User  with ID {id} and all related records deleted successfully.')
            
            # Kembalikan respons dalam format JSON
            return jsonify({'message': 'User  and all related employees and attendance records deleted successfully!'}), 200
        except Exception as e:
            db.session.rollback()
            logging.error(f'Error deleting user with ID {id}: {e}')
            
            # Kembalikan respons kesalahan dalam format JSON
            return jsonify({'message': f'Error deleting user: {str(e)}'}), 500

    # Jika metode GET, render halaman konfirmasi penghapusan
    return render_template('admin/confirm_delete.html', user=user)

@admin_bp.route('/list_employees', methods=['GET', 'POST'])
@login_required
def list_employee():
    employees = Employee.query.all()  # Ambil semua pegawai dari tabel Employee
    logging.info(f'{len(employees)} employees listed.')

    if request.method == 'POST':
        # Kembalikan respons dalam format JSON
        employee_list = [
            {
                'id': employee.id,
                'name': employee.name,
                'gender': employee.gender,
                'email': employee.email,
                'phone_number': employee.phone_number
            }
            for employee in employees
        ]
        return jsonify(employee_list), 200

    # Jika metode GET, render halaman HTML
    return render_template('admin/list_employees.html', employees=employees)

@admin_bp.route('/attendance_report', methods=['GET', 'POST'])
@login_required
def attendance_report():
    if current_user.status != 1:  # Pastikan hanya admin yang bisa mengakses
        return jsonify({'message': 'Access denied! This page is for admin only.'}), 403

    # Ambil semua catatan absensi dengan relasi ke Employee
    attendance_records = Attendance.query.options(db.joinedload(Attendance.employee)).all()
    logging.info(f'{len(attendance_records)} attendance records fetched for report.')

    if request.method == 'POST':
        # Kembalikan respons dalam format JSON
        attendance_list = [
            {
                'employee_id': record.employee_id,
                'employee_name': record.employee.name if record.employee else 'N/A',
                'status': record.status,
                'date': record.date.strftime('%Y-%m-%d'),
                'time': record.time.strftime('%H:%M:%S'),
                'time_out': record.time_out.strftime('%H:%M:%S') if record.time_out else 'Not Clocked Out',
                'reason': record.reason if record.reason else 'N/A',
                'photo': record.photo if record.photo else 'No photo uploaded'
            }
            for record in attendance_records
        ]
        return jsonify(attendance_list), 200

    # Jika metode GET, render halaman HTML
    return render_template('admin/attendance_report.html', attendance_records=attendance_records)

@admin_bp.route('/location_settings', methods=['GET', 'POST'])
@login_required
def location_settings():
    if request.method == 'POST':
        # Ambil data dari body request JSON
        data = request.get_json()
        if not data:
            return jsonify({'message': 'Body request kosong atau tidak valid!'}), 400

        # Ambil data dari JSON
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        radius = data.get('radius')
        clock_in_str = data.get('clock_in')
        clock_out_str = data.get('clock_out')

        # Validasi input
        if not latitude or not longitude or not radius or not clock_in_str or not clock_out_str:
            return jsonify({'message': 'Semua field harus diisi!'}), 400

        try:
            # Convert clock_in dan clock_out ke format time
            clock_in = datetime.strptime(clock_in_str, '%H:%M').time()
            clock_out = datetime.strptime(clock_out_str, '%H:%M').time()

            # Simpan data ke database
            new_setting = LocationSetting(
                latitude=latitude,
                longitude=longitude,
                radius=radius,
                clock_in=clock_in,
                clock_out=clock_out
            )
            db.session.add(new_setting)
            db.session.commit()

            logging.info('New location setting added successfully.')

            # Kembalikan respons JSON
            return jsonify({'message': 'Location settings saved successfully!', 'setting': {
                'latitude': latitude,
                'longitude': longitude,
                'radius': radius,
                'clock_in': clock_in_str,
                'clock_out': clock_out_str
            }}), 201

        except ValueError:
            return jsonify({'message': 'Format waktu clock_in dan clock_out harus HH:MM!'}), 400
        except Exception as e:
            db.session.rollback()
            logging.error(f'Error saving location setting: {e}')
            return jsonify({'message': 'Terjadi kesalahan saat menyimpan pengaturan lokasi!'}), 500

    # Jika metode GET, render halaman HTML
    return render_template('admin/location_settings.html')
