from app import create_app, db
from models import Note, User


app = create_app()

with app.app_context():
    db.drop_all()
    db.create_all()

    alice = User(username="alice")
    alice.set_password("secret123")
    bob = User(username="bob")
    bob.set_password("secret123")

    db.session.add_all([alice, bob])
    db.session.commit()

    notes = [
        Note(title="Plan sprint", content="Finish the API lab", category="work", user_id=alice.id),
        Note(title="Grocery list", content="Milk and bread", category="personal", user_id=alice.id),
        Note(title="Workout", content="30 min run", category="fitness", user_id=bob.id),
    ]
    db.session.add_all(notes)
    db.session.commit()
    print("Seed data created")
