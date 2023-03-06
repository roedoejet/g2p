import unittest

from fastapi.testclient import TestClient

from g2p.api_v2 import api

API_CLIENT = TestClient(api)


class TestAPIV2(unittest.TestCase):
    def test_langs(self):
        response = API_CLIENT.get("/langs")
        self.assertEqual(response.status_code, 200)
        codes = {x["code"] for x in response.json()}
        self.assertTrue("fin" in codes)
        self.assertTrue("atj" in codes)
        self.assertFalse("generated" in codes)
        self.assertFalse("atj-ipa" in codes)
        names = {x["name"] for x in response.json()}
        self.assertTrue("Finnish" in names)

    def test_langs_allcodes(self):
        response = API_CLIENT.get("/langs?allnodes=true")
        self.assertEqual(response.status_code, 200)
        codes = {x["code"] for x in response.json()}
        self.assertTrue("eng-arpabet" in codes)
        self.assertTrue("eng-ipa" in codes)
        self.assertTrue("atj" in codes)
        self.assertFalse("generated" in codes)

    def test_outputs_for(self):
        response = API_CLIENT.get("/outputs_for/fin")
        self.assertEqual(response.status_code, 200)
        self.assertTrue("eng-arpabet" in response.json())
        self.assertTrue("eng-ipa" in response.json())

    def test_inputs_for(self):
        response = API_CLIENT.get("/inputs_for/eng-arpabet")
        self.assertEqual(response.status_code, 200)
        self.assertTrue("fin" in response.json())
        self.assertTrue("eng-ipa" in response.json())

    def test_convert(self):
        response = API_CLIENT.post(
            "/convert",
            json={
                "in_lang": "fin",
                "out_lang": "eng-arpabet",
                "text": "hyvää yötä",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            [
                {
                    "conversions": [
                        {
                            "in_lang": "eng-ipa",
                            "out_lang": "eng-arpabet",
                            "alignments": [
                                ["h", "HH "],
                                ["u", "UW "],
                                ["w", "W "],
                                ["æ", "AE "],
                            ],
                        },
                        {
                            "in_lang": "fin-ipa",
                            "out_lang": "eng-ipa",
                            "alignments": [
                                ["h", "h"],
                                ["y", "u"],
                                ["ʋ", "w"],
                                ["æː", "æ"],
                            ],
                        },
                        {
                            "in_lang": "fin",
                            "out_lang": "fin-ipa",
                            "alignments": [
                                ["h", "h"],
                                ["y", "y"],
                                ["v", "ʋ"],
                                ["ä", "æ"],
                                ["ä", "ː"],
                            ],
                        },
                    ]
                },
                {
                    "conversions": [
                        {"in_lang": None, "out_lang": None, "alignments": [[" ", " "]]}
                    ]
                },
                {
                    "conversions": [
                        {
                            "in_lang": "eng-ipa",
                            "out_lang": "eng-arpabet",
                            "alignments": [
                                ["u", "UW "],
                                ["ə", "AH "],
                                ["t", "T "],
                                ["æ", "AE "],
                            ],
                        },
                        {
                            "in_lang": "fin-ipa",
                            "out_lang": "eng-ipa",
                            "alignments": [
                                ["y", "u"],
                                ["ø", "ə"],
                                ["t", "t"],
                                ["æ", "æ"],
                            ],
                        },
                        {
                            "in_lang": "fin",
                            "out_lang": "fin-ipa",
                            "alignments": [
                                ["y", "y"],
                                ["ö", "ø"],
                                ["t", "t"],
                                ["ä", "æ"],
                            ],
                        },
                    ]
                },
            ],
        )

    def test_convert_composed(self):
        response = API_CLIENT.post(
            "/convert",
            json={
                "in_lang": "fin",
                "out_lang": "eng-arpabet",
                "text": "hyvää yötä",
                "compose_from": "fin",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            [
                {
                    "conversions": [
                        {
                            "in_lang": "fin",
                            "out_lang": "eng-arpabet",
                            "alignments": [
                                ["h", "HH "],
                                ["y", "UW "],
                                ["v", "W "],
                                ["ää", "AE "],
                            ],
                        },
                    ],
                },
                {
                    "conversions": [
                        {"in_lang": None, "out_lang": None, "alignments": [[" ", " "]]}
                    ]
                },
                {
                    "conversions": [
                        {
                            "in_lang": "fin",
                            "out_lang": "eng-arpabet",
                            "alignments": [
                                ["y", "UW "],
                                ["ö", "AH "],
                                ["t", "T "],
                                ["ä", "AE "],
                            ],
                        },
                    ]
                },
            ],
        )

    def test_convert_compose_from(self):
        response = API_CLIENT.post(
            "/convert",
            json={
                "in_lang": "fin",
                "out_lang": "eng-arpabet",
                "text": "hyvää yötä",
                "compose_from": "fin-ipa",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            [
                {
                    "conversions": [
                        {
                            "in_lang": "fin-ipa",
                            "out_lang": "eng-arpabet",
                            "alignments": [
                                ["h", "HH "],
                                ["y", "UW "],
                                ["ʋ", "W "],
                                ["æː", "AE "],
                            ],
                        },
                        {
                            "in_lang": "fin",
                            "out_lang": "fin-ipa",
                            "alignments": [
                                ["h", "h"],
                                ["y", "y"],
                                ["v", "ʋ"],
                                ["ä", "æ"],
                                ["ä", "ː"],
                            ],
                        },
                    ],
                },
                {
                    "conversions": [
                        {"in_lang": None, "out_lang": None, "alignments": [[" ", " "]]}
                    ]
                },
                {
                    "conversions": [
                        {
                            "in_lang": "fin-ipa",
                            "out_lang": "eng-arpabet",
                            "alignments": [
                                ["y", "UW "],
                                ["ø", "AH "],
                                ["t", "T "],
                                ["æ", "AE "],
                            ],
                        },
                        {
                            "in_lang": "fin",
                            "out_lang": "fin-ipa",
                            "alignments": [
                                ["y", "y"],
                                ["ö", "ø"],
                                ["t", "t"],
                                ["ä", "æ"],
                            ],
                        },
                    ]
                },
            ],
        )

    def test_convert_no_path(self):
        response = API_CLIENT.post(
            "/convert",
            json={
                "in_lang": "fin",
                "out_lang": "fra",
                "text": "hyvää yötä",
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_convert_invalid(self):
        response = API_CLIENT.post(
            "/convert",
            json={
                "in_lang": "Finnish",
                "out_lang": "eng-arpabet",
                "text": "hyvää yötä",
            },
        )
        self.assertEqual(response.status_code, 422)
        self.assertIn("not a valid enumeration", response.json()["detail"][0]["msg"])

    def test_path(self):
        response = API_CLIENT.get("/path/fin/eng-arpabet")
        self.assertEqual(response.status_code, 200)
        path = response.json()
        self.assertEqual(path, ["fin", "fin-ipa", "eng-ipa", "eng-arpabet"])

    def test_no_path(self):
        response = API_CLIENT.get("/path/fin/fra")
        self.assertEqual(response.status_code, 400)
        self.assertIn("No path", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
