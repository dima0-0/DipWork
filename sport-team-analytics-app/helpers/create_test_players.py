from app import app
from extensions import db
from src.models.models import User, Player, Team

with app.app_context():
    # Get the first team to assign players to (if any)
    # team = Team.query.first()
    for i in range(1, 11):
        username = f'testplayer{i}'
        email = f'testplayer{i}@example.com'
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            continue
        user = User()
        user.username=username,
        user.firstname=f'Player{i}',
        user.lastname=f'Test{i}',
        user.email=email,
        user.role='player',
        user.set_password('password123')
        db.session.add(user)
        db.session.flush()
        
        player = Player()
        player.user_id = user.id
        player.team_id = None
        db.session.add(player)
    db.session.commit()
    print('Added 10 test players.') 