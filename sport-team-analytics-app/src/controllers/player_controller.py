from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from src.models.models import Match, PlayerMatchStat


def player_required(f):
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role != 'player':
            flash('Player access required.')
            return redirect(url_for('hello_world'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

player_bp = Blueprint('player', __name__, url_prefix='/player')

@player_bp.route('/')
@player_required
def dashboard():
    player = current_user.player

    stats = PlayerMatchStat.query.filter_by(player_id=player.id).join(Match).order_by(Match.date.asc()).all()
    matches = [stat.match for stat in stats]

    total_matches = len(stats)
    total_goals = sum(stat.goals for stat in stats)
    total_assists = sum(stat.assists for stat in stats)
    goals_per_match = round(total_goals / total_matches, 2) if total_matches else 0
    assists_per_match = round(total_assists / total_matches, 2) if total_matches else 0

    perf_labels = [m.date.strftime('%Y-%m-%d') for m in matches]
    perf_goals = [stat.goals for stat in stats]
    perf_assists = [stat.assists for stat in stats]

    recent_stats = stats[-5:][::-1]

    team_avg_goals = team_avg_assists = None
    if player.team:
        team_player_ids = [p.id for p in player.team.players]
        team_stats = PlayerMatchStat.query.filter(PlayerMatchStat.player_id.in_(team_player_ids)).all()
        team_total_matches = len(team_stats)
        team_total_goals = sum(s.goals for s in team_stats)
        team_total_assists = sum(s.assists for s in team_stats)
        team_avg_goals = round(team_total_goals / team_total_matches, 2) if team_total_matches else 0
        team_avg_assists = round(team_total_assists / team_total_matches, 2) if team_total_matches else 0
    
    return render_template('player/dashboard.html', player=player, total_matches=total_matches, total_goals=total_goals, total_assists=total_assists, goals_per_match=goals_per_match, assists_per_match=assists_per_match, perf_labels=perf_labels, perf_goals=perf_goals, perf_assists=perf_assists, recent_stats=recent_stats, team_avg_goals=team_avg_goals, team_avg_assists=team_avg_assists) 