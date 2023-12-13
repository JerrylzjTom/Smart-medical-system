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
import requests
import json
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
# The Doctor class represents a doctor in a database with attributes such as id, name, phone,
# birthdate, gender, title, and department_id, and has a relationship with the Appointment class.
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


# The `users` class is a user model that represents a user with attributes such as username, phone,
# password hash, and id, and provides methods for verifying passwords and retrieving user information.
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
    """
    The `register` function handles the registration process for new users, validating the input data
    and creating a new user in the database.
    :return: If the request method is 'POST' and the password and confirm_password fields match, the
    function will add a new user to the database and redirect to the login page. If the request method
    is 'GET', the function will render the registration.html template.
    """
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
    """
    The `login` function checks if the submitted login form is valid, retrieves user information from
    the database, and logs the user in if the username and password match.
    :return: the rendered template 'login.html' along with the form object.
    """
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


@app.route('/aichat')
@login_required
def aichat():
    return render_template('aichat.html')


@app.route('/chat', methods=['POST'])
def chat():
    # 获取用户输入作为对话内容
    user_input = request.form['user_input']

    # 设置文心一言 API 的 URL 和访问令牌
    url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions_pro?access_token=24.bce7459693fedd212db6188a733f9ade.2592000.1704781892.282335-44516318"

    # 构造对话内容的 JSON 格式数据
    payload = json.dumps({
        "messages": [
            {
                "role": "user",
                "content": user_input
            }
        ]
    })

    # 设置请求头
    headers = {
        'Content-Type': 'application/json'
    }

    # 发送 POST 请求
    response = requests.request("POST", url, headers=headers, data=payload)

    # 获取 API 响应的文本内容
    assistant_response = response.text

    # 将助手的回复发送到前端
    return jsonify({'assistant_response': assistant_response})


@app.route('/search')
def search():
    departments = Department.query.all()
    return render_template('search.html', departments=departments)


@app.route('/get_doctor_details/<doctor_name>', methods=['GET'])
def get_doctor_details(doctor_name):
    """
    This function retrieves details of a doctor based on their name and returns the details in JSON
    format.
    :param doctor_name: The `doctor_name` parameter is a string that represents the name of the doctor
    whose details we want to retrieve
    :return: a JSON response containing the details of the doctor(s) with the specified name. The
    details include the doctor's name, phone number, birthday, gender, and title.
    """
    doctors = Doctor.query.filter_by(name=doctor_name).all()
    print(doctors)
    doctor_data = [{'name': doctor.name, 'phone': doctor.phone, 'birthday': doctor.birthdate, 'gender': doctor.gender, 'title': doctor.title} for doctor in doctors]
    return jsonify({'doctorDetails': doctor_data})


if __name__ == '__main__':
    app.debug = True
    app.run()
