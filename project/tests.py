"""Tests."""

import unittest
import os

from project.views import app, db, complete_emoji_for_all_users
from project._config import basedir
from project.tokens import SLACK_OUTGOING_TOKEN

TEST_DB = 'test.db'


class MainTests(unittest.TestCase):
    """Mog test class."""

    def setUp(self):
        """Set up."""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['DEBUG'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + \
            os.path.join(basedir, TEST_DB)
        self.app = app.test_client()
        db.create_all()

        self.assertEquals(app.debug, False)

    def tearDown(self):
        """Tear Down."""
        db.session.remove()
        db.drop_all()

    # helper methods

    """
    Slack dict sent to endpoint, use to build mock

    ('token', u'xxxx'),
    ('team_domain', u'trollpalace'),
    ('channel_name', u'general'),
    ('user_id', u'U0HEM650W'),
    ('response_url', u'https://hooks.slack.com../xxxx'),
    ('channel_id', u'C0GTML45A'),
    ('command', u'/mog'),
    ('text', u'list'),
    ('team_id', u'T0GTTK2CQ'),
    ('user_name', u'josh')
    """

    def issue_command(self, text, user_name, token=SLACK_OUTGOING_TOKEN):
        return self.app.post(
            '/',
            data=dict(
                token=token,
                text=text,
                user_name=user_name
            )
        )

    # tests

    def test_duplicate_desires_cannot_be_added_by_same_user(self):
        self.issue_command('add chopz', 'powerlanguage')
        response = self.issue_command('add chopz', 'powerlanguage')
        self.assertNotIn("`:chopz:` was added", response.data)

    def test_duplicate_desires_can_be_added_by_different_users(self):
        self.issue_command('add chopz', 'powerlanguage')
        response = self.issue_command('add chopz', 'codhand')
        self.assertIn("`:chopz:` was added", response.data)

    def test_add_desire_via_command(self):
        response = self.issue_command('add chopz', 'powerlanguage')
        self.assertIn("`:chopz:` was added", response.data)

    def test_user_can_delete_desire_they_added(self):
        self.issue_command('add chopz', 'powerlanguage')
        response = self.issue_command('delete chopz', 'powerlanguage')
        self.assertIn("`:chopz:` was deleted", response.data)

    def test_user_cannot_delete_desire_they_did_not_add(self):
        self.issue_command('add chopz', 'powerlanguage')
        response = self.issue_command('delete chopz', 'codhand')
        self.assertNotIn("`:chopz:` was deleted", response.data)

    def test_error_when_user_sends_no_command(self):
        response = self.issue_command('', 'codhand')
        self.assertIn("no command found", response.data)

    def test_error_on_invalid_command(self):
        response = self.issue_command('krinkle chopz', 'powerlanguage')
        self.assertIn("invalid command", response.data)

    def test_error_when_user_sends_no_args_with_arg_command(self):
        response = self.issue_command('add', 'powerlanguage')
        self.assertIn("invalid command", response.data)

    def test_extra_args_are_ignored_with_arg_command(self):
        response = self.issue_command('add chopz yo yo cat', 'powerlanguage')
        self.assertIn("`:chopz:` was added", response.data)

    def test_extra_args_are_ignored_with_solo_command(self):
        response = self.issue_command('list cats', 'powerlanguage')
        self.assertNotIn("invalid command", response.data)

    def test_error_if_emoji_name_contains_invalid_chars(self):
        response = self.issue_command('add cat*s', 'powerlanguage')
        self.assertIn(
            "emoji names can only contain lower case letters, numbers, "
            "dashes and underscores",
            response.data)

    def test_error_if_emoji_name_too_long(self):
        response = self.issue_command(
            "add "
            "123456789012345678901234567890123456789012345678901234567890"
            "123456789012345678901234567890123456789012345678901234567890",
            'powerlanguage'
        )
        self.assertIn("emoji names can only be 100 chars max", response.data)

    def test_emoji_added_if_issued_with_colons(self):
        response = self.issue_command('add :chopz:', 'powerlanguage')
        self.assertIn("`:chopz:` was added", response.data)

    def test_error_if_custom_emoji_already_exists_on_slack(self):
        response = self.issue_command('add rage4', 'powerlanguage')
        self.assertIn(
            "`:rage4:` already exists.it looks like :rage4:",
            response.data
        )

    def test_error_if_standard_emoji_already_exists_on_slack(self):
        response = self.issue_command('add shit', 'powerlanguage')
        self.assertIn(
            "`:shit:` already exists.it looks like :shit:",
            response.data
        )

    def test_user_can_request_list_of_emoji(self):
        self.issue_command('add chopz', 'powerlanguage')
        self.issue_command('add chopz', 'codhand')
        self.issue_command('add biff', 'tonyhat')
        self.issue_command('add chopz', 'tonyhat')
        self.issue_command('add kunk', 'user_blep')
        self.issue_command('add kunk', 'user_heh')
        self.issue_command('add kunk', 'user_jef')
        self.issue_command('add kunk', 'user_feg')
        response = self.issue_command('list', 'codhand')
        self.assertIn(
            ":chopz: powerlanguage, codhand, tonyhat", response.data
        )

    def test_user_cant_delete_completed_desire(self):
        self.issue_command('add chopz', 'powerlanguage')
        complete_emoji_for_all_users('chopz')
        response = self.issue_command('delete chopz', 'powerlanguage')
        self.assertNotIn("`:chopz:` was deleted", response.data)
        self.assertIn(
            "you have not desired that emoji or the desire has been fulfilled",
            response.data
        )

    def test_return_string_on_empty_list(self):
        response = self.issue_command('list', 'powerlanguage')
        self.assertIn(
            "There are no currently outstanding requests.", response.data
        )

    def test_error_on_invalid_token_from_slack(self):
        response = self.issue_command('list', 'powerlanguage', 'bogus_token')
        self.assertIn(
            "Invalid token.", response.data
        )


if __name__ == "__main__":
    unittest.main()
