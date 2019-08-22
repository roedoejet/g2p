from unittest import main, TestCase
from g2p.mappings import Mapping
from g2p.transducer import CompositeTransducer, Transducer


class TransducerTest(TestCase):
    ''' Basic Transducer Test
    '''
    @classmethod
    def setUpClass(cls):
        cls.test_mapping_moh = Mapping(in_lang="moh", out_lang='moh-ipa')
        cls.test_mapping = Mapping([{'in': 'a', "out": 'b'}])
        cls.test_mapping_rev = Mapping(
            [{"in": 'a', "out": 'b'}], reverse=True)
        cls.test_mapping_ordered_feed = Mapping(
            [{"in": "a", "out": "b"}, {"in": "b", "out": "c"}], as_is=True)
        cls.test_mapping_ordered_counter_feed = Mapping(
            [{"in": "b", "out": "c"}, {"in": "a", "out": "b"}], as_is=True)
        cls.test_as_is_mapping = Mapping(
            [{"in": "j", "out": "ʣ"}, {"in": "'y", "out": "jˀ"}], as_is=True)
        cls.test_not_as_is_mapping = Mapping(
            [{"in": "j", "out": "ʣ"}, {"in": "'y", "out": "jˀ"}])
        cls.test_case_sensitive_mapping = Mapping(
            [{"in": "'n", "out": "n̓"}], case_sensitive=True)
        cls.test_case_insensitive_mapping = Mapping(
            [{"in": "'n", "out": "n̓"}], case_sensitive=False)
        cls.test_case_sensitive_transducer = Transducer(
            cls.test_case_sensitive_mapping)
        cls.test_case_insensitive_transducer = Transducer(
            cls.test_case_insensitive_mapping)
        cls.test_trans_as_is = Transducer(cls.test_as_is_mapping)
        cls.test_trans_not_as_is = Transducer(cls.test_not_as_is_mapping)
        cls.test_trans = Transducer(cls.test_mapping)
        cls.test_trans_ordered_feed = Transducer(
            cls.test_mapping_ordered_feed)
        cls.test_trans_ordered_counter_feed = Transducer(
            cls.test_mapping_ordered_counter_feed)
        cls.test_trans_rev = Transducer(cls.test_mapping_rev)
        cls.test_trans_moh = Transducer(cls.test_mapping_moh)
        cls.test_trans_composite = CompositeTransducer(
            [cls.test_trans, cls.test_trans_rev])
        cls.test_trans_composite_2 = CompositeTransducer(
            [cls.test_trans_rev, cls.test_trans])

    def test_ordered(self):
        transducer_i_feed = self.test_trans_ordered_feed('a', True)
        transducer_feed = self.test_trans_ordered_feed('a')
        transducer_i_counter_feed = self.test_trans_ordered_counter_feed(
            'a', True)
        transducer_counter_feed = self.test_trans_ordered_counter_feed('a')
        # These should feed b -> c
        self.assertEqual(transducer_feed, 'c')
        self.assertEqual(transducer_i_feed[1](), [((0, "a"), (0, "c"))])
        # These should counter-feed b -> c
        self.assertEqual(transducer_counter_feed, 'b')
        self.assertEqual(transducer_i_counter_feed[1](), [
                         ((0, "a"), (0, "b"))])

    def test_forward(self):
        self.assertEqual(self.test_trans('a'), "b")
        self.assertEqual(self.test_trans('b'), "b")

    def test_backward(self):
        self.assertEqual(self.test_trans_rev("b"), 'a')
        self.assertEqual(self.test_trans_rev("a"), 'a')

    def test_lang_import(self):
        self.assertEqual(self.test_trans_moh('kawennón:nis'), 'kawẽnõːnis')

    def test_composite(self):
        self.assertEqual(self.test_trans_composite('aba'), 'aaa')
        self.assertEqual(self.test_trans_composite_2('aba'), 'bbb')

    def test_as_is(self):
        self.assertEqual(self.test_trans_as_is("'y"), "jˀ")
        self.assertEqual(self.test_trans_not_as_is("'y"), "ʣˀ")

    def test_case_sensitive(self):
        self.assertEqual(self.test_case_sensitive_transducer("'N"), "'N")
        self.assertEqual(self.test_case_sensitive_transducer("'n"), "n̓")
        self.assertEqual(self.test_case_insensitive_transducer("'N"), "n̓")
        self.assertEqual(self.test_case_insensitive_transducer("'n"), "n̓")


if __name__ == "__main__":
    main()
