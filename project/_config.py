"""Mog config file."""

import os

# get the dir where this script lives
basedir = os.path.abspath(os.path.dirname(__file__))

DATABASE = 'mog.db'

# def the full path for the db
DATABASE_PATH = os.path.join(basedir, DATABASE)

# database URI
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + DATABASE_PATH

SQLALCHEMY_TRACK_MODIFICATIONS = False
