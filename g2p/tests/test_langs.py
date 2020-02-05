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
    ''' Basic Test for individual lookup tables
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
            with open(fn) as csvfile:
                reader = csv.reader(csvfile, delimiter=delimiter)
                for row in reader:
                    if len(row) != 4:
                        LOGGER.warning(f'Row in {fn} containing values {row} does not have the right values. Please check your data.')
                    else:
                        self.langs_to_test.append(row)

    def test_io(self):
        # go through each language declared in the test case set up
        for test in self.langs_to_test:
            transducer = make_g2p(test[0], test[1])
            self.assertEqual(transducer(test[2]), test[3])

    def test_index(self):
        # go through each language declared in the test case set up
        for test in self.langs_to_test:
            transducer = make_g2p(test[0], test[1])
            self.assertEqual(transducer(test[2], index=True)[0], test[3])

if __name__ == "__main__":
    main()
