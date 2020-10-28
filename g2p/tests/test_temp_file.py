#!/usr/bin/env python3

"""
Test PortableNamedTemporaryFile class
"""

import os
import sys
import unittest
from tempfile import NamedTemporaryFile

from g2p.log import LOGGER
from g2p.tempfile import PortableNamedTemporaryFile


class TestTempFile(unittest.TestCase):
    def testBasicFile(self):
        f = open("delme_test_temp_file", mode="w")
        f.write("some text")
        f.close()
        os.unlink("delme_test_temp_file")

    def testNTF(self):
        tf = NamedTemporaryFile(prefix="testtempfile_testNTF_", delete=False, mode="w")
        tf.write("Some text")
        # LOGGER.debug("tf.name {}".format(tf.name))
        tf.close()
        readf = open(tf.name, mode="r")
        text = readf.readline()
        self.assertEqual(text, "Some text")
        readf.close()
        os.unlink(tf.name)

    def testDeleteFalse(self):
        tf = PortableNamedTemporaryFile(
            prefix="testtempfile_testDeleteFalse_", delete=False, mode="w"
        )
        tf.write("Some text")
        tf.close()
        # LOGGER.info(tf.name)
        readf = open(tf.name, mode="r")
        text = readf.readline()
        readf.close()
        self.assertEqual(text, "Some text")
        os.unlink(tf.name)

    def testTypicalUsage(self):
        tf = PortableNamedTemporaryFile(
            prefix="testtempfile_testTypicalUsage_", delete=True, mode="w"
        )
        # LOGGER.info(tf.name)
        tf.write("Some text")
        tf.close()
        # LOGGER.info(tf.name)
        readf = open(tf.name, mode="r")
        text = readf.readline()
        readf.close()
        self.assertEqual(text, "Some text")

    def testUsingWith(self):
        with PortableNamedTemporaryFile(
            prefix="testtempfile_testUsingWith_", delete=True, mode="w"
        ) as tf:
            # LOGGER.info(tf.name)
            tf.write("Some text")
            tf.close()
            # LOGGER.info(tf.name)
            readf = open(tf.name, mode="r")
            text = readf.readline()
            readf.close()
            self.assertEqual(text, "Some text")

    def testSeek(self):
        tf = PortableNamedTemporaryFile(
            prefix="testtempfile_testSeek_", delete=True, mode="w+"
        )
        tf.write("Some text")
        tf.seek(0)
        text = tf.readline()
        self.assertEqual(text, "Some text")
        tf.close()
        os.unlink(tf.named_temporary_file.name)


if __name__ == "__main__":
    LOGGER.setLevel("DEBUG")
    unittest.main()
