"""Vbot3 tester."""
from telemulator3 import Telemulator, private_command, private_text, private_document, send_text
from telemulator3.update.message import Text, Command, Contact
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


class Vbot3Tester(TestFlask, TestGae3, Telemulator):
    """Tester for Vbot3."""

    teleuser = None
    private = None
    group = None
    tele_message = None
    group_message = None

    def init(self, flask_app, vbot3, bot_name, bot_username, queue_yaml_dir):
        """Init tests stuff."""
        TestFlask.set_up(self, flask_app)
        TestGae3.set_up(self, queue_yaml_dir)
        self.set_tested_bot(vbot3, name=bot_name, username=bot_username)

        self.teleuser = self.api.create_user('Test', 'User', language_code='en')
        self.private = self.teleuser.private()
        self.group = self.teleuser.create_group("Test group")
        self.tele_message = Text(self.private, self.teleuser, "Hello private!")
        self.group_message = Text(self.group, self.teleuser, "Hello group!")

    def tearDown(self):
        """Clear tests."""
        TestGae3.tear_down(self)
        super().tearDown()

    def send2chat(self, chat, message):
        """Send message to given chat."""
        with self.app.test_request_context():
            return chat.send(message)

    def send_command(self, chat, command, from_user=None, **kwargs):
        """Send command to given chat."""
        from_user = from_user or self.teleuser
        return self.send2chat(chat, Command(chat, from_user, command, **kwargs))

    def send_contact(  # pylint: disable=too-many-arguments
      self, chat, phone_number, from_user=None, first_name='Contact', last_name='User', user_id=777, **kwargs
    ):
        """Send contact to given chat."""
        from_user = from_user or self.teleuser
        return self.send2chat(
          chat,
          Contact(chat, from_user, phone_number, first_name, last_name, user_id, **kwargs)
        )

    def send_text(self, chat, text, from_user=None):
        """Send text to chat and return sended message."""
        from_user = from_user or self.teleuser
        return send_text(chat, text, from_user)

    def tg_button(self, row, index=0, chat=None, user=None):
        """Send custom keyboard item to chat."""
        chat = chat or self.private
        user = user or self.teleuser
        chat.keyboard.menu_item(user, index, row=row)

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

    def private_document(self, file_name, from_user=None, file_size=600):
        """Call private command."""
        from_user = from_user or self.teleuser
        with self.app.test_request_context():
            private_document(file_name, from_user=from_user, file_size=file_size)

    def private_contact(  # pylint: disable=too-many-arguments
      self, phone_number, from_user=None, first_name='Contact', last_name='User', user_id=777, **kwargs
    ):
        """Send contact to private chat."""
        from_user = from_user or self.teleuser
        return self.send_contact(
          from_user.private(), phone_number, from_user=from_user,
          first_name=first_name, last_name=last_name, user_id=user_id, **kwargs
        )

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
