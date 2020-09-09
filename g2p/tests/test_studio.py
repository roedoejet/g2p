#!/usr/bin/env python3

from unittest import TestCase

from g2p.app import APP, SOCKETIO

class StudioTest(TestCase):
    def setUp(self):
        self.flask_test_client = APP.test_client()
        self.socketio_test_client = SOCKETIO.test_client(APP, flask_test_client=self.flask_test_client)

    def test_socket_connection(self):
        self.assertTrue(self.socketio_test_client.is_connected())
