"""Mog Views."""

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from slackclient import SlackClient
import re
import json
import tokens

# Config

app = Flask(__name__)
app.config.from_object('_config')
db = SQLAlchemy(app)

# Needs to be here due to an import loop
from models import Desire

# Slack stuff
sc = SlackClient(tokens.SLACK_ACCESS_TOKEN)

# Actions that can be requested
SOLO_ACTIONS = ['list']
ARG_ACTIONS = ['add', 'delete']


# Methods


def add_emoji_for_user(emoji, user):
    """Add the desire to the DB."""
    db.session.add(Desire(
        emoji,
        user,
        1)
    )
    db.session.commit()


def delete_emoji_for_user(emoji, user):
    """Delete the desire from the DB."""
    desire = db.session.query(Desire).filter_by(emoji=emoji, user=user)
    desire.delete()
    db.session.commit()


def complete_emoji_for_all_users(emoji):
    """Mark desire as completed."""
    desires = db.session.query(Desire).filter_by(emoji=emoji)
    for desire in desires:
        desire.status = 0
        # desire.date_completed = datetime.datetime.utcnow()
    db.session.commit()


def update_completed_emoji():
    """Mark updated emoji as completed."""
    for emoji in uncompleted_emoji():
        if emoji in slack_emoji():
            complete_emoji_for_all_users(emoji)


def uncompleted_emoji():
    """Get all the distinct emoji that have been desired and not completed."""
    uncompleted_emoji = []
    desires = db.session.query(Desire.emoji).distinct().filter_by(status=1)
    for desire in desires:
        uncompleted_emoji.append(desire.emoji)
    return uncompleted_emoji


def all_desires():
    """Return all the desires in the DB as a dict."""
    all_desires = {}
    desires = db.session.query(Desire).filter_by(status=1)
    for desire in desires:
        emoji = desire.emoji
        user = desire.user
        if emoji in all_desires:
            all_desires[emoji].append(user)
        else:
            all_desires[emoji] = [user]
    return all_desires


def uncompleted_emojis_by_user(user):
    """Return a list of emojis desired by a user."""
    emojis = []
    desires = db.session.query(Desire).filter_by(user=user, status=1)
    for desire in desires:
        emojis.append(desire.emoji)
    return emojis


def users_by_uncompleted_emoji(emoji):
    """Return a list of users who desire this emoji."""
    users = []
    desires = db.session.query(Desire).filter_by(emoji=emoji, status=1)
    for desire in desires:
        users.append(desire.user)
    return users


def user_desires_uncompleted_emoji(emoji, user):
    """Return if the user desires emoji."""
    return db.session.query(Desire).filter_by(
        emoji=emoji, user=user, status=1).first()


def slack_emoji():
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


def validate_command(request_form):
    """Check command entered by user is valid."""
    # Obect that will be returned.
    validated_command = {
        'user': '',
        'action': '',
        'args': '',
        'error': False,
        'error_text': ''
    }

    raw_command = request_form['text']
    validated_command['user'] = request_form['user_name']

    parsed_command = raw_command.split()

    if request_form['token'] != tokens.SLACK_OUTGOING_TOKEN:
        # Request is not coming from slack
        validated_command['error'] = True
        validated_command['error_text'] = "Invalid token."
    elif len(parsed_command) == 0:
        # No command was entered
        validated_command['error'] = True
        validated_command['error_text'] = "no command found"
    else:
        if parsed_command[0] in SOLO_ACTIONS:
            # Solo action, ignore any args
            validated_command['action'] = parsed_command[0]
        elif parsed_command[0] in ARG_ACTIONS and len(parsed_command) > 1:
            # Arg action, check for args and validate
            validated_command['action'] = parsed_command[0]
            arg = parsed_command[1].strip(':')
            # validate arg
            if len(arg) > 100:
                validated_command['error'] = True
                validated_command['error_text'] = \
                    "emoji names can only be 100 chars max"
            elif re.match(r'^[0-9a-z-_]+$', arg) is None:
                validated_command['error'] = True
                validated_command['error_text'] = \
                    "emoji names can only contain lower case letters, " \
                    "numbers, dashes and underscores"
            else:
                # arg is valid!
                validated_command['args'] = arg
        else:
            validated_command['error'] = True
            validated_command['error_text'] = 'invalid command'

    return validated_command


# Routes


@app.route('/', methods=['POST'])
def index():
    """Main endpoint that handles all MOG requests."""
    # validate command passed by user
    validated_command = validate_command(request.form)
    # load response into local variables
    user = validated_command['user']
    action = validated_command['action']
    args = validated_command['args']
    error = validated_command['error']
    error_text = validated_command['error_text']

    # String variable that will eventually be json encoded and returned
    output = ""

    if not error:
        # check outstanding desires against emoji in slack
        # includes an api call slack, so only run if the command was valid
        update_completed_emoji()

    if error:
        output = error_text

    elif action == 'list':

        # LIST

        emoji_dict = all_desires()
        if emoji_dict:
            for sorted_key in sorted(
                    emoji_dict,
                    key=lambda x: len(emoji_dict[x]),
                    reverse=True):
                output += "`:{}:` requested by {}".format(
                    sorted_key, ", ".join(emoji_dict[sorted_key])
                )
                output += "\n"
        else:
            output = "There are no currently outstanding requests."

    elif action == 'add':

        # ADD

        emoji = args
        if user_desires_uncompleted_emoji(emoji, user):
            # check to prevent same user adding multiple desires
            output = "you have already desired that emoji"
        elif emoji in slack_emoji():
            # emoji already exists
            output = "`:{0}:` already exists.it looks like :{0}:".format(emoji)
        else:
            add_emoji_for_user(
                emoji,
                user
            )
            output = "`:{}:` was added".format(emoji)

    elif action == 'delete':

        # DELETE

        emoji = args
        # check if user has desired emoji
        if user_desires_uncompleted_emoji(emoji, user):
            delete_emoji_for_user(emoji, user)
            output = "`:{}:` was deleted".format(emoji)
        else:
            output = "you have not desired that emoji " \
                "or the desire has been fulfilled"

    else:
        # UH OH
        output = "something went horribly wrong"

    # ephemeral response means only the user that issues the command sees it
    data = {"reponse_type": "ephemeral", "text": output}
    return jsonify(data)
