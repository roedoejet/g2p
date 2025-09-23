#!/usr/bin/env python

import uvicorn

from g2p.app import APP
from g2p.log import LOGGER

host = "127.0.0.1"
port = 5000
LOGGER.info(f"g2p-studio listening on http://{host}:{port}")

uvicorn.run(APP, host=host, port=port)
