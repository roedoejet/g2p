# -*- coding: utf-8 -*-

from unittest import main, TestCase
import os
from g2p import make_g2p
from g2p.mappings import Mapping
from g2p.transducer import Transducer


class LangTest(TestCase):
    ''' Basic Test for individual lookup tables
    '''

    def setUp(self):
        git = [
            {"in_lang": "git",
                "out_lang": "git-ipa",
                "samples": [
                    ('gwila', '\u0261ʷilæ'),
                    ("hlik\u0332'sxw", "ɬiq\u0294sx\u02b7")
                ],
             },
            {'in_lang': 'git',
                'out_lang': 'eng-arpabet',
                "samples": [
                    ("K̲'ay", 'K HH AE Y'),
                    ("guts'uusgi'y", 'G UW T S HH UW S G IY HH Y')
                ]},
            {'in_lang': 'str-sen',
                'out_lang': 'eng-arpabet',
                "samples": [
                    ('X̱I¸ÁM¸', 'SH W IY HH EY M HH')
                ]},
            {'in_lang': 'ctp',
                'out_lang': 'eng-arpabet',
                "samples": [
                    ('Qneᴬ', 'HH N EY')
                ]}
        ]

        self.langs_to_test = git

    def test_io(self):
        # go through each language declared in the test case set up
        for lang in self.langs_to_test:
            in_lang = lang['in_lang']
            out_lang = lang['out_lang']
            transducer = make_g2p(in_lang, out_lang)
            # go through each table in the current lang
            for sample in lang['samples']:
                # assert that the transduced first item in the tuple is equal to the second item in the tuple
                self.assertEqual(transducer(sample[0]), sample[1])


if __name__ == "__main__":
    main()
