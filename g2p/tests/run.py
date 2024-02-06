#!/usr/bin/env python

""" Organize tests into Test Suites

Run with "python run.py <suite>" where <suite> can be all, dev, or a few other
options (see run_tests() for the full list).

Add --describe to list the contents of the selected suite instead of running it.
"""

import os
import re
import sys
from unittest import TestLoader, TestSuite, TextTestRunner

# Unit tests
from g2p.log import LOGGER
from g2p.tests.test_api_resources import ResourceIntegrationTest
from g2p.tests.test_check_ipa_arpabet import CheckIpaArpabetTest
from g2p.tests.test_cli import CliTest
from g2p.tests.test_create_mapping import MappingCreationTest
from g2p.tests.test_doctor import DoctorTest
from g2p.tests.test_doctor_expensive import ExpensiveDoctorTest
from g2p.tests.test_fallback import FallbackTest
from g2p.tests.test_indices import IndicesTest
from g2p.tests.test_langs import LangTest
from g2p.tests.test_lexicon_transducer import LexiconTransducerTest
from g2p.tests.test_mappings import MappingTest
from g2p.tests.test_network import NetworkTest
from g2p.tests.test_tokenize_and_map import TokenizeAndMapTest
from g2p.tests.test_tokenizer import TokenizerTest
from g2p.tests.test_transducer import TransducerTest
from g2p.tests.test_unidecode_transducer import UnidecodeTransducerTest
from g2p.tests.test_utils import UtilsTest
from g2p.tests.test_z_local_config import LocalConfigTest

LOADER = TestLoader()

TRANSDUCER_TESTS = [
    LOADER.loadTestsFromTestCase(test)
    for test in [
        IndicesTest,
        TransducerTest,
        UnidecodeTransducerTest,
        LexiconTransducerTest,
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
        ExpensiveDoctorTest,
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


def list_tests(suite: TestSuite):
    for subsuite in suite:
        for match in re.finditer(r"tests=\[([^][]+)\]>", str(subsuite)):
            for test_case in match[1].split(", "):
                yield test_case.replace("g2p.tests.", "")


def describe_suite(suite: TestSuite):
    full_suite = LOADER.discover(os.path.dirname(__file__))
    full_list = list(list_tests(full_suite))
    requested_list = list(list_tests(suite))
    requested_set = set(requested_list)
    print("Test suite includes:", *sorted(requested_list), sep="\n")
    print(
        "\nTest suite excludes:",
        *sorted(test for test in full_list if test not in requested_set),
        sep="\n"
    )


SUITES = ("all", "dev", "integ", "langs", "mappings", "trans")


def run_tests(suite: str, describe: bool = False) -> bool:
    """Run the test suite specified in suite.

    Args:
        suite: one of SUITES, "dev" if the empty string
        describe: if True, list all the test cases instead of running them.

    Returns: Bool: True iff success
    """
    if not suite:
        LOGGER.info("No test suite specified, defaulting to dev.")
        suite = "dev"

    if suite == "all":
        test_suite = LOADER.discover(os.path.dirname(__file__))
    elif suite == "trans":
        test_suite = TestSuite(TRANSDUCER_TESTS)
    elif suite == "langs":
        test_suite = TestSuite(LANGS_TESTS)
    elif suite == "mappings":
        test_suite = TestSuite(MAPPINGS_TESTS)
    elif suite == "integ":
        test_suite = TestSuite(INTEGRATION_TESTS)
    elif suite == "dev":
        test_suite = TestSuite(DEV_TESTS)
    else:
        LOGGER.error("Please specify a test suite to run among: " + ", ".join(SUITES))
        return False

    if describe:
        describe_suite(test_suite)
        return True
    else:
        runner = TextTestRunner(verbosity=3)
        success = runner.run(test_suite).wasSuccessful()
        if not success:
            LOGGER.error("Some tests failed. Please see log above.")
        return success


if __name__ == "__main__":
    describe_opt = "--describe" in sys.argv
    if describe_opt:
        sys.argv.remove("--describe")

    result = run_tests("" if len(sys.argv) <= 1 else sys.argv[1], describe_opt)
    if not result:
        sys.exit(1)
