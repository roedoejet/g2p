import os
import click
import yaml
from pprint import PrettyPrinter as pp
from flask.cli import FlaskGroup
from collections import OrderedDict
from networkx import draw, has_path

from g2p.transducer import CompositeTransducer, Transducer
from g2p.mappings.create_fallback_mapping import align_to_dummy_fallback, DUMMY_INVENTORY
from g2p.mappings.langs import cache_langs, LANGS_NETWORK, MAPPINGS_AVAILABLE
from g2p.mappings.langs.utils import check_ipa_known_segs
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


@click.option('--out-dir', type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help='Output results in DIRECTORY instead of the global "generated" directory.')
@click.option('--list-dummy', default=False, is_flag=True, help="List the dummy phone inventory.")
@click.option('--dummy/--no-dummy', default=False, help="Generate dummy fallback mapping to minimalist phone inventory.")
@click.option('--ipa/--no-ipa', default=False, help="Generate mapping from LANG-ipa to eng-ipa.")
@click.argument('in_lang', type=click.Choice([x for x in LANGS_NETWORK.nodes if not is_ipa(x) and not is_xsampa(x)]))
@cli.command(context_settings=CONTEXT_SETTINGS, short_help="Generate English IPA or dummy mapping.")
def generate_mapping(in_lang, dummy, ipa, list_dummy, out_dir):
    ''' For specified IN_LANG, generate a mapping from IN_LANG-ipa to eng-ipa,
        or from IN_LANG-ipa to a dummy minimalist phone inventory.

        If you just modified or wrote the IN_LANG to IN_LANG-ipa mapping, don't forget
        to call "g2p update" first so "g2p generate-mapping" sees the latest version.

        Call "g2p update" again after calling "g2p generate-mapping" to make the new
        IN_LANG-ipa to eng-ipa mapping available.
    '''
    if not ipa and not dummy and not list_dummy:
        click.echo('You have to choose to generate either an IPA-based mapping or a dummy fallback mapping. Check the docs for more information.')
    if out_dir and (os.path.exists(os.path.join(out_dir, 'config.yaml')) or os.path.exists(os.path.join(out_dir, 'config.yaml'))):
        click.echo(
            f'There is already a mapping config file in \'{out_dir}\' \nPlease choose another path.')
        return
    if list_dummy:
        print("Dummy phone inventory: {}".format(DUMMY_INVENTORY))
    if ipa:
        check_ipa_known_segs([f'{in_lang}-ipa'])
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


@click.option('--debugger/--no-debugger', '-d',
    default=False, help="Show all the conversion steps applied."
)
@click.option('--path',
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    help="Read text to convert from FILE.",
)
@click.argument('out_lang')
@click.argument('in_lang')
@click.argument('input_text', type=click.STRING)
@cli.command(context_settings=CONTEXT_SETTINGS, short_help="Convert text through a g2p mapping path.")
def convert(in_lang, out_lang, input_text, path, debugger):
    '''Convert INPUT_TEXT through g2p mapping(s) from IN_LANG to OUT_LANG.

       Visit http://g2p-studio.herokuapp.com/api/v1/langs for a list of languages.

       There must be a path from IN_LANG to OUT_LANG, possibly via some intermediates.
       For example, mapping from fra to eng-arpabet will successively apply
       fra->fra-ipa, fra-ipa->eng-ipa and eng-ipa->eng-arpabet.
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


# Note: with -m eng-ipa, we actually check all the mappings from lang-ipa to eng-ipa.
@click.option("--list-all", is_flag=True, help="List all mappings that can be specified")
@click.option("--list-ipa", is_flag=True, help="List IPA mappings that can be specified")
@click.option(
    "--mapping", "-m", multiple=True,
    help="Check specified IPA mapping(s) (default: check all IPA mappings)."
)
@cli.command(context_settings=CONTEXT_SETTINGS)
def doctor(mapping, list_all, list_ipa):
    """ Check for common errors in mappings.
        There should eventually be more checks here, but doctor currently checks for:

        1. Characters that are in IPA mappings but are not recognized by panphon library.

        You can list available mappings with --list-all or --list-ipa, or by visiting
        http://g2p-studio.herokuapp.com/api/v1/langs .
    """
    if list_all or list_ipa:
        out_langs = sorted(set([x["out_lang"] for x in MAPPINGS_AVAILABLE]))
        if list_ipa:
            out_langs = [x for x in out_langs if is_ipa(x)]
        LOGGER.info("Specifying an output language will check all mappings into that language:\n")
        for m in out_langs:
            print(f"{m}: ", end="")
            print(
                ("\n" + " " * len(m) + "  ").join(
                    [x["in_lang"] for x in MAPPINGS_AVAILABLE if x["out_lang"] == m]
                )
            )
            print("")
        return

    for m in mapping:
        if m not in [x["out_lang"] for x in MAPPINGS_AVAILABLE]:
            raise click.UsageError(
                f"No known mappings into '{m}'. "
                "Use --list-all or --list-ipa to list valid options."
            )
        if not is_ipa(m):
            LOGGER.warning(
                f"No checks implemented yet for non-IPA mappings: '{m}' will not be checked."
            )

    if not mapping:
        LOGGER.info("Checking all IPA mappings.")
    else:
        LOGGER.info("Checking the following mappings: \n" + "\n".join(mapping))

    check_ipa_known_segs(list(mapping))


@cli.command(context_settings=CONTEXT_SETTINGS)
def update():
    ''' Update cached language files
    '''
    cache_langs()
    update_docs()
    network_to_echart(write_to_file=True)
