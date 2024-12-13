import logging
from flask import current_app
import jwt
import datetime
from flask_login import UserMixin
from sqlalchemy import Column, Integer, DateTime, Text, Float, Time, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from enum import Enum
from sqlalchemy import Enum as SQLAlchemyEnum

Base = declarative_base()

# Impor db di bagian bawah file
from . import db

# Konfigurasi Logging
logging.basicConfig(level=logging.INFO,  # Atur level log yang diinginkan (INFO, ERROR, DEBUG, dsb)
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.StreamHandler(),  # Output log ke konsol
                        logging.FileHandler('app.log')  # Simpan log ke file app.log
                    ])

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    status = db.Column(db.Integer, default=0)  # 0 = user, 1 = admin

    # Relasi ke Employee
    employees = db.relationship('Employee', back_populates='user', lazy=True, cascade="all, delete-orphan")

    def get_reset_token(self, expires_in=600):
        logging.info(f"Generating reset token for user with ID: {self.id}")  # Log saat token reset dibuat
        return jwt.encode({'reset_password': self.id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_in)},
                           current_app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_reset_token(token):
        try:
            user_id = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])['reset_password']
            logging.info(f"Token verified for user with ID: {user_id}")  # Log setelah token diverifikasi
        except Exception as e:
            logging.error(f"Token verification failed: {str(e)}")  # Log error jika token tidak valid
            return None
        return User.query.get(user_id)


class Employee(db.Model):
    __tablename__ = 'employees'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    gender = db.Column(db.String(6), nullable=False)
    photo_profile = db.Column(db.Text)
    email = db.Column(db.String(255), nullable=False, unique=True)
    phone_number = db.Column(db.String(15), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Relasi ke User
    user = db.relationship('User', back_populates='employees')

    # Relasi ke Attendance
    attendances = db.relationship('Attendance', back_populates='employee', lazy=True, cascade="all, delete-orphan")


class AttendanceStatus(Enum):
    ALPHA = "ALPHA"
    CLOCK_IN = "CLOCK_IN"
    CLOCK_OUT = "CLOCK_OUT"
    IJIN = "IJIN"


class Attendance(db.Model):
    __tablename__ = 'attendance'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.user_id'), nullable=False)
    status = db.Column(db.Enum(AttendanceStatus), nullable=False, default=AttendanceStatus.ALPHA)
    date = db.Column(db.DateTime, nullable=False)
    time = db.Column(db.DateTime, nullable=False)
    time_out = db.Column(db.DateTime)
    photo = db.Column(db.Text)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    reason = db.Column(db.Text)

    # Relasi ke Employee
    employee = db.relationship('Employee', back_populates='attendances', lazy=True)

    def save(self):
        """Override save method to log when attendance is saved or updated"""
        if self.id is None:
            logging.info(f"Creating new attendance record for employee ID: {self.employee_id}")
        else:
            logging.info(f"Updating attendance record ID: {self.id} for employee ID: {self.employee_id}")
        db.session.add(self)
        db.session.commit()


class LocationSetting(db.Model):
    __tablename__ = 'location_settings'

    id = db.Column(db.Integer, primary_key=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    radius = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False)
    clock_in = db.Column(db.Time, nullable=False)
    clock_out = db.Column(db.Time, nullable=False)

    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return f"<LocationSetting Latitude {self.latitude}, Longitude {self.longitude}, Radius {self.radius}>"
    
    def save(self):
        """Override save method to log location setting changes"""
        logging.info(f"Saving location setting ID: {self.id} with latitude: {self.latitude}, longitude: {self.longitude}")
        db.session.add(self)
        db.session.commit()
