#!/usr/bin/env python3

""" Organize tests into Test Suites
"""

import os
import sys
from unittest import TestLoader, TestSuite, TextTestRunner

# Unit tests
from g2p.log import LOGGER
from g2p.tests.test_api_resources import ResourceIntegrationTest
from g2p.tests.test_check_ipa_arpabet import CheckIpaArpabetTest
from g2p.tests.test_cli import CliTest
from g2p.tests.test_create_mapping import MappingCreationTest
from g2p.tests.test_doctor import DoctorTest
from g2p.tests.test_fallback import FallbackTest
from g2p.tests.test_indices import IndicesTest
from g2p.tests.test_langs import LangTest
from g2p.tests.test_mappings import MappingTest
from g2p.tests.test_network import NetworkTest
from g2p.tests.test_tokenize_and_map import TokenizeAndMapTest
from g2p.tests.test_tokenizer import TokenizerTest
from g2p.tests.test_transducer import TransducerTest
from g2p.tests.test_unidecode_transducer import UnidecodeTransducerTest
from g2p.tests.test_utils import UtilsTest
from g2p.tests.test_z_local_config import LocalConfigTest

# Deliberately left out:
# from g2p.tests.test_doctor_expensive import ExpensiveDoctorTest

LOADER = TestLoader()

TRANSDUCER_TESTS = [
    LOADER.loadTestsFromTestCase(test)
    for test in [
        IndicesTest,
        TransducerTest,
        UnidecodeTransducerTest,
    ]
]

MAPPINGS_TESTS = [
    LOADER.loadTestsFromTestCase(test)
    for test in [
        FallbackTest,
        MappingCreationTest,
        MappingTest,
        NetworkTest,
        UtilsTest,
        TokenizerTest,
        TokenizeAndMapTest,
        CheckIpaArpabetTest,
    ]
]

LANGS_TESTS = [
    LOADER.loadTestsFromTestCase(test)
    for test in [
        LangTest,
    ]
]

INTEGRATION_TESTS = [
    LOADER.loadTestsFromTestCase(test)
    for test in [
        CliTest,
        ResourceIntegrationTest,
        DoctorTest,
    ]
]

# LocalConfigTest has to get run last, to avoid interactions with other test
# cases, since it has side effects on the global database
LAST_DEV_TEST = [
    LOADER.loadTestsFromTestCase(test)
    for test in [
        LocalConfigTest,
    ]
]

DEV_TESTS = (
    TRANSDUCER_TESTS + MAPPINGS_TESTS + LANGS_TESTS + INTEGRATION_TESTS + LAST_DEV_TEST
)


def run_tests(suite):
    """Decide which Test Suite to run"""
    if suite == "all":
        suite = LOADER.discover(os.path.dirname(__file__))
    elif suite == "trans":
        suite = TestSuite(TRANSDUCER_TESTS)
    elif suite == "langs":
        suite = TestSuite(LANGS_TESTS)
    elif suite == "mappings":
        suite = TestSuite(MAPPINGS_TESTS)
    elif suite == "integ":
        suite = TestSuite(INTEGRATION_TESTS)
    elif suite == "dev":
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
