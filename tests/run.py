import os
from unittest import TestLoader, TextTestRunner, TestSuite
# Unit tests
from .test_transducer import TransducerTest

loader = TestLoader()

dev_tests = [
        loader.loadTestsFromTestCase(test)
        for test in [TransducerTest]
    ]

def run_tests(suite):
    if suite == 'all':
        suite = loader.discover(os.path.dirname(__file__))
    elif suite == 'dev':
        suite = TestSuite(dev_tests)
    runner = TextTestRunner(verbosity=3)
    runner.run(suite)

if __name__ == "__main__":
    run_tests('all')