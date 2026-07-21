from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, operator, alc
    email = db.Column(db.String(120))
    full_name = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    inward_entries = db.relationship('Inward', backref='created_by', lazy=True)
    outward_entries = db.relationship('Outward', backref='created_by', lazy=True)
    activities = db.relationship('Activity', backref='created_by', lazy=True)

class Inward(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reference_no = db.Column(db.String(50), unique=True)
    sender_name = db.Column(db.String(100))
    subject = db.Column(db.String(200))
    received_date = db.Column(db.DateTime, default=datetime.utcnow)
    document_type = db.Column(db.String(50))
    status = db.Column(db.String(20), default='pending')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    alc_acknowledged = db.Column(db.Boolean, default=False)
    acknowledgment_date = db.Column(db.DateTime)

class Outward(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reference_no = db.Column(db.String(50), unique=True)
    receiver_name = db.Column(db.String(100))
    subject = db.Column(db.String(200))
    sent_date = db.Column(db.DateTime, default=datetime.utcnow)
    document_type = db.Column(db.String(50))
    status = db.Column(db.String(20), default='pending')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    activity_type = db.Column(db.String(50))  # event, marketing, promotion
    date = db.Column(db.DateTime, default=datetime.utcnow)
    location = db.Column(db.String(200))
    photo_path = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)