# -*- coding: utf-8 -*-

from unittest import main, TestCase
import os
from g2p.cors import Correspondence
from g2p.transducer import Transducer


class LangTest(TestCase):
    ''' Basic Test for individual lookup tables
    '''

    def setUp(self):
        git = {"name": "git",
               "tables": {
                   "RAPA_no_free_variation": [
                       ('gwiila', '\u025fwiːlæ'),
                       ("eji'i'n", "i\u02a3i\u0294i\u0294n")
                   ]}
               }

        self.langs_to_test = [git]

    def test_io(self):
        # go through each language declared in the test case set up
        for lang in self.langs_to_test:
            lang_name = lang['name']
            # go through each table in the current lang
            for table in lang['tables'].keys():
                cors = Correspondence(language={'lang': lang_name, 'table': table})
                transducer = Transducer(cors, as_is=True)
                # go through each input/output pair
                for pair in lang['tables'][table]:
                    # assert that the transduced first item in the tuple is equal to the second item in the tuple
                    self.assertEqual(transducer(pair[0]), pair[1])

if __name__ == "__main__":
    main()
