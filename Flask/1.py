from datetime import datetime
import random
import string
from flask import Flask, flash, redirect, request, session, url_for
from flask import render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from werkzeug.security import check_password_hash
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, EqualTo
from flask_wtf import FlaskForm
from datetime import datetime
from sqlalchemy import event
from flask import jsonify
app = Flask(__name__)

HOSTNAME = "127.0.0.1"
PORT = 3306
USERNAME = "root"
PASSWORD = "2004723118"
DATABASE = "medical"

app.config['SECRET_KEY'] = '13132'
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{USERNAME}:{PASSWORD}@{HOSTNAME}:{PORT}/{DATABASE}"

db = SQLAlchemy()
# 初始化db,关联flask 项目
db.app = app    
db.init_app(app)
 
login_manager = LoginManager(app)
login_manager.login_view = 'login'


class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)


# Define Doctor model
class Doctor(db.Model):
    id = db.Column(db.String(10), primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(15), nullable=False, unique=True)
    birthdate = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    title = db.Column(db.String(50), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False)
    # Define the relationship between Doctor and Department
    appointments = db.relationship('Appointment', backref='doctor', lazy=True)


class User(db.Model):
    id = db.Column(db.String(10), primary_key=True)
    real_name = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    birthdate = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    appointments = db.relationship('Appointment', backref='patient', lazy=True)


class Appointment(db.Model):
    id = db.Column(db.String(3), primary_key=True)
    appointment_date = db.Column(db.Date, nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=False)
    notes = db.Column(db.Text)
    patient_id = db.Column(db.String(10), db.ForeignKey('user.id'), nullable=False)
    doctor_id = db.Column(db.String(10), db.ForeignKey('doctor.id'), nullable=False)


class Hospitalization(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.String(10), db.ForeignKey('user.id'), nullable=True)
    bed_status = db.Column(db.String(20), nullable=False)  # Assuming bed status can be a string like "Occupied" or "Vacant"
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'), nullable=False)


with app.app_context():
    db.create_all()


class users(UserMixin):
    """用户类"""
    def __init__(self, user):
        self.username = user.real_name
        self.phone = user.phone
        self.password_hash = user.password
        self.id = user.id

    def verify_password(self, password):
        if self.password_hash is None:
            return False
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return self.id

    @staticmethod
    def get(user_id):
        return users(User.query.get(user_id))


@login_manager.user_loader  # 定义获取登录用户的方法
def load_user(user, force=True):
    return users.get(user)


@app.route('/')
def index():
    return render_template('main.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        real_name = request.form['real_name']
        username = request.form['username']
        phone = request.form['phone']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        birthdate = datetime.strptime(request.form['birthdate'], '%Y-%m-%d').date()
        gender = request.form['gender']

        if password != confirm_password:
            return "Passwords do not match. Please try again."
        
        generated_id = ''.join(random.choices(string.digits, k=10))
        
        new_user = User(
            id=generated_id,
            real_name=real_name,
            username=username,
            phone=phone,
            password=password,
            birthdate=birthdate,
            gender=gender,
        )

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('registration.html')


class LoginForm(FlaskForm):
    """登录表单类"""
    username = StringField('用户名', validators=[DataRequired()])
    password = PasswordField('密码', validators=[DataRequired()])


@app.route('/login/', methods=('GET', 'POST'))  # 登录
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user_name = form.username.data
        password = form.password.data
        user_info = User.query.filter_by(username=user_name).first()
        if user_info is None:
            print("The user is not existed")
        else:
            user = users(user_info)
            if user_info.password == password:  # 校验密码
                login_user(user)  # 创建用户 Session
                return redirect('/')
            else:
                print("The username or password is error")
    return render_template('login.html', form=form)


@app.route('/logout')  # 登出
@login_required
def logout():
    logout_user()
    return redirect('/')


@app.route('/save_doctor', methods=['POST'])
def save_doctor():
    name = request.form.get('name')
    phone = request.form.get('phone')
    password = request.form.get('password')
    birthdate = datetime.strptime(request.form.get('birthdate'), '%Y-%m-%d') if request.form.get('birthdate') else None
    gender = request.form.get('gender')
    title = request.form.get('title')
    department = request.form.get('department')

    new_doctor = Doctor(name=name, phone=phone, password=password, birthdate=birthdate, gender=gender, title=title, department=department)
    db.session.add(new_doctor)
    db.session.commit()

    return f'Doctor {name} saved successfully!'


@event.listens_for(Appointment, 'before_insert')
def generate_appointment_id(mapper, connection, target):
    target.id = generate_unique_id()

def generate_unique_id():
    # Add logic to generate a unique three-digit ID (you may use a random generator, etc.)
    # Here, I'll generate a simple sequential ID for demonstration purposes
    last_appointment = Appointment.query.order_by(Appointment.id.desc()).first()

    if last_appointment:
        last_id = int(last_appointment.id)
        new_id = str(last_id + 1).zfill(3)
    else:
        new_id = '001'

    return new_id


@app.route('/order', methods=['GET', 'POST'])
@login_required
def order():
    departments = Department.query.all()
    if request.method == 'POST':
        patient_id = current_user.id
        phone = current_user.phone
        appointment_date = datetime.strptime(request.form['appointmentDate'], '%Y-%m-%d').date()
        comments = request.form['comments']
        doctor_id = request.form['doctor']
        new_user = Appointment(
            patient_id=patient_id,
            phone=phone,
            appointment_date=appointment_date,
            doctor_id=doctor_id,
            notes=comments,
        )

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('index'))

    return render_template('order.html', departments=departments)


@app.route('/get_doctors/<department_id>', methods=['GET'])
def get_doctors(department_id):
    doctors = Doctor.query.filter_by(department_id=department_id).all()
    doctors_data = [{'id': doctor.id, 'name': doctor.name} for doctor in doctors]
    return jsonify({'doctors': doctors_data})


@app.route('/get_beds/<department_id>', methods=['GET'])
def get_beds(department_id):
    beds = Hospitalization.query.filter_by(department_id=department_id).all()
    beds_data = [{'id': bed.id, 'bed_status': bed.bed_status} for bed in beds]
    return jsonify({'beds': beds_data})


@app.route('/doctor')
def doctor_main():
    return render_template('doctor.html')


@app.route("/doctor/inhospital", methods=['GET', 'POST'])
def hospital():
    departments = Department.query.all()
    if request.method == 'POST':
        patient_id = request.form['ID']
        bed_status = 'Using'
        id = request.form['ward']
        result = Hospitalization.query.filter(Hospitalization.id == id).first()
        result.patient_id = patient_id
        result.bed_status = bed_status
        db.session.commit()
        print(2)
        return redirect('/doctor')
    return render_template('inhospital.html', departments=departments)


@app.route('/doctor/wards', methods=['GET'])
def view_all_wards():
    wards = Hospitalization.query.all()
    return render_template('all_wards.html', wards=wards)


if __name__ == '__main__':
    app.debug = True
    app.run()
