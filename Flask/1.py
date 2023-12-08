from datetime import datetime
import random
import string
from flask import Flask, redirect, request, url_for
from flask import render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, current_user, logout_user
from datetime import datetime
app = Flask(__name__)

HOSTNAME = "127.0.0.1"
PORT = 3306
USERNAME = "root"
PASSWORD = "2004723118"
DATABASE = "medical"

app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{USERNAME}:{PASSWORD}@{HOSTNAME}:{PORT}/{DATABASE}"

db = SQLAlchemy()
# 初始化db,关联flask 项目
db.app = app    # 这一步需先设置属性，很多老的教程都缺少这一步，导致连不上数据库
db.init_app(app)
 
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(phone, password):
    return User.query.filter_by(phone=phone, password=password).first()

# 测试是否连接成功
@app.route('/')
def main():
    return render_template("main.html")


class User(db.Model):
    id = db.Column(db.String(10), primary_key=True)
    real_name = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    phone = db.Column(db.String(15), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    birthdate = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(10), nullable=True)


with app.app_context():
    db.create_all()


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
            gender=gender
        )

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('registration.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone = request.form['phone']
        password = request.form['password']

        user = User.query.filter_by(phone=phone, password=password).first()

        if user:
            # Successful login (you can implement session handling or JWT here)
            return redirect(url_for('user_home', phone=phone))
        else:
            return "Invalid phone or password. Please try again."

    return render_template('main.html')


@app.route('/user_home/<user_phone>')
@login_required
def user_home(user_phone):
    if current_user.phone == user_phone:
        return render_template('user_home.html', user=current_user)
    else:
        # Redirect to a page indicating unauthorized access or handle it as appropriate
        return redirect(url_for('main'))


if __name__ == '__main__':
    app.debug = True
    app.run()

