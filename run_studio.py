#!/usr/bin/env python3

from g2p.app import APP, SOCKETIO
from g2p.log import LOGGER

host = "0.0.0.0"
port = 5000
LOGGER.info(f"g2p-studio listening on http://{host}:{port}")

SOCKETIO.run(APP, host=host, port=port, debug=True)
