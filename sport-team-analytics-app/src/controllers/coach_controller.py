from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, make_response
from flask_login import login_required, current_user
from src.models.models import Team, TrainingSession, Player, Match, PlayerMatchStat
from extensions import db
from datetime import date
from weasyprint import HTML


def coach_required(f):
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role != 'coach':
            flash('Coach access required.')
            return redirect(url_for('hello_world'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

coach_bp = Blueprint('coach', __name__, url_prefix='/coach')

@coach_bp.route('/')
@coach_required
def dashboard():
    teams = Team.query.filter_by(coach_id=current_user.coach.id).all() if current_user.coach else []
    player_count = sum(len(team.players) for team in teams)
    # Get upcoming trainings (next 3, future only)
    team_ids = [team.id for team in teams]
    upcoming_trainings = []
    
    if team_ids:
        upcoming_trainings = TrainingSession.query.filter(
            TrainingSession.team_id.in_(team_ids),
            TrainingSession.date >= date.today()
        ).order_by(TrainingSession.date.asc()).limit(3).all()
    
    return render_template('coach/dashboard.html', teams=teams, player_count=player_count, upcoming_trainings=upcoming_trainings)

@coach_bp.route('/teams')
@coach_required
def teams():
    search = request.args.get('search', '').strip()
    query = Team.query.filter_by(coach_id=current_user.coach.id)
    
    if search:
        query = query.filter(Team.name.ilike(f'%{search}%'))
    teams = query.all()
    
    return render_template('coach/teams.html', teams=teams)

@coach_bp.route('/players')
@coach_required
def players():
    search = request.args.get('search', '').strip()
    team_id = request.args.get('team_id', type=int)
    position = request.args.get('position', '').strip()
    teams = Team.query.filter_by(coach_id=current_user.coach.id).all()
    players = []
    
    for team in teams:
        players.extend(team.players)
    if team_id:
        players = [p for p in players if p.team_id == team_id]
    if search:
        players = [p for p in players if search.lower() in p.user.firstname.lower() or search.lower() in p.user.lastname.lower() or search.lower() in p.user.username.lower()]
    if position:
        players = [p for p in players if p.position and p.position.lower() == position.lower()]

    positions = sorted(set([p.position for p in players if p.position]))
    return render_template('coach/players.html', players=players, teams=teams, positions=positions, selected_position=position)

@coach_bp.route('/trainings')
@coach_required
def trainings():
    teams = Team.query.filter_by(coach_id=current_user.coach.id).all() if current_user.coach else []
    trainings = TrainingSession.query.filter(TrainingSession.team_id.in_([t.id for t in teams])).order_by(TrainingSession.date.desc()).all() if teams else []

    base_colors = [
        '#007bff', '#28a745', '#dc3545', '#ffc107', '#17a2b8', '#6610f2', '#fd7e14', '#6f42c1', '#20c997', '#e83e8c'
    ]
    team_colors = {team.id: base_colors[i % len(base_colors)] for i, team in enumerate(teams)}
    
    return render_template('coach/trainings.html', trainings=trainings, teams=teams, team_colors=team_colors)

@coach_bp.route('/trainings/add', methods=['GET', 'POST'])
@coach_required
def add_training():
    teams = Team.query.filter_by(coach_id=current_user.coach.id).all() if current_user.coach else []
    
    if request.method == 'POST':
        team_id = int(request.form['team_id'])
        date = request.form['date']
        notes = request.form['notes']
        training = TrainingSession()
        training.team_id = team_id
        training.date = date
        training.notes = notes
        db.session.add(training)
        db.session.commit()
        
        flash('Training session added!')
        return redirect(url_for('coach.trainings'))
    
    return render_template('coach/add_training.html', teams=teams)

@coach_bp.route('/trainings/edit/<int:training_id>', methods=['GET', 'POST'])
@coach_required
def edit_training(training_id):
    training = TrainingSession.query.get_or_404(training_id)
    teams = Team.query.filter_by(coach_id=current_user.coach.id).all() if current_user.coach else []
    
    if request.method == 'POST':
        training.team_id = int(request.form['team_id'])
        training.date = request.form['date']
        training.notes = request.form['notes']
        db.session.commit()
       
        flash('Training session updated!')
        return redirect(url_for('coach.trainings'))
    
    return render_template('coach/edit_training.html', training=training, teams=teams)

@coach_bp.route('/matches')
@coach_required
def matches():
    teams = Team.query.filter_by(coach_id=current_user.coach.id).all() if current_user.coach else []
    matches = Match.query.filter(Match.team_id.in_([t.id for t in teams])).order_by(Match.date.desc()).all() if teams else []

    base_colors = [
        '#007bff', '#28a745', '#dc3545', '#ffc107', '#17a2b8', '#6610f2', '#fd7e14', '#6f42c1', '#20c997', '#e83e8c'
    ]
    team_colors = {team.id: base_colors[i % len(base_colors)] for i, team in enumerate(teams)}
    
    return render_template('coach/matches.html', matches=matches, teams=teams, team_colors=team_colors)

@coach_bp.route('/matches/add', methods=['GET', 'POST'])
@coach_required
def add_match():
    teams = Team.query.filter_by(coach_id=current_user.coach.id).all() if current_user.coach else []
    
    if request.method == 'POST':
        team_id = int(request.form['team_id'])
        date = request.form['date']
        opponent = request.form['opponent']
        location = request.form['location']
        goals_scored = request.form.get('goals_scored')
        goals_missed = request.form.get('goals_missed')
        result = f"{goals_scored}-{goals_missed}" if goals_scored and goals_missed else ""
        notes = request.form['notes']
        
        match = Match()
        match.team_id = team_id
        match.date = date
        match.opponent = opponent
        match.location = location
        match.result = result
        match.notes = notes
        db.session.add(match)
        db.session.flush()  # Get match.id before commit
        # Automatically assign all players from the team
        players = Player.query.filter_by(team_id=team_id).all()
        for player in players:
            stat = PlayerMatchStat()
            stat.player_id = player.id
            stat.match_id = match.id
            db.session.add(stat)
        db.session.commit()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(success=True)
        flash('Match added! Players from the team were automatically assigned.')
        return redirect(url_for('coach.matches'))

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template('coach/add_match_form.html', teams=teams)
    return render_template('coach/add_match.html', teams=teams)

@coach_bp.route('/matches/edit/<int:match_id>', methods=['GET', 'POST'])
@coach_required
def edit_match(match_id):
    match = Match.query.get_or_404(match_id)
    teams = Team.query.filter_by(coach_id=current_user.coach.id).all() if current_user.coach else []
    if request.method == 'POST':
        match.team_id = int(request.form['team_id'])
        match.date = request.form['date']
        match.opponent = request.form['opponent']
        match.location = request.form['location']
        goals_scored = request.form.get('goals_scored')
        goals_missed = request.form.get('goals_missed')
        match.result = f"{goals_scored}-{goals_missed}" if goals_scored and goals_missed else ""
        match.notes = request.form['notes']
        db.session.commit()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(success=True)
        flash('Match updated!')
        return redirect(url_for('coach.matches'))

    goals_scored = ''
    goals_missed = ''
    if match.result and '-' in match.result:
        try:
            goals_scored, goals_missed = match.result.split('-', 1)
        except ValueError:
            pass  # Keep them empty if format is wrong

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render_template('coach/edit_match_form.html', match=match, teams=teams, goals_scored=goals_scored, goals_missed=goals_missed)
    return render_template('coach/edit_match.html', match=match, teams=teams, goals_scored=goals_scored, goals_missed=goals_missed)

@coach_bp.route('/matches/<int:match_id>/assign_players', methods=['GET', 'POST'])
@coach_required
def assign_players(match_id):
    match = Match.query.get_or_404(match_id)
    team = match.team
    # Only allow coach's own team
    if not team or team.coach_id != current_user.coach.id:
        flash('You do not have permission to assign players to this match.')
        return redirect(url_for('coach.matches'))
    players = Player.query.filter_by(team_id=team.id).all()
    assigned_player_ids = {stat.player_id for stat in match.player_stats}
    if request.method == 'POST':
        selected_player_ids = set(map(int, request.form.getlist('player_ids')))
        # Add new assignments
        for player in players:
            if player.id in selected_player_ids and player.id not in assigned_player_ids:
                stat = PlayerMatchStat()
                stat.player_id = player.id
                stat.match_id = match.id
                db.session.add(stat)
            elif player.id not in selected_player_ids and player.id in assigned_player_ids:
                # Remove assignment
                PlayerMatchStat.query.filter_by(player_id=player.id, match_id=match.id).delete()
        db.session.commit()
        flash('Player assignments updated!')
        return redirect(url_for('coach.edit_match', match_id=match.id))
    return render_template('coach/assign_players.html', match=match, players=players, assigned_player_ids=assigned_player_ids)

@coach_bp.route('/matches/<int:match_id>/edit_stats', methods=['GET', 'POST'])
@coach_required
def edit_match_stats(match_id):
    match = Match.query.get_or_404(match_id)
    team = match.team
    if not team or team.coach_id != current_user.coach.id:
        flash('You do not have permission to edit stats for this match.')
        return redirect(url_for('coach.matches'))
    player_stats = PlayerMatchStat.query.filter_by(match_id=match.id).all()
    if request.method == 'POST':
        for stat in player_stats:
            stat.goals = int(request.form.get(f'goals_{stat.id}', 0))
            stat.assists = int(request.form.get(f'assists_{stat.id}', 0))
            stat.minutes_played = int(request.form.get(f'minutes_{stat.id}', 0))
            stat.notes = request.form.get(f'notes_{stat.id}', '')
        db.session.commit()
        flash('Player stats updated!')
        return redirect(url_for('coach.edit_match', match_id=match.id))
    return render_template('coach/edit_match_stats.html', match=match, player_stats=player_stats)

@coach_bp.route('/teams/<int:team_id>/view')
@coach_required
def view_team(team_id):
    team = Team.query.get_or_404(team_id)
    if team.coach_id != current_user.coach.id:
        return '', 403
    return render_template('coach/team_detail_modal.html', team=team)

@coach_bp.route('/players/<int:player_id>/view')
@coach_required
def view_player(player_id):
    player = Player.query.get_or_404(player_id)
    if not player.team or player.team.coach_id != current_user.coach.id:
        return '', 403
    return render_template('coach/player_detail_modal.html', player=player)

def get_team_stats_for_coach(coach_id):
    teams = Team.query.filter_by(coach_id=coach_id).all()
    team_stats = []
    for team in teams:
        matches = getattr(team, 'matches', [])
        match_count = len(matches)
        total_goals = 0
        win_count = 0
        loss_count = 0
        draw_count = 0
        player_goal_map = {}
        player_assist_map = {}
        player_name_map = {}
        goals_vs_opponent = {}
        goals_by_month = {}
        match_labels = []
        goals_per_match = []
        for match in matches:
            match_labels.append(str(match.date))
            if hasattr(match, 'player_stats') and match.player_stats:
                goals = sum([stat.goals for stat in match.player_stats])
                for stat in match.player_stats:
                    player_goal_map[stat.player_id] = player_goal_map.get(stat.player_id, 0) + stat.goals
                    player_assist_map[stat.player_id] = player_assist_map.get(stat.player_id, 0) + stat.assists
                    if stat.player and stat.player.user:
                        player_name_map[stat.player_id] = stat.player.user.firstname + ' ' + stat.player.user.lastname
                    else:
                        player_name_map[stat.player_id] = 'Unknown'
                    if match.opponent:
                        goals_vs_opponent[match.opponent] = goals_vs_opponent.get(match.opponent, 0) + stat.goals
                    month = match.date.strftime('%Y-%m')
                    goals_by_month[month] = goals_by_month.get(month, 0) + stat.goals
                goals_per_match.append(goals)
                total_goals += goals
                if match.result and '-' in match.result:
                    try:
                        team_goals, opp_goals = map(int, match.result.split('-'))
                        if team_goals > opp_goals:
                            win_count += 1
                        elif team_goals < opp_goals:
                            loss_count += 1
                        else:
                            draw_count += 1
                    except Exception:
                        pass
        avg_goals = round(total_goals / match_count, 2) if match_count else 0
        top_scorers = sorted(player_goal_map.items(), key=lambda x: x[1], reverse=True)[:5]
        top_scorers = [{
            'name': player_name_map[pid],
            'goals': goals
        } for pid, goals in top_scorers]
        top_assists = sorted(player_assist_map.items(), key=lambda x: x[1], reverse=True)[:5]
        top_assists = [{
            'name': player_name_map[pid],
            'assists': assists
        } for pid, assists in top_assists]
        goals_vs_opponent_list = [{'opponent': k, 'goals': v} for k, v in goals_vs_opponent.items()]
        goals_by_month_list = [{'month': k, 'goals': v} for k, v in sorted(goals_by_month.items())]
        team_stats.append({
            'team': team,
            'match_count': match_count,
            'total_goals': total_goals,
            'match_labels': match_labels,
            'goals_per_match': goals_per_match,
            'win_count': win_count,
            'loss_count': loss_count,
            'draw_count': draw_count,
            'avg_goals': avg_goals,
            'top_scorers': top_scorers,
            'goals_vs_opponent': goals_vs_opponent_list,
            'goals_by_month': goals_by_month_list,
            'top_assists': top_assists,
        })
    return team_stats

@coach_bp.route('/analytics')
@coach_required
def analytics():
    team_stats = get_team_stats_for_coach(current_user.coach.id)
    return render_template('coach/analytics.html', team_stats=team_stats)

@coach_bp.route('/analytics/pdf')
@coach_required
def analytics_pdf():
    team_stats = get_team_stats_for_coach(current_user.coach.id)
    html = render_template('coach/analytics_pdf.html', team_stats=team_stats)
    pdf = HTML(string=html).write_pdf()
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=team_analytics.pdf'
    return response

@coach_bp.route('/matches/<int:match_id>/edit_stats/player/<int:stat_id>', methods=['POST'])
@coach_required
def update_player_stat(match_id, stat_id):
    stat = PlayerMatchStat.query.get_or_404(stat_id)
    match = Match.query.get_or_404(match_id)
    team = match.team
    # Only allow coach of the team
    if not team or team.coach_id != current_user.coach.id:
        return jsonify({'success': False, 'error': 'Permission denied'}), 403
    # Only allow stats for this match
    if stat.match_id != match.id:
        return jsonify({'success': False, 'error': 'Invalid stat for match'}), 400
    try:
        stat.goals = int(request.form.get('goals', 0))
        stat.assists = int(request.form.get('assists', 0))
        stat.minutes_played = int(request.form.get('minutes', 0))
        stat.notes = request.form.get('notes', '')
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400 