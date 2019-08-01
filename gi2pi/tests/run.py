import os
from unittest import TestLoader, TextTestRunner, TestSuite
# Unit tests
from gi2pi.tests.test_mappings import MappingTest
from gi2pi.tests.test_indices import IndicesTest
from gi2pi.tests.test_langs import LangTest
from gi2pi.tests.test_transducer import TransducerTest


loader = TestLoader()

transducer_tests = [
    loader.loadTestsFromTestCase(test)
    for test in [IndicesTest, TransducerTest]
]

mappings_tests = [
    loader.loadTestsFromTestCase(test)
    for test in [MappingTest]
]

langs_tests = [
    loader.loadTestsFromTestCase(test) for test in [
        LangTest,
    ]
]

dev_tests = transducer_tests + mappings_tests + langs_tests


def run_tests(suite):
    if suite == 'all':
        suite = loader.discover(os.path.dirname(__file__))
    if suite == 'trans':
        suite = TestSuite(transducer_tests)
    if suite == 'langs':
        suite = TestSuite(langs_tests)
    if suite == 'mappings':
        suite = TestSuite(mappings_tests)
    elif suite == 'dev':
        suite = TestSuite(dev_tests)
    runner = TextTestRunner(verbosity=3)
    runner.run(suite)


if __name__ == "__main__":
    run_tests('all')
