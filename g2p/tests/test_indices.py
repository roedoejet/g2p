#!/usr/bin/env python3

"""
    Unittests for index preservation
"""

from unittest import main, TestCase
from g2p.mappings import Mapping
from g2p.transducer import Transducer


class IndicesTest(TestCase):
    ''' Basic Transducer Test
    Preserve character-level mappings:

    Test Case #1
        # Simple conversion

        0 1 2 3
        t e s t

        p e s t
        0 1 2 3

        [ ((0, 't'), (0, 'p')),
          ((1, 'e'), (1, 'e')),
          ((2, 's'), (2, 's')),
          ((3, 't'), (3, 't')) ]

    Test Case #2:
        # Allow for deletion of segments

        0 1 2 3
        t e s t

        t s t
        0 1 2

        [ ((0, 't'), (0, 't')),
          ((1, 'e'), (1, '')),
          ((2, 's'), (2, 's')),
          ((3, 't'), (3, 't')) ]

    Test Case #3
        # Allow for one-to-many

        0 1 2 3
        t e s t

        c h e s t
        0 1 2 3 4

        [ ((0, 't'), (0, 'c')),
          ((0, 't'), (1, 'h')),
          ((1, 'e'), (2, 'e')),
          ((2, 's'), (3, 's')),
          ((3, 't'), (4, 't')) ]

    Test Case #4
        # Allow for many-to-one

        0 1 2 3
        t e s t

        p s t
        0 1 2

        [ ((0, 't'), (0, 'p')),
          ((1, 'e'), (0, 'p')),
          ((2, 's'), (1, 's')),
          ((3, 't'), (2, 't')) ]

    Test Case #5
        # Allow for epenthesis
         0 1 2 3
         t e s t

         t e s t y
         0 1 2 3 4

        [ ((-1, 'y'), (4, 'y')),
          ((0, 't'), (0, 't')),
          ((1, 'e'), (1, 'e')),
          ((2, 's'), (2, 's')),
          ((3, 't'), (3, 't')) ]

     Test Case #6
        # Allow metathesis
         0 1 2 3
         t e s t

         t s e t
         0 1 2 3

        [ ((0, 't'), (0, 't')),
          ((1, 'e'), (2, 'e')),
          ((2, 's'), (1, 's')),
          ((3, 't'), (3, 't')) ]

    Test Case #7
        # Allow order-sensitive operations
        0 1 2 3
        t e s t

        t e s h t
        0 1 2 3 4

        t e s t
        0 1 2 3

        AS IS

        [ ((0, 't'), (0, 't')),
          ((1, 'e'), (1, 'e')),
          ((2, 's'), (2, 's')),
          ((3, 't'), (3, 't')) ]

          or not

        [ ((0, 't'), (0, 't')),
          ((1, 'e'), (1, 'e')),
          ((2, 's'), (2, 's')),
          ((2, 's'), (3, 'h')),
          ((3, 't'), (4, 't')) ]

    Test Case #8
        # Allow multiple processes which alter the indices
        0 1 2 3
        t e s t

        c h e s t
        0 1 2 3 4

        c h e s s
        0 1 2 3 4

        [ ((0, 't'), (0, 'c')),
          ((1, 'e'), (1, 'h')),
          ((1, 'e'), (2, 'e')),
          ((2, 's'), (3, 's')),
          ((3, 't'), (4, 's')) ]

    '''

    def setUp(self):
        self.test_mapping_one = Mapping(
            [{'in': 't', "out": 'p', 'context_after': 'e'}])
        self.test_mapping_two = Mapping([{"in": 'e', "out": ""}])
        self.test_mapping_three = Mapping(
            [{"in": 't', 'out': 'ch', 'context_after': 'e'}])
        self.test_mapping_four = Mapping([{'in': 'te', 'out': 'p'}])
        self.test_mapping_five = Mapping(
            [{'context_before': 't', 'context_after': '$', 'in': '', 'out': 'y'}])
        self.test_mapping_six = Mapping(
            [{"in": "e{1}s{2}", "out": "s{2}e{1}"}]
        )
        self.test_mapping_seven = Mapping(
            [{"in": "s", "out": "sh"}, {"in": "sh", "out": "s"}], rule_ordering="apply-longest-first"
        )
        self.test_mapping_seven_as_written = Mapping(
            [{"in": "s", "out": "sh"}, {"in": "sh", "out": "s"}])
        self.test_mapping_eight = Mapping([{"in": "te", "out": "che"},
                                           {"in": "t", "out": "s"}])
        self.test_mapping_nine = Mapping([{'in': 'aa', 'out': ''}])
        self.test_mapping_ten = Mapping([{'in': 'abc', 'out': 'a'}])
        self.test_mapping_combining = Mapping(
            [{'in': 'k{1}\u0313{2}', 'out': "'{2}k{1}"}])
        self.test_mapping_wacky = Mapping(
            [{"in": "\U0001f600{1}\U0001f603\U0001f604{2}\U0001f604{3}",
              "out": "\U0001f604\U0001f604\U0001f604{2}\U0001f604{3}\U0001f604{1}"}]
        )
        self.test_mapping_wacky_lite = Mapping(
            [{"in": "a{1}bc{2}c{3}",
              "out": "ccc{2}c{3}c{1}"}]
        )
        self.test_mapping_circum = Mapping(
            [{'in': 'a{1}c{2}', 'out': 'c{2}a{1}c{2}'}]
        )
        self.trans_one = Transducer(self.test_mapping_one)
        self.trans_two = Transducer(self.test_mapping_two)
        self.trans_three = Transducer(self.test_mapping_three)
        self.trans_four = Transducer(self.test_mapping_four)
        self.trans_five = Transducer(self.test_mapping_five)
        self.trans_six = Transducer(self.test_mapping_six)
        self.trans_seven = Transducer(self.test_mapping_seven)
        self.test_seven_as_written = Transducer(self.test_mapping_seven_as_written)
        self.trans_eight = Transducer(self.test_mapping_eight)
        self.trans_nine = Transducer(self.test_mapping_nine)
        self.trans_ten = Transducer(self.test_mapping_ten)
        self.trans_combining = Transducer(self.test_mapping_combining)
        self.trans_wacky = Transducer(self.test_mapping_wacky)
        self.trans_wacky_lite = Transducer(self.test_mapping_wacky_lite)
        self.trans_circum = Transducer(self.test_mapping_circum)

    def test_no_indices(self):
        """ Test straightforward conversion without returning indices.
        """
        transducer = self.trans_combining('k\u0313am')
        self.assertEqual(transducer.output_string, "'kam")

    def test_combining(self):
        """ Test index preserving combining characters
        """
        transducer = self.trans_combining('k\u0313am')
        self.assertEqual(transducer.output_string, "'kam")
        self.assertEqual(transducer.edges, [(0, 1),
                                            (1, 0),
                                            (2, 2),
                                            (3, 3)])

    def test_wacky(self):
        """ Test weird Unicode emoji transformation...
        """
        transducer_lite = self.trans_wacky_lite(
            'abcc')
        transducer_lite_extra = self.trans_wacky_lite(
            'abcca')
        self.assertEqual(
            transducer_lite.output_string, 'ccccc')
        self.assertEqual(
            transducer_lite_extra.output_string, 'ccccca')
        self.assertEqual(
            transducer_lite.edges, [(0, 4), (1, 0), (2, 1), (2, 2), (3, 3)])
        self.assertEqual(
            transducer_lite_extra.edges, [(0, 4), (1, 0), (2, 1), (2, 2), (3, 3), (4, 5)])
        transducer_no_i = self.trans_wacky(
            '\U0001f600\U0001f603\U0001f604\U0001f604')
        self.assertEqual(
            transducer_no_i.output_string, '\U0001f604\U0001f604\U0001f604\U0001f604\U0001f604')
        transducer = self.trans_wacky(
            '\U0001f600\U0001f603\U0001f604\U0001f604')
        self.assertEqual(
            transducer.output_string, '\U0001f604\U0001f604\U0001f604\U0001f604\U0001f604')
        self.assertEqual(
            transducer.edges, [(0, 4), (1, 0), (2, 1), (2, 2), (3, 3)])

    def test_circum(self):
        """ Test circumfixing
        """
        transducer = self.trans_circum('ac')
        self.assertEqual(transducer.output_string, 'cac')
        self.assertEqual(transducer.edges, [(0, 1), (1, 0), (1, 2)])

    def test_case_one(self):
        """ Test case one
        """
        transducer = self.trans_one('test')
        self.assertEqual(transducer.output_string, 'pest')
        self.assertEqual(transducer.edges, [(0, 0), (1, 1), (2, 2), (3, 3)])

    def test_case_two(self):
        transducer = self.trans_two('test')
        self.assertEqual(transducer.output_string, 'tst')
        self.assertEqual(transducer.edges, [(0, 0), (1, None), (2, 1), (3, 2)])

    def test_case_three(self):
        transducer = self.trans_three('test')
        self.assertEqual(transducer.output_string, 'chest')
        self.assertEqual(transducer.edges, [(0, 0),
                                            (0, 1),
                                            (1, 2),
                                            (2, 3),
                                            (3, 4)])

    def test_case_four(self):
        transducer = self.trans_four('test')
        self.assertEqual(transducer.output_string, 'pst')
        self.assertEqual(transducer.edges, [(0, 0),
                                            (1, 0),
                                            (2, 1),
                                            (3, 2)])

    def test_case_six(self):
        transducer = self.trans_six('test')
        self.assertEqual(transducer.output_string, 'tset')
        self.assertEqual(transducer.edges, [(0, 0), (1, 2), (2, 1), (3, 3)])

    def test_case_long_six(self):
        transducer = self.trans_six('esesse')
        self.assertEqual(transducer.output_string, 'sesese')

    def test_case_seven(self):
        transducer_as_written = self.test_seven_as_written('test')
        self.assertEqual(transducer_as_written.output_string, 'test')
        self.assertEqual(transducer_as_written.edges, [
                         (0, 0), (1, 1), (2, 2), (3, 3)])
        transducer = self.trans_seven('test')
        self.assertEqual(transducer.output_string, 'tesht')
        self.assertEqual(transducer.edges, [(0, 0),
                                            (1, 1),
                                            (2, 2),
                                            (2, 3),
                                            (3, 4)])

    def test_case_eight(self):
        transducer = self.trans_eight('test')
        self.assertEqual(transducer.output_string, 'chess')
        self.assertEqual(transducer.edges, [(0, 0),
                                            (1, 1),
                                            (1, 2),
                                            (2, 3),
                                            (3, 4)])

    def test_case_nine(self):
        transducer = self.trans_nine('aa')
        self.assertEqual(transducer.output_string, '')
        self.assertEqual(transducer.edges, [(0, None), (1, None)])

    def test_case_ten(self):
        transducer = self.trans_ten('abc')
        self.assertEqual(transducer.output_string, 'a')
        self.assertEqual(transducer.edges, [(0, 0), (1, 0), (2, 0)])

    def test_case_acdc(self):
        transducer = Transducer(
            Mapping([{"in": "a{1}c{2}", "out": "c{2}a{1}c{2}"}]))
        tg = transducer('acdc')
        self.assertEqual(tg.output_string, 'cacdc')
        self.assertEqual(tg.edges, [(0, 1),
                                    (1, 0),
                                    (1, 2),
                                    (2, 3),
                                    (3, 4)])

    def test_case_acac(self):
        transducer = Transducer(Mapping([{"in": "ab{1}c{2}", "out": "ab{2}"}]))
        transducer_default = Transducer(
            Mapping([{"in": "ab", "out": ""}, {"in": "c", "out": "ab"}]))
        tg = transducer('abcabc')
        tg_default = transducer_default('abcabc')
        self.assertEqual(tg.output_string, 'abab')
        self.assertEqual(tg_default.output_string, 'abab')
        self.assertEqual(tg.edges, [(0, None),
                                    (1, None),
                                    (2, 0),
                                    (2, 1),
                                    (3, None),
                                    (4, None),
                                    (5, 2),
                                    (5, 3)])
        self.assertEqual(tg_default.edges, [(0, None),
                                            (1, None),
                                            (2, 0),
                                            (2, 1),
                                            (3, None),
                                            (4, None),
                                            (5, 2),
                                            (5, 3)])


if __name__ == "__main__":
    main()
