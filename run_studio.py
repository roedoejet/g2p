#!/usr/bin/env python

import sys

if sys.version_info < (3, 7, 0):  # pragma: no cover
    raise Exception("")
    sys.exit(
        "ERROR: While the g2p CLI and library can still run on Python 3.6, "
        "g2p-studio requires Python 3.7 or more recent.\n"
        f"You are using {sys.version}.\n"
        "Please use a newer version of Python."
    )

from g2p.app import APP, SOCKETIO
from g2p.log import LOGGER

host = "127.0.0.1"
port = 5000
LOGGER.info(f"g2p-studio listening on http://{host}:{port}")

SOCKETIO.run(APP, host=host, port=port, debug=True)
