#!/usr/bin/env python3

import os
from unittest import TestCase, main

from g2p import make_g2p


class UnidecodeTransducerTest(TestCase):
    def test_unidecode(self):
        transducer = make_g2p("und", "und-ascii")
        tg = transducer("éçà")
        self.assertEqual(tg.output_string, "eca")
        self.assertEqual(tg.edges, [(0,0),(1,0),(2,1),(3,1),(4,2),(5,2)])

    def test_unidecide_empty_output(self):
        transducer = make_g2p("und", "und-ascii")
        # \u0361 on its own gets deleted completely by unidecode
        tg = transducer("\u0361")
        self.assertEqual(tg.output_string, "")
        self.assertEqual(tg.edges, [])

    def test_unidecode_to_arpabet(self):
        transducer = make_g2p("und", "eng-arpabet")
        tg = transducer("été Nunavut ᓄᓇᕗᑦ")
        self.assertEqual(tg.output_string, "EY T EY  N UW N AA V UW T  N OW N AA F OW T ")


if __name__ == "__main__":
    main()
