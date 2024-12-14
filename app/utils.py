import logging
from flask import current_app
import datetime  # Pastikan ini diimpor
from flask_mail import Message
from flask_login import current_user
from app.models import Attendance, User, Employee  # Pastikan untuk mengimpor model EmailConfig
from app import mail
import jwt
from app import db

# Konfigurasi Logging
logging.basicConfig(level=logging.INFO,  # Atur level log yang diinginkan (INFO, ERROR, DEBUG, dsb)
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.StreamHandler(),  # Output log ke konsol
                        logging.FileHandler('app.log')  # Simpan log ke file app.log
                    ])


def get_attendance_for_today(employee_id):
    today = datetime.datetime.now().date()  # Get today's date
    attendance = Attendance.query.filter_by(employee_id=employee_id, date=today).first()
    logging.info(f"Attendance for employee {employee_id} on {today}: {attendance}")  # Log saat attendance diambil
    return attendance

def get_all_employees():
    logging.info("Fetching all employees")  # Log saat mengambil data semua karyawan
    from app.models import Employee  # Move import here
    employees = Employee.query.all()
    logging.info(f"Found {len(employees)} employees")  # Log jumlah karyawan yang ditemukan
    return employees

def get_employee_by_id(employee_id):
    logging.info(f"Fetching employee with ID: {employee_id}")  # Log saat mengambil data karyawan berdasarkan ID
    from app.models import Employee  # Move import here
    employee = Employee.query.get(employee_id)
    logging.info(f"Employee details: {employee}")  # Log data karyawan
    return employee

def delete_employee_and_related_data(user_id):
    logging.info(f"Deleting employee and related data for user ID: {user_id}")  # Log sebelum menghapus data
    # Menghapus data attendance berdasarkan employee_id
    employee = Employee.query.filter_by(user_id=user_id).first()
    if employee:
        # Menghapus data attendance terkait
        deleted_attendance_count = Attendance.query.filter_by(employee_id=employee.id).delete()
        logging.info(f"Deleted {deleted_attendance_count} attendance records for employee {employee.id}")  # Log jumlah attendance yang dihapus
        
        # Menghapus data employee
        db.session.delete(employee)
        logging.info(f"Deleted employee with ID: {employee.id}")  # Log saat data employee dihapus
    
    # Menghapus data user
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        logging.info(f"Deleted user with ID: {user.id}")  # Log saat data user dihapus

    # Commit perubahan ke database
    db.session.commit()
    logging.info(f"Changes committed to the database for user ID: {user_id}")  # Log setelah commit perubahan


def generate_access_token(user, expires_in=3600):
    """Menghasilkan token akses untuk pengguna."""
    payload = {
        'user_id': user.id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_in)
    }
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')

def generate_reset_token(user_id, expires_in=600):
    """Menghasilkan token reset password untuk pengguna."""
    logging.info(f"Generating reset token for user ID: {user_id}")  # Log saat token reset dibuat
    return jwt.encode({'reset_password': user_id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_in)},
                       current_app.config['SECRET_KEY'], algorithm='HS256')

def verify_reset_token(token):
    """Memverifikasi token reset password dan mengembalikan user_id jika valid."""
    try:
        user_id = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])['reset_password']
        logging.info(f"Token verified for user ID: {user_id}")  # Log setelah token diverifikasi
    except Exception as e:
        logging.error(f"Token verification failed: {str(e)}")  # Log error jika token tidak valid
        return None
    return user_id
