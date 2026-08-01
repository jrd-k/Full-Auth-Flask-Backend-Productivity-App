from flask import Flask, jsonify, request, session
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from sqlalchemy.exc import IntegrityError

from config import Config
from models import Note, User, db


bcrypt = Bcrypt()
migrate = Migrate()


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)

    if test_config:
        app.config.update(test_config)

    bcrypt.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)

    @app.route("/signup", methods=["POST"])
    def signup():
        data = request.get_json()
        if not data or not data.get("username") or not data.get("password"):
            return jsonify({"error": "username and password are required"}), 400

        user = User(username=data["username"])
        user.set_password(data["password"])

        try:
            db.session.add(user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return jsonify({"error": "username already exists"}), 409

        session["user_id"] = user.id
        return jsonify({"id": user.id, "username": user.username}), 201

    @app.route("/login", methods=["POST"])
    def login():
        data = request.get_json()
        if not data or not data.get("username") or not data.get("password"):
            return jsonify({"error": "username and password are required"}), 400

        user = User.query.filter_by(username=data["username"]).first()
        if not user or not user.check_password(data["password"]):
            return jsonify({"error": "invalid credentials"}), 401

        session["user_id"] = user.id
        return jsonify({"id": user.id, "username": user.username}), 200

    @app.route("/logout", methods=["POST"])
    def logout():
        session.pop("user_id", None)
        return jsonify({"message": "logged out"}), 200

    @app.route("/me")
    def me():
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "not authenticated"}), 401

        user = db.session.get(User, user_id)
        if not user:
            session.pop("user_id", None)
            return jsonify({"error": "not authenticated"}), 401

        return jsonify({"id": user.id, "username": user.username}), 200

    @app.before_request
    def require_auth():
        public_routes = {"/signup", "/login", "/logout"}
        if request.path in public_routes:
            return None

        if request.path.startswith("/static"):
            return None

        user_id = session.get("user_id")
        if not user_id:
            return jsonify({"error": "not authenticated"}), 401

        user = db.session.get(User, user_id)
        if not user:
            session.pop("user_id", None)
            return jsonify({"error": "not authenticated"}), 401

    @app.route("/notes", methods=["GET"])
    def index_notes():
        user_id = session["user_id"]
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 5, type=int)
        pagination = Note.query.filter_by(user_id=user_id).order_by(Note.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
        return jsonify({"items": [note.to_dict() for note in pagination.items], "page": pagination.page, "pages": pagination.pages, "total": pagination.total}), 200

    @app.route("/notes", methods=["POST"])
    def create_note():
        data = request.get_json()
        if not data or not data.get("title") or not data.get("content") or not data.get("category"):
            return jsonify({"error": "title, content, and category are required"}), 400

        note = Note(title=data["title"], content=data["content"], category=data["category"], user_id=session["user_id"])
        db.session.add(note)
        db.session.commit()
        return jsonify(note.to_dict()), 201

    @app.route("/notes/<int:note_id>", methods=["GET"])
    def get_note(note_id):
        note = db.session.get(Note, note_id)
        if not note or note.user_id != session["user_id"]:
            return jsonify({"error": "note not found"}), 404
        return jsonify(note.to_dict()), 200

    @app.route("/notes/<int:note_id>", methods=["PATCH"])
    def update_note(note_id):
        note = db.session.get(Note, note_id)
        if not note or note.user_id != session["user_id"]:
            return jsonify({"error": "note not found"}), 404

        data = request.get_json()
        if not data:
            return jsonify({"error": "request body is required"}), 400

        for field in ["title", "content", "category"]:
            if field in data:
                setattr(note, field, data[field])

        db.session.commit()
        return jsonify(note.to_dict()), 200

    @app.route("/notes/<int:note_id>", methods=["DELETE"])
    def delete_note(note_id):
        note = db.session.get(Note, note_id)
        if not note or note.user_id != session["user_id"]:
            return jsonify({"error": "note not found"}), 404

        db.session.delete(note)
        db.session.commit()
        return jsonify({}), 204

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
