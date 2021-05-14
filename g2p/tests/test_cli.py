#!/usr/bin/env python3

from unittest import main, TestCase
import os
import csv
import re
from glob import glob

from g2p.app import APP
from g2p.log import LOGGER
from g2p.cli import convert, update, doctor, scan
from g2p.tests.public.data import __file__ as data_dir


class CliTest(TestCase):
    def setUp(self):
        self.runner = APP.test_cli_runner()
        self.data_dir = os.path.dirname(data_dir)
        self.langs_to_test = []
        for fn in glob(f"{self.data_dir}/*.*sv"):
            if fn.endswith("csv"):
                delimiter = ","
            elif fn.endswith("psv"):
                delimiter = "|"
            elif fn.endswith("tsv"):
                delimiter = "\t"
            with open(fn, encoding="utf-8") as csvfile:
                reader = csv.reader(csvfile, delimiter=delimiter)
                for row in reader:
                    if len(row) < 4:
                        LOGGER.warning(
                            f"Row in {fn} containing values {row} does not have the right values."
                            f"Please check your data."
                        )
                    else:
                        self.langs_to_test.append(row)

    def test_update(self):
        result = self.runner.invoke(update)
        self.assertEqual(result.exit_code, 0)

    def test_convert(self):
        error_count = 0
        for tok_option in [["--tok", "--check"], ["--no-tok"]]:
            for test in self.langs_to_test:
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
        self.assertIn("vagon", result.stdout)

        result = self.runner.invoke(doctor)
        self.assertEqual(result.exit_code, 0)
        self.assertGreaterEqual(len(result.stdout), 10000)

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

    def not_test_scan_fra(self):
        # TODO: fix fra g2p so fra_panagrams.txt passes
        result = self.runner.invoke(scan, f"fra {self.data_dir}/fra_panagrams.txt")
        self.assertEqual(result.exit_code, 0)
        self.assertLogs(level="WARNING")
        diacritics = "àâéèêëîïôùûüç"
        for d in diacritics:
            self.assertNotIn(d, result.stdout)
        unmapped_chars = ":/.,'-&()2"
        for c in unmapped_chars:
            self.assertIn(c, result.stdout)

    def test_scan_fra_simple(self):
        # For now, unit test g2p scan using a simpler piece of French
        result = self.runner.invoke(scan, f"fra {self.data_dir}/fra_simple.txt")
        self.assertEqual(result.exit_code, 0)
        self.assertLogs(level="WARNING")
        diacritics = "àâéèêëîïôùûüç"
        for d in diacritics:
            self.assertNotIn(d, result.stdout)
        unmapped_chars = ":,"
        for c in unmapped_chars:
            self.assertIn(c, result.stdout)
    
    def test_scan_str_case(self):
        result = self.runner.invoke(scan, f'str {self.data_dir}/str_un_human_rights.txt')
        returned_set = re.search('{(.*)}', result.stdout).group(1)
        self.assertEqual(result.exit_code, 0)
        self.assertLogs(level='WARNING')
        unmapped_upper = 'FGR'
        for u in unmapped_upper:
            self.assertIn(u, returned_set)
        unmapped_lower = 'abcdefghijklqrtwxyz'
        for low in unmapped_lower:
            self.assertIn(low, returned_set)
        mapped_upper = 'ABCDEHIJKLMNOPQSTUVWXYZ'
        for u in mapped_upper:
            self.assertNotIn(u, returned_set)
        mapped_lower = 's'
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


if __name__ == "__main__":
    main()
