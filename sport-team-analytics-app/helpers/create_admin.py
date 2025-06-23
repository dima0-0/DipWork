from app import app
from extensions import db
from src.models.models import User, Coach

with app.app_context():
    if not User.query.filter_by(username='admin').first():
        user = User()
        user.username = 'admin'
        user.firstname = 'Іван'
        user.lastname = 'Палійчук'
        user.email = 'admin@example.com'
        user.role = 'admin'
        user.set_password('adminpass')
        db.session.add(user)
        db.session.commit()
        print("Admin user created: username=admin, password=adminpass")
    else:
        print("Admin user already exists.")

    coaches = User.query.filter_by(role='coach').all()
    created = 0
    for user in coaches:
        if not user.coach:
            coach = Coach()
            coach.user_id = user.id
            db.session.add(coach)
            created += 1
    db.session.commit()
    print(f"Backfilled {created} coach records.")