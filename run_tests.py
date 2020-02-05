from g2p.tests.run import run_tests
import sys
import unittest

try:
    result = run_tests(sys.argv[1])
    if not result.wasSuccessful():
        raise Exception(f'Some tests failed. Please see log above.')
except IndexError:
    print("Please specify a test suite to run: i.e. 'dev' or 'all'")