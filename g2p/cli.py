import os
import click
import yaml
from pprint import PrettyPrinter as pp
from flask.cli import FlaskGroup
from collections import OrderedDict
from networkx import draw, has_path

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


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.version_option(version=VERSION, prog_name="g2p")
@click.group(cls=FlaskGroup, create_app=create_app, context_settings=CONTEXT_SETTINGS)
def cli():
    '''Management script for G2P'''


@click.option('--out-dir', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--ipa/--no-ipa', default=False)
@click.option('--dummy/--no-dummy', default=False)
@click.argument('in_lang', type=click.Choice([x for x in LANGS_NETWORK.nodes if not is_ipa(x) and not is_xsampa(x)]))
@cli.command(context_settings=CONTEXT_SETTINGS)
def generate_mapping(in_lang, dummy, ipa, out_dir):
    ''' Generate English mapping.
    '''
    if not ipa and not dummy:
        click.echo('You have to choose to generate either an IPA-based mapping or a dummy fallback mapping. Check the docs for more information.')
    if out_dir and (os.path.exists(os.path.join(out_dir, 'config.yaml')) or os.path.exists(os.path.join(out_dir, 'config.yaml'))):
        click.echo(
            f'There is already a mapping config file in \'{out_dir}\' \nPlease choose another path.')
        return
    if ipa:
        eng_ipa = Mapping(in_lang='eng-ipa', out_lang='eng-arpabet')
        new_mapping = Mapping(in_lang=in_lang, out_lang=f'{in_lang}-ipa')
        click.echo(f"Writing English IPA mapping for {in_lang} to file")
        create_mapping(new_mapping, eng_ipa,
                       write_to_file=True, out_dir=out_dir)
    if dummy:
        new_mapping = Mapping(in_lang=in_lang, out_lang=f'{in_lang}-ipa')
        click.echo(f"Writing dummy fallback mapping for {in_lang} to file")
        dummy_config, dummy_mapping = align_to_dummy_fallback(
            new_mapping, write_to_file=True, out_dir=out_dir)


@click.argument('path', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@cli.command(context_settings=CONTEXT_SETTINGS)
def generate_mapping_network(path):
    ''' Generate a png of the network of mapping languages. Requires matplotlib.
    '''
    import matplotlib.pyplot as plt
    draw(LANGS_NETWORK, with_labels=True)
    plt.show()


@click.option('--debugger/--no-debugger', default=False)
@click.option('--path', type=click.Path(exists=True, file_okay=True, dir_okay=False))
@click.argument('out_lang')
@click.argument('in_lang')
@click.argument('input_text', type=click.STRING)
@cli.command(context_settings=CONTEXT_SETTINGS)
def convert(in_lang, out_lang, input_text, path, debugger):
    '''Convert from in-lang to out-lang. Visit http://g2p-studio.herokuapp.com/api/v1/langs for a list of options.
    '''
    # Check valid input
    # Check input != output
    if in_lang == out_lang:
        raise click.UsageError(
            "Values must be different for 'IN_LANG' and 'OUT_LANG'")
    # Check input lang exists
    if not in_lang in LANGS_NETWORK.nodes:
        raise click.UsageError(
            f"'{in_lang}' is not a valid value for 'IN_LANG'")
    # Check output lang exists
    if not out_lang in LANGS_NETWORK.nodes:
        raise click.UsageError(
            f"'{out_lang}' is not a valid value for 'OUT_LANG'")
    # Check if path exists
    if not has_path(LANGS_NETWORK, in_lang, out_lang):
        raise click.UsageError(
            f"Path between '{in_lang}' and '{out_lang}' does not exist")
    if os.path.exists(input_text) and input_text.endswith('txt'):
        with open(input_text, encoding='utf8') as f:
            input_text = f.read()
    if in_lang and out_lang:
        transducer = make_g2p(in_lang, out_lang)
    elif path:
        transducer = Transducer(Mapping(path))
    tg = transducer(input_text)
    if debugger:
        output = [tg.output_string, tg.edges, tg.debugger]
        PRINTER.pprint(output)
    else:
        output = tg.output_string
        click.echo(output)


@cli.command(context_settings=CONTEXT_SETTINGS)
def update():
    ''' Update cached language files
    '''
    cache_langs()
    update_docs()
    network_to_echart(write_to_file=True)
