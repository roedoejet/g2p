from unittest import main, TestCase

import requests

from g2p import APP
from g2p.log import LOGGER
from g2p.cli import update

class CliTest(TestCase):
    def setUp(self):
        self.runner = APP.test_cli_runner()

    def test_update(self):
        result = self.runner.invoke(update)
        self.assertEqual(result.exit_code, 0)

if __name__ == '__main__':
    main()