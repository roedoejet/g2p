#!/usr/bin/env python3

from g2p.app import APP, SOCKETIO

SOCKETIO.run(APP, host='0.0.0.0', port=5000, debug=True)
