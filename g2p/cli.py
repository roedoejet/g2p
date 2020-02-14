import os
import click
import yaml
from pprint import PrettyPrinter as pp
from flask.cli import FlaskGroup
from collections import OrderedDict
from networkx import draw

from g2p.transducer import CompositeTransducer, Transducer
from g2p.mappings.create_fallback_mapping import align_to_dummy_fallback
from g2p.mappings.langs import cache_langs, LANGS_NETWORK
from g2p.mappings.create_ipa_mapping import create_mapping
from g2p.mappings.utils import is_ipa, is_xsampa
from g2p.mappings import Mapping
from g2p._version import VERSION
from g2p.app import APP, SOCKETIO, network_to_echart
from g2p.api import update_docs
from g2p.log import LOGGER
from g2p import make_g2p

PRINTER = pp(indent=4)

def create_app():
    return APP

@click.version_option(version=VERSION, prog_name="g2p")
@click.group(cls=FlaskGroup, create_app=create_app)
def cli():
    '''Management script for G2P'''

@click.option('--out-dir', default='', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--ipa/--no-ipa', default=False)
@click.option('--dummy/--no-dummy', default=False)
@click.argument('in_lang', type=click.Choice([x for x in LANGS_NETWORK.nodes if not is_ipa(x) and not is_xsampa(x)]))
@cli.command()
def generate_mapping(in_lang, dummy, ipa, out_dir):
    ''' Generate English mapping
    '''
    if not ipa and not dummy:
        click.echo('You have to choose to generate either an IPA-based mapping or a dummy fallback mapping. Check the docs for more information.')
    if ipa:
        eng_ipa = Mapping(in_lang='eng-ipa', out_lang='eng-arpabet')
        new_mapping = Mapping(in_lang=in_lang, out_lang=f'{in_lang}-ipa')
        click.echo(f"Writing English IPA mapping for {in_lang} to file")
        create_mapping(new_mapping, eng_ipa, write_to_file=True, out_dir=out_dir)
    if dummy:
        new_mapping = Mapping(in_lang=in_lang, out_lang=f'{in_lang}-ipa')
        click.echo(f"Writing dummy fallback mapping for {in_lang} to file")
        dummy_config, dummy_mapping = align_to_dummy_fallback(new_mapping, write_to_file=True, out_dir=out_dir)

@click.argument('path', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@cli.command()
def generate_mapping_network(path):
    ''' Generate a png of the network of mapping languages. Requires matplotlib.
    '''
    import matplotlib.pyplot as plt
    draw(LANGS_NETWORK, with_labels=True)
    plt.show()

@click.option('--json-safe/--json-unsafe', default=False)
@click.option('--index/--no-index', default=False)
@click.option('--debugger/--no-debugger', default=False)
@click.argument('out_lang', type=click.Choice(LANGS_NETWORK.nodes))
@click.argument('in_lang', type=click.Choice(LANGS_NETWORK.nodes))
@click.argument('input_text', type=click.STRING)
@cli.command()
def convert(in_lang, out_lang, input_text, debugger, index, json_safe):
    ''' Convert any text
    '''
    if os.path.exists(input_text) and input_text.endswith('txt'):
        with open(input_text, encoding='utf8') as f:
            input_text = f.read()
    transducer = make_g2p(in_lang, out_lang)
    output = list(transducer(input_text, index=index, debugger=debugger))
    if json_safe and debugger and index:
        output[1] = output[1].reduced()
        output[2] = Transducer.make_debugger_output_safe(output[2])
    elif json_safe and index:
        output[1] = output[1].reduced()
    elif json_safe and debugger:
        output[1] = Transducer.make_debugger_output_safe(output[1])
    if debugger:
        PRINTER.pprint(output)
    else:
        click.echo(output)

@cli.command()
def update():
    ''' Update cached language files
    '''
    cache_langs()
    update_docs()
    network_to_echart(write_to_file=True)
