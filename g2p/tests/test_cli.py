from unittest import main, TestCase
import os
import csv
from glob import glob

from g2p.app import APP
from g2p.log import LOGGER
from g2p.cli import convert, update
from g2p.tests.public.data import __file__ as data_dir

class CliTest(TestCase):
    def setUp(self):
        self.runner = APP.test_cli_runner()
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

    def test_update(self):
        result = self.runner.invoke(update)
        self.assertEqual(result.exit_code, 0)
    
    def test_convert(self):
        error_count = 0
        for test in self.langs_to_test:
            output_string = self.runner.invoke(convert, [test[2], test[0], test[1]]).stdout.strip()
            if output_string != test[3]:
                LOGGER.warning("test_cli.py: mapping error: {} from {} to {} should be {}, got {}".format(test[2], test[0], test[1], test[3], output_string))
                if error_count == 0:
                    first_failed_test = test
                error_count += 1

        if error_count > 0:
            output_string = self.runner.invoke(convert, [first_failed_test[2], first_failed_test[0], first_failed_test[1]]).stdout.strip()
            self.assertEqual(output_string, first_failed_test[3])

if __name__ == '__main__':
    main()
