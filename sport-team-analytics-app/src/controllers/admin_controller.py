from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from src.models.models import User, Team, Player, Coach
from extensions import db

def admin_required(f):
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role != 'admin':
            flash('Admin access required.')
            return redirect(url_for('hello_world'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
@admin_required
def dashboard():
    search = request.args.get('search', '').strip()
    role = request.args.get('role', '').strip()
    team_id = request.args.get('team_id', '').strip()
    users_query = User.query
    
    if search:
        users_query = users_query.filter(
            (User.username.ilike(f'%{search}%')) |
            (User.firstname.ilike(f'%{search}%')) |
            (User.lastname.ilike(f'%{search}%')) |
            (User.email.ilike(f'%{search}%'))
        )
    if role:
        users_query = users_query.filter_by(role=role)
    if team_id:
        # from models.models import Player
        users_query = users_query.join(Player).filter(Player.team_id == int(team_id))
    
    users = users_query.all()
    teams = Team.query.all()
    
    return render_template('admin/dashboard.html', users=users, teams=teams, search=search, role=role, team_id=team_id)

@admin_bp.route('/users/add', methods=['GET', 'POST'])
@admin_required
def add_user():
    if request.method == 'POST':
        username = request.form['username']
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        if User.query.filter_by(username=username).first():
            html = render_template('admin/add_user.html', error='Username already exists.')
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify(success=False, html=html)
            flash('Username already exists.')
            return redirect(url_for('admin.add_user'))
        user = User()
        user.username = username
        user.firstname = firstname
        user.lastname = lastname
        user.email = email
        user.role = role
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        if role == 'player':
            player = Player()
            player.user_id = user.id
            db.session.add(player)
        if role == 'coach':
            coach = Coach()
            coach.user_id = user.id
            db.session.add(coach)
        db.session.commit()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(success=True)
        flash('User added successfully!')
        return redirect(url_for('admin.dashboard'))
    
    html = render_template('admin/add_user.html', error=None)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return html
    
    return render_template('admin/add_user.html', error=None)

@admin_bp.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        user.username = request.form['username']
        user.firstname = request.form['firstname']
        user.lastname = request.form['lastname']
        user.email = request.form['email']
        user.role = request.form['role']
        if request.form['password']:
            user.set_password(request.form['password'])
        if user.role == 'player' and not user.player:
            player = Player()
            player.user_id = user.id
            db.session.add(player)
        if user.role == 'coach' and not user.coach:
            coach = Coach()
            coach.user_id = user.id
            db.session.add(coach)
        db.session.commit()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(success=True)
        flash('User updated successfully!')
        return redirect(url_for('admin.dashboard'))
    
    html = render_template('admin/edit_user.html', user=user, error=None)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return html
    
    return render_template('admin/edit_user.html', user=user, error=None)

@admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot delete yourself!')
        return redirect(url_for('admin.dashboard'))
    db.session.delete(user)
    db.session.commit()
    
    flash('User deleted successfully!')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/teams/add', methods=['GET', 'POST'])
@admin_required
def add_team():
    coaches = Coach.query.all()
    
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        coach_id = request.form['coach_id']
        
        if Team.query.filter_by(name=name).first():
            html = render_template('admin/add_team.html', error='Team name already exists.', coaches=coaches)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify(success=False, html=html)
            flash('Team name already exists.')
            return redirect(url_for('admin.add_team'))
        team = Team()
        team.name = name
        team.description = description
        team.coach_id = int(coach_id)
        db.session.add(team)
        db.session.commit()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(success=True)
        flash('Team added successfully!')
        return redirect(url_for('admin.dashboard'))
    
    html = render_template('admin/add_team.html', error=None, coaches=coaches)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return html
    
    return render_template('admin/add_team.html', error=None, coaches=coaches)

@admin_bp.route('/teams/edit/<int:team_id>', methods=['GET', 'POST'])
@admin_required
def edit_team(team_id):
    team = Team.query.get_or_404(team_id)
    coaches = Coach.query.all()
    
    if request.method == 'POST':
        team.name = request.form['name']
        team.description = request.form['description']
        team.coach_id = int(request.form['coach_id'])
        db.session.commit()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(success=True)
        flash('Team updated successfully!')
        return redirect(url_for('admin.dashboard'))
    
    html = render_template('admin/edit_team.html', team=team, error=None, coaches=coaches)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return html
    
    return render_template('admin/edit_team.html', team=team, error=None, coaches=coaches)

@admin_bp.route('/teams/delete/<int:team_id>', methods=['POST'])
@admin_required
def delete_team(team_id):
    team = Team.query.get_or_404(team_id)
    db.session.delete(team)
    db.session.commit()

    flash('Team deleted successfully!')
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/users/assign_team/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def assign_team(user_id):
    user = User.query.get_or_404(user_id)

    # from models.models import Team
    teams = Team.query.all()

    if not user.player and user.role == 'player':
        player = Player()
        player.user = user
        db.session.add(player)
        db.session.commit()
    if not user.player:
        msg = 'This user is not a player and cannot be assigned to a team.'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(success=False, html=f'<div class="alert alert-danger">{msg}</div>')
        flash(msg)
        return redirect(url_for('admin.dashboard'))
    
    if request.method == 'POST':
        team_id = request.form.get('team_id')
        if team_id and team_id != 'none':
            team = Team.query.get(int(team_id))
            user.player.team = team
        else:
            user.player.team = None
        db.session.commit()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(success=True)
        flash('Team assignment updated!')
        return redirect(url_for('admin.dashboard'))
    
    html = render_template('admin/assign_team.html', user=user, teams=teams)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return html
    
    return render_template('admin/assign_team.html', user=user, teams=teams) 