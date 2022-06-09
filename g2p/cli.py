import json
import os
import pprint
import re
import sys

import click
import yaml
from flask.cli import FlaskGroup
from networkx import draw, has_path

from g2p import make_g2p
from g2p._version import VERSION
from g2p.api import update_docs
from g2p.app import APP, network_to_echart
from g2p.exceptions import InvalidLanguageCode, MappingMissing, NoPath
from g2p.log import LOGGER
from g2p.mappings import Mapping
from g2p.mappings.create_fallback_mapping import (
    DUMMY_INVENTORY,
    align_to_dummy_fallback,
)
from g2p.mappings.create_ipa_mapping import (
    DISTANCE_METRICS,
    create_mapping,
    create_multi_mapping,
)
from g2p.mappings.langs import LANGS_NETWORK, MAPPINGS_AVAILABLE, cache_langs
from g2p.mappings.langs.utils import check_ipa_known_segs
from g2p.mappings.utils import is_ipa, is_xsampa, load_mapping_from_path, normalize
from g2p.transducer import Transducer

PRINTER = pprint.PrettyPrinter(indent=4)


def create_app():
    """Return the flask app for g2p"""
    return APP


CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


def parse_from_or_to_lang_spec(lang_spec):
    """Parse a value given to g2p generate-mapping --from or --to.

    See the documentation of generate_mapping() for the syntax of lang_spec.

    Returns list[tuple[Mapping, io (str)]]:
        the mapping(s) lang_spec refers to, and "in" or "out", to indicate if the
        relevant inventory is the mapping's in_lang or out_lang.

    Raises:
        click.BadParameter if lang_spec is not valid
    """
    mapping_spec, _, in_or_out = lang_spec.partition("[")
    in_or_out.rstrip("]")
    in_lang, _, out_lang = mapping_spec.partition("_to_")

    if out_lang:
        try:
            mapping = Mapping(in_lang=in_lang, out_lang=out_lang)
        except MappingMissing as e:
            raise click.BadParameter(
                f'Cannot find mapping {in_lang}->{out_lang} for --from or --to spec "{lang_spec}": {e}'
            )
        if not in_or_out:
            if is_ipa(out_lang):
                in_or_out = "out"
            elif is_ipa(in_lang):
                in_or_out = "in"
            else:
                raise click.BadParameter(
                    f'Cannot guess in/out for IPA lang spec "{lang_spec}" because neither {in_lang} '
                    f'nor {out_lang} is IPA. Specify "[in]" or "[out]" if you are sure it is correct.'
                )
        if in_or_out not in ("in", "out"):
            raise click.BadParameter(
                f'Invalid IPA language specification "{lang_spec}": only "in" or "out" '
                "is allowed in square brackets, to disambiguate between input or output "
                "inventory when necessary."
            )
        return [(mapping, in_or_out)]

    else:
        if in_or_out:
            raise click.BadParameter(
                f'Bad IPA lang spec "{lang_spec}": the [in]/[out] qualifier is only '
                "supported with the full in-lang_to_out-lang[[in]|[out]] syntax."
            )
        if in_lang == "eng":
            mapping = Mapping(in_lang="eng-ipa", out_lang="eng-arpabet")
            in_or_out = "in"
            return [(mapping, in_or_out)]
        else:
            out_lang = in_lang + "-ipa"
            # check_ipa_known_segs([out_lang])  # this outputs a lot of spurious noise...
            mappings = [
                (Mapping(in_lang=m["in_lang"], out_lang=m["out_lang"]), "out")
                for m in MAPPINGS_AVAILABLE
                if m["out_lang"] == out_lang and not is_ipa(m["in_lang"])
            ]
            if not mappings:
                raise click.BadParameter(f'No IPA mappings found for "{lang_spec}".')
            return mappings


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
    "--to",
    "to_langs",
    default=None,
    help='Colon- or comma-separated list of "to" languages in from/to mode',
)
@click.option(
    "--from",
    "from_langs",
    default=None,
    help='Colon- or comma-separated list of "from" languages in from/to mode',
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
@click.argument("out_lang", required=False, default=None, type=str)
@click.argument("in_lang", required=False, default=None, type=str)
@cli.command(
    context_settings=CONTEXT_SETTINGS,
    short_help="Generate English IPA or dummy mapping.",
)
@click.option(
    "--distance",
    type=click.Choice(DISTANCE_METRICS),
    required=False,
    default="weighted_feature_edit_distance",
)
def generate_mapping(
    in_lang,
    out_lang,
    dummy,
    ipa,
    list_dummy,
    out_dir,
    merge,
    from_langs,
    to_langs,
    distance,
):
    """Generate a new mapping from existing mappings in the g2p system.

    This command has different modes of operation.

    Standard mode:

      g2p generate-mapping [--dummy|--ipa] IN_LANG [OUT_LANG]

      For specified IN_LANG, generate a mapping from IN_LANG-ipa to eng-ipa,
      or from IN_LANG-ipa to a dummy minimalist phone inventory. This assumes
      the mapping IN_LANG -> IN_LANG-ipa exists and creates a mapping from its
      output inventory.

      To generate a mapping from IN_LANG-ipa to eng-ipa from a mapping
      following a different patterns, e.g., from crl-equiv -> crl-ipa, specify
      both IN_LANG (crl-equiv in this example) and OUT_LANG (crl-ipa in this
      example).

      \b
      Sample usage:
        Generate Algonquin IPA to English IPA from alq -> alq-ipa:
            g2p generate-mapping --ipa alq
        Generate Mohawk IPA to English IPA from moh-equiv -> moh-ipa:
            g2p generate-mapping --ipa moh-equiv moh-ipa
        Generate Michif IPA to English IPA from the union of crg-dv -> crg-ipa
        and crg-tmd -> crg-ipa:
            g2p generate-mapping --ipa --merge crg-dv:crg-tmd crg-ipa

    List the dummy inventory used by --dummy:

      g2p generate-mapping --list-dummy

    From/to IPA mode:

    \b
      g2p generate-mapping --from FROM_L1 --to TO_L1
      g2p generate-mapping --from FROM_L1:FROM_L2:... --to TO_L1:TO_L2:...

      Generate an IPA mapping from the union of FROM_L1-ipa, FROM-L2-ipa, etc to
      the union of TO_L1-ipa, TO-L2-ipa, etc. One or more from/to language
      code(s) can be specified in colon- or comma-separated lists. Note, by default
      we use Panphon's weighted_feature_edit_distance, but you can change this with
      the --distance argument

    \b
      Sample usage:
        Generate a mapping from kwk-ipa to moh-ipa based on all mappings into
        kwk-ipa and moh-ipa:
            g2p generate-mapping --from kwk --to moh
        Generate a mapping from eng-ipa to crg-ipa based only on crg-dv -> crg-ipa:
            g2p generate-mapping --from eng --to crg-dv_to_crg-ipa
        Generate a mapping from kwk-ipa to moh-ipa+crg-ipa+eng-ipa based on
        all mappings into kwk-ipa (from side) and the union of all mappings
        into moh-ipa and crg-ipa plus eng-ipa_to_eng-arpabet (to side):
            g2p generate-mapping --from kwk --to moh:crg:eng

      Full syntax for specifying FROM_Ln and TO_Ln:

      \b
        lang (i.e., 3-letter code):
         - If there is only one mapping into lang-ipa, "lang" refers to the
           output of that mapping, e.g., "fra" means "fra_to_fra-ipa[out]".
         - If there are several mappings into lang-ipa, "lang" refers to the
           union of the outputs of those mappings, e.g., "moh" means the union
           of "moh-equiv_to_moh-ipa[out]" and "moh-festival_to_moh-ipa[out]".
         - It is an error if there are no mappings into lang-ipa.
         - Only mappings from non-IPA to IPA are considered (i.e., IPA-to-IPA
           mappings created by this command will not be included: use the
           longer syntax below if you want to use them).
         - Special case: "eng" refers to "eng-ipa_to_eng-arpabet[in]".

      \b
        in-lang_to_out-lang[[in]|[out]]:
         - This expanded syntax is used to avoid the union when it is not
           desired, e.g., "moh-equiv_to_moh-ipa" refers only to
           "moh-equiv_to_moh-ipa,out" rather than the union "moh" represents.
         - If out-lang is IPA, the output inventory is used; else if in-lang
           is IPA, the input inventory is used; it is an error if neither
           language is IPA.
         - Specify "[in]" or "[out]" to override the above default.
         - "_to_" is the joiner used to specify "the mapping from 'in-lang' to
           'out-lang'" in the g2p network, regardless of the name of the file
           it is stored in.

    If you just modified or created the mappings from which the new mapping is
    to be generated, don't forget to call "g2p update" first, so that "g2p
    generate-mapping" can see the latest version.

    Call "g2p update" again after calling "g2p generate-mapping" to compile
    the newly generated mapping and make it available.

    Note: exactly one of --ipa, --dummy, --from/--to, or --list-dummy is
    required.

    You can list available mappings with "g2p doctor --list-ipa", or by
    visiting http://g2p-studio.herokuapp.com/api/v1/langs .
    """

    # Make sure only one mode was specified on the command line
    mode_count = (
        (1 if ipa else 0)
        + (1 if dummy else 0)
        + (1 if list_dummy else 0)
        + (1 if (from_langs or to_langs) else 0)
    )
    if mode_count == 0:
        raise click.UsageError(
            "Nothing to do! Please specify at least one of --ipa, --dummy, "
            "--list-dummy, or --from/--to."
        )
    if mode_count > 1:
        raise click.UsageError(
            "Multiple modes selected. Choose only one of --ipa, --dummy, "
            "--list-dummy, or --from/--to."
        )

    if list_dummy or from_langs is not None or to_langs is not None:
        if in_lang is not None:
            raise click.UsageError(
                "IN_LANG is not allowed with --list-dummy or --from/--too",
            )

    if from_langs is not None or to_langs is not None:
        if from_langs is None or to_langs is None:
            raise click.UsageError("--from and --to must be used together")

    if merge:
        if not ipa and not dummy:
            raise click.UsageError("--merge is only compatible with --ipa and --dummy.")
        if out_lang is None:
            raise click.UsageError("OUT_LANG is required with --merge.")

    if out_dir and not os.path.isdir(out_dir):
        raise click.BadParameter(
            f'Output directory "{out_dir}" does not exist. Cannot write mapping.',
            param_hint="--out-dir",
        )

    if list_dummy:
        # --list-dummy mode
        print("Dummy phone inventory: {}".format(DUMMY_INVENTORY))

    elif ipa or dummy:
        # --ipa and --dummy modes
        if in_lang is None:
            raise click.UsageError("Missing argument 'IN_LANG'.")
        if merge:
            in_langs = in_lang.split(":")
        else:
            in_langs = [in_lang]

        in_lang_choices = [
            x for x in LANGS_NETWORK.nodes if not is_ipa(x) and not is_xsampa(x)
        ]
        for l in in_langs:
            if l not in in_lang_choices:
                raise click.UsageError(
                    f'Invalid value for IN_LANG: "{l}".\n'
                    "IN_LANG must be a non-IPA language code with an existing IPA mapping, "
                    f"i.e., one of:\n{', '.join(in_lang_choices)}."
                )

        out_lang_choices = [x for x in LANGS_NETWORK.nodes if is_ipa(x)]
        if out_lang is None:
            out_lang = f"{in_lang}-ipa"
        elif out_lang not in out_lang_choices:
            raise click.UsageError(
                f'Invalid value for OUT_LANG: "{out_lang}".\n'
                "OUT_LANG must be an IPA language code with an existing mapping from IN_LANG, "
                f"i.e., one of:\n{', '.join(out_lang_choices)}"
            )

        source_mappings = []
        for l in in_langs:
            try:
                source_mapping = Mapping(in_lang=l, out_lang=out_lang)
            except MappingMissing as e:
                raise click.BadParameter(
                    f'Cannot find IPA mapping from "{l}" to "{out_lang}": {e}',
                    param_hint=["IN_LANG", "OUT_LANG"],
                )
            source_mappings.append(source_mapping)

        if ipa:
            check_ipa_known_segs([f"{in_lang}-ipa"])
            eng_ipa = Mapping(in_lang="eng-ipa", out_lang="eng-arpabet")
            click.echo(f"Writing English IPA mapping for {out_lang} to file")
            new_mapping = create_mapping(source_mappings[0], eng_ipa, distance=distance)
            for m in source_mappings[1:]:
                new_mapping.extend(create_mapping(m, eng_ipa, distance=distance))
        else:  # dummy
            click.echo(f"Writing dummy fallback mapping for {out_lang} to file")
            new_mapping = align_to_dummy_fallback(source_mappings[0], distance=distance)
            for m in source_mappings[1:]:
                new_mapping.extend(align_to_dummy_fallback(m, distance=distance))

        new_mapping.deduplicate()

        if out_dir:
            new_mapping.config_to_file(out_dir)
            new_mapping.mapping_to_file(out_dir)
        else:
            new_mapping.config_to_file()
            new_mapping.mapping_to_file()

    elif from_langs is not None:
        # --from/--to mode
        assert to_langs is not None

        from_mappings = []
        for from_lang in re.split(r"[:,]", from_langs):
            from_mappings.extend(parse_from_or_to_lang_spec(from_lang))
        to_mappings = []
        for to_lang in re.split(r"[:,]", to_langs):
            to_mappings.extend(parse_from_or_to_lang_spec(to_lang))

        if not from_mappings:
            raise click.UsageError(
                f'Invalid --from value "{from_langs}": no mappings found.'
            )
        if not to_mappings:
            raise click.UsageError(
                f'Invalid --to value "{to_langs}": no mappings found.'
            )

        for from_mapping, in_or_out in from_mappings:
            LOGGER.info(
                f'From mapping: {from_mapping.kwargs["in_lang"]}_to_{from_mapping.kwargs["out_lang"]}[{in_or_out}]'
            )
        for to_mapping, in_or_out in to_mappings:
            LOGGER.info(
                f'To mapping: {to_mapping.kwargs["in_lang"]}_to_{to_mapping.kwargs["out_lang"]}[{in_or_out}]'
            )

        new_mapping = create_multi_mapping(
            from_mappings, to_mappings, distance=distance
        )

        if out_dir:
            new_mapping.config_to_file(out_dir)
            new_mapping.mapping_to_file(out_dir)
        else:
            new_mapping.config_to_file()
            new_mapping.mapping_to_file()


# TODO the path argument is ignored. What was it supposed to do? Code it...
@click.argument("path", type=click.Path(exists=True, file_okay=False, dir_okay=True))
@cli.command(context_settings=CONTEXT_SETTINGS)
def generate_mapping_network(path):
    """Generate a png of the network of mapping languages. Requires matplotlib."""
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
    "--tok-lang",
    default=None,
    help="Override the tokenizing language. Implies --tok.",
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
                LOGGER.warning(
                    f"A mapping with the name '{pair[0]}' is already defined in g2p. "
                    "Your local mapping with the same name might not function properly."
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
    """Check for common errors in mappings.

    There should eventually be more checks here, but doctor currently checks for:

    1. Characters that are in IPA mappings but are not recognized by panphon library.

    You can list available mappings with --list-all or --list-ipa, or by visiting
    http://g2p-studio.herokuapp.com/api/v1/langs .
    """
    if list_all or list_ipa:
        out_langs = sorted({x["out_lang"] for x in MAPPINGS_AVAILABLE})
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
                        x["in_lang"] for x in MAPPINGS_AVAILABLE if x["out_lang"] == m
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
    """Update cached language files."""
    cache_langs()
    update_docs()
    network_to_echart(write_to_file=True)


@click.argument("path", type=click.Path(exists=True, file_okay=True, dir_okay=False))
@click.argument("lang")
@cli.command(
    context_settings=CONTEXT_SETTINGS,
    short_help="Scan a document for unknown characters.",
)
def scan(lang, path):
    """Scan a document for non target language characters.

    Displays the set of un-mapped characters in a document.
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


@click.option(
    "-a",
    "--all",
    "all_mappings",
    is_flag=True,
    help="Display all mappings in the database",
)
@click.argument("lang2", required=False, default=None)
@click.argument("lang1", required=False, default=None)
@cli.command(context_settings=CONTEXT_SETTINGS, short_help="Show cached mappings.")
def show_mappings(all_mappings, lang1, lang2):
    """Show cached mappings, as last updated by "g2p update".

    Mappings on the path from LANG1 to LANG2 are displayed.
    If only LANG1 is used, all mappings to or from LANG1 are displayed.
    With --all, all mappings in the database are displayed.
    """

    if all_mappings:
        mappings = (
            Mapping(in_lang=m["in_lang"], out_lang=m["out_lang"])
            for m in MAPPINGS_AVAILABLE
        )

    elif lang1 is not None and lang2 is not None:
        try:
            transducer = make_g2p(lang1, lang2)
        except (NoPath, InvalidLanguageCode) as e:
            raise click.UsageError(
                f'Cannot find mapping from "{lang1}" to "{lang2}": {e}'
            ) from e

        if isinstance(transducer, Transducer):
            mappings = [transducer.mapping]
        else:
            mappings = (t.mapping for t in transducer._transducers)

    elif lang1 is not None:
        mappings = [
            Mapping(in_lang=m["in_lang"], out_lang=m["out_lang"])
            for m in MAPPINGS_AVAILABLE
            if m["in_lang"] == lang1 or m["out_lang"] == lang1
        ]
        if not mappings:
            raise click.BadParameter(
                f'No mapping found to or from "{lang1}".', param_hint="lang1"
            )

    else:
        raise click.UsageError("Nothing to do!")

    for m in mappings:
        json.dump(m.kwargs, sys.stdout, indent=4, ensure_ascii=False)
        print()
        m.mapping_to_stream(sys.stdout)
        print()
        print()
