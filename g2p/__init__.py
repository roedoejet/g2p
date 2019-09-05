"""

Views and config to the g2p Studio web app

"""
import sys
import io
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from flask_talisman import Talisman
from g2p.mappings import Mapping
from g2p.mappings.langs import LANGS
from g2p.transducer import Transducer
from g2p.transducer.indices import Indices
from g2p.mappings.utils import expand_abbreviations, flatten_abbreviations
from g2p._version import VERSION

if sys.stdout.encoding != 'utf8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf8")

if sys.stderr.encoding != 'utf8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf8")


APP = Flask(__name__)
SOCKETIO = SocketIO(APP)
DEFAULT_N = 10

def return_echart_data(indices: Indices):
    input_string = indices.input()
    input_x = 300
    input_y = 300

    output_string = indices.output()
    output_x = 500
    output_y = 300

    inputs = [{'name': f"{x} (in-{i})", "x": input_x, "y": input_y + (i*50)} for i,x in enumerate(input_string)]
    outputs = [{'name': f"{x} (out-{i})", "x": output_x, "y": output_y + (i*50)} for i,x in enumerate(output_string)]

    data = inputs + outputs

    links = [{"source": x[0][0], "target": x[1][0] + len(input_string)} for x in indices()]

    return data, links

def return_empty_mappings(n=DEFAULT_N):
    ''' Return 'n' * empty mappings
    '''
    y = 0
    mappings = []
    while y < n:
        mappings.append({
            "in": '',
            "out": '',
            "context_before": '',
            "context_after": ''
        })
        y += 1
    return mappings

def hot_to_mappings(hot_data):
    ''' Parse data from HandsOnTable to Mapping format
    '''
    return [{"context_before": x[2], "in": x[0], "context_after": x[3],
             "out": x[1]} for x in hot_data if x[0] and x[1]]

@APP.route('/')
def home():
    """ Return homepage of g2p Studio
    """
    return render_template('index.html', langs=LANGS)

@SOCKETIO.on('index conversion event', namespace='/test')
def index_convert(message):
    """ Convert input text and return output with indices for echart
    """
    mappings = Mapping(hot_to_mappings(message['data']['mappings']), abbreviations=flatten_abbreviations(
        message['data']['abbreviations']), **message['data']['kwargs'])
    transducer = Transducer(mappings)
    output_string, indices = transducer(message['data']['input_string'], index=True)
    data, links = return_echart_data(indices)
    emit('index conversion response', {'output_string': output_string, 'index_data': data, 'index_links': links})

@SOCKETIO.on('conversion event', namespace='/test')
def convert(message):
    """ Convert input text and return output
    """
    mappings = Mapping(hot_to_mappings(message['data']['mappings']), abbreviations=flatten_abbreviations(
        message['data']['abbreviations']), **message['data']['kwargs'])
    transducer = Transducer(mappings)
    output_string = transducer(message['data']['input_string'])
    emit('conversion response', {'output_string': output_string})


@SOCKETIO.on('table event', namespace='/test')
def change_table(message):
    """ Change the lookup table
    """
    if message['in_lang'] == 'custom' or message['out_lang'] == 'custom':
        mappings = Mapping(return_empty_mappings())
    else:
        mappings = Mapping(
            in_lang=message['in_lang'], out_lang=message['out_lang'])
    emit('table response', {'mappings': mappings.plain_mapping(),
                            'abbs': expand_abbreviations(mappings.abbreviations),
                            'kwargs': mappings.kwargs})


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
