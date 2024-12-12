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

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # Auto-increment
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    status = db.Column(db.Integer, default=0)  # 0 = user, 1 = admin
    
    # Relasi ke model Employee
    employees = db.relationship('Employee', backref='user', lazy=True)

    def get_reset_token(self, expires_in=600):
        return jwt.encode({'reset_password': self.id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_in)},
                           current_app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_reset_token(token):
        try:
            user_id = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])['reset_password']
        except Exception:
            return None
        return User.query.get(user_id)


class Employee(db.Model):
    __tablename__ = 'employees'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # Auto-increment
    name = db.Column(db.String(255), nullable=False)
    gender = db.Column(db.String(6), nullable=False)
    photo_profile = db.Column(db.Text)  # Kolom untuk menyimpan nama file foto
    email = db.Column(db.String(255), nullable=False, unique=True)
    phone_number = db.Column(db.String(15), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Foreign key to User

class AttendanceStatus(Enum):
    ALPHA = "ALPHA"
    CLOCK_IN = "CLOCK_IN"
    CLOCK_OUT = "CLOCK_OUT"
    IJIN = "IJIN"

class Attendance(db.Model):
    __tablename__ = 'attendance'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.user_id'), nullable=False)  # Ubah ke user_id
    status = db.Column(db.Enum(AttendanceStatus), nullable=False, default=AttendanceStatus.ALPHA)
    date = db.Column(db.DateTime, nullable=False)
    time = db.Column(db.DateTime, nullable=False)
    time_out = db.Column(db.DateTime)  # Tambahkan kolom untuk waktu clock out
    photo = db.Column(db.Text)  # Kolom untuk menyimpan nama file foto
    latitude = db.Column(db.Float)  # Kolom untuk menyimpan latitude
    longitude = db.Column(db.Float)  # Kolom untuk menyimpan longitude
    reason = db.Column(db.Text)  # Kolom untuk menyimpan alasan izin

    # Relasi dengan Employee
    employee = db.relationship('Employee', backref='attendances', primaryjoin='Attendance.employee_id == Employee.user_id')


# Model LocationSetting
class LocationSetting(db.Model):
    __tablename__ = 'location_settings'

    id = db.Column(db.Integer, primary_key=True)
    latitude = db.Column(db.Float, nullable=False)  # Ganti 'lat' dengan 'latitude'
    longitude = db.Column(db.Float, nullable=False)  # Ganti 'long' dengan 'longitude'
    radius = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False)
    clock_in = db.Column(db.Time, nullable=False)
    clock_out = db.Column(db.Time, nullable=False)

    
    def get_id(self):
        return str(self.id)  # Pastikan ini mengembalikan id dalam bentuk string

    def __repr__(self):
        return f"<LocationSetting Lat {self.lat}, Long {self.long}, Radius {self.radius}>"
