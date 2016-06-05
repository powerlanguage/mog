"""Mog db models."""

from views import db


class Desire(db.Model):

    __tablename__ = "desires"

    id = db.Column(db.Integer, primary_key=True)
    emoji = db.Column(db.String, nullable=False)
    user = db.Column(db.String, nullable=False)
    status = db.Column(db.Integer, nullable=False)

    def __init__(self, emoji, user, status):
        self.emoji = emoji
        self.user = user
        self.status = status
