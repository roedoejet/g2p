from gi2pi.tests.run import run_tests
import sys

try:
    run_tests(sys.argv[1])
except IndexError:
    print("Please specify a test suite to run: i.e. 'dev' or 'all'")