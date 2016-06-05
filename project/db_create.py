"""Mog db creator."""

from views import db
from models import Desire

db.create_all()

# insert data


db.session.commit()
