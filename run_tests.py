#!/usr/bin/env python

import sys

from g2p.tests.run import run_tests

result = run_tests("" if len(sys.argv) <= 1 else sys.argv[1])
if not result:
    sys.exit(1)
