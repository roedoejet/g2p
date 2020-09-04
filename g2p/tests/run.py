#!/usr/bin/env python3

""" Organize tests into Test Suites
"""

import os
import sys
from unittest import TestLoader, TextTestRunner, TestSuite

# Unit tests
from g2p.log import LOGGER
from g2p.tests.test_create_mapping import MappingCreationTest
from g2p.tests.test_mappings import MappingTest
from g2p.tests.test_network import NetworkTest
from g2p.tests.test_indices import IndicesTest
from g2p.tests.test_langs import LangTest
from g2p.tests.test_transducer import TransducerTest
from g2p.tests.test_cli import CliTest
from g2p.tests.test_utils import UtilsTest
from g2p.tests.test_fallback import FallbackTest
from g2p.tests.test_api_resources import ResourceIntegrationTest
from g2p.tests.test_studio import StudioTest
from g2p.tests.test_doctor import DoctorTest


LOADER = TestLoader()

TRANSDUCER_TESTS = [
    LOADER.loadTestsFromTestCase(test)
    for test in [
        IndicesTest,
        TransducerTest
    ]
]

MAPPINGS_TESTS = [
    LOADER.loadTestsFromTestCase(test)
    for test in [
        FallbackTest,
        MappingCreationTest,
        MappingTest,
        NetworkTest,
        UtilsTest
    ]
]

LANGS_TESTS = [
    LOADER.loadTestsFromTestCase(test) for test in [
        LangTest,
    ]
]

INTEGRATION_TESTS = [
    LOADER.loadTestsFromTestCase(test) for test in [
        CliTest, ResourceIntegrationTest, StudioTest, DoctorTest
    ]
]

DEV_TESTS = TRANSDUCER_TESTS + MAPPINGS_TESTS + LANGS_TESTS + INTEGRATION_TESTS


def run_tests(suite):
    ''' Decide which Test Suite to run
    '''
    if suite == 'all':
        suite = LOADER.discover(os.path.dirname(__file__))
    if suite == 'trans':
        suite = TestSuite(TRANSDUCER_TESTS)
    if suite == 'langs':
        suite = TestSuite(LANGS_TESTS)
    if suite == 'mappings':
        suite = TestSuite(MAPPINGS_TESTS)
    if suite == 'integ':
        suite = TestSuite(INTEGRATION_TESTS)
    elif suite == 'dev':
        suite = TestSuite(DEV_TESTS)
    runner = TextTestRunner(verbosity=3)
    if isinstance(suite, str):
        LOGGER.error("Please specify a test suite to run: i.e. 'dev' or 'all'")
    else:
        return runner.run(suite)
    


if __name__ == "__main__":
    try:
        run_tests(sys.argv[1])
    except IndexError:
        LOGGER.error("Please specify a test suite to run: i.e. 'dev' or 'all'")
