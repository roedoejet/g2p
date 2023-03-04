"""REST API for G2P index-preserving grapheme-to-phoneme conversion using FastAPI."""

from enum import Enum
from typing import List

from fastapi import FastAPI, HTTPException, Query
from networkx.algorithms.dag import ancestors, descendants

from g2p import make_g2p
from g2p.exceptions import InvalidLanguageCode, NoPath
from g2p.mappings.langs import LANGS_NETWORK

# Create the v1 version of the API
api = FastAPI(
    title="Simple G2P API",
    description="A simple API for the G2P module",
    version="1.1.0",
    contact={"email": "hello@aidanpine.ca"},
    license_info={
        "name": "MIT",
        "url": "https://github.com/roedoejet/g2p/blob/main/LICENSE",
    },
    openapi_tags=[
        {
            "name": "ancestors",
            "description": "Find which mappings can convert to a given node",
        },
        {
            "name": "descendants",
            "description": "Find which mappings can be converted to from a given node",
        },
        {"name": "g2p", "description": "Transduced, g2p'ed forms"},
        {"name": "langs", "description": "Languages/mappings available for G2P"},
    ],
)


# Get the langs
LANGS = sorted(LANGS_NETWORK.nodes)
Lang = Enum("Lang", [(name, name) for name in LANGS])  # type: ignore


@api.get(
    "/ancestors/{node}",
    summary="get all ancestors of node",
    tags=["ancestors"],
    operation_id="getAncestors",
    response_description="The valid ancestors of a node",
)
async def ancestors_(node: Lang = Query(description="language node name")) -> List[str]:
    """Get the valid ancestors in the network's path to a given node. These
    are all the mappings that you can convert from in order to get the
    given node."""
    return sorted(ancestors(LANGS_NETWORK, node.name))


@api.get(
    "/descendants/{node}",
    summary="get all descendants of node",
    tags=["descendants"],
    operation_id="getDescendants",
    response_description="The valid descendants of a node",
)
async def get_all_descendants_of_node(
    node: Lang = Query(description="language node name"),
) -> List[str]:
    return sorted(descendants(LANGS_NETWORK, node.name))


@api.get(
    "/g2p",
    summary="get g2p'ed form",
    tags=["g2p"],
    operation_id="convertString",
    response_description="The converted text",
)
async def g2p(
    in_lang: Lang = Query(alias="in-lang", description="input lang of string"),
    out_lang: Lang = Query(alias="out-lang", description="output lang of string"),
    text: str = Query(description="string to convert"),
    index: bool = Query(False, description="return indices"),
    debug: bool = Query(False, description="return debugging information"),
) -> dict:
    """Get the converted version of a string, given an input and output lang"""
    try:
        transducer = make_g2p(in_lang.name, out_lang.name)
        tg = transducer(text)
        return {
            "input-text": tg.input_string,
            "output-text": tg.output_string,
            "debugger": tg.debugger if debug else debug,
            "index": tg.edges if index else index,
        }
    except NoPath:
        raise HTTPException(
            status_code=400, detail=f"No path from {in_lang} to {out_lang}"
        )
    except InvalidLanguageCode:
        # Actually should never happen!
        raise HTTPException(
            status_code=404, detail="Unknown input or output language code"
        )


@api.get(
    "/langs",
    summary="find all possible languages in g2p",
    tags=["langs"],
    operation_id="searchTable",
    response_description="search results matching criteria",
)
async def langs() -> List[str]:
    """By passing in the appropriate options, you can find available mappings"""
    return LANGS
