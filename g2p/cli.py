import click
from flask.cli import FlaskGroup
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