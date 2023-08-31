"""

Module for all things related to lookup tables

"""

import csv
import json
import os
import re
from copy import deepcopy
from pathlib import Path
from typing import List, Pattern, Union

import yaml

from g2p import exceptions
from g2p.log import LOGGER
from g2p.mappings.langs import MAPPINGS_AVAILABLE
from g2p.mappings.langs import __file__ as LANGS_FILE
from g2p.mappings.utils import (
    MAPPING_TYPE,
    NORM_FORM_ENUM,
    RULE_ORDERING_ENUM,
    CompactJSONMappingEncoder,
    IndentDumper,
    Rule,
    _MappingModelDefinition,
    create_fixed_width_lookbehind,
    escape_special_characters,
    expand_abbreviations,
    find_mapping,
    normalize,
)

GEN_DIR = os.path.join(os.path.dirname(LANGS_FILE), "generated")


class Mapping:
    """Class for lookup tables"""

    def __init__(  # noqa: C901
        self,
        mapping: Union[List[str], List[Rule], Union[Path, str], None] = None,
        **kwargs,
    ):
        self.processed = False
        # Sometimes raw data gets passed instead of a path to a config... ugh
        # This block determines the mapping configuration
        if mapping is not None and (
            isinstance(mapping, list)
            or (
                isinstance(mapping, str)
                and not mapping.endswith("yaml")
                and not mapping.endswith("yml")
            )
        ):
            kwargs["mapping"] = mapping
            self.mapping_config: _MappingModelDefinition = _MappingModelDefinition(
                **kwargs
            )
        elif kwargs.get("in_lang", False) and kwargs.get("out_lang", False):
            loaded_config = find_mapping(
                kwargs.get("in_lang", ""), kwargs.get("out_lang", "")
            )
            if isinstance(loaded_config, _MappingModelDefinition):
                self.mapping_config: _MappingModelDefinition = loaded_config
            else:
                self.mapping_config: _MappingModelDefinition = _MappingModelDefinition(
                    **loaded_config
                )
        elif kwargs.get("id", False):
            loaded_config = self.find_mapping_by_id(kwargs.get("id"))
            if isinstance(loaded_config, _MappingModelDefinition):
                self.mapping_config: _MappingModelDefinition = loaded_config
            else:
                self.mapping_config: _MappingModelDefinition = _MappingModelDefinition(
                    **loaded_config
                )
        elif isinstance(mapping, str) and (
            mapping.endswith("yaml") or mapping.endswith("yml")
        ):
            # This is for if the config.yaml file gets passed
            parent_dir = Path(mapping).parent
            with open(mapping, encoding="utf8") as f:
                loaded_config = yaml.safe_load(f)
            loaded_config["parent_dir"] = parent_dir
            self.mapping_config: _MappingModelDefinition = _MappingModelDefinition(
                **loaded_config
            )
        elif not mapping and kwargs.get("type", False) in [
            MAPPING_TYPE.lexicon.value,
            MAPPING_TYPE.unidecode.value,
        ]:
            self.mapping_config: _MappingModelDefinition = _MappingModelDefinition(
                **kwargs
            )
        else:
            raise Exception(f"Sorry we can't process {mapping}")
        # Process the loaded configuration
        self.process_loaded_config()
        if self.mapping_config.type == MAPPING_TYPE.unidecode:
            self.mapping_config.mapping = []
        elif self.mapping_config.type == MAPPING_TYPE.lexicon:
            self.mapping_config.mapping = []
        self.in_lang = self.mapping_config.in_lang
        self.out_lang = self.mapping_config.out_lang
        if not self.processed:
            self.mapping = self.process_model_specs()

    def __len__(self):
        return len(self.mapping)

    def __call__(self):
        return self.mapping

    def __iter__(self):
        return iter(self.mapping)

    def __getitem__(self, item):
        if isinstance(item, int):  # item is an integer
            return self.mapping[item]
        if isinstance(item, slice):  # item is a slice
            return self.mapping[item.start or 0 : item.stop or len(self.mapping)]
        else:  # invalid index type
            raise TypeError(
                "{cls} indices must be integers or slices, not {idx}".format(
                    cls=type(self).__name__,
                    idx=type(item).__name__,
                )
            )

    @staticmethod
    def find_mapping_by_id(map_id: str):
        """Find the mapping with a given ID"""
        for mapping in MAPPINGS_AVAILABLE:
            if (isinstance(mapping, dict) and mapping.get("id", "") == map_id) or (
                isinstance(mapping, _MappingModelDefinition) and mapping.id == map_id
            ):
                return deepcopy(mapping)

    @staticmethod
    def _string_to_pua(string: str, offset: int) -> str:
        """Given an string of length n, and an offset m,
           produce a string of n * chr(983040 + m).
           This makes use of the Supplementary Private Use Area A Unicode block.

        Args:
            string (str): The string to convert
            offset (int): The offset from the start of the Supplementary Private Use Area

        Returns:
            str: The resulting string
        """
        intermediate_char = chr(983040 + offset)
        return intermediate_char * len(string)

    def index(self, item):
        """Find the location of an item in self"""
        return self.mapping.index(item)

    def inventory(self, in_or_out: str = "in"):
        """Return just inputs or outputs as inventory of mapping"""
        if in_or_out == "in":
            in_or_out = "in_char"
        if in_or_out == "out":
            in_or_out = "out_char"
        return [getattr(x, in_or_out) for x in self.mapping]

    def process_loaded_config(self):
        """For a mapping loaded from a file, take the keyword arguments and supply them to the
        Mapping, and get any abbreviations data.
        """
        if self.mapping_config.type == MAPPING_TYPE.unidecode:
            self.mapping = []
        elif self.mapping_config.type == MAPPING_TYPE.lexicon:
            self.mapping = []
            self.alignments = self.mapping_config.alignments
        else:
            self.mapping = self.mapping_config.mapping
            self.abbreviations = self.mapping_config.abbreviations

    def plain_mapping(self, skip_none: bool = False, skip_defaults: bool = False):
        """Return the plain mapping for displaying or saving to disk.

        Args:
            skip_empty_contexts: when set, filter out empty context_before/after
        """
        assert isinstance(self.mapping, list)
        assert isinstance(self.mapping[0], Rule)
        return [rule.export_to_dict() for rule in self.mapping]

    def process_model_specs(self):  # noqa: C901
        """Process all model specifications"""

        if self.mapping_config.as_is is not None:
            appropriate_setting = (
                RULE_ORDERING_ENUM.as_written
                if self.mapping_config.as_is
                else RULE_ORDERING_ENUM.apply_longest_first
            )
            self.mapping_config.rule_ordering = appropriate_setting

            LOGGER.warning(
                f"mapping from {self.in_lang} to {self.out_lang} "
                'is using the deprecated parameter "as_is"; '
                f"replace `as_is: {self.mapping_config.as_is}` with `rule_ordering: {appropriate_setting.value}`"
            )

        # Sorting must happen before the calculation of PUA intermediate forms for proper indexing
        if self.mapping_config.rule_ordering == RULE_ORDERING_ENUM.apply_longest_first:
            self.mapping_config.mapping = sorted(
                # Temporarily normalize to NFD for heuristic sorting of NFC-defined rules
                self.mapping_config.mapping,
                key=lambda x: len(normalize(x.in_char, "NFD"))
                if isinstance(x, Rule)
                else len(normalize(x["in"], "NFD")),
                reverse=True,
            )

        non_empty_mappings: List[Rule] = []
        for i, rule in enumerate(self.mapping_config.mapping):
            if isinstance(rule, dict):
                rule = Rule(**rule)
            # Expand Abbreviations
            if (
                self.mapping_config.abbreviations
                and self.mapping_config.mapping
                and "match_pattern" not in self.mapping_config.mapping[0]
            ):
                for key in [
                    "in_char",
                    "context_before",
                    "context_after",
                ]:
                    setattr(
                        rule,
                        key,
                        expand_abbreviations(getattr(rule, key), self.abbreviations),
                    )
            # Reverse Rule
            if self.mapping_config.reverse:
                rule.in_char, rule.out_char = rule.out_char, rule.in_char
                rule.context_before = ""
                rule.context_after = ""
            # Escape Special
            if self.mapping_config.escape_special:
                rule = escape_special_characters(rule)
            # Unicode Normalization
            if self.mapping_config.norm_form != NORM_FORM_ENUM.none:
                for k in ["in_char", "out_char", "context_before", "context_after"]:
                    value = getattr(rule, k)
                    if value:
                        setattr(
                            rule,
                            k,
                            normalize(value, self.mapping_config.norm_form.value),
                        )
            # Prevent Feeding
            if self.mapping_config.prevent_feeding or rule.prevent_feeding:
                rule.intermediate_form = self._string_to_pua(rule.out_char, i)
            # Create match pattern
            rule.match_pattern = self.rule_to_regex(rule)
            # Only add non-empty rules
            if rule.match_pattern:
                non_empty_mappings.append(rule)

        self.processed = True
        return non_empty_mappings

    def rule_to_regex(self, rule: Union[Rule, dict]) -> Union[Pattern, None]:
        """Turns an input string (and the context) from an input/output pair
        into a regular expression pattern"

        The 'in' key is the match.
        The 'context_after' key creates a lookahead.
        The 'context_before' key creates a lookbehind.

        Args:
            rule: A dictionary containing 'in', 'out', 'context_before', and 'context_after' keys

        Raises:
            Exception: This is raised when un-supported regex characters or symbols exist in the rule

        Returns:
            Pattern: returns a regex pattern (re.Pattern)
            None: if input is null
        """
        # Prevent null input. See, https://github.com/roedoejet/g2p/issues/24
        if isinstance(rule, dict):
            rule = Rule(**rule)
        if not rule.in_char:
            LOGGER.warning(
                f"Rule with input '{rule.in_char}' and output '{rule.out_char}' has no input. "
                "This is disallowed. Please check your mapping file for rules with null inputs."
            )
            return None
        input_match = re.sub(re.compile(r"{\d+}"), "", rule.in_char)
        try:
            inp = create_fixed_width_lookbehind(rule.context_before) + input_match
            if rule.context_after:
                inp += f"(?={rule.context_after})"
            if not self.mapping_config.case_sensitive:
                rule_regex = re.compile(inp, re.I)
            else:
                rule_regex = re.compile(inp)
        except re.error as e:
            in_lang = self.in_lang
            out_lang = self.out_lang
            LOGGER.error(
                "Your regex in mapping between %s and %s is malformed.  "
                "Do you have un-escaped regex characters in your input %s, contexts %s, %s?  "
                "Error is: %s",
                in_lang,
                out_lang,
                inp,
                rule.context_before,
                rule.context_after,
                e.msg,
            )
            raise exceptions.MalformedMapping(
                f"Your regex in mapping between {in_lang} and {out_lang} is malformed.  "
                f"Do you have un-escaped regex characters in your input {inp}, contexts {rule.context_before}, {rule.context_after}?"
            ) from e
        return rule_regex

    def extend(self, mapping):
        """Add all the rules from mapping into self, effectively merging two mappings

        Caveat: if self and mapping have contradictory rules, which one will
        "win" is unspecified, and may depend on mapping configuration options.
        """
        self.mapping.extend(mapping.mapping)

    def deduplicate(self):
        """Remove duplicate rules found in self, keeping the first copy found."""
        # Since Python 3.6, dict keeps its element in insertion order (while
        # set does not), so deduplicating the rules is a one-liner:
        self.mapping = list({repr(rule): rule for rule in self.mapping}.values())

    def mapping_to_stream(self, out_stream, file_type: str = "json"):
        """Write mapping to a stream"""

        if file_type == "json":
            json.dump(
                self.plain_mapping(skip_none=True, skip_defaults=True),
                out_stream,
                indent=4,
                ensure_ascii=False,
                cls=CompactJSONMappingEncoder,
            )
            print("\n", end="", file=out_stream)
        elif file_type == "csv":
            fieldnames = ["in", "out", "context_before", "context_after"]
            writer = csv.DictWriter(
                out_stream, fieldnames=fieldnames, extrasaction="ignore"
            )
            for io in self.mapping:
                assert isinstance(io, Rule)
                writer.writerow(io.export_to_dict())
        else:
            raise exceptions.IncorrectFileType(f"File type {file_type} is invalid.")

    def mapping_to_file(self, output_path: str = GEN_DIR, file_type: str = "json"):
        """Write mapping to file"""

        if not os.path.isdir(output_path):
            raise Exception(f"Path {output_path} is not a directory")
        fn = os.path.join(
            output_path,
            self.in_lang + "_to_" + self.out_lang + "." + file_type,
        )
        with open(fn, "w", encoding="utf8", newline="\n") as f:
            self.mapping_to_stream(f, file_type)

    def config_to_file(
        self,
        output_path: str = os.path.join(GEN_DIR, "config.yaml"),
        mapping_type: str = "json",
    ):
        """Write config to file"""
        add_config = False
        if os.path.isdir(output_path):
            output_path = os.path.join(output_path, "config.yaml")
        if os.path.exists(output_path) and os.path.isfile(output_path):
            LOGGER.warning(f"Adding mapping config to file at {output_path}")
            add_config = True
        else:
            LOGGER.warning(f"writing mapping config to file at {output_path}")
        fn = output_path
        config_template = json.loads(
            self.mapping_config.json(exclude_none=True, exclude={"parent_dir": True})
        )
        config_template[
            "mapping"
        ] = f"{self.mapping_config.in_lang}_to_{self.mapping_config.out_lang}.{mapping_type}"
        template = {"mappings": [config_template]}
        # If config file exists already, just add the mapping.
        if add_config:
            with open(fn, encoding="utf8") as f:
                existing_data = yaml.safe_load(f.read())
            updated = False
            for i, mapping in enumerate(existing_data["mappings"]):
                # if the mapping exists, just update the generation data
                if (
                    mapping["in_lang"] == template["mappings"][0]["in_lang"]
                    and mapping["out_lang"] == template["mappings"][0]["out_lang"]
                ):
                    existing_data["mappings"][i]["authors"] = template["mappings"][0][
                        "authors"
                    ]
                    updated = True
                    break
            if not updated:
                existing_data["mappings"].append(template["mappings"][0])
            template = existing_data
        with open(fn, "w", encoding="utf8", newline="\n") as f:
            yaml.dump(template, f, Dumper=IndentDumper, default_flow_style=False)
