import os
import pprint
import re

import click
import yaml
from flask.cli import FlaskGroup
from networkx import draw, has_path

from g2p import make_g2p
from g2p._version import VERSION
from g2p.api import update_docs
from g2p.app import APP, network_to_echart
from g2p.exceptions import MappingMissing
from g2p.log import LOGGER
from g2p.mappings import Mapping
from g2p.mappings.create_fallback_mapping import (
    DUMMY_INVENTORY,
    align_to_dummy_fallback,
)
from g2p.mappings.create_ipa_mapping import create_mapping
from g2p.mappings.langs import LANGS_NETWORK, MAPPINGS_AVAILABLE, cache_langs
from g2p.mappings.langs.utils import check_ipa_known_segs
from g2p.mappings.utils import is_ipa, is_xsampa, load_mapping_from_path, normalize
from g2p.transducer import Transducer

PRINTER = pprint.PrettyPrinter(indent=4)


def create_app():
    return APP


CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


@click.version_option(version=VERSION, prog_name="g2p")
@click.group(cls=FlaskGroup, create_app=create_app, context_settings=CONTEXT_SETTINGS)
def cli():
    """Management script for G2P"""


@click.option(
    "--out-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help='Output results in DIRECTORY instead of the global "generated" directory.',
)
@click.option(
    "--list-dummy", default=False, is_flag=True, help="List the dummy phone inventory."
)
@click.option(
    "--dummy/--no-dummy",
    default=False,
    help="Generate dummy fallback mapping to minimalist phone inventory.",
)
@click.option(
    "--ipa/--no-ipa", default=False, help="Generate mapping from LANG-ipa to eng-ipa."
)
@click.option(
    "--merge/--no-merge",
    default=False,
    help="Merge multiple mappings together, in which case IN_LANG is a colon-seperated list and OUT_LANG is required.",
)
@click.argument(
    "out_lang",
    required=False,
    default=None,
    type=str,
)
@click.argument(
    "in_lang",
    type=str,
)
@cli.command(
    context_settings=CONTEXT_SETTINGS,
    short_help="Generate English IPA or dummy mapping.",
)
def generate_mapping(in_lang, out_lang, dummy, ipa, list_dummy, out_dir, merge):
    """ For specified IN_LANG, generate a mapping from IN_LANG-ipa to eng-ipa,
        or from IN_LANG-ipa to a dummy minimalist phone inventory.
        This assumes the mapping IN_LANG -> IN_LANG-ipa exists and creates a mapping
        from the its output inventory.

        To generate a mapping from IN_LANG-ipa to eng-ipa from a mapping following a
        different patterns, e.g., from crl-equiv -> crl-ipa, specify both IN_LANG
        (crl-equiv in this example) and OUT_LANG (crl-ipa in this example).

        If you just modified or created the IN_LANG to IN_LANG-ipa/OUT_LANG mapping,
        don't forget to call "g2p update" first so "g2p generate-mapping" sees the
        latest version.

        Call "g2p update" again after calling "g2p generate-mapping" to make the new
        IN_LANG-ipa/OUT_LANG to eng-ipa mapping available.

        Note: at least one of --ipa, --dummy or --list-dummy is required.

        You can list available mappings with "g2p doctor --list-ipa", or by visiting
        http://g2p-studio.herokuapp.com/api/v1/langs .

        \b
        Sample usage:
            Generate Algonquin IPA to English IPA from alq -> alq-ipa
                g2p generate-mapping --ipa alq
            Generate Mohawk IPA to English IPA from moh-equiv -> moh-ipa
                g2p generate-mapping --ipa moh-equiv moh-ipa
            Generate Michif IPA to English IPA from the union of crg-dv ->
            crg-ipa and crg-tmd -> crg-ipa
                g2p generate-mapping --ipa --merge crg-dv:crg-tmd crg-ipa
    """

    if merge:
        if out_lang is None:
            raise click.BadParameter("OUT_LANG is required with --merge.")
        in_langs = in_lang.split(":")
    else:
        in_langs = [in_lang]

    in_lang_choices = [x for x in LANGS_NETWORK.nodes if not is_ipa(x) and not is_xsampa(x)]
    for l in in_langs:
        if l not in in_lang_choices:
            raise click.BadParameter(
                f'Invalid value for IN_LANG: "{l}".\n'
                "IN_LANG must be a non-IPA language code with an existing IPA mapping, "
                f"i.e., one of:\n{', '.join(in_lang_choices)}."
            )

    out_lang_choices = [x for x in LANGS_NETWORK.nodes if is_ipa(x)]
    if out_lang is None:
        out_lang = f"{in_lang}-ipa"
    elif out_lang not in out_lang_choices:
        raise click.BadParameter(
            f'Invalid value for OUT_LANG: "{out_lang}".\n'
            "OUT_LANG must be an IPA language code with an existing mapping from IN_LANG, "
            f"i.e., one of:\n{', '.join(out_lang_choices)}"
        )

    if not ipa and not dummy and not list_dummy:
        raise click.BadParameter(
            "Nothing to do! Please specify at least one of --ipa, --dummy or --list-dummy."
        )

    if ipa and dummy:
        raise click.BadParameter(
            "Cannot do both --ipa and --dummy at the same time, please choose one or the other."
        )

    if out_dir and not os.path.isdir(out_dir):
        raise click.BadParameter(
            f'Output directory "{out_dir}" does not exist. Cannot write mapping.'
        )

    if list_dummy:
        print("Dummy phone inventory: {}".format(DUMMY_INVENTORY))

    if ipa or dummy:
        source_mappings = []
        for l in in_langs:
            try:
                source_mapping = Mapping(in_lang=l, out_lang=out_lang)
            except MappingMissing as e:
                raise click.BadParameter(f'Cannot find IPA mapping for "{l}": {e}')
            source_mappings.append(source_mapping)

        if ipa:
            check_ipa_known_segs([f"{in_lang}-ipa"])
            eng_ipa = Mapping(in_lang="eng-ipa", out_lang="eng-arpabet")
            click.echo(f"Writing English IPA mapping for {out_lang} to file")
            new_mapping = create_mapping(source_mappings[0], eng_ipa)
            for m in source_mappings[1:]:
                new_mapping.extend(create_mapping(m, eng_ipa))
        else:  # dummy
            click.echo(f"Writing dummy fallback mapping for {out_lang} to file")
            new_mapping = align_to_dummy_fallback(source_mappings[0])
            for m in source_mappings[1:]:
                new_mapping.extend(align_to_dummy_fallback(m))

        new_mapping.deduplicate()

        if out_dir:
            new_mapping.config_to_file(out_dir)
            new_mapping.mapping_to_file(out_dir)
        else:
            new_mapping.config_to_file()
            new_mapping.mapping_to_file()


@click.argument("path", type=click.Path(exists=True, file_okay=False, dir_okay=True))
@cli.command(context_settings=CONTEXT_SETTINGS)
def generate_mapping_network(path):
    """ Generate a png of the network of mapping languages. Requires matplotlib.
    """
    import matplotlib.pyplot as plt

    draw(LANGS_NETWORK, with_labels=True)
    plt.show()


@click.option(
    "--pretty-edges",
    "-e",
    default=False,
    is_flag=True,
    help="Show the traduction graph in a pretty, plain-text format.",
)
@click.option(
    "--debugger/--no-debugger",
    "-d",
    default=False,
    is_flag=True,
    help="Show all the conversion steps applied.",
)
@click.option(
    "--check/--no-check",
    "-c",
    default=False,
    is_flag=True,
    help="Check IPA outputs against panphon and/or eng-arpabet output against ARPABET",
)
@click.option(
    "--tok-lang", default=None, help="Override the tokenizing language. Implies --tok.",
)
@click.option(
    "--tok/--no-tok",
    "-t",
    default=None,  # three-way var: None=not set, True/False=set to True/False
    is_flag=True,
    help="Tokenize INPUT_TEXT before converting.",
)
@click.option(
    "--path",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    help="Read text to convert from FILE.",
)
@click.option(
    "--config",
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    help="A path to a mapping configuration file to use",
)
@click.argument("out_lang")
@click.argument("in_lang")
@click.argument("input_text", type=click.STRING)
@cli.command(
    context_settings=CONTEXT_SETTINGS,
    short_help="Convert text through a g2p mapping path.",
)
def convert(
    in_lang,
    out_lang,
    input_text,
    path,
    tok,
    check,
    debugger,
    pretty_edges,
    tok_lang,
    config,
):
    """Convert INPUT_TEXT through g2p mapping(s) from IN_LANG to OUT_LANG.

       Visit http://g2p-studio.herokuapp.com/api/v1/langs for a list of languages.

       There must be a path from IN_LANG to OUT_LANG, possibly via some intermediates.
       For example, mapping from fra to eng-arpabet will successively apply
       fra->fra-ipa, fra-ipa->eng-ipa and eng-ipa->eng-arpabet.
    """
    # Check valid input
    # Check input != output
    if in_lang == out_lang:
        raise click.UsageError("Values must be different for 'IN_LANG' and 'OUT_LANG'")
    if config:
        # This isn't that DRY - copied from g2p/mappings/langs/__init__.py
        mappings_legal_pairs = []
        with open(config, encoding="utf8") as f:
            data = yaml.safe_load(f)
        if "mappings" in data:
            for index, mapping in enumerate(data["mappings"]):
                mappings_legal_pairs.append(
                    (
                        data["mappings"][index]["in_lang"],
                        data["mappings"][index]["out_lang"],
                    )
                )
                data["mappings"][index] = load_mapping_from_path(config, index)
        else:
            mapping = load_mapping_from_path(config)
            data["mappings"] = [mapping]
            mappings_legal_pairs.append((mapping["in_lang"], mapping["out_lang"]))
        for pair in mappings_legal_pairs:
            if pair[0] in LANGS_NETWORK.nodes:
                LOGGER.warn(
                    f"A mapping with the name '{pair[0]}' is already defined in g2p. Your local mapping with the same name might not function properly."
                )
        LANGS_NETWORK.add_edges_from(mappings_legal_pairs)
        MAPPINGS_AVAILABLE.extend(data["mappings"])
    # Check input lang exists
    if in_lang not in LANGS_NETWORK.nodes:
        raise click.UsageError(f"'{in_lang}' is not a valid value for 'IN_LANG'")
    # Check output lang exists
    if out_lang not in LANGS_NETWORK.nodes:
        raise click.UsageError(f"'{out_lang}' is not a valid value for 'OUT_LANG'")
    # Check if path exists
    if not has_path(LANGS_NETWORK, in_lang, out_lang):
        raise click.UsageError(
            f"Path between '{in_lang}' and '{out_lang}' does not exist"
        )
    if os.path.exists(input_text) and input_text.endswith("txt"):
        with open(input_text, encoding="utf8") as f:
            input_text = f.read()
    # Determine which tokenizer to use, if any
    if tok is not None and not tok and tok_lang is not None:
        raise click.UsageError("Specified conflicting --no-tok and --tok-lang options.")
    if tok and tok_lang is None:
        tok_lang = "path"
    # Transduce!!!
    if in_lang and out_lang:
        transducer = make_g2p(in_lang, out_lang, tok_lang=tok_lang)
    elif path:
        transducer = Transducer(Mapping(path))
    tg = transducer(input_text)
    if check:
        transducer.check(tg, display_warnings=True)
    outputs = [tg.output_string]
    if pretty_edges:
        outputs += [tg.pretty_edges()]
    if debugger:
        outputs += [tg.edges, tg.debugger]
    if len(outputs) > 1:
        click.echo(pprint.pformat(outputs, indent=4))
    else:
        click.echo(tg.output_string)


# Note: with -m eng-ipa, we actually check all the mappings from lang-ipa to eng-ipa.
@click.option(
    "--list-all", is_flag=True, help="List all mappings that can be specified"
)
@click.option(
    "--list-ipa", is_flag=True, help="List IPA mappings that can be specified"
)
@click.option(
    "--mapping",
    "-m",
    multiple=True,
    help="Check specified IPA mapping(s) (default: check all IPA mappings).",
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
        LOGGER.info(
            "Specifying an output language will check all mappings into that language:\n"
        )
        for m in out_langs:
            print(f"{m}: ", end="")
            print(
                ("\n" + " " * len(m) + "  ").join(
                    sorted(
                        [x["in_lang"] for x in MAPPINGS_AVAILABLE if x["out_lang"] == m]
                    )
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
    """ Update cached language files
    """
    cache_langs()
    update_docs()
    network_to_echart(write_to_file=True)


@click.argument("path", type=click.Path(exists=True, file_okay=True, dir_okay=False))
@click.argument("lang")
@cli.command(
    context_settings=CONTEXT_SETTINGS,
    short_help="Scan a document for non target language characters.",
)
def scan(lang, path):
    """ Returns the set of non-mapped characters in a document.
        Accounts for case sensitivity in the configuration.
    """
    # Check input lang exists
    if not lang in LANGS_NETWORK.nodes:
        raise click.UsageError(f"'{lang}' is not a valid value for 'LANG'")

    # Retrieve the mappings for lang
    case_sensitive = True
    mappings = []
    for mapping in MAPPINGS_AVAILABLE:
        mapping_name = mapping["in_lang"]
        # Exclude mappings for converting between IPAs
        if mapping_name.startswith(lang) and "ipa" not in mapping_name:
            case_sensitive = case_sensitive and mapping.get("case_sensitive", True)
            mappings.append(mapping)

    # Get input chars in mapping
    mapped_chars = set()
    for lang_mapping in mappings:
        for x in lang_mapping["mapping_data"]:
            mapped_chars.add(normalize(x["in"], "NFD"))
    # Find unmapped chars
    filter_chars = " \n"
    mapped_string = "".join(mapped_chars)
    pattern = "[^" + mapped_string + filter_chars + ".]"
    prog = re.compile(pattern)

    with open(path, "r", encoding="utf8") as file:
        data = normalize(file.read(), "NFD")
        if not case_sensitive:
            data = data.lower()
        unmapped = set(prog.findall(data))
        if unmapped:
            LOGGER.warning("The following characters are not mapped:")
            print(unmapped)
