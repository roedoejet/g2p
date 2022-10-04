#!/usr/bin/env python3

from unittest import TestCase, main

from g2p import make_g2p
from g2p.log import LOGGER
from g2p.tests.public.data import load_public_test_data


class LangTest(TestCase):
    """Basic Test for individual lookup tables.

    Test files (in g2p/tests/public/data) are either .csv, .psv, or
    .tsv files, the only difference being the delimiter used (comma,
    pipe, or tab).

    Each line in the test file consists of SOURCE,TARGET,INPUT,OUTPUT

    """

    def test_io(self):
        langs_to_test = load_public_test_data()

        # go through each language declared in the test case set up
        # Instead of asserting immediately, we go through all the cases first, so that
        # running test_langs.py prints all the errors at once, to help debugging a given g2p mapping.
        # Then we call assertEqual on the first failed case, to make unittest register the failure.
        error_count = 0
        for test in langs_to_test:
            transducer = make_g2p(test[0], test[1])
            output_string = transducer(test[2]).output_string.strip()
            if output_string != test[3].strip():
                LOGGER.warning(
                    "test_langs.py: mapping error: {} from {} to {} should be {}, got {}".format(
                        test[2], test[0], test[1], test[3], output_string
                    )
                )
                if error_count == 0:
                    first_failed_test = test
                error_count += 1

        if error_count > 0:
            transducer = make_g2p(first_failed_test[0], first_failed_test[1])
            self.assertEqual(
                transducer(first_failed_test[2]).output_string.strip(),
                first_failed_test[3].strip(),
            )

        # for test in langs_to_test:
        #    transducer = make_g2p(test[0], test[1])
        #    self.assertEqual(transducer(test[2]).output_string, test[3])


if __name__ == "__main__":
    main()
