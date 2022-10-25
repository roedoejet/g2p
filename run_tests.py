#!/usr/bin/env python

import sys

from g2p.tests.run import run_tests

try:
    result = run_tests(sys.argv[1])
    if not result:
        print("Some tests failed. Please see log above.")
        sys.exit(1)
except IndexError:
    print("Please specify a test suite to run: i.e. 'dev' or 'all'")
    sys.exit(1)
