import os
from unittest import TestLoader, TextTestRunner, TestSuite
# Unit tests
from g2p.tests.test_correspondences import CorrespondenceTest
from g2p.tests.test_indices import IndicesTest
from g2p.tests.test_transducer import TransducerTest

loader = TestLoader()

dev_tests = [
    loader.loadTestsFromTestCase(test)
    for test in [CorrespondenceTest, IndicesTest, TransducerTest]
]

transducer_tests = [
    loader.loadTestsFromTestCase(test)
    for test in [IndicesTest, TransducerTest]
]

cors_tests = [
    loader.loadTestsFromTestCase(test)
    for test in [CorrespondenceTest]
]


def run_tests(suite):
    if suite == 'all':
        suite = loader.discover(os.path.dirname(__file__))
    if suite == 'trans':
        suite = TestSuite(transducer_tests)
    if suite == 'cors':
        suite = TestSuite(cors_tests)
    elif suite == 'dev':
        suite = TestSuite(dev_tests)
    runner = TextTestRunner(verbosity=3)
    runner.run(suite)


if __name__ == "__main__":
    run_tests('all')
