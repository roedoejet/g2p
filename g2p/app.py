"""

Views and config to the g2p Studio web app

"""
import json
import os
import requests
from networkx.algorithms.dag import ancestors, descendants
from networkx.drawing.layout import spring_layout, spectral_layout, shell_layout, circular_layout
from flask import Flask, render_template
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from flask_talisman import Talisman
from typing import List

from g2p.mappings import Mapping
from g2p.mappings.langs import LANGS, LANGS_NETWORK
from g2p.transducer import CompositeTransducer, Transducer
from g2p.transducer.indices import Indices, IndexSequence
from g2p.static import __file__ as static_file
from g2p.mappings.utils import expand_abbreviations, flatten_abbreviations
from g2p.api import g2p_api
from g2p.log import LOGGER
from g2p import make_g2p

APP = Flask(__name__)
APP.register_blueprint(g2p_api, url_prefix='/api/v1')
CORS(APP)
SOCKETIO = SocketIO(APP)
DEFAULT_N = 10

def network_to_echart(write_to_file: bool = False, layout: bool = False):
    nodes = []
    no_nodes = len(LANGS_NETWORK.nodes)
    for node in LANGS_NETWORK.nodes:
        lang_name = node.split('-')[0]
        no_ancestors = len(ancestors(LANGS_NETWORK, node))
        no_descendants = len(descendants(LANGS_NETWORK, node))
        size = min(20, max(2, ((no_ancestors/no_nodes)*100 + (no_descendants/no_nodes)*100)))
        node = {'name': node, 'symbolSize': size, 'id': node, 'category': lang_name}
        nodes.append(node)
    edges = []
    for edge in LANGS_NETWORK.edges:
        edges.append({'source': edge[0], 'target': edge[1]})
    if write_to_file:
        with open(os.path.join(os.path.dirname(static_file), 'languages-network.json'), 'w') as f:
            f.write(json.dumps({'nodes': nodes, 'edges': edges}))
        LOGGER.info(f'Wrote network nodes and edges to static file.')
    return nodes, edges

def return_echart_data(index_sequence: IndexSequence):
    x = 100
    diff = 200
    nodes = []
    edges = []
    index_offset = 0
    for ind, indices in enumerate(index_sequence.states):
        input_string = indices.input()
        if ind == 0:
            input_x = x + (ind * diff)
            input_y = 300
            x += diff
            inputs = [{'name': f"{x}", 'id': f"(in{ind+index_offset}-in{i+index_offset})",  "x": input_x, "y": input_y + (i*50)}
                for i, x in enumerate(input_string)]
            nodes += inputs
            edges += [{"source": x[0][0] + index_offset, "target": x[1]
                [0] + len(input_string) + index_offset} for x in indices()]
            index_offset += len(input_string)
        else:
            edges += [{"source": x[0][0] + index_offset, "target": x[1]
                [0] + len(input_string) + index_offset} for x in indices()]
            index_offset += len(output_string)
        output_string = indices.output()
        output_x = x + (ind * diff)
        output_y = 300      
        outputs = [{'name': f"{x}", 'id': f"({ind+index_offset}-{i+index_offset})", "x": output_x, "y": output_y + (i*50)}
                for i, x in enumerate(output_string)]
        nodes += outputs
        
    return nodes, edges


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
    return [{"context_before": str(x[2] or ''), "in": str(x[0] or ''), "context_after": str(x[3] or ''),
             "out": str(x[1] or '')} for x in hot_data if x[0] or x[1]]


def return_descendant_nodes(node: str):
    ''' Return possible outputs for a given input
    '''
    return [x for x in descendants(LANGS_NETWORK, node)]


@APP.route('/')
def home():
    """ Return homepage of g2p studio
    """
    return render_template('index.html')


@APP.route('/docs')
def docs():
    """ Return swagger docs of g2p studio API
    """
    return render_template('docs.html')

@SOCKETIO.on('conversion event', namespace='/convert')
def convert(message):
    """ Convert input text and return output
    """
    transducers = []
    for mapping in message['data']['mappings']:
        mappings_obj = Mapping(hot_to_mappings(mapping['mapping']), abbreviations=flatten_abbreviations(
            mapping['abbreviations']), **mapping['kwargs'])
        transducer = Transducer(mappings_obj)
        transducers.append(transducer)
    transducer = CompositeTransducer(transducers)
    if message['data']['index']:
        output_string, iseq = transducer(message['data']['input_string'], index=True)
        data, links = return_echart_data(iseq)
        emit('conversion response', {'output_string': output_string, 'index_data': data, 'index_links': links})
    else:
        output_string = transducer(message['data']['input_string'])
        emit('conversion response', {'output_string': output_string})


@SOCKETIO.on('table event', namespace='/table')
def change_table(message):
    """ Change the lookup table
    """
    if message['in_lang'] == 'custom' or message['out_lang'] == 'custom':
        mappings = Mapping(return_empty_mappings())
    else:
        transducer = make_g2p(message['in_lang'], message['out_lang'])
    if isinstance(transducer, Transducer):
        mappings = [transducer.mapping]
    elif isinstance(transducer, CompositeTransducer):
        mappings = [x.mapping for x in transducer._transducers]
    else:
        pass
    emit('table response', [{'mappings': x.plain_mapping(),
                            'abbs': expand_abbreviations(x.abbreviations),
                            'kwargs': x.kwargs} for x in mappings])


@SOCKETIO.on('connect', namespace='/connect')
def test_connect():
    """ Let client know disconnected
    """
    emit('connection response', {'data': 'Connected'})


@SOCKETIO.on('disconnect', namespace='/connect')
def test_disconnect():
    """ Let client know disconnected
    """
    emit('connection response', {'data': 'Disconnected'})
