"""REST API for G2P index-preserving grapheme-to-phoneme conversion using FastAPI.

You can run the API app for development purposes on any platform with:
    pip install uvicorn fastapi
    DEVELOPMENT=1 uvicorn g2p.api_v2:app --reload --port 5000
- The --reload switch will watch for changes under the directory where it's
  running and reload the code whenever it changes.
- DEVELOPMENT=1 tells the API to accept cross-origin requests (i.e. by sending the
  appropriate CORS headers) from development servers running on localhost, e.g.
  http://localhost:4200

For deployment, you can use the ORIGIN environment variable to set the
URL of your application in order to make it accept requests from that
site.  For instance if you deployed an application that uses it at
https://my.awesome.site you would set ORIGIN=https://my.awesome.site
in your environment variables.  This is usually done through an
environment variable file (or in a dashboard) and will depend on your
hosting environment.

You can also spin up the API server grade (on Linux, not Windows) with gunicorn:
    pip install -r requirements.api.txt
    gunicorn -b 127.0.0.1:5000 -w 4 -k uvicorn.workers.UvicornWorker g2p.api_v2:app

Once spun up, the API will be visible at
http://localhost:5000/api/v2/docs

"""

import os
from enum import Enum
from typing import Dict, List, Tuple, Union

from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from networkx.algorithms.dag import ancestors, descendants
from pydantic import BaseModel, Field

import g2p
from g2p.exceptions import InvalidLanguageCode, NoPath
from g2p.log import LOGGER
from g2p.mappings.langs import LANGS_NETWORK
from g2p.transducer import TransductionGraph

# Create the v2 version of the API
api = FastAPI(
    title="Simple G2P API",
    description="A simple API for the G2P module",
    version="2.0.0",
    contact={"email": "dhd@ecolingui.ca"},
    license_info={
        "name": "MIT",
        "url": "https://github.com/roedoejet/g2p/blob/main/LICENSE",
    },
)

# Create an "app" that mounts it in the appropriate place
app = FastAPI()
app.mount("/api/v2", api)
middleware_args: Dict[str, Union[str, List[str]]]
if os.getenv("DEVELOPMENT", False):
    LOGGER.info(
        "Running in development mode, will allow requests from http://localhost:*"
    )
    # Allow requests from localhost dev servers
    middleware_args = dict(
        allow_origin_regex="http://localhost(:.*)?",
    )
else:
    # Allow requests *only* from mt app (or otherwise configured site name)
    middleware_args = dict(
        allow_origins=[
            os.getenv("ORIGIN", "https://readalong-studio.mothertongues.org"),
        ],
    )
app.add_middleware(
    CORSMiddleware, allow_methods=["GET", "POST", "OPTIONS"], **middleware_args
)


# Get the langs
LANGS = sorted(LANGS_NETWORK.nodes)
LanguageNode = Enum("LanguageNode", [(name, name) for name in LANGS])  # type: ignore


@api.get("/langs", response_description="List of supported language code strings")
def langs() -> List[str]:
    """Return list of supported language codes.  Note that these are not
    exactly *languages* but rather writing or phonetic systems
    associated with a given language.
    """
    return LANGS


class ConvertRequest(BaseModel):
    """Request conversion from one writing or phonetic system to another."""

    in_lang: LanguageNode = Field(
        description="Name of input language", example="eng-ipa"
    )
    out_lang: LanguageNode = Field(
        description="Name of output language", example="eng-arpabet"
    )
    text: str = Field(description="Text to convert", example="hɛloʊ")
    compose: bool = Field(
        False, description="Compose returned conversions into a single step"
    )


class Conversion(BaseModel):
    """One step in G2P conversion"""

    in_lang: Union[None, LanguageNode] = Field(
        None,
        description="Name of input language, absent if no conversion was done",
        example="eng-ipa",
    )
    out_lang: Union[None, LanguageNode] = Field(
        None,
        description="Name of output language, absent if no conversion was done",
        example="eng-arpabet",
    )
    alignments: List[Tuple[str, str]] = Field(
        description="Alignments of input to output substrings",
        example=[
            ["h", "HH "],
            ["ɛ", "EH "],
            ["l", "L "],
            ["oʊ", "OW "],
        ],
    )


class Segment(BaseModel):
    """Result of G2P conversion of one segment of input, with
    intermediate steps and alignments."""

    conversions: List[Conversion] = Field(
        description="Sequence of conversions in reverse order.",
        example=[
            {
                "in_lang": "eng-ipa",
                "out_lang": "eng-arpabet",
                "alignments": [
                    ["h", "HH "],
                    ["ɛ", "EH "],
                    ["l", "L "],
                    ["oʊ", "OW "],
                ],
            }
        ],
    )


@api.post("/convert")
def convert(
    request: ConvertRequest = Body(
        examples={
            "eng-ipa to eng-arpabet": {
                "summary": "Convert English IPA to ARPABET",
                "description": "G2P can do simple conversions between equivalent phonetic notations",
                "value": {
                    "in_lang": "eng-ipa",
                    "out_lang": "eng-arpabet",
                    "text": "hɛloʊ",
                },
            },
            "fin to eng-arpabet": {
                "summary": "Convert Finnish orthography to nearest ARPABET phones",
                "description": """
G2P can do also (sometimes) approximate one language's phonology using phones from another.
To find out possible output languages for an input, use the 'outputs_for' endpoint.""",
                "value": {
                    "in_lang": "fin",
                    "out_lang": "eng-arpabet",
                    "text": "hyvää yötä",
                },
            },
            "composed conversion": {
                "summary": "Convert Finnish orthography directly to nearest ARPABET phones",
                "description": "By default all the conversion steps are returned.  "
                "You can get the direct mapping from input to output by setting compose: True",
                "value": {
                    "in_lang": "fin",
                    "out_lang": "eng-arpabet",
                    "text": "hyvää huomenta",
                    "compose": True,
                },
            },
            "tokenized conversion": {
                "summary": "Convert Finnish orthography with punctuation directly to nearest ARPABET phones",
                "description": "Non-word segments are returned with in_lang and out_lang as null",
                "value": {
                    "in_lang": "fin",
                    "out_lang": "eng-arpabet",
                    "text": "Varaus! Sieni, joka kasvaa korvessa, on myrkyllinen!",
                    "compose": True,
                },
            },
        }
    )
) -> List[Segment]:
    """Tokenize a text return the converted and intermediate forms of each
    segment (non-token segments will have converted=False).  The final
    conversion comes first in the output, followed by prevoius
    conversions.  If you do not want the intermediate conversions, set
    "compose" to True.

    """
    in_lang = request.in_lang.name
    out_lang = request.out_lang.name
    try:
        transducer = g2p.make_g2p(in_lang, out_lang)
        tokenizer = g2p.make_tokenizer(in_lang)
    except NoPath:
        raise HTTPException(
            status_code=400, detail=f"No path from {in_lang} to {out_lang}"
        )
    except InvalidLanguageCode:
        # Actually should never happen!
        raise HTTPException(
            status_code=404, detail="Unknown input or output language code"
        )

    segments: List[Segment] = []
    for token in tokenizer.tokenize_text(request.text):
        conversions: List[Conversion] = []
        if not token["is_word"]:
            tg = TransductionGraph(token["text"])
            conversions.append(
                Conversion(
                    alignments=tg.alignments(),
                )
            )
        else:
            tg = transducer(token["text"])
            if request.compose:
                conversions.append(
                    Conversion(
                        in_lang=transducer.in_lang,
                        out_lang=transducer.out_lang,
                        alignments=tg.alignments(),
                    )
                )
            else:
                for tr, tier in zip(transducer.transducers, tg.tiers):
                    conversions.insert(
                        0,
                        Conversion(
                            in_lang=tr.in_lang,
                            out_lang=tr.out_lang,
                            alignments=tier.alignments(),
                        ),
                    )
        segments.append(Segment(conversions=conversions))
    return segments


@api.get(
    "/outputs_for/{lang}",
    response_description="List of language codes into which {lang} can be converted",
)
def outputs_for(
    lang: LanguageNode = Query(description="Input language name"),
) -> List[str]:
    """Get the possible output languages for a given input language. These
    are all the phonetic or orthographic systems into which you can convert
    this input.
    """
    return sorted(descendants(LANGS_NETWORK, lang.name))


@api.get(
    "/inputs_for/{lang}",
    response_description="List of language codes which can be converted into {lang}",
)
def inputs_for(
    lang: LanguageNode = Query(description="Output language name"),
) -> List[str]:
    """Get the possible input languages for a given output language. These
    are all the phonetic or orthographic systems that you can convert
    into this output.
    """
    return sorted(ancestors(LANGS_NETWORK, lang.name))
