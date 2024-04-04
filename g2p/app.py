"""
The g2p Studio web app.

You can run the app (and API) for development purposes on any platform with:
    pip install uvicorn
    uvicorn g2p.app:APP --reload --port 5000
- The --reload switch will watch for changes under the directory where it's
  running and reload the code whenever it changes.

You can also spin up the app server grade (on Linux, not Windows) with gunicorn:
    gunicorn -w 4 -k uvicorn.workers.UvicornWorker g2p.app:APP --port 5000

Once spun up, the application will be visible at
http://localhost:5000/ and the API at http://localhost:5000/api/v1/docs

"""

from typing import List, Union

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi_socketio import SocketManager  # type: ignore
from networkx import shortest_path  # type: ignore

from g2p import make_g2p
from g2p.api import api as api_v1
from g2p.log import LOGGER
from g2p.mappings import Mapping, Rule
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

DEFAULT_N = 10

TEMPLATES = Jinja2Templates(directory="g2p/templates")
APP = FastAPI()
SOCKET_MANAGER = SocketManager(
    app=APP,
    # This next argument is very important
    # and requires FastApi>=0.109.0
    # (and thus Starlette>=0.33.0).
    # See https://github.com/encode/starlette/discussions/2413
    socketio_path="/ws/socket.io",
)
APP.mount("/api/v1", api_v1)
APP.mount("/static", StaticFiles(directory="g2p/static"), name="static")


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


@APP.get("/", response_class=HTMLResponse)
def home(request: Request):
    """Return homepage of g2p studio"""
    return TEMPLATES.TemplateResponse("index.html", {"request": request})


@APP.sio.on("conversion event", namespace="/convert")  # type: ignore
async def convert(sid, message):
    """Convert input text and return output"""
    transducers = []
    LOGGER.debug("/convert: %s", message)
    for mapping in message["data"]["mappings"]:
        mapping_args = {**mapping["kwargs"]}
        mapping_args["abbreviations"] = flatten_abbreviations_format(
            mapping["abbreviations"]
        )
        if mapping_args["type"] == "lexicon":
            lexicon = Mapping.find_mapping(
                mapping_args["in_lang"], mapping_args["out_lang"]
            )
            mapping_args["alignments"] = lexicon.alignments
        else:
            mapping_args["rules"] = mapping["rules"]
        try:
            mappings_obj = Mapping(**mapping_args)
            transducer = Transducer(mappings_obj)
            transducers.append(transducer)
        except Exception as e:
            LOGGER.warning(
                "Skipping invalid mapping %s->%s:\n%s",
                mapping_args["in_lang"],
                mapping_args["out_lang"],
                e,
            )
    if len(transducers) == 0:
        await APP.sio.emit(
            "conversion response",
            {"output_string": message["data"]["input_string"]},
            sid,
            namespace="/convert",
        )
        return
    transducer = CompositeTransducer(transducers)
    if message["data"]["index"]:
        tg = transducer(message["data"]["input_string"])
        data, links = return_echart_data(tg)
        await APP.sio.emit(  # type: ignore
            "conversion response",
            {
                "output_string": tg.output_string,
                "index_data": data,
                "index_links": links,
            },
            sid,
            namespace="/convert",
        )
    else:
        output_string = transducer(message["data"]["input_string"]).output_string
        await APP.sio.emit(  # type: ignore
            "conversion response",
            {"output_string": output_string},
            sid,
            namespace="/convert",
        )


@APP.sio.on("table event", namespace="/table")  # type: ignore
async def change_table(sid, message):
    """Change the lookup table"""
    LOGGER.debug("/table: %s", message)
    if "in_lang" not in message or "out_lang" not in message:
        await APP.sio.emit(
            "table response",
            [],
            sid,
            namespace="/table",
        )
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
            # Put something here to silence a warning
            rules=[Rule(rule_input="a", rule_output="a")],
        ).model_dump()
        kwargs["rules"] = []
        # Remove the bogus rule we used to silence the validator
        kwargs["include"] = False
        await APP.sio.emit(
            "table response",
            [
                {
                    "mappings": mappings,
                    "abbs": abbs,
                    "kwargs": kwargs,
                }
            ],
            sid,
            namespace="/table",
        )
    else:
        path = shortest_path(LANGS_NETWORK, message["in_lang"], message["out_lang"])
        mappings: List[Mapping] = []
        for lang1, lang2 in zip(path[:-1], path[1:]):
            transducer = make_g2p(lang1, lang2, tokenize=False)
            mappings.append(transducer.mapping)
        await APP.sio.emit(
            "table response",
            [
                {
                    "mappings": x.plain_mapping(),
                    "abbs": expand_abbreviations_format(x.abbreviations),
                    "kwargs": x.model_dump(exclude=["alignments"]),
                }
                for x in mappings
            ],
            sid,
            namespace="/table",
        )


@APP.sio.on("connect", namespace="/connect")  # type: ignore
async def test_connect(sid, message):
    """Let client know disconnected"""
    await APP.sio.emit(  # type: ignore
        "connection response", {"data": "Connected"}, sid, namespace="/connect"
    )


@APP.sio.on("disconnect", namespace="/connect")  # type: ignore
async def test_disconnect(sid):
    """Let client know disconnected"""
    await APP.sio.emit(  # type: ignore
        "connection response", {"data": "Disconnected"}, sid, namespace="/connect"
    )
