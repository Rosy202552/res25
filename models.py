from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Denuncia(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.Integer, nullable=False)
    nombre = db.Column(db.String(100))
    lugar = db.Column(db.String(200), nullable=False)