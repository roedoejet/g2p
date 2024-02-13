"""

Views and config to the g2p Studio web app

"""
import json
from typing import List, Union

from flask import Flask, render_template
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from networkx import shortest_path

from g2p import make_g2p
from g2p.api import g2p_api
from g2p.log import LOGGER
from g2p.mappings import Mapping
from g2p.mappings.langs import LANGS_NETWORK
from g2p.mappings.utils import (
    _MappingModelDefinition,
    expand_abbreviations_format,
    flatten_abbreviations_format,
)
from g2p.transducer import (
    CompositeTransducer,
    CompositeTransductionGraph,
    Transducer,
    TransductionGraph,
)

APP = Flask(__name__)
APP.register_blueprint(g2p_api, url_prefix="/api/v1")
CORS(APP)
SOCKETIO = SocketIO(APP)
DEFAULT_N = 10


def shade_colour(colour, percent, r=0, g=0, b=0):
    R = hex(min(255, int((int(colour[1:3], 16) * (100 + percent + r) / 100)))).lstrip(
        "0x"
    )
    G = hex(min(255, int((int(colour[3:5], 16) * (100 + percent + g) / 100)))).lstrip(
        "0x"
    )
    B = hex(min(255, int((int(colour[5:], 16) * (100 + percent + b) / 100)))).lstrip(
        "0x"
    )
    return "#" + str(R) + str(G) + str(B)


def contrasting_text_color(hex_str):
    (R, G, B) = (hex_str[1:3], hex_str[3:5], hex_str[5:])
    return (
        "#000"
        if 1 - (int(R, 16) * 0.299 + int(G, 16) * 0.587 + int(B, 16) * 0.114) / 255
        < 0.5
        else "#fff"
    )


def return_echart_data(tg: Union[CompositeTransductionGraph, TransductionGraph]):
    x = 100
    diff = 200
    nodes = []
    edges = []
    index_offset = 0
    colour = "#222222"
    if isinstance(tg, CompositeTransductionGraph):
        steps = len(tg.tiers)
    else:
        steps = 1
    for ind, tier in enumerate(tg.tiers):
        if ind == 0:
            symbol_size = min(300 / len(tier.input_string), 40)
            input_x = x + (ind * diff)
            input_y = 300
            x += diff
            inputs = [
                {
                    "name": f"{x}",
                    "id": f"(in{ind+index_offset}-in{i+index_offset})",
                    "x": input_x,
                    "y": input_y + (i * 50),
                    "symbolSize": symbol_size,
                    "label": {"color": contrasting_text_color(colour)},
                    "itemStyle": {
                        "color": colour,
                        "borderColor": contrasting_text_color(colour),
                    },
                }
                for i, x in enumerate(tier.input_string)
            ]
            nodes += inputs
        edges += [
            {
                "source": x[0] + index_offset,
                "target": x[1] + len(tier.input_string) + index_offset,
            }
            for x in tier.edges
            if x[1] is not None
        ]
        index_offset += len(tier.input_string)
        symbol_size = min(300 / max(1, len(tier.output_string)), 40)
        colour = shade_colour(colour, (1 / steps) * 350, g=50, b=20)
        output_x = x + (ind * diff)
        output_y = 300
        outputs = [
            {
                "name": f"{x}",
                "id": f"({ind+index_offset}-{i+index_offset})",
                "x": output_x,
                "y": output_y + (i * 50),
                "symbolSize": symbol_size,
                "label": {"color": contrasting_text_color(colour)},
                "itemStyle": {
                    "color": colour,
                    "borderColor": contrasting_text_color(colour),
                },
            }
            for i, x in enumerate(tier.output_string)
        ]
        nodes += outputs
    return nodes, edges


@APP.route("/")
def home():
    """Return homepage of g2p studio"""
    return render_template("index.html")


@APP.route("/docs")
def docs():
    """Return swagger docs of g2p studio API"""
    return render_template("docs.html")


@SOCKETIO.on("conversion event", namespace="/convert")
def convert(message):
    """Convert input text and return output"""
    transducers = []
    for mapping in message["data"]["mappings"]:
        mapping_args = {**mapping["kwargs"]}
        mapping_args["abbreviations"] = flatten_abbreviations_format(
            mapping["abbreviations"]
        )
        mapping_args["rules"] = mapping["rules"]
        try:
            mappings_obj = Mapping(**mapping_args)
            transducer = Transducer(mappings_obj)
            transducers.append(transducer)
        except Exception as e:
            LOGGER.warning("Skipping invalid mapping: %s", e)
    if len(transducers) == 0:
        emit("conversion response", {"output_string": message["data"]["input_string"]})
        return
    transducer = CompositeTransducer(transducers)
    if message["data"]["index"]:
        tg = transducer(message["data"]["input_string"])
        data, links = return_echart_data(tg)
        emit(
            "conversion response",
            {
                "output_string": tg.output_string,
                "index_data": data,
                "index_links": links,
            },
        )
    else:
        output_string = transducer(message["data"]["input_string"]).output_string
        emit("conversion response", {"output_string": output_string})


@SOCKETIO.on("table event", namespace="/table")
def change_table(message):
    """Change the lookup table"""
    if "in_lang" not in message or "out_lang" not in message:
        emit("table response", [])
    elif message["in_lang"] == "custom" or message["out_lang"] == "custom":
        # These are only used to generate JSON to send to the client,
        # so it's safe to create a list of references to the same thing.
        mappings = [
            {"in": "", "out": "", "context_before": "", "context_after": ""}
        ] * DEFAULT_N
        abbs = [[""] * 6] * DEFAULT_N

        kwargs = _MappingModelDefinition(
            language_name="Custom",
            display_name="Custom",
            in_lang="custom",
            out_lang="custom",
            type="mapping",
            norm_form="NFC",
        ).model_dump()
        kwargs["include"] = False
        emit(
            "table response",
            [
                {
                    "mappings": mappings,
                    "abbs": abbs,
                    "kwargs": kwargs,
                }
            ],
        )
    else:
        path = shortest_path(LANGS_NETWORK, message["in_lang"], message["out_lang"])
        mappings: List[Mapping] = []
        for lang1, lang2 in zip(path[:-1], path[1:]):
            transducer = make_g2p(lang1, lang2, tokenize=False)
            mappings.append(transducer.mapping)
        emit(
            "table response",
            [
                {
                    "mappings": x.plain_mapping(),
                    "abbs": expand_abbreviations_format(x.abbreviations),
                    "kwargs": json.loads(x.model_dump_json()),
                }
                for x in mappings
            ],
        )


@SOCKETIO.on("connect", namespace="/connect")
def test_connect():
    """Let client know disconnected"""
    emit("connection response", {"data": "Connected"})


@SOCKETIO.on("disconnect", namespace="/connect")
def test_disconnect():
    """Let client know disconnected"""
    emit("connection response", {"data": "Disconnected"})
