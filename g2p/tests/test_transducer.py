#!/usr/bin/env python3

import os
from unittest import main, TestCase
from g2p.mappings import Mapping
from g2p.tests.public import PUBLIC_DIR
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
            [{"in": "a", "out": "b"}, {"in": "b", "out": "c"}])
        cls.test_mapping_ordered_counter_feed = Mapping(
            [{"in": "b", "out": "c"}, {"in": "a", "out": "b"}])
        cls.test_longest_first = Mapping(
            [{"in": "j", "out": "ʣ"}, {"in": "'y", "out": "jˀ"}])
        cls.test_rules_as_written_mapping = Mapping(
            [{"in": "j", "out": "ʣ"}, {"in": "'y", "out": "jˀ"}], rule_ordering="apply-longest-first")
        cls.test_case_sensitive_mapping = Mapping(
            [{"in": "'n", "out": "n̓"}], case_sensitive=True)
        cls.test_case_insensitive_mapping = Mapping(
            [{"in": "'n", "out": "n̓"}], case_sensitive=False)
        cls.test_case_sensitive_transducer = Transducer(
            cls.test_case_sensitive_mapping)
        cls.test_case_insensitive_transducer = Transducer(
            cls.test_case_insensitive_mapping)
        cls.test_trans_as_written = Transducer(cls.test_longest_first)
        cls.test_trans_longest_first = Transducer(cls.test_rules_as_written_mapping)
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
        cls.test_regex_set_transducer_sanity = Transducer(
            Mapping([{"in": "a", "out": "b", "context_before": "c"}]))
        cls.test_regex_set_transducer = Transducer(
            Mapping([{"in": "a", "out": "b", "context_before": "[cd]|[fgh]"}]))
        cls.test_deletion_transducer = Transducer(
            Mapping([{'in': 'a', "out": ''}]))
        csv_deletion_mapping = Mapping(os.path.join(
            PUBLIC_DIR, 'mappings', 'deletion_config_csv.yaml'))
        cls.test_deletion_transducer_csv = Transducer(csv_deletion_mapping)
        cls.test_deletion_transducer_json = Transducer(
            Mapping(os.path.join(PUBLIC_DIR, 'mappings', 'deletion_config_json.yaml')))

    def test_ordered(self):
        transducer_i_feed = self.test_trans_ordered_feed('a')
        transducer_feed = self.test_trans_ordered_feed('a')
        transducer_i_counter_feed = self.test_trans_ordered_counter_feed('a')
        transducer_counter_feed = self.test_trans_ordered_counter_feed('a')
        # These should feed b -> c
        self.assertEqual(transducer_feed.output_string, 'c')
        # These should counter-feed b -> c
        self.assertEqual(transducer_counter_feed.output_string, 'b')

    def test_forward(self):
        self.assertEqual(self.test_trans('a').output_string, "b")
        self.assertEqual(self.test_trans('b').output_string, "b")

    def test_backward(self):
        self.assertEqual(self.test_trans_rev("b").output_string, 'a')
        self.assertEqual(self.test_trans_rev("a").output_string, 'a')

    def test_lang_import(self):
        self.assertEqual(self.test_trans_moh('kawennón:nis').output_string, 'kawẽnõːnis')

    def test_composite(self):
        self.assertEqual(self.test_trans_composite('aba').output_string, 'aaa')
        self.assertEqual(self.test_trans_composite_2('aba').output_string, 'bbb')

    def test_rule_ordering(self):
        self.assertEqual(self.test_trans_as_written("'y").output_string, "jˀ")
        self.assertEqual(self.test_trans_longest_first("'y").output_string, "ʣˀ")

    def test_case_sensitive(self):
        self.assertEqual(self.test_case_sensitive_transducer("'N").output_string, "'N")
        self.assertEqual(self.test_case_sensitive_transducer("'n").output_string, "n̓")
        self.assertEqual(self.test_case_insensitive_transducer("'N").output_string, "n̓")
        self.assertEqual(self.test_case_insensitive_transducer("'n").output_string, "n̓")

    def test_regex_set(self):
        # https://github.com/roedoejet/g2p/issues/15
        self.assertEqual(self.test_regex_set_transducer_sanity('ca').output_string, 'cb')
        self.assertEqual(self.test_regex_set_transducer('ca').output_string, 'cb')
        self.assertEqual(self.test_regex_set_transducer('fa').output_string, 'fb')

    def test_deletion(self):
        self.assertEqual(self.test_deletion_transducer('a').output_string, '')
        self.assertEqual(self.test_deletion_transducer_csv('a').output_string, '')
        self.assertEqual(self.test_deletion_transducer_json('a').output_string, '')


if __name__ == "__main__":
    main()
