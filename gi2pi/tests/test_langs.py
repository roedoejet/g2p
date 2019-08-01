# -*- coding: utf-8 -*-

from unittest import main, TestCase
import os
from gi2pi.mappings import Mapping
from gi2pi.transducer import Transducer


class LangTest(TestCase):
    ''' Basic Test for individual lookup tables
    '''

    def setUp(self):
        git = {"name": "git",
               "tables": {
                   "Orthography (Deterministic)": [
                       ('gwiila', '\u025fʷiːlæ'),
                       ("eji'i'n", "i\u02a3i\u0294i\u0294n"),
                       ("li'lp'en", "lilˀpˀin"), 
                       ("hlik\u0332'sxw", "ɬiq\u0294sx\u02b7"),
                    #    ("wets'utsetl'e", "wiʦ\u0294uʦit\u0361ɬˀi"),                       
                       ("x\u0332uu'w", "χuːwˀ"),
                    #    ("gyee'eg", "\u025fe\u02d0\u0294i\u025f") 
                   ],
                #    "APA (Deterministic)": [
                    #    ("ekʰek\u0313qen", "\u0259kʰek\u02C0qen"),
                    #    ("ʔyeːʔqʰ", "ʔyeːʔqʰ"),
                    #    ("æʒiʔbiʔtʰ", "æʣiʔbiʔtʰ"),
                    #    ("weʔƛuce", "weʔt\u0361ɬuce"),
                    #    ("bωkʷʰɛɬɛ", "bʊ\u031Ekʷʰɛɬɛ"),
                    #    ("ʔyeʔqʰ", "ʔjeʔqʰ"),
                    #    ("xʷiʔcʰiʔmi", "xʷiʔ\u02a6ʰiʔmi")
                #    ],
                   # "RAPA_no_free_variation": [
                      # ('gwiila', '\u025fwiːlæ'),
                      # ("eji'i'n", "i\u02a3i\u0294i\u0294n")
                   #]
                   }
               }

        self.langs_to_test = [git]

    def test_io(self):
        # go through each language declared in the test case set up
        for lang in self.langs_to_test:
            lang_name = lang['name']
            # go through each table in the current lang
            for table in lang['tables'].keys():
                mappings = Mapping(
                    language={'lang': lang_name, 'table': table})
                transducer = Transducer(mappings, as_is=True)
                # go through each input/output pair
                for pair in lang['tables'][table]:
                    # assert that the transduced first item in the tuple is equal to the second item in the tuple
                    self.assertEqual(transducer(pair[0]), pair[1])


if __name__ == "__main__":
    main()
