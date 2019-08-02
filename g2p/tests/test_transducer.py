from unittest import main, TestCase
from g2p.mappings import Mapping
from g2p.transducer import CompositeTransducer, Transducer


class TransducerTest(TestCase):
    ''' Basic Transducer Test
    '''

    def setUp(self):
        self.test_mapping = Mapping([{'in': 'a', "out": 'b'}])
        self.test_mapping_rev = Mapping([{"in": 'a', "out": 'b'}], reverse=True)
        self.test_mapping_moh = Mapping(
            language={"lang": "moh", "table": "Orthography"})
        self.test_mapping_ordered_feed = Mapping(
            [{"in": "a", "out": "b"}, {"in": "b", "out": "c"}])
        self.test_mapping_ordered_counter_feed = Mapping(
            [{"in": "b", "out": "c"}, {"in": "a", "out": "b"}])
        self.test_as_is_mapping = Mapping(
            [{"in": "j", "out": "ʣ"}, {"in": "'y", "out": "jˀ"}])
        self.test_case_sensitive_mapping = Mapping([{"in": "'n", "out": "n̓"}], case_sensitive=True)
        self.test_case_insensitive_mapping = Mapping([{"in": "'n", "out": "n̓"}], case_sensitive=False)
        self.test_case_sensitive_transducer = Transducer(self.test_case_sensitive_mapping)
        self.test_case_insensitive_transducer = Transducer(self.test_case_insensitive_mapping)
        self.test_trans_as_is = Transducer(self.test_as_is_mapping, as_is=True)
        self.test_trans_not_as_is = Transducer(self.test_as_is_mapping)
        self.test_trans = Transducer(self.test_mapping)
        self.test_trans_ordered_feed = Transducer(
            self.test_mapping_ordered_feed, True)
        self.test_trans_ordered_counter_feed = Transducer(
            self.test_mapping_ordered_counter_feed, True)
        self.test_trans_rev = Transducer(self.test_mapping_rev)
        self.test_trans_moh = Transducer(self.test_mapping_moh, True)
        self.test_trans_composite = CompositeTransducer(
            [self.test_trans, self.test_trans_rev])
        self.test_trans_composite_2 = CompositeTransducer(
            [self.test_trans_rev, self.test_trans])

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
        self.assertEqual(self.test_trans_moh('kawennón:nis'), 'kawẽnonnis')

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
