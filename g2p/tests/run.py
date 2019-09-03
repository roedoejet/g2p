""" Organize tests into Test Suites
"""

import os
from unittest import TestLoader, TextTestRunner, TestSuite

# Unit tests
from g2p.tests.test_mappings import MappingTest
from g2p.tests.test_indices import IndicesTest
from g2p.tests.test_langs import LangTest
from g2p.tests.test_transducer import TransducerTest
from g2p.tests.test_cli import CliTester
from g2p.tests.test_utils import UtilsTester


LOADER = TestLoader()

TRANSDUCER_TESTS = [
    LOADER.loadTestsFromTestCase(test)
    for test in [IndicesTest, TransducerTest]
]

MAPPINGS_TESTS = [
    LOADER.loadTestsFromTestCase(test)
    for test in [MappingTest, UtilsTester]
]

LANGS_TESTS = [
    LOADER.loadTestsFromTestCase(test) for test in [
        LangTest,
    ]
]

INTEGRATION_TESTS = [
    LOADER.loadTestsFromTestCase(test) for test in [
        CliTester,
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
    elif suite == 'dev':
        suite = TestSuite(DEV_TESTS)
    runner = TextTestRunner(verbosity=3)
    runner.run(suite)

if __name__ == "__main__":
    run_tests('all')
