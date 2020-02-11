''' Very Basic API
'''

from flask import jsonify, Blueprint, abort
import json
from flask_restful import (Resource, Api, reqparse,
                           inputs, fields, url_for, marshal_with)
from flask_cors import CORS
from wordweaver.resources.affix import affix_fields
from wordweaver.data import affix_data, verb_data
from wordweaver.resources import require_appkey
from slugify import slugify

from networkx import shortest_path
from networkx.exception import NetworkXError, NetworkXNoPath
from networkx.algorithms.dag import ancestors, descendants
from g2p.mappings.langs import LANGS_NETWORK
from g2p import make_g2p

verb_fields = {
    'thematic_relation': fields.String,
    'display': fields.String,
    'gloss': fields.String,
    'tag': fields.String,
    'required_affixes': fields.List(fields.Nested(affix_fields)),
    'position': fields.Integer
}

class Ancestors(Resource):
    def get(self, node):
        try:
            return [x for x in ancestors(LANGS_NETWORK, node)]
        except NetworkXError:
            abort(404)

class Descendants(Resource):
    def get(self, node):
        try:
            return [x for x in descendants(LANGS_NETWORK, node)]
        except NetworkXError:
            abort(404)

class Langs(Resource):
    def get(self):
        return [x for x in LANGS_NETWORK.nodes]

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
    def get(self):
        args = self.parser.parse_args()
        in_lang = args['in-lang']
        out_lang = args['out-lang']
        text = args['text']
        try:
            transducer = make_g2p(in_lang, out_lang)
            return transducer(text)
        except NetworkXNoPath:
            abort(400)
        except FileNotFoundError:
            abort(404)

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
