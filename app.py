from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import db, User, Inward, Outward, Activity
from datetime import datetime
import os
import pandas as pd

app = Flask(__name__)
app.config['SECRET_KEY'] = '123456'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///office.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create tables
with app.app_context():
    db.create_all()
    # Create default admin if not exists
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            password=generate_password_hash('admin123'),
            role='admin',
            full_name='System Admin'
        )
        db.session.add(admin)
        db.session.commit()

# ============ ROUTES ============

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for(f'{user.role}_dashboard'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ============ ADMIN ROUTES ============

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('login'))
    
    total_users = User.query.count()
    total_inward = Inward.query.count()
    total_outward = Outward.query.count()
    total_activities = Activity.query.count()
    
    return render_template('admin/dashboard.html', 
                         total_users=total_users,
                         total_inward=total_inward,
                         total_outward=total_outward,
                         total_activities=total_activities)

@app.route('/admin/users', methods=['GET', 'POST'])
@login_required
def manage_users():
    if current_user.role != 'admin':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        full_name = request.form['full_name']
        email = request.form['email']
        
        # Check if user exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
        else:
            new_user = User(
                username=username,
                password=generate_password_hash(password),
                role=role,
                full_name=full_name,
                email=email
            )
            db.session.add(new_user)
            db.session.commit()
            flash('User created successfully')
    
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/reports')
@login_required
def reports():
    if current_user.role != 'admin':
        return redirect(url_for('login'))
    
    # Generate reports
    inward_data = Inward.query.all()
    outward_data = Outward.query.all()
    activity_data = Activity.query.all()
    
    return render_template('admin/reports.html', 
                         inward_data=inward_data,
                         outward_data=outward_data,
                         activity_data=activity_data)

# ============ OPERATOR ROUTES ============

@app.route('/operator/dashboard')
@login_required
def operator_dashboard():
    if current_user.role != 'operator':
        return redirect(url_for('login'))
    return render_template('operator/dashboard.html')

@app.route('/operator/inward', methods=['GET', 'POST'])
@login_required
def inward_management():
    if current_user.role != 'operator':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        inward = Inward(
            reference_no=request.form['reference_no'],
            sender_name=request.form['sender_name'],
            subject=request.form['subject'],
            document_type=request.form['document_type'],
            user_id=current_user.id
        )
        db.session.add(inward)
        db.session.commit()
        flash('Inward entry created successfully')
    
    inward_entries = Inward.query.all()
    return render_template('operator/inward.html', entries=inward_entries)

@app.route('/operator/outward', methods=['GET', 'POST'])
@login_required
def outward_management():
    if current_user.role != 'operator':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        outward = Outward(
            reference_no=request.form['reference_no'],
            receiver_name=request.form['receiver_name'],
            subject=request.form['subject'],
            document_type=request.form['document_type'],
            user_id=current_user.id
        )
        db.session.add(outward)
        db.session.commit()
        flash('Outward entry created successfully')
    
    outward_entries = Outward.query.all()
    return render_template('operator/outward.html', entries=outward_entries)

@app.route('/operator/activities', methods=['GET', 'POST'])
@login_required
def operator_activities():
    if current_user.role != 'operator':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        activity = Activity(
            title=request.form['title'],
            description=request.form['description'],
            activity_type=request.form['activity_type'],
            location=request.form['location'],
            user_id=current_user.id
        )
        
        # Handle photo upload
        if 'photo' in request.files:
            photo = request.files['photo']
            if photo.filename:
                filename = secure_filename(photo.filename)
                photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                activity.photo_path = filename
        
        db.session.add(activity)
        db.session.commit()
        flash('Activity added successfully')
    
    activities = Activity.query.all()
    return render_template('operator/activities.html', activities=activities)

# ============ ALC ROUTES ============

@app.route('/alc/dashboard')
@login_required
def alc_dashboard():
    if current_user.role != 'alc':
        return redirect(url_for('login'))
    
    pending_acknowledgments = Inward.query.filter_by(alc_acknowledged=False).all()
    activities = Activity.query.all()
    
    return render_template('alc/dashboard.html', 
                         pending=pending_acknowledgments,
                         activities=activities)

@app.route('/alc/acknowledge/<int:inward_id>', methods=['POST'])
@login_required
def acknowledge_inward(inward_id):
    if current_user.role != 'alc':
        return redirect(url_for('login'))
    
    inward = Inward.query.get_or_404(inward_id)
    inward.alc_acknowledged = True
    inward.acknowledgment_date = datetime.utcnow()
    db.session.commit()
    flash('Material received acknowledged successfully')
    return redirect(url_for('alc_dashboard'))

@app.route('/alc/activities', methods=['POST'])
@login_required
def alc_upload_activity():
    if current_user.role != 'alc':
        return redirect(url_for('login'))
    
    activity = Activity(
        title=request.form['title'],
        description=request.form['description'],
        activity_type=request.form['activity_type'],
        location=request.form['location'],
        user_id=current_user.id
    )
    
    if 'photo' in request.files:
        photo = request.files['photo']
        if photo.filename:
            filename = secure_filename(photo.filename)
            photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            activity.photo_path = filename
    
    db.session.add(activity)
    db.session.commit()
    flash('Activity uploaded successfully')
    return redirect(url_for('alc_dashboard'))

if __name__ == '__name__':
    app.run(debug=True, host='0.0.0.0', port=5000)