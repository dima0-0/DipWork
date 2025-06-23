from app import app
from extensions import db
from src.models.models import Player
from faker import Faker
import random

POSITIONS = ["Forward", "Midfielder", "Defender", "Goalkeeper"]
fake = Faker()

with app.app_context():
    players = Player.query.all()
    for player in players:
        player.position = random.choice(POSITIONS)
        player.number = random.randint(1, 99)
        # Random date of birth between 1990-01-01 and 2010-12-31
        player.date_of_birth = fake.date_between(start_date="-34y", end_date="-14y")
    db.session.commit()
    print(f"Updated {len(players)} players with random data.") 