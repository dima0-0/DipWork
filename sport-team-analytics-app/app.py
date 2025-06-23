import os
from dotenv import load_dotenv

from flask import Flask
from flask import render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

from extensions import db
from src.models.models import User
from src.controllers.admin_controller import admin_bp
from flask_migrate import Migrate
from src.controllers.coach_controller import coach_bp
from src.controllers.player_controller import player_bp

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.getenv('SECRET_KEY', 'dev_secret_key')

db.init_app(app)

migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)
setattr(login_manager, 'login_view', 'login')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def hello_world():
    return render_template('home.html')

# Registration route (admin only for now)
@app.route('/register', methods=['GET', 'POST'])
@login_required
# Only allow admin to register new users
def register():
    if current_user.role != 'admin':
        flash('Only admin can register new users.')
        return redirect(url_for('hello_world'))
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        if User.query.filter_by(username=username).first():
            flash('Username already exists.')
            return redirect(url_for('register'))
        user = User()
        user.username = username
        user.email = email
        user.role = role
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('User registered successfully!')
        return redirect(url_for('hello_world'))
    return render_template('register.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            # Redirect to dashboard based on role
            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif user.role == 'coach':
                return redirect(url_for('coach.dashboard'))
            elif user.role == 'player':
                return redirect(url_for('player.dashboard'))
            else:
                return redirect(url_for('hello_world'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Example role_required decorator
def role_required(role):
    def decorator(f):
        @login_required
        def decorated_function(*args, **kwargs):
            if current_user.role != role:
                flash('You do not have access to this page.')
                return redirect(url_for('hello_world'))
            return f(*args, **kwargs)
        decorated_function.__name__ = f.__name__
        return decorated_function
    return decorator

app.register_blueprint(admin_bp)
app.register_blueprint(coach_bp)
app.register_blueprint(player_bp)

if __name__ == '__main__':
    app.run()
