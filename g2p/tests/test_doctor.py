#!/usr/bin/env python3

from unittest import main, TestCase
from g2p.log import LOGGER
from g2p.mappings.langs.utils import check_ipa_known_segs

class DoctorTest(TestCase):
    def setUp(self):
        pass

    def test_ipa_known_segs_fra(self):
        with self.assertLogs(LOGGER, level='WARNING') as cm:
            check_ipa_known_segs(["fra-ipa"])
        self.assertIn("vagon", "".join(cm.output))
        self.assertIn("panphon", "".join(cm.output))
        self.assertGreaterEqual(len(cm.output), 2)

    def test_ipa_known_segs_all(self):
        with self.assertLogs(LOGGER, level='WARNING') as cm:
            check_ipa_known_segs()
        self.assertGreaterEqual(len(cm.output), 20)


if __name__ == '__main__':
    main()
