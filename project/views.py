"""Mog Views."""

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from slackclient import SlackClient
import json
import os

# Config

app = Flask(__name__)
app.config.from_object('_config')
db = SQLAlchemy(app)

# Needs to be here due to an import loop
from mog import Mog
from models import Desire

# If on heroku, pull tokens from enviroment vars, otherwise pull from
# gitignored tokens file

if 'ON_HEROKU' in os.environ:
    slack_access_token = os.environ['SLACK_ACCESS_TOKEN']
else:
    import tokens
    slack_access_token = tokens.SLACK_ACCESS_TOKEN

# Slack stuff
sc = SlackClient(slack_access_token)


# Helper Methods

def get_slack_emoji():
    """Return list of all emoji (custom and stock) currently in slack."""
    all_slack_emoji = []

    # load stock emoji from file
    with app.open_resource('../static/emoji-aliases.json') as f:
        stock_emojis = json.load(f)
        for category in stock_emojis:
            all_slack_emoji += stock_emojis[category]

    # concat custom emoji by slack API call
    all_slack_emoji += sc.api_call('emoji.list')['emoji'].keys()
    return all_slack_emoji


def update_completed_emoji():
    """Mark updated emoji as completed."""
    for emoji in Desire.uncompleted_emoji():
        if emoji in get_slack_emoji():
            Desire.complete_emoji_for_all_users(emoji)


def format_slack_message(text, response_type):
    """Format text to be returned to slack."""
    data = {
        'response': response_type,
        'text': text
    }
    return jsonify(data)


# Routes


@app.route('/', methods=['POST'])
def index():
    """Main endpoint that handles all MOG requests."""
    mog = Mog(request.form)
    if not mog.error:
        update_completed_emoji()
        mog.perform_action()

    return format_slack_message(mog.response_message, mog.response_type)
