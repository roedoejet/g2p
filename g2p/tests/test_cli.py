#!/usr/bin/env python3

import os
import re
import shutil
import tempfile
from unittest import TestCase, main

from g2p.app import APP
from g2p.cli import convert, doctor, generate_mapping, scan, show_mappings, update
from g2p.log import LOGGER
from g2p.mappings.langs import load_langs, load_network
from g2p.tests.public.data import DATA_DIR, load_public_test_data


class CliTest(TestCase):
    """Test suite for the g2p Command Line Interface"""

    def setUp(self):
        self.runner = APP.test_cli_runner()

    def test_update(self):
        result = self.runner.invoke(update)
        # Test running in another directory
        with tempfile.TemporaryDirectory() as tmpdir:
            lang1_dir = os.path.join(tmpdir, "lang1")
            os.mkdir(lang1_dir)
            mappings_dir = os.path.join(DATA_DIR, "..", "mappings")
            for name in os.listdir(mappings_dir):
                if name.startswith("minimal."):
                    shutil.copy(
                        os.path.join(mappings_dir, name), os.path.join(lang1_dir, name)
                    )
            shutil.copy(
                os.path.join(mappings_dir, "minimal_configs.yaml"),
                os.path.join(lang1_dir, "config.yaml"),
            )
            result = self.runner.invoke(update, ["-i", tmpdir])
            langs_pkl = os.path.join(tmpdir, "langs.pkl")
            network_pkl = os.path.join(tmpdir, "network.pkl")
            self.assertTrue(os.path.exists(langs_pkl))
            self.assertTrue(os.path.exists(network_pkl))

        # Make sure it produces output
        with tempfile.TemporaryDirectory() as tmpdir:
            result = self.runner.invoke(update, ["-o", tmpdir])
            self.assertEqual(result.exit_code, 0)
            langs_pkl = os.path.join(tmpdir, "langs.pkl")
            network_pkl = os.path.join(tmpdir, "network.pkl")
            self.assertTrue(os.path.exists(langs_pkl))
            self.assertTrue(os.path.exists(network_pkl))
            langs = load_langs(langs_pkl)
            self.assertTrue(langs is not None)
            network = load_network(network_pkl)
            self.assertTrue(network is not None)
            # Corrupt the output and make sure we still can run
            with open(langs_pkl, "wb") as fh:
                fh.write(b"spam spam spam")
            with open(network_pkl, "wb") as fh:
                fh.write(b"eggs bacon spam")
            with self.assertLogs(LOGGER, "WARNING"):
                langs = load_langs(langs_pkl)
            self.assertTrue(langs is not None)
            with self.assertLogs(LOGGER, "WARNING"):
                network = load_network(network_pkl)
            self.assertTrue(network is not None)
        # Make sure it fails meaningfully on invalid input
        with tempfile.TemporaryDirectory() as tmpdir:
            bad_langs_dir = os.path.join(DATA_DIR, "..", "mappings", "bad_langs")
            result = self.runner.invoke(update, ["-i", bad_langs_dir, "-o", tmpdir])
            self.assertNotEqual(result.exit_code, 0)
            self.assertIn("language_name", str(result.exception))
        with tempfile.TemporaryDirectory() as tmpdir:
            bad_langs_dir = os.path.join(DATA_DIR, "..", "mappings", "bad_langs2")
            result = self.runner.invoke(update, ["-i", bad_langs_dir, "-o", tmpdir])
            self.assertNotEqual(result.exit_code, 0)
            self.assertIn("language_name", str(result.exception))
            self.assertIn("min to min", str(result.exception))

    def test_convert(self):
        langs_to_test = load_public_test_data()
        LOGGER.info(
            f"Running {len(langs_to_test)} g2p convert test cases found in public/data"
        )
        error_count = 0
        for tok_option in [["--tok", "--check"], ["--no-tok"]]:
            for test in langs_to_test:
                output_string = self.runner.invoke(
                    convert, [*tok_option, test[2], test[0], test[1]]
                ).stdout.strip()
                if output_string != test[3].strip():
                    LOGGER.warning(
                        f"test_cli.py: {test[0]}->{test[1]} mapping error: '{test[2]}' "
                        f"should map to '{test[3]}', got '{output_string}' (with {tok_option})."
                    )
                    if error_count == 0:
                        first_failed_test = test + [tok_option]
                    error_count += 1

        if error_count > 0:
            reference_string = first_failed_test[3]
            output_string = self.runner.invoke(
                convert,
                [
                    first_failed_test[4],  # tok_option
                    first_failed_test[2],  # word to convert
                    first_failed_test[0],  # in_lang
                    first_failed_test[1],  # out_lang
                ],
            ).stdout.strip()
            self.assertEqual(
                output_string,
                reference_string.strip(),
                f"{first_failed_test[0]}->{first_failed_test[1]} mapping error "
                "for '{first_failed_test[2]}'.\n"
                "Look for warnings in the log for any more mapping errors",
            )

    def test_doctor(self):
        result = self.runner.invoke(doctor, "-m fra")
        self.assertEqual(result.exit_code, 2)

        result = self.runner.invoke(doctor, "-m fra-ipa")
        self.assertEqual(result.exit_code, 0)

        # Disable this test: it's very slow (8s, just by itself) and does not assert
        # anything useful.
        # Migrated to test_doctor_expensive.py so we can still run it, manually or via
        # ./run.py all.
        # result = self.runner.invoke(doctor)
        # self.assertEqual(result.exit_code, 0)
        # self.assertGreaterEqual(len(result.stdout), 10000)

        result = self.runner.invoke(doctor, "-m eng-arpabet")
        self.assertEqual(result.exit_code, 0)
        self.assertIn("No checks implemented", result.stdout)

    def test_doctor_lists(self):
        result = self.runner.invoke(doctor, "--list-all")
        self.assertEqual(result.exit_code, 0)
        self.assertIn("eng-arpabet:", result.stdout)
        self.assertIn("eng-ipa:", result.stdout)

        result = self.runner.invoke(doctor, "--list-ipa")
        self.assertEqual(result.exit_code, 0)
        self.assertNotIn("eng-arpabet:", result.stdout)
        self.assertIn("eng-ipa:", result.stdout)

    def test_scan_fra(self):
        """Test g2p scan with all French characters, in NFC and NFD"""
        for paragram_file in ["fra_panagrams.txt", "fra_panagrams_NFD.txt"]:
            result = self.runner.invoke(
                scan, ["fra", os.path.join(DATA_DIR, paragram_file)]
            )
            self.assertEqual(result.exit_code, 0)
            self.assertLogs(level="WARNING")
            diacritics = "àâéèêëîïôùûüç"
            for d in diacritics:
                self.assertNotIn(d, result.stdout)
            unmapped_chars = ":/,'-()2"
            for c in unmapped_chars:
                self.assertIn(c, result.stdout)

    def test_scan_fra_simple(self):
        # For now, unit test g2p scan using a simpler piece of French
        result = self.runner.invoke(
            scan, ["fra", os.path.join(DATA_DIR, "fra_simple.txt")]
        )
        self.assertEqual(result.exit_code, 0)
        self.assertLogs(level="WARNING")
        diacritics = "àâéèêëîïôùûüç"
        for d in diacritics:
            self.assertNotIn(d, result.stdout)
        unmapped_chars = ":,"
        for c in unmapped_chars:
            self.assertIn(c, result.stdout)

    def test_scan_str_case(self):
        result = self.runner.invoke(
            scan, ["str", os.path.join(DATA_DIR, "str_un_human_rights.txt")]
        )
        returned_set = re.search("{(.*)}", result.stdout).group(1)
        self.assertEqual(result.exit_code, 0)
        self.assertLogs(level="WARNING")
        unmapped_upper = "FGR"
        for u in unmapped_upper:
            self.assertIn(u, returned_set)
        unmapped_lower = "abcdefghijklqrtwxyz"
        for low in unmapped_lower:
            self.assertIn(low, returned_set)
        mapped_upper = "ABCDEHIJKLMNOPQSTUVWXYZ"
        for u in mapped_upper:
            self.assertNotIn(u, returned_set)
        mapped_lower = "s"
        self.assertNotIn(mapped_lower, returned_set)

    def test_convert_option_e(self):
        result = self.runner.invoke(convert, "-e est fra eng-arpabet")
        for s in [
            "[['e', 'ɛ'], ['s', 'ɛ'], ['t', 'ɛ']]",
            "[['ɛ', 'ɛ']]",
            "[['ɛ', 'E'], ['ɛ', 'H'], ['ɛ', ' ']]",
        ]:
            self.assertIn(s, result.stdout)

    def test_convert_option_d(self):
        result = self.runner.invoke(convert, "-d est fra eng-arpabet")
        for s in ["'input': 'est'", "'output': 'ɛ'", "'input': 'ɛ'", "'output': 'EH '"]:
            self.assertIn(s, result.stdout)

    def test_convert_option_t(self):
        result = self.runner.invoke(convert, "-t e\\'i oji oji-ipa")
        self.assertIn("eːʔi", result.stdout)

    def test_convert_option_tl(self):
        result = self.runner.invoke(convert, "--tok-lang fra e\\'i oji oji-ipa")
        self.assertIn("eː'i", result.stdout)

    def test_generate_mapping_errors(self):
        """Exercise various error situations with the g2p generate-mapping CLI command"""

        # We don't exercise valid calls to generate_mapping here. The underlying
        # create_mapping() function is tested in test_create_mapping.py, and
        # align_to_dummy_fallback() in test_fallback.py, with less expensive
        # inputs than our real g2p mappings, and with predictable results.

        results = self.runner.invoke(generate_mapping)
        self.assertNotEqual(results.exit_code, 0)
        self.assertIn("Nothing to do", results.output)

        results = self.runner.invoke(generate_mapping, "--ipa")
        self.assertNotEqual(results.exit_code, 0)
        self.assertIn("Missing argument", results.output)

        results = self.runner.invoke(generate_mapping, "fra")
        self.assertNotEqual(results.exit_code, 0)
        self.assertIn(
            "Nothing to do",
            results.output,
            '"g2p generate-mapping fra" should say need --ipa or --dummy or --list-dummy',
        )

        results = self.runner.invoke(generate_mapping, "--ipa foo")
        self.assertNotEqual(results.exit_code, 0)
        self.assertIn("Invalid value for IN_LANG", results.output)

        results = self.runner.invoke(generate_mapping, "--dummy fra foo")
        self.assertNotEqual(results.exit_code, 0)
        self.assertIn("Invalid value for OUT_LANG", results.output)

        results = self.runner.invoke(generate_mapping, "--ipa crl")
        self.assertNotEqual(results.exit_code, 0)
        self.assertIn("Cannot find IPA mapping", results.output)

        results = self.runner.invoke(generate_mapping, "--ipa fra dan-ipa")
        self.assertNotEqual(results.exit_code, 0)
        self.assertIn("Cannot find IPA mapping", results.output)

        results = self.runner.invoke(generate_mapping, "--list-dummy")
        self.assertEqual(results.exit_code, 0)  # this one not an error
        self.assertIn("Dummy phone inventory", results.output)

        results = self.runner.invoke(generate_mapping, "--ipa --dummy fra")
        self.assertNotEqual(results.exit_code, 0)
        self.assertIn("Error: Multiple modes selected", results.output)

        results = self.runner.invoke(
            generate_mapping, "--out-dir does-not-exist --ipa fra"
        )
        self.assertNotEqual(results.exit_code, 0)
        self.assertIn(
            "does not exist",
            results.output,
            "Non-existent out-dir must be reported as error",
        )

        results = self.runner.invoke(generate_mapping, "--from asdf")
        self.assertNotEqual(results.exit_code, 0)
        self.assertIn("Error: --from and --to must be used together", results.output)

        results = self.runner.invoke(
            generate_mapping, "--from fra_to_fra-ipa --to haa_to_haa-equiv"
        )
        self.assertNotEqual(results.exit_code, 0)
        self.assertIn("Cannot guess in/out for IPA lang spec", results.output)

        results = self.runner.invoke(generate_mapping, "--from eng --to fra[out]")
        self.assertNotEqual(results.exit_code, 0)
        self.assertIn("is only supported with the full", results.output)

        results = self.runner.invoke(
            generate_mapping, "--from fra_to_fra-ipa[foo] --to eng"
        )
        self.assertNotEqual(results.exit_code, 0)
        self.assertIn("is allowed in square brackets", results.output)

        results = self.runner.invoke(generate_mapping, "--from fra_to_eng --to eng")
        self.assertNotEqual(results.exit_code, 0)
        self.assertIn("Cannot find mapping", results.output)

    def test_show_mappings(self):
        # One arg = all mappings to or from that language
        results = self.runner.invoke(show_mappings, ["fra-ipa", "--verbose"])
        self.assertEqual(results.exit_code, 0)
        self.assertIn("French to IPA", results.output)
        self.assertIn("French IPA to English IPA", results.output)
        self.assertEqual(len(re.findall(r"display_name", results.output)), 2)

        # One arg = all mappings to or from that language, terse output
        results = self.runner.invoke(show_mappings, ["fra-ipa"])
        self.assertEqual(results.exit_code, 0)
        self.assertIn("fra-ipa", results.output)
        self.assertIn("eng-ipa", results.output)
        self.assertEqual(len(re.findall(r"→", results.output)), 2)

        # Two conencted args = that mapping
        results = self.runner.invoke(show_mappings, ["fra", "fra-ipa", "--verbose"])
        self.assertEqual(results.exit_code, 0)
        self.assertIn("French to IPA", results.output)
        self.assertIn(r'{"in": "&", "out": "et"},', results.output)
        self.assertIn(
            r'{"in": "c", "out": "s", "context_after": "e|i|è|é|ê|ë|î|ï|ÿ"},',
            results.output,
        )
        self.assertIn(
            r'{"in": "e", "out": "", "context_before": "\\S", "context_after": "\\b"},',
            results.output,
        )
        self.assertEqual(len(re.findall(r"display_name", results.output)), 1)

        # Two args connected via a intermediate steps = all mappings on that path
        results = self.runner.invoke(show_mappings, ["fra", "eng-arpabet", "--verbose"])
        self.assertEqual(results.exit_code, 0)
        self.assertIn("French to IPA", results.output)
        self.assertIn("French IPA to English IPA", results.output)
        self.assertIn("English IPA to Arpabet", results.output)
        self.assertEqual(len(re.findall(r"display_name", results.output)), 3)

        # --all = all mappings
        results = self.runner.invoke(show_mappings, [])
        self.assertEqual(results.exit_code, 0)
        self.assertGreater(len(re.findall(r"→", results.output)), 100)

        # --csv = CSV formatted output
        results = self.runner.invoke(show_mappings, ["--csv", "crl-equiv", "--verbose"])
        self.assertEqual(results.exit_code, 0)
        self.assertIn("Northern East Cree Equivalencies", results.output)
        self.assertIn("thwaa,ᕨ,,", results.output)
        self.assertIn("Northern East Cree to IPA", results.output)
        self.assertIn("ᐧᕓ,vʷeː,,", results.output)

        # Bad language code
        results = self.runner.invoke(show_mappings, ["not-a-lang"])
        self.assertNotEqual(results.exit_code, 0)
        results = self.runner.invoke(show_mappings, ["fra", "not-a-lang"])
        self.assertNotEqual(results.exit_code, 0)

        # No path
        results = self.runner.invoke(show_mappings, ["fra", "moe"])
        self.assertNotEqual(results.exit_code, 0)


if __name__ == "__main__":
    main()
