from unittest import main, TestCase
import os
from g2p.cors import Correspondence
from g2p.transducer import Transducer


class IndicesTest(TestCase):
    ''' Basic Transducer Test
    Preserve character-level correspondences:

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

    '''

    def setUp(self):
        self.test_cor_one = Correspondence(
            [{'from': 't', "to": 'p', 'after': 'e'}])
        self.test_cor_two = Correspondence([{"from": 'e', "to": ""}])
        self.test_cor_three = Correspondence(
            [{"from": 't', 'to': 'ch', 'after': 'e'}])
        self.test_cor_four = Correspondence([{'from': 'te', 'to': 'p'}])
        self.test_cor_five = Correspondence(
            [{'before': 't', 'after': '$', 'from': '', 'to': 'y'}])
        self.test_cor_six = Correspondence(
            [{"from": "e{1}s{2}", "to": "s{2}e{1}"}]
        )
        self.test_cor_seven = Correspondence(
            [{"from": "s", "to": "sh"}, {"from": "sh", "to": "s"}]
        )
        self.test_cor_combining = Correspondence(
            [{'from': 'k{1}\u0313{2}', 'to': "'{2}k{1}"}])
        self.test_cor_wacky = Correspondence(
            [{"from": "\U0001f600{1}\U0001f603\U0001f604{2}\U0001f604{3}",
                "to": "\U0001f604\U0001f604\U0001f604{2}\U0001f604{3}\U0001f604{1}"}]
        )
        self.test_cor_circum = Correspondence(
            [{'from': 'a{1}c{2}', 'to': 'c{2}a{1}c{2}'}]
        )
        self.trans_one = Transducer(self.test_cor_one)
        self.trans_two = Transducer(self.test_cor_two)
        self.trans_three = Transducer(self.test_cor_three)
        self.trans_four = Transducer(self.test_cor_four)
        self.trans_five = Transducer(self.test_cor_five)
        self.trans_six = Transducer(self.test_cor_six)
        self.trans_seven = Transducer(self.test_cor_seven)
        self.trans_seven_as_is = Transducer(self.test_cor_seven, True)
        self.trans_combining = Transducer(self.test_cor_combining)
        self.trans_wacky = Transducer(self.test_cor_wacky)
        self.trans_circum = Transducer(self.test_cor_circum)

    def test_no_indices(self):
        transducer = self.trans_combining('k\u0313am')
        self.assertEqual(transducer, "'kam")

    def test_combining(self):
        transducer = self.trans_combining('k\u0313am', index=True)
        self.assertEqual(transducer[0], "'kam")
        self.assertEqual(transducer[1](), [((0, "k"), (1, 'k')),
                                           ((1, '\u0313'),
                                            (0, "'")),
                                           ((2, 'a'),
                                            (2, 'a')),
                                           ((3, 'm'), (3, 'm'))])

    def test_wacky(self):
        transducer = self.trans_wacky(
            '\U0001f600\U0001f603\U0001f604\U0001f604', index=True)
        self.assertEqual(
            transducer[0], '\U0001f604\U0001f604\U0001f604\U0001f604\U0001f604')
        self.assertEqual(transducer[1](), [
            ((1, "\U0001f600"), (2, "\U0001f604")),
            ((0, "\U0001f603\U0001f604"), (0, "\U0001f604\U0001f604\U0001f604")),
            ((2, "\U0001f604"), (1, "\U0001f604"))
        ])

    def test_circum(self):
        transducer = self.trans_circum('ac', index=True)
        self.assertEqual(transducer[0], 'cac')
        self.assertEqual(transducer[1](), [((0, 'a'), (1, 'a')),
                                           ((1, 'c'), (0, 'c')),
                                           ((1, 'c'), (2, 'c'))])

    def test_case_one(self):
        transducer = self.trans_one('test', True)
        self.assertEqual(transducer[0], 'pest')
        self.assertEqual(transducer[1](), [((0, 't'), (0, 'p')),
                                           ((1, 'e'),
                                            (1, 'e')),
                                           ((2, 's'),
                                            (2, 's')),
                                           ((3, 't'), (3, 't'))])

    def test_case_two(self):
        transducer = self.trans_two('test', True)
        self.assertEqual(transducer[0], 'tst')
        self.assertEqual(transducer[1](), [((0, 't'), (0, 't')),
                                           ((1, 'e'),
                                            (1, '')),
                                           ((2, 's'),
                                            (2, 's')),
                                           ((3, 't'), (3, 't'))])

    def test_case_three(self):
        transducer = self.trans_three('test', True)
        self.assertEqual(transducer[0], 'chest')
        self.assertEqual(transducer[1](), [((0, 't'), (0, 'c')),
                                           ((0, 't'),
                                            (1, 'h')),
                                           ((1, 'e'),
                                            (2, 'e')),
                                           ((2, 's'),
                                            (3, 's')),
                                           ((3, 't'), (4, 't'))])

    def test_case_four(self):
        transducer = self.trans_four('test', True)
        self.assertEqual(transducer[0], 'pst')
        self.assertEqual(transducer[1](), [((0, 't'), (0, 'p')),
                                           ((1, 'e'),
                                            (0, 'p')),
                                           ((2, 's'),
                                            (1, 's')),
                                           ((3, 't'), (2, 't'))])

    def test_case_six(self):
        transducer = self.trans_six('test', True)
        self.assertEqual(transducer[0], 'tset')
        self.assertEqual(transducer[1](), [((0, 't'), (0, 't')),
                                           ((1, 'e'), (2, 'e')),
                                           ((2, 's'), (1, 's')),
                                           ((3, 't'), (3, 't'))])

    def test_case_seven(self):
        transducer_as_is = self.trans_seven_as_is('test', True)
        transducer_as_is[1]()
        self.assertEqual(transducer_as_is[0], 'test')
        self.assertEqual(transducer_as_is[1](), [((0, 't'), (0, 't')),
                                                 ((1, 'e'), (1, 'e')),
                                                 ((2, 's'), (2, 's')),
                                                 ((3, 't'), (3, 't'))])
        transducer = self.trans_seven('test', True)
        self.assertEqual(transducer[0], 'tesht')
        self.assertEqual(transducer[1](), [((0, 't'), (0, 't')),
                                           ((1, 'e'), (1, 'e')),
                                           ((2, 's'), (2, 's')),
                                           ((2, 's'), (3, 'h')),
                                           ((3, 't'), (4, 't'))])


if __name__ == "__main__":
    main()
