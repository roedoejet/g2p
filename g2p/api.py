""" Very Basic API
"""
import json
import os

from flask import Blueprint, abort
from flask_cors import CORS
from flask_restful import Api, Resource, inputs, reqparse
from networkx.algorithms.dag import ancestors, descendants
from networkx.exception import NetworkXError

from g2p import make_g2p
from g2p.exceptions import InvalidLanguageCode, NoPath
from g2p.log import LOGGER
from g2p.mappings.langs import LANGS_NETWORK, MAPPINGS_AVAILABLE
from g2p.static import __file__ as static_file


class Ancestors(Resource):
    def get(self, node):
        try:
            return sorted(ancestors(LANGS_NETWORK, node))
        except NetworkXError:
            abort(404)


class Descendants(Resource):
    def get(self, node):
        try:
            return sorted(descendants(LANGS_NETWORK, node))
        except NetworkXError:
            abort(404)


class Langs(Resource):
    def __init__(self):
        self.AVAILABLE_MAPPINGS = sorted(
            [
                {
                    k: v
                    for k, v in x.items()
                    if k not in ["mapping_data", "abbreviations_data"]
                }
                for x in MAPPINGS_AVAILABLE
            ],
            key=lambda x: x["in_lang"],
        )
        self.parser = reqparse.RequestParser()
        self.parser.add_argument(
            "verbose",
            dest="verbose",
            type=bool,
            location="args",
            default=False,
            required=False,
            help="Return verbose mappings information",
        )

    def get(self):
        args = self.parser.parse_args()
        verbose = args["verbose"]
        if verbose:
            return self.AVAILABLE_MAPPINGS
        else:
            return sorted(LANGS_NETWORK.nodes)


class Text(Resource):
    def __init__(self):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument(
            "in-lang",
            dest="in-lang",
            type=str,
            location="args",
            required=True,
            help="The input language",
        )
        self.parser.add_argument(
            "out-lang",
            dest="out-lang",
            type=str,
            location="args",
            required=True,
            help="The output language",
        )
        self.parser.add_argument(
            "text",
            dest="text",
            type=str,
            location="args",
            required=True,
            help="The text in the input language",
        )
        self.parser.add_argument(
            "index",
            dest="index",
            type=inputs.boolean,
            location="args",
            default=False,
            required=False,
            help="Return indices",
        )
        self.parser.add_argument(
            "debugger",
            dest="debugger",
            type=inputs.boolean,
            location="args",
            default=False,
            required=False,
            help="Debugging information about the transduction process",
        )

    def get(self):
        args = self.parser.parse_args()
        in_lang = args["in-lang"]
        out_lang = args["out-lang"]
        text = args["text"]
        index = args["index"]
        debugger = args["debugger"]
        try:
            transducer = make_g2p(in_lang, out_lang)
            tg = transducer(text)
            text = tg.output_string
            input_text = tg.input_string
            debugger = tg.debugger if debugger else debugger
            index = tg.edges if index else index
            return {
                "input-text": input_text,
                "output-text": text,
                "index": index,
                "debugger": debugger,
            }
        except NoPath:
            abort(400)
        except InvalidLanguageCode:
            abort(404)


def update_docs():
    """Update the swagger documentation with all nodes from the network"""
    swagger_path = os.path.join(os.path.dirname(static_file), "swagger.json")
    with open(swagger_path) as f:
        data = json.load(f)
    data["components"]["schemas"]["Langs"]["enum"] = sorted(LANGS_NETWORK.nodes)
    with open(swagger_path, "w") as f:
        f.write(json.dumps(data))
    LOGGER.info("Updated API documentation")


g2p_api = Blueprint("resources-g2p", __name__)

CORS(g2p_api)

api = Api(g2p_api)

api.add_resource(Ancestors, "/ancestors/<string:node>", endpoint="ancestors")

api.add_resource(Descendants, "/descendants/<string:node>", endpoint="descendants")

api.add_resource(Langs, "/langs", endpoint="langs")

api.add_resource(Text, "/g2p", endpoint="g2p")
