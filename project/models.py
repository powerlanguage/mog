"""Mog db models."""

from views import db
from sqlalchemy import func

class Desire(db.Model):

    __tablename__ = "desires"

    id = db.Column(db.Integer, primary_key=True)
    emoji = db.Column(db.String, nullable=False)
    user = db.Column(db.String, nullable=False)
    status = db.Column(db.Integer, nullable=False)

    def __init__(self, emoji, user, status):
        """Constructor."""
        self.emoji = emoji
        self.user = user
        self.status = status

    @classmethod
    def add_emoji_for_user(cls, emoji, user):
        """Add the desire to the DB."""
        db.session.add(Desire(emoji, user, 1))
        db.session.commit()

    @classmethod
    def delete_emoji_for_user(cls, emoji, user):
        """Delete the desire from the DB."""
        desire = db.session.query(Desire).filter_by(emoji=emoji, user=user)
        desire.delete()
        db.session.commit()

    @classmethod
    def complete_emoji_for_all_users(cls, emoji):
        """Mark desire as completed."""
        desires = db.session.query(Desire).filter_by(emoji=emoji)
        for desire in desires:
            desire.status = 0
        db.session.commit()

    @classmethod
    def uncompleted_emoji(cls):
        """Get all the distinct desired, uncompleted emoji."""
        uncompleted_emoji = []
        desires = db.session.query(Desire.emoji).distinct().filter_by(status=1)
        for desire in desires:
            uncompleted_emoji.append(desire.emoji)
        return uncompleted_emoji

    @classmethod
    def all_desires(cls, _status):
        """Return all the desires by status as list sorted by most reqs."""
        all_desires = {}
        desires = db.session.query(Desire).filter_by(status=_status)
        for desire in desires:
            emoji = desire.emoji
            user = desire.user
            if emoji in all_desires:
                all_desires[emoji].append(user)
            else:
                all_desires[emoji] = [user]
        return sorted(all_desires, key=lambda x: len(
            all_desires[x]), reverse=True)

    @classmethod
    def emojis_by_user(cls, user, status):
        """Return a list of emojis desired by a user."""
        emojis = []
        desires = db.session.query(Desire).filter_by(user=user, status=status)
        for desire in desires:
            emojis.append(desire.emoji)
        return emojis

    @classmethod
    def users_by_emoji(cls, emoji, status):
        """Return a list of users who desire this emoji."""
        users = []
        desires = db.session.query(Desire).filter_by(emoji=emoji, status=status)
        for desire in desires:
            users.append(desire.user)
        return users

    @classmethod
    def user_desires_uncompleted_emoji(cls, emoji, user):
        """Return if the user desires emoji."""
        return db.session.query(Desire).filter_by(
            emoji=emoji, user=user, status=1).first()
