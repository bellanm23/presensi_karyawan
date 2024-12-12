# app/utils.py
from flask import current_app
import datetime  # Pastikan ini diimpor
from flask_mail import Message
from flask_login import current_user
from app.models import Attendance, User  # Pastikan untuk mengimpor model EmailConfig
from app import mail
import jwt


def get_attendance_for_today(employee_id):
    today = datetime.now().date()  # Get today's date
    return Attendance.query.filter_by(employee_id=employee_id, date=today).first()

def get_all_employees():
    from app.models import Employee  # Move import here
    return Employee.query.all()

def get_employee_by_id(employee_id):
    from app.models import Employee  # Move import here
    return Employee.query.get(employee_id)


def generate_reset_token(user_id, expires_in=600):
    """Menghasilkan token reset password untuk pengguna."""
    return jwt.encode({'reset_password': user_id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_in)},
                       current_app.config['SECRET_KEY'], algorithm='HS256')

def verify_reset_token(token):
    """Memverifikasi token reset password dan mengembalikan user_id jika valid."""
    try:
        user_id = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])['reset_password']
    except Exception:
        return None
    return user_id