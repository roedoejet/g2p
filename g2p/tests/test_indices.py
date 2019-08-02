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
            [{"in": "s", "out": "sh"}, {"in": "sh", "out": "s"}]
        )
        self.test_mapping_eight = Mapping([{"in": "te", "out": "che"},
                                           {"in": "t", "out": "s"}])
        self.test_mapping_combining = Mapping(
            [{'in': 'k{1}\u0313{2}', 'out': "'{2}k{1}"}])
        self.test_mapping_wacky = Mapping(
            [{"in": "\U0001f600{1}\U0001f603\U0001f604{2}\U0001f604{3}",
              "out": "\U0001f604\U0001f604\U0001f604{2}\U0001f604{3}\U0001f604{1}"}]
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
        self.trans_seven_as_is = Transducer(
            self.test_mapping_seven, as_is=True)
        self.trans_eight = Transducer(self.test_mapping_eight)
        self.trans_combining = Transducer(self.test_mapping_combining)
        self.trans_wacky = Transducer(self.test_mapping_wacky)
        self.trans_circum = Transducer(self.test_mapping_circum)

    def test_no_indices(self):
        """ Test straightforward conversion without returning indices.
        """
        transducer = self.trans_combining('k\u0313am')
        self.assertEqual(transducer, "'kam")

    def test_combining(self):
        """ Test index preserving combining characters
        """
        transducer = self.trans_combining('k\u0313am', index=True)
        self.assertEqual(transducer[0], "'kam")
        self.assertEqual(transducer[1](), [((0, "k"), (1, 'k')),
                                           ((1, '\u0313'),
                                            (0, "'")),
                                           ((2, 'a'),
                                            (2, 'a')),
                                           ((3, 'm'), (3, 'm'))])

    def test_wacky(self):
        """ Test weird Unicode emoji transformation...
        """
        transducer = self.trans_wacky(
            '\U0001f600\U0001f603\U0001f604\U0001f604', index=True, debugger=True)
        self.assertEqual(
            transducer[0], '\U0001f604\U0001f604\U0001f604\U0001f604\U0001f604')
        # TODO: Should this be indexing based on characters
        # self.assertEqual(transducer[1](), [
        #     ((0, '😀'), (4, '😄')),
        #     ((1, '😃'), (0, '😄')),
        #     ((2, '😄'), (1, '😄')),
        #     ((2, '😄'), (2, '😄')),
        #     ((3, '😄'), (3, '😄'))])
        # Or based on match groups? Maybe this is more readable?
        self.assertEqual(transducer[1](), [
            ((0, '😀'), (4, '😄')),
            ((1, '😃😄'), (0, '😄😄😄')),
            ((3, '😄'), (3, '😄'))])

    def test_circum(self):
        """ Test circumfixing
        """
        transducer = self.trans_circum('ac', index=True)
        self.assertEqual(transducer[0], 'cac')
        self.assertEqual(transducer[1](), [((0, 'a'), (1, 'a')),
                                           ((1, 'c'), (0, 'c')),
                                           ((1, 'c'), (2, 'c'))])

    def test_case_one(self):
        """ Test case one
        """
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
        self.assertEqual(transducer_as_is[0], 'test')
        # self.assertEqual(transducer_as_is[1](), [((0, 't'), (0, 't')),
        #                                          ((1, 'e'), (1, 'e')),
        #                                          ((2, 's'), (2, 's')),
        #                                          ((3, 't'), (3, 't'))])
        # transducer = self.trans_seven('test', True)
        # self.assertEqual(transducer[0], 'tesht')

        # self.assertEqual(transducer[1](), [((0, 't'), (0, 't')),
        #                                    ((1, 'e'), (1, 'e')),
        #                                    ((2, 's'), (2, 's')),
        #                                    ((2, 's'), (3, 'h')),
        #                                    ((3, 't'), (4, 't'))])

    def test_case_eight(self):
        transducer = self.trans_eight('test', True)
        self.assertEqual(transducer[0], 'chess')
        self.assertEqual(transducer[1](), [((0, 't'), (0, 'c')),
                                           ((1, 'e'), (1, 'h')),
                                           ((1, 'e'), (2, 'e')),
                                           ((2, 's'), (3, 's')),
                                           ((3, 't'), (4, 's'))])


if __name__ == "__main__":
    main()
