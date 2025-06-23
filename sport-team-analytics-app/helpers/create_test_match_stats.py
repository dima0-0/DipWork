import random
from app import app
from extensions import db
from src.models.models import Match, Player, PlayerMatchStat

def random_result():
    goals1 = random.randint(0, 5)
    goals2 = random.randint(0, 5)
    return f"{goals1}-{goals2}"

with app.app_context():
    matches = Match.query.all()
    for match in matches:
        if not match.result or match.result.strip() == '':
            match.result = random_result()

        players = Player.query.filter_by(team_id=match.team_id).all()
        for player in players:

            if PlayerMatchStat.query.filter_by(player_id=player.id, match_id=match.id).first():
                continue
            goals = random.randint(0, 3)
            assists = random.randint(0, 2)
            minutes_played = random.randint(30, 90)
            notes = random.choice(['', 'Good game', 'Needs improvement', 'Excellent performance'])
            
            stat = PlayerMatchStat()
            stat.player_id=player.id,
            stat.match_id=match.id,
            stat.goals=goals,
            stat.assists=assists,
            stat.minutes_played=minutes_played,
            stat.notes=notes

            db.session.add(stat)
    db.session.commit()
    print('Populated PlayerMatchStat and match results for all matches.') 