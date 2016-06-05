#MOG

Emoji requester bot, designed to be used on as a [Slack slash command](https://api.slack.com/slash-commands).

Web app built with Flask.

A user in a slack channel can issue the following actions:

`add {emoji}` - Records the user's request for the `{emoji}`
`delete {emoji}` - Deletes the user's request for the `{emoji}`
`list` - Lists all emojis that have been requested and who requested them, ordered by emoji that have the most requests.
