from extensions import db
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    firstname = db.Column(db.String(80), nullable=False)
    lastname = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin', 'coach', 'player'
    is_active = db.Column(db.Boolean, default=True)

    player = relationship('Player', uselist=False, back_populates='user')
    coach = relationship('Coach', uselist=False, back_populates='user')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return f'<User {self.username} ({self.firstname} {self.lastname}, {self.role})>' 


class Coach(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)
    user = relationship('User', back_populates='coach')
    teams = relationship('Team', back_populates='coach')

    def __repr__(self):
        return f'<Coach {self.user.username}>'


class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)
    user = relationship('User', back_populates='player')
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    team = relationship('Team', back_populates='players')
    position = db.Column(db.String(50))
    number = db.Column(db.Integer)
    date_of_birth = db.Column(db.Date)
    photo_url = db.Column(db.String(255))

    def __repr__(self):
        return f'<Player {self.user.username}>'


class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    players = relationship('Player', back_populates='team')
    coach_id = db.Column(db.Integer, db.ForeignKey('coach.id'))
    coach = relationship('Coach', back_populates='teams')
    matches = db.relationship('Match', back_populates='team')

    def __repr__(self):
        return f'<Team {self.name}>'


class TrainingSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    team = relationship('Team')
    notes = db.Column(db.Text)
    player_trainings = relationship('PlayerTraining', back_populates='training_session')

    def __repr__(self):
        return f'<TrainingSession {self.team.name} on {self.date}>'


class PlayerTraining(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    player = relationship('Player')
    training_session_id = db.Column(db.Integer, db.ForeignKey('training_session.id'))
    training_session = relationship('TrainingSession', back_populates='player_trainings')
    attended = db.Column(db.Boolean, default=False)
    performance_notes = db.Column(db.Text)


class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('team.id'))
    team = db.relationship('Team', back_populates='matches')
    opponent = db.Column(db.String(100))
    location = db.Column(db.String(100))
    result = db.Column(db.String(20))
    notes = db.Column(db.Text)
    player_stats = relationship('PlayerMatchStat', back_populates='match')

    def __repr__(self):
        return f'<Match {self.team.name} vs {self.opponent}>'


class PlayerMatchStat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    player = relationship('Player')
    match_id = db.Column(db.Integer, db.ForeignKey('match.id'))
    match = relationship('Match', back_populates='player_stats')
    goals = db.Column(db.Integer, default=0)
    assists = db.Column(db.Integer, default=0)
    minutes_played = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text) 