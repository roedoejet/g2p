#!/usr/bin/env python3
# -*- coding: utf-8 -*-

""" Checks all data resources give 200s
"""

from unittest import main, TestCase
import re
import os
import json

import requests

from g2p.app import APP
from g2p.log import LOGGER
from g2p.mappings.langs import LANGS_NETWORK
from g2p.tests.public import __file__ as PUB_FILE

PUB_DIR = os.path.dirname(PUB_FILE)

class ResourceIntegrationTest(TestCase):
    """
    This tests that the api returns 200s for all basic
    GET requests.
    """

    def setUp(self):
        # Test external hosts
        self.client = APP.test_client
        self.prefix = "/api/v1"
        # routes
        self.conversion_route = '/api/v1/g2p'
        self.static_route = "/static/<path:filename>"
        self.routes = [str(route) for route in APP.url_map.iter_rules()]
        self.routes_no_args = [
            route for route in self.routes if not "<" in route and route != self.conversion_route]
        self.routes_only_args = [
            route for route in self.routes if "<" in route and route != self.static_route]
        # endpoints
        self.rules_by_endpoint = APP.url_map._rules_by_endpoint
        self.endpoints = [rt for rt in self.rules_by_endpoint.keys()]
        # args
        self.arg_match = re.compile(r'\<[a-z:]+\>')
        self.args_to_check = ("node")

    def return_endpoint_arg(self, ep):
        split = ep.split('.')
        split_length = len(split)
        return split[split_length-1]

    def return_route_from_endpoint(self, ep):
        return str(self.rules_by_endpoint[ep][0])

    def test_response_code(self):
        '''
        Ensure all routes return 200
        '''
        for rt in self.routes_no_args:
            try:
                r = self.client().get(rt)
                self.assertEqual(r.status_code, 200)
                LOGGER.debug("Route " + rt +
                             " returned " + str(r.status_code))
            except:
                LOGGER.error("Couldn't connect. Is flask running?")

    def test_response_code_with_args(self):
        '''
        Ensure all args return 200
        '''
        for ep in self.routes_only_args:
            for node in LANGS_NETWORK.nodes:
                rt = re.sub(self.arg_match, node, ep)
                try:
                    r = self.client().get(rt)
                    self.assertEqual(r.status_code, 200)
                except:
                    LOGGER.error("Couldn't connect. Is flask running?")
            LOGGER.debug("Successfully tested " + str(len(LANGS_NETWORK.nodes)
                                                      ) + " node resources at route " + ep + " .")

    def test_g2p_conversion(self):
        '''
        Ensure conversion returns proper response
        '''
        params = {'in-lang': 'dan', 'out-lang': 'eng-arpabet',
                  'text': "hej", 'debugger': True, 'index': True}
        bad_params = {'in-lang': 'dan', 'out-lang': 'moh', 'text': "hej"}
        missing_params = {'in-lang': 'not-here',
                          'out-lang': 'eng-arpabet', 'text': "hej"}
        self.maxDiff = None
        response = self.client().get(self.conversion_route, query_string=params)
        res_json = response.get_json()
        self.assertEqual(response.status_code, 200)
        with open(os.path.join(PUB_DIR, 'sample_response.json')) as f:
            data = json.load(f)
        self.assertEqual(
            res_json, data)
        bad_response = self.client().get(self.conversion_route, query_string=bad_params)
        self.assertEqual(bad_response.status_code, 400)
        missing_response = self.client().get(
            self.conversion_route, query_string=missing_params)
        self.assertEqual(missing_response.status_code, 404)


if __name__ == '__main__':
    main()
