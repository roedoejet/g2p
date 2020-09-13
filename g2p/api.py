''' Very Basic API
'''
import os
import json

from flask import Blueprint, abort
from flask_restful import (Resource, Api, reqparse)
from flask_cors import CORS

from networkx.exception import NetworkXError, NetworkXNoPath
from networkx.algorithms.dag import ancestors, descendants
from g2p.static import __file__ as static_file
from g2p.transducer import Transducer
from g2p.mappings.langs import LANGS_NETWORK, MAPPINGS_AVAILABLE
from g2p.log import LOGGER
from g2p import make_g2p


class Ancestors(Resource):
    def get(self, node):
        try:
            return sorted([x for x in ancestors(LANGS_NETWORK, node)])
        except NetworkXError:
            abort(404)


class Descendants(Resource):
    def get(self, node):
        try:
            return sorted([x for x in descendants(LANGS_NETWORK, node)])
        except NetworkXError:
            abort(404)


class Langs(Resource):
    def __init__(self):
        self.AVAILABLE_MAPPINGS = sorted(
            [
                {k: v for k, v in x.items() if k not in [
                    'mapping_data', 'abbreviations_data']}
                for x in MAPPINGS_AVAILABLE
            ],
            key=lambda x: x['in_lang'])
        self.parser = reqparse.RequestParser()
        self.parser.add_argument(
            'verbose', dest='verbose',
            type=bool, location='args',
            default=False, required=False,
            help="Return verbose mappings information"
        )

    def get(self):
        args = self.parser.parse_args()
        verbose = args['verbose']
        if verbose:
            return self.AVAILABLE_MAPPINGS
        else:
            return sorted([x for x in LANGS_NETWORK.nodes])


class Text(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument(
            'in-lang', dest='in-lang',
            type=str, location='args',
            required=True, help='The input language',
        )
        self.parser.add_argument(
            'out-lang', dest='out-lang',
            type=str, location='args',
            required=True, help="The output language",
        )
        self.parser.add_argument(
            'text', dest='text',
            type=str, location='args',
            required=True, help="The text in the input language",
        )
        self.parser.add_argument(
            'index', dest='index',
            type=bool, location='args',
            default=False, required=False,
            help="Return indices",
        )
        self.parser.add_argument(
            'debugger', dest='debugger',
            type=bool, location='args',
            default=False, required=False,
            help="The text in the input language",
        )

    def get(self):
        args = self.parser.parse_args()
        in_lang = args['in-lang']
        out_lang = args['out-lang']
        text = args['text']
        index = args['index']
        debugger = args['debugger']
        try:
            transducer = make_g2p(in_lang, out_lang)
            tg = transducer(text)
            text = tg.output_string
            input_text = tg.input_string
            if debugger:
                debugger = tg.debugger
            if index:
                index = tg.edges
            return {'input-text': input_text, 'output-text': text, 'index': index, 'debugger': debugger}
        except NetworkXNoPath:
            abort(400)
        except FileNotFoundError:
            abort(404)


def update_docs():
    ''' Update the swagger documentation with all nodes from the network
    '''
    swagger_path = os.path.join(os.path.dirname(static_file), 'swagger.json')
    with open(swagger_path) as f:
        data = json.load(f)
    data['components']['schemas']['Langs']['enum'] = sorted(
        [x for x in LANGS_NETWORK.nodes])
    with open(swagger_path, 'w') as f:
        f.write(json.dumps(data))
    LOGGER.info('Updated API documentation')


g2p_api = Blueprint('resources.g2p', __name__)

CORS(g2p_api)

api = Api(g2p_api)

api.add_resource(
    Ancestors,
    '/ancestors/<string:node>',
    endpoint='ancestors'
)

api.add_resource(
    Descendants,
    '/descendants/<string:node>',
    endpoint='descendants'
)

api.add_resource(
    Langs,
    '/langs',
    endpoint='langs'
)

api.add_resource(
    Text,
    '/g2p',
    endpoint='g2p'
)
