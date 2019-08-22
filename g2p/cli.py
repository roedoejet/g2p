import click
import yaml
from flask.cli import FlaskGroup
from collections import OrderedDict
from g2p.mappings.langs import cache_langs
from g2p._version import VERSION
from g2p import APP


def create_app():
    return APP


@click.version_option(version=VERSION, prog_name="g2p")
@click.group(cls=FlaskGroup, create_app=create_app)
def cli():
    '''Management script for G2P'''


@cli.command()
def update_langs():
    ''' Update cached language files
    '''
    cache_langs()


class IndentDumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super(IndentDumper, self).increase_indent(flow, False)

@cli.command()
@click.argument('language-name', type=click.STRING)
@click.argument('in-lang', type=click.STRING)
@click.argument('out-lang', type=click.STRING)
def create_table(**kwargs):
    '''Create a lookup table configuration
    '''
    csv = kwargs['in_lang'] + '_to_' + kwargs['out_lang'] + '.csv'
    template = {"mappings": [
        {"language_name": kwargs['language_name'],
         "display_name": kwargs['language_name'],
         "in_lang": kwargs['in_lang'],
         "out_lang": kwargs['out_lang'],
         "authors": ["Sample Sampleson"],
         "as_is": False,
         "case_sensitive": True,
         "escape_special": False,
         "norm_form": "NFC",
         "reverse": False,
         "mapping": csv}
    ]}
    with open('config.yaml', 'w') as f:
        yaml.dump(template, f, Dumper=IndentDumper, default_flow_style=False)
    with open(csv, 'w') as f:
        pass
