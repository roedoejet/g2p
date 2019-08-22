# -*- coding: utf-8 -*-

from unittest import main, TestCase
import os
from g2p.mappings import Mapping
from g2p.transducer import Transducer


class LangTest(TestCase):
    ''' Basic Test for individual lookup tables
    '''

    def setUp(self):
        git = [{"in_lang": "git",
               "out_lang": "git-ipa",
               "samples": [
                       ('gwila', '\u025fʷilæ'),
                       ("li'lp'en", "lilˀpˀin"),
                       ("hlik\u0332'sxw", "ɬɛq\u0294sx\u02b7")
                   ],
               }]

        self.langs_to_test = git

    def test_io(self):
        # go through each language declared in the test case set up
        for lang in self.langs_to_test:
            in_lang = lang['in_lang']
            out_lang = lang['out_lang']
            mappings = Mapping(in_lang=in_lang, out_lang=out_lang)
            transducer=Transducer(mappings)
            # go through each table in the current lang
            for sample in lang['samples']:
                # assert that the transduced first item in the tuple is equal to the second item in the tuple
                self.assertEqual(transducer(sample[0]), sample[1])


if __name__ == "__main__":
    main()
