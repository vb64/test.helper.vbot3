"""Vbot3 tester."""
from telemulator3 import Telemulator, private_command, private_text
from tester_flask import TestFlask
from test_helper_gae3 import TestGae3


class MockReq:
    """Mock flask request."""

    def __init__(self, data):
        """Set request data."""
        self.data = data


class MockRequests:
    """Mock requests package."""

    def __init__(self):
        """Set calls counter."""
        self.calls = {}
        self.timeout = 0

    def get(self, url, timeout=10):
        """Get method emulator."""
        self.timeout = timeout
        if url not in self.calls:
            self.calls[url] = 0
        self.calls[url] += 1


def start_command_dflt(message, bot):
    """Handle private /start command."""
    user = bot.user_entry_point(message)
    bot.reply(message, "Hi ID {}".format(user.key.id()))


class Vbot3Tester(TestFlask, TestGae3, Telemulator):
    """Tester for Vbot3."""

    teleuser = None
    private = None
    group = None

    def init(self, flask_app, vbot3, bot_name, bot_username, queue_yaml_dir, start_command_cust=None):
        """Init tests stuff."""
        TestFlask.set_up(self, flask_app)
        TestGae3.set_up(self, queue_yaml_dir)
        self.set_tested_bot(vbot3, name=bot_name, username=bot_username)

        start_command = start_command_cust or start_command_dflt
        vbot3.private_command('start')(lambda msg: start_command(msg, vbot3))
        vbot3.set_default_content_handlers()  # must be last in handlers chain

        self.teleuser = self.api.create_user('Test', 'User', language_code='en')
        self.private = self.teleuser.private()
        self.group = self.teleuser.create_group("Test group")
        self.private_command('/start')

    def tearDown(self):
        """Clear tests."""
        TestGae3.tear_down(self)
        super().tearDown()

    def private_command(self, cmd, from_user=None):
        """Call private command."""
        from_user = from_user or self.teleuser
        with self.app.test_request_context():
            private_command(cmd, from_user)

    def private_text(self, text, from_user=None):
        """Call private command."""
        from_user = from_user or self.teleuser
        with self.app.test_request_context():
            private_text(text, from_user)

    def assert_in_history(self, substring, chat=None):
        """Check substring in the history of given chat."""
        chat = chat or self.private
        assert chat.history.contain(substring)

    def assert_not_in_history(self, substring, chat=None):
        """Check substring not in the history of given chat."""
        chat = chat or self.private
        assert not chat.history.contain(substring)

    def assert_menu_size(self, size, chat=None):
        """Check custom keyboard size in chat."""
        chat = chat or self.private
        assert chat.keyboard.menu_size() == size

    def execute_taskqueue(self, queue_name='default'):
        """Run all tasks for given GAE taskqueue."""
        tasks = self.gae_tasks(queue_name=queue_name, flush_queue=True)
        for task in tasks:
            # print "#->", task['method'], task['url'], task['body']
            if task['method'] == 'GET':
                response = self.client.get(task['url'])
            elif task['method'] == 'POST':
                response = self.client.post(task['url'], data=task['body'])
            else:
                response = 'Wrong taskqueue method: {}'.format(task['method']), 500, {}

            assert response.status_code == 200
