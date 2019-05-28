from unittest import main, TestCase
import os
from g2p.cors import Correspondence
from g2p.transducer import Transducer

class TransducerTest(TestCase):
    ''' Basic Transducer Test
    '''

    def setUp(self):
        self.test_cor = Correspondence([{'from': 'a', "to": 'b'}])
        self.test_cor_rev = Correspondence([{"from": 'a', "to": 'b'}], True)
        self.test_cor_moh = Correspondence(language={"lang": "moh", "table": "orth"})
        self.test_cor_ordered_feed = Correspondence([{"from": "a", "to": "b"}, {"from": "b", "to": "c"}])
        self.test_cor_ordered_counter_feed = Correspondence([{"from": "b", "to": "c"}, {"from": "a", "to": "b"}])
        self.test_trans = Transducer(self.test_cor)
        self.test_trans_ordered_feed = Transducer(self.test_cor_ordered_feed, True)
        self.test_trans_ordered_counter_feed = Transducer(self.test_cor_ordered_counter_feed, True)
        self.test_trans_rev = Transducer(self.test_cor_rev)
        self.test_trans_moh = Transducer(self.test_cor_moh, True)

    def test_ordered(self):
        transducer_i_feed = self.test_trans_ordered_feed('a', True)
        transducer_feed = self.test_trans_ordered_feed('a')
        transducer_i_counter_feed = self.test_trans_ordered_counter_feed('a', True)
        transducer_counter_feed = self.test_trans_ordered_counter_feed('a')
        # These should feed b -> c
        self.assertEqual(transducer_feed, 'c')
        self.assertEqual(transducer_i_feed[1](), [((0, "a"), (0, "c"))])
        # These should counter-feed b -> c
        self.assertEqual(transducer_counter_feed, 'b')
        self.assertEqual(transducer_i_counter_feed[1](), [((0, "a"), (0, "b"))])
    
    def test_forward(self):
        self.assertEqual(self.test_trans('a'), "b")
        self.assertEqual(self.test_trans('b'), "b")

    def test_backward(self):
        self.assertEqual(self.test_trans_rev("b"), 'a')
        self.assertEqual(self.test_trans_rev("a"), 'a')
    
    def test_lang_import(self):
        self.assertEqual(self.test_trans_moh('kawennón:nis'), 'kawẽnonnis')

if __name__ == "__main__":
    main()
    