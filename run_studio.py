#!/usr/bin/env python

import sys

if sys.version_info < (3, 8, 0):  # pragma: no cover
    raise Exception("")
    sys.exit(
        "ERROR: While the g2p CLI and library can still run on Python 3.7, "
        "g2p-studio requires Python 3.8 or more recent.\n"
        f"You are using {sys.version}.\n"
        "Please use a newer version of Python."
    )

import uvicorn

from g2p.app import APP
from g2p.log import LOGGER

host = "127.0.0.1"
port = 5000
LOGGER.info(f"g2p-studio listening on http://{host}:{port}")

uvicorn.run(APP, host=host, port=port)
