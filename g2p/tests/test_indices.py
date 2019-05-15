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
          ((1, 'e'), (-1, '')),
          ((2, 's'), (1, 's')),
          ((3, 't'), (2, 't')) ]

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
        self.trans_one = Transducer(self.test_cor_one)
        self.trans_two = Transducer(self.test_cor_two)
        self.trans_three = Transducer(self.test_cor_three)
        self.trans_four = Transducer(self.test_cor_four)
        self.trans_five = Transducer(self.test_cor_five)

    def test_case_one(self):
        self.assertEqual(self.trans_one('test', True), ('pest', [((0, 't'), (0, 'p')),
                                                                 ((1, 'e'),
                                                                  (1, 'e')),
                                                                 ((2, 's'),
                                                                  (2, 's')),
                                                                 ((3, 't'), (3, 't'))]))

    # def test_case_two(self):
    #     self.assertEqual(self.trans_two('test', True), ('tst', [((0, 't'), (0, 't')),
    #                                                             ((1, 'e'),
    #                                                              (-1, '')),
    #                                                             ((2, 's'),
    #                                                              (1, 's')),
    #                                                             ((3, 't'), (2, 't'))]))

    def test_case_three(self):
        self.assertEqual(self.trans_three('test', True), ('chest', [((0, 't'), (0, 'c')),
                                                                    ((0, 't'),
                                                                     (1, 'h')),
                                                                    ((1, 'e'),
                                                                     (2, 'e')),
                                                                    ((2, 's'),
                                                                     (3, 's')),
                                                                    ((3, 't'), (4, 't'))]))

    # def test_case_four(self):
    #     self.assertEqual(self.trans_four('test', True), ('pst', [((0, 't'), (0, 'p')),
    #                                                              ((1, 'e'),
    #                                                               (0, 'p')),
    #                                                              ((2, 's'),
    #                                                               (1, 's')),
    #                                                              ((3, 't'), (2, 't'))]))


if __name__ == "__main__":
    main()
