"""

Module for all things related to lookup tables

"""

import csv
import json
import os
import re
from copy import deepcopy
from pathlib import Path
from typing import Dict, List, Pattern, Union

import yaml
from pydantic import BaseModel

from g2p import exceptions
from g2p.log import LOGGER
from g2p.mappings.langs import _LANGS, _MAPPINGS_AVAILABLE
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
    normalize,
)

GEN_DIR = os.path.join(os.path.dirname(LANGS_FILE), "generated")


class Mapping(_MappingModelDefinition):
    """Class for lookup tables"""

    @staticmethod
    def find_mapping(
        in_lang: Union[None, str] = None, out_lang: Union[None, str] = None
    ) -> "Mapping":
        """Given an input and an output language, find a mapping to get between them."""
        if in_lang is None or out_lang is None:
            raise exceptions.MappingMissing(in_lang, out_lang)
        for mapping in MAPPINGS_AVAILABLE:
            if mapping.in_lang == in_lang and mapping.out_lang == out_lang:
                if mapping.type == "lexicon":
                    # do *not* deep copy this, because alignments are big!
                    return mapping.model_copy()
                else:
                    return deepcopy(mapping)
        raise exceptions.MappingMissing(in_lang, out_lang)

    @staticmethod
    def find_mapping_by_id(map_id: str) -> "Mapping":
        """Find the mapping with a given ID, i.e., the "id" found in the mapping, like in the "panphon_preprocessor" mapping."""
        for mapping in MAPPINGS_AVAILABLE:
            if mapping.id == map_id:
                return deepcopy(mapping)
        raise exceptions.MappingMissing(map_id, None)

    @staticmethod
    def load_mapping_from_path(path_to_mapping_config: Union[str, Path], index=0):
        """Loads a mapping from a path, if there is more than one mapping, then it loads based on the int
        provided to the 'index' argument. Default is 0.
        """
        mapping_config = MappingConfig.load_mapping_config_from_path(
            path_to_mapping_config
        )
        return mapping_config.mappings[index]

    def model_post_init(self, *args, **kwargs) -> None:
        """After the model is constructed, we process the model specs by applying all the configuration to the rules (ie prevent feeding, unicode normalization etc..)"""
        if self.type == MAPPING_TYPE.mapping or self.type is None:
            # This is required so that we don't keep escaping special characters for example
            self.rules = self.process_model_specs()
        else:
            self.rules = []

    def __len__(self):
        return len(self.rules)

    def __call__(self):
        return self.rules

    def __iter__(self):
        return iter(self.rules)

    def __getitem__(self, item):
        if isinstance(item, int):  # item is an integer
            return self.rules[item]
        if isinstance(item, slice):  # item is a slice
            return self.rules[item.start or 0 : item.stop or len(self.rules)]
        else:  # invalid index type
            raise TypeError(
                "{cls} indices must be integers or slices, not {idx}".format(
                    cls=type(self).__name__,
                    idx=type(item).__name__,
                )
            )

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
        return self.rules.index(item)

    def inventory(self, in_or_out: str = "in"):
        """Return just inputs or outputs as inventory of mapping"""
        if in_or_out == "in":
            in_or_out = "rule_input"
        if in_or_out == "out":
            in_or_out = "rule_output"
        try:
            return [getattr(x, in_or_out) for x in self.rules]
        except TypeError as e:
            raise exceptions.MappingNotInitializedProperlyError from e

    def plain_mapping(self, skip_none: bool = False, skip_defaults: bool = False):
        """Return the plain mapping for displaying or saving to disk.

        Args:
            skip_empty_contexts: when set, filter out empty context_before/after
        """
        assert isinstance(self.rules, list)
        if self.rules:
            assert isinstance(self.rules[0], Rule)
        return [rule.export_to_dict() for rule in self.rules]

    def process_model_specs(self):  # noqa: C901
        """Process all model specifications"""
        if self.as_is is not None:
            appropriate_setting = (
                RULE_ORDERING_ENUM.as_written
                if self.as_is
                else RULE_ORDERING_ENUM.apply_longest_first
            )
            self.rule_ordering = appropriate_setting

            LOGGER.warning(
                f"mapping from {self.in_lang} to {self.out_lang} "
                'is using the deprecated parameter "as_is"; '
                f"replace `as_is: {self.as_is}` with `rule_ordering: {appropriate_setting.value}`"
            )

        # Sorting must happen before the calculation of PUA intermediate forms for proper indexing
        if self.rule_ordering == RULE_ORDERING_ENUM.apply_longest_first:
            self.rules = sorted(
                # Temporarily normalize to NFD for heuristic sorting of NFC-defined rules
                self.rules,
                key=lambda x: len(normalize(x.rule_input, "NFD"))
                if isinstance(x, Rule)
                else len(normalize(x["in"], "NFD")),
                reverse=True,
            )

        non_empty_mappings: List[Rule] = []
        for i, rule in enumerate(self.rules):
            if isinstance(rule, dict):
                rule = Rule(**rule)
            # Expand Abbreviations
            if (
                self.abbreviations
                and self.rules
                and "match_pattern" not in self.rules[0]
            ):
                for key in [
                    "rule_input",
                    "context_before",
                    "context_after",
                ]:
                    setattr(
                        rule,
                        key,
                        expand_abbreviations(getattr(rule, key), self.abbreviations),
                    )
            # Reverse Rule
            if self.reverse:
                rule.rule_input, rule.rule_output = rule.rule_output, rule.rule_input
                rule.context_before = ""
                rule.context_after = ""
            # Escape Special
            if self.escape_special:
                rule = escape_special_characters(rule)
            # Unicode Normalization
            if self.norm_form != NORM_FORM_ENUM.none:
                for k in [
                    "rule_input",
                    "rule_output",
                    "context_before",
                    "context_after",
                ]:
                    value = getattr(rule, k)
                    if value:
                        setattr(
                            rule,
                            k,
                            normalize(value, self.norm_form.value),
                        )
            # Prevent Feeding
            if self.prevent_feeding or rule.prevent_feeding:
                rule.intermediate_form = self._string_to_pua(rule.rule_output, i)
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
        if not rule.rule_input:
            LOGGER.warning(
                f"Rule with input '{rule.rule_input}' and output '{rule.rule_output}' has no input. "
                "This is disallowed. Please check your mapping file for rules with null inputs."
            )
            return None
        input_match = re.sub(re.compile(r"{\d+}"), "", rule.rule_input)
        try:
            inp = create_fixed_width_lookbehind(rule.context_before) + input_match
            if rule.context_after:
                inp += f"(?={rule.context_after})"
            if not self.case_sensitive:
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

    def extend(self, mapping: "Mapping"):
        """Add all the rules from mapping into self, effectively merging two mappings

        Caveat: if self and mapping have contradictory rules, which one will
        "win" is unspecified, and may depend on mapping configuration options.
        """
        try:
            self.rules.extend(mapping.rules)
        except TypeError as e:
            raise exceptions.MappingNotInitializedProperlyError from e

    def deduplicate(self):
        """Remove duplicate rules found in self, keeping the first copy found."""
        # Since Python 3.6, dict keeps its element in insertion order (while
        # set does not), so deduplicating the rules is a one-liner:
        self.rules = list({repr(rule): rule for rule in self.rules}.values())

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
            try:
                for io in self.rules:
                    writer.writerow(io.export_to_dict())
            except TypeError as e:
                raise exceptions.MappingNotInitializedProperlyError from e
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

    def export_to_dict(self, mapping_type="json"):
        model_dict = json.loads(
            self.model_dump_json(exclude_none=True, exclude={"parent_dir": True})
        )
        model_dict["rules"] = f"{self.in_lang}_to_{self.out_lang}.{mapping_type}"
        return model_dict

    def config_to_file(
        self,
        output_path: str = os.path.join(GEN_DIR, "config-g2p.yaml"),
        mapping_type: str = "json",
    ):
        """Write config to file"""
        add_config = False
        if os.path.isdir(output_path):
            output_path = os.path.join(output_path, "config-g2p.yaml")
        if os.path.exists(output_path) and os.path.isfile(output_path):
            LOGGER.warning(f"Adding mapping config to file at {output_path}")
            add_config = True
        else:
            LOGGER.warning(f"writing mapping config to file at {output_path}")
        fn = output_path
        config_template = self.export_to_dict()
        # Serialize piece-by-piece, which is why this is a list of type dict and not type Mapping
        # If config file exists already, just add the mapping.
        to_export = None
        if add_config:
            existing_data = MappingConfig.load_mapping_config_from_path(fn)
            updated = False
            for i, mapping in enumerate(existing_data.mappings):
                # if the mapping exists, just update the generation data
                if (
                    mapping.in_lang == config_template["in_lang"]
                    and mapping.out_lang == config_template["out_lang"]
                ):
                    existing_data.mappings[i].authors = config_template["authors"]
                    updated = True
                    break
            if not updated:
                existing_data.mappings.append(config_template)
            to_export = {
                "mappings": [
                    x.export_to_dict() if isinstance(x, Mapping) else x
                    for x in existing_data.mappings
                ]
            }
        else:
            to_export = {"mappings": [config_template]}
        with open(fn, "w", encoding="utf8", newline="\n") as f:
            yaml.dump(to_export, f, Dumper=IndentDumper, default_flow_style=False)


MAPPINGS_AVAILABLE: List[Mapping] = [
    Mapping(**mapping) for mapping in _MAPPINGS_AVAILABLE
]


class MappingConfig(BaseModel):
    """This is the format used by g2p for configuring mappings."""

    mappings: List[Mapping]

    def export_to_dict(self):
        return {"mappings": [mapping.export_to_dict() for mapping in self.mappings]}

    @staticmethod
    def load_mapping_config_from_path(path_to_mapping_config: Union[str, Path]):
        """Loads a mapping configuration from a path, if you just want one specific mapping
        from the config, you can try Mapping.load_mapping_from_path instead.
        """
        if isinstance(path_to_mapping_config, str):
            path = Path(path_to_mapping_config)
        else:
            path = path_to_mapping_config
        parent_dir = path.parent
        with open(path, encoding="utf8") as f:
            loaded_config = yaml.safe_load(f)
            if "mappings" in loaded_config:
                for mapping in loaded_config["mappings"]:
                    mapping["parent_dir"] = parent_dir
        try:
            return MappingConfig(**loaded_config)
        except TypeError as e:
            raise exceptions.MalformedMapping from e


LANGS: Dict[str, MappingConfig] = {k: MappingConfig(**v) for k, v in _LANGS.items()}
