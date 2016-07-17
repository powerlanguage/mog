"""Mog class."""

import os
import re


# If on heroku, pull tokens from enviroment vars, otherwise pull from
# gitignored tokens file

if 'ON_HEROKU' in os.environ:
    slack_outgoing_token = os.environ['SLACK_OUTGOING_TOKEN']
else:
    import tokens
    slack_outgoing_token = tokens.SLACK_OUTGOING_TOKEN

# Actions that can be requested
SOLO_ACTIONS = ['list', 'completed', 'mine', 'help', 'count']
ARG_ACTIONS = ['add', 'delete']

import views
from models import Desire


class Mog(object):
    """Mog class."""

    def __init__(self, request_form):
        """Constructor."""
        self.request = request_form
        self.request_text = request_form['text']
        self.user = request_form['user_name']
        self.action = ''
        self.emoji = ''
        self.error = False
        self.response_message = ''
        self.response_type = 'ephemeral'
        self.parse_request()

    def set_error(self, error_message):
        """Set error and error message."""
        self.error = True
        self.response_message = "Error. " + error_message

    def set_response(self, response_message):
        """Set response."""
        self.response_message = response_message

    def parse_request(self):
        """Parse and validate incoming requests."""
        # check if request is from slack, return error if not
        if self.request['token'] != slack_outgoing_token:
            self.set_error('Invalid token.')
            return

        # check if user entered request
        if self.request_text == '':
            self.set_error('No command found.')
            return

        split = self.request_text.split()

        if len(split) > 0:
            action = split[0]

        if len(split) > 1:
            emoji = split[1].strip(':')

        if action in SOLO_ACTIONS:
            self.action = action
        elif action in ARG_ACTIONS and len(split) <= 1:
            self.set_error("`{}` requires an emoji name.".format(action))
        elif action in ARG_ACTIONS and len(split) > 1:
            self.action = action
            emoji_match = re.match('^(?P<emoji>[a-zA-Z0-9_-]{0,100})$', emoji)
            if emoji_match:
                self.emoji = emoji_match.group('emoji')
            else:
                self.set_error("Invalid emoji name `:{}:`.".format(emoji))
        else:
            self.set_error("Unknown command `{}`.".format(action))

        return

    def perform_action(self):
        """Perform the required action and set the response."""
        action_methods = {
            'list': self.list_uncompleted_emoji,
            'completed': self.list_completed_emoji,
            'add': self.add_emoji,
            'delete': self.delete_emoji,
            'mine': self.get_user_uncompleted_emoji,
            'help': self.get_help,
        }
        # call the action method from by getting the action from the dict
        response = action_methods[self.action]()
        self.set_response(response)

    def list_uncompleted_emoji(self):
        """Return uncompleted emoji and who requested them."""
        status = 1
        output = ''
        emojis = self.list_emoji(status)
        if emojis:
            for emoji in emojis:
                    output += "`:{}:` requested by {}\n".format(
                        emoji, ", ".join(Desire.users_by_emoji(emoji, status))
                    )
        else:
            output = "There are no outstanding requests."
        return output

    def list_completed_emoji(self):
        """Return completed emoji and who requested them."""
        status = 0
        output = ''
        emojis = self.list_emoji(status)
        if emojis:
            for emoji in emojis:
                    output += ":{0}: - `:{0}:` requested by {1}\n".format(
                        emoji, ", ".join(Desire.users_by_emoji(emoji, status))
                    )
        else:
            output = "There are no completed requests."
        return output

    def list_emoji(self, status):
        """Helper method to get desires by status."""
        return Desire.all_desires(status)

    def add_emoji(self):
        """Add a request for emoji by user and returns confirmation text."""
        emoji = self.emoji
        user = self.user
        if Desire.user_desires_uncompleted_emoji(emoji, user):
            # check to prevent same user adding multiple desires
            output = "You have already requested `:{}:`".format(emoji)
        elif emoji in views.get_slack_emoji():
            # emoji already exists
            output = "`:{0}:` already exists. It looks like :{0}:".format(
                emoji)
        else:
            Desire.add_emoji_for_user(emoji, user)
            output = "You requested `:{}:`".format(emoji)
        return output

    def delete_emoji(self):
        """Delete a request for emoji by user and returns confirmation text."""
        emoji = self.emoji
        user = self.user
        # check if user has desired emoji
        if Desire.user_desires_uncompleted_emoji(emoji, user):
            Desire.delete_emoji_for_user(emoji, user)
            output = "Your request for `:{}:` was deleted.".format(emoji)
        else:
            output = "You have not desired that emoji " \
                "or the desire has been fulfilled."
        return output

    def get_user_uncompleted_emoji(self):
        """Return list of users uncompleted emoji."""
        user = self.user
        emojis = Desire.emojis_by_user(user, 1)
        if emojis:
            output = "You've requested: {}".format(
                ", ".join("`:{}:`".format(emoji) for emoji in emojis)
            )
        else:
            output = "You do not have any outstanding desires."
        return output

    def get_help(self):
        """Return help string."""
        output = "Valid commands: {}".format(
            ', '.join(ARG_ACTIONS + SOLO_ACTIONS)
        )
        output += ".\n\n"
        output += "Request emoji that you'd like to see on Slack and see the "\
            "most popular requests."
        return output
