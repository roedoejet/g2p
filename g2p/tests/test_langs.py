#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from unittest import main, TestCase
import os
import csv
from glob import glob
from g2p.log import LOGGER
from g2p import make_g2p
from g2p.mappings import Mapping
from g2p.transducer import Transducer
from g2p.tests.public.data import __file__ as data_dir


class LangTest(TestCase):
    '''Basic Test for individual lookup tables.

    Test files (in g2p/tests/public/data) are either .csv, .psv, or
    .tsv files, the only difference being the delimiter used (comma,
    pipe, or tab).

    Each line in the test file consists of SOURCE,TARGET,INPUT,OUTPUT

    '''

    def setUp(self):
        DATA_DIR = os.path.dirname(data_dir)
        self.langs_to_test = []
        for fn in glob(f'{DATA_DIR}/*.*sv'):
            if fn.endswith('csv'):
                delimiter = ','
            elif fn.endswith('psv'):
                delimiter = '|'
            elif fn.endswith('tsv'):
                delimiter = '\t'
            with open(fn, encoding="utf-8") as csvfile:
                reader = csv.reader(csvfile, delimiter=delimiter)
                for row in reader:
                    if len(row) != 4:
                        LOGGER.warning(f'Row in {fn} containing values {row} does not have the right values. Please check your data.')
                    else:
                        self.langs_to_test.append(row)

    def test_io(self):
        # go through each language declared in the test case set up
        # Instead of asserting immediately, we go through all the cases first, so that
        # running test_langs.py prints all the errors at once, to help debugging a given g2p mapping.
        # Then we call assertEqual on the first failed case, to make unittest register the failure.
        error_count = 0
        for test in self.langs_to_test:
            transducer = make_g2p(test[0], test[1])
            output_string = transducer(test[2]).output_string
            if output_string != test[3]:
                LOGGER.warning("test_langs.py: mapping error: {} from {} to {} should be {}, got {}".format(test[2], test[0], test[1], test[3], output_string))
                if error_count == 0:
                    first_failed_test = test
                error_count += 1

        if error_count > 0:
            transducer = make_g2p(first_failed_test[0], first_failed_test[1])
            self.assertEqual(transducer(first_failed_test[2]).output_string, first_failed_test[3])

        #for test in self.langs_to_test:
        #    transducer = make_g2p(test[0], test[1])
        #    self.assertEqual(transducer(test[2]).output_string, test[3])

if __name__ == "__main__":
    main()
