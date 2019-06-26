"""

Views and config to the G2P Studio web app

"""

from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from flask_talisman import Talisman
from g2p.cors import Correspondence
from g2p.cors.langs import LANGS
from g2p.transducer import Transducer
from g2p.cors.utils import expand_abbreviations, flatten_abbreviations


VERSION = '0.0.1'

APP = Flask(__name__)
SOCKETIO = SocketIO(APP)
DEFAULT_N = 10


def return_empty_cors(n=DEFAULT_N):
    ''' Return 'n' * empty cors
    '''
    y = 0
    cors = []
    while y < n:
        cors.append({
            "from": '',
            "to": '',
            "before": '',
            "after": ''
        })
        y += 1
    return cors


def hot_to_cors(hot_data):
    ''' Parse data from HandsOnTable to Correspondence format
    '''
    return [{"before": x[2], "from": x[0], "after": x[3],
             "to": x[1]} for x in hot_data if x[0] and x[1]]


@APP.route('/')
def home():
    """ Return homepage of G2P Studio
    """
    return render_template('index.html', langs=LANGS)


@SOCKETIO.on('conversion event', namespace='/test')
def convert(message):
    """ Convert input text and return output
    """
    cors = Correspondence(hot_to_cors(message['data']['cors']), abbreviations=flatten_abbreviations(
        message['data']['abbreviations']))
    transducer = Transducer(cors)
    output_string = transducer(message['data']['input_string'])
    emit('conversion response', {'output_string': output_string})


@SOCKETIO.on('table event', namespace='/test')
def change_table(message):
    """ Change the lookup table
    """
    if message['lang'] == 'custom':
        cors = Correspondence(return_empty_cors())
    else:
        cors = Correspondence(
            language={'lang': message['lang'], 'table': message['table']})
    emit('table response', {'cors': cors(),
                            'abbs': expand_abbreviations(cors.abbreviations)})


@SOCKETIO.on('connect', namespace='/test')
def test_connect():
    """ Let client know disconnected
    """
    emit('connection response', {'data': 'Connected'})


@SOCKETIO.on('disconnect', namespace='/test')
def test_disconnect():
    """ Let client know disconnected
    """
    print('Client disconnected')
