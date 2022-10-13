#!/usr/bin/env python3

"""
Test suite for the g2p-studio web app.

Requirements: python 3.8 and requirements/requirements.test.txt

Before running this test suite, launch the g2p-studio server:
minimal dev mode:
    python run_studio.py
or robust server mode (*nix only, gunicorn does not work on Windows):
    gunicorn --worker-class eventlet  -w 1 g2p.app:APP --no-sendfile --bind 0.0.0.0:5000 --daemon
"""

from datetime import datetime

# flake8: noqa: C901
from unittest import IsolatedAsyncioTestCase, main

from playwright.async_api import async_playwright

from g2p.app import APP, SOCKETIO
from g2p.log import LOGGER
from g2p.tests.public.data import load_public_test_data


class StudioTest(IsolatedAsyncioTestCase):
    def __init__(self, *args):
        super().__init__(*args)
        self.port = 5000
        self.debug = True

    def setUp(self):
        self.flask_test_client = APP.test_client()
        self.socketio_test_client = SOCKETIO.test_client(
            APP, flask_test_client=self.flask_test_client
        )

    def test_socket_connection(self):
        self.assertTrue(self.socketio_test_client.is_connected())

    async def test_sanity(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(channel="chrome", headless=True)
            page = await browser.new_page()
            await page.goto(f"http://localhost:{self.port}")
            await page.wait_for_timeout(1000)
            input_el = page.locator("#input")
            output_el = page.locator("#output")
            await page.type("#input", "hello world")
            await page.wait_for_timeout(1000)
            input_text = await input_el.input_value()
            output_text = await output_el.input_value()
            self.assertEqual(input_text, output_text)
            self.assertEqual(input_text, "hello world")
            await input_el.fill("")
            await output_el.fill("")

    async def test_langs(self):

        langs_to_test = load_public_test_data()
        error_count = 0

        # The current g2p-studio app leaks memory, so that if we try to run all the test
        # cases in one single browser instance, a case (not always the same) eventually
        # breaks. While that should get patched, for now, let's make unit testing
        # reliable by running tests by blocks we know the app can handle.
        block_size = 50

        max_action_delay = 5000  # in ms - max time we'll wait for an action to work
        polling_period = 20  # in ms - polling period for action effects

        for block in range((len(langs_to_test) - 1) // block_size + 1):
            LOGGER.info("Lauching async_playwright")
            async with async_playwright() as p:
                LOGGER.info(("L" if block == 0 else "Rel") + "aunching browser")
                browser = await p.chromium.launch(channel="chrome", headless=True)
                LOGGER.info("Loading page")
                page = await browser.new_page()
                await page.goto(
                    f"http://localhost:{self.port}", wait_until="networkidle"
                )

                # Define element locators
                input_el = page.locator("#input")
                output_el = page.locator("#output")
                in_lang_selector = page.locator("#input-langselect")
                out_lang_selector = page.locator("#output-langselect")

                for i, test in enumerate(
                    langs_to_test[block_size * block : block_size * (block + 1)]
                ):
                    LOGGER.info(
                        f"{i+block*block_size} {datetime.now()} "
                        f"{test[0]}->{test[1]} {test[2]} -> {test[3]}"
                    )
                    for attempt in range(1, 4):
                        if attempt > 1:
                            LOGGER.info(f"Attempt #{attempt}")
                            await page.wait_for_timeout(1000)
                        # Clear input and output
                        await input_el.fill("")
                        await output_el.fill("")
                        output_text = ""

                        # Select the input language
                        await in_lang_selector.select_option(value=test[0])
                        # wait up to max_action_delay ms for input lang to be set
                        # and for mappings to be populated
                        loop_time = 0
                        while loop_time <= max_action_delay:
                            input_lang = await in_lang_selector.input_value()
                            if input_lang.strip() == test[0].strip():
                                await page.wait_for_timeout(polling_period)
                                break
                            await page.wait_for_timeout(polling_period)
                            loop_time += polling_period
                        else:
                            LOGGER.warning(
                                f"Reached timeout setting in_lang for {test}"
                            )
                            continue

                        # Select the output language
                        await out_lang_selector.select_option(value=test[1])
                        # wait up to max_action_delay ms for output lang to be set
                        # and for mappings to be populated
                        loop_time = 0
                        while loop_time <= max_action_delay:
                            output_lang = await out_lang_selector.input_value()
                            if output_lang.strip() == test[1].strip():
                                await page.wait_for_timeout(polling_period)
                                break
                            await page.wait_for_timeout(polling_period)
                            loop_time += polling_period
                        else:
                            LOGGER.warning(
                                f"Reached timeout setting out_lang for {test}"
                            )
                            continue

                        # Type fill input, then trigger rendering with keyup event
                        # optimization: make sure there is only 1 keyup event
                        await input_el.fill(test[2] + " ")
                        await input_el.press("Backspace")

                        loop_time = 0
                        # wait up to max_action_delay ms for output to be populated
                        while loop_time <= max_action_delay:
                            output_text = await output_el.input_value()
                            if output_text.strip() == test[3].strip():
                                break
                            await page.wait_for_timeout(polling_period)
                            loop_time += polling_period
                        else:
                            LOGGER.warning(
                                f"Reached timeout setting input text for {test}"
                            )
                            continue

                        # We're done trying once an attempt succeeds
                        if output_text.strip() == test[3].strip():
                            break

                    # Check that output is correct after the first succesful attempt or
                    # after all the attempts have failed.
                    if not self.debug:
                        self.assertEqual(output_text.strip(), test[3].strip())
                        LOGGER.info(
                            f"Successfully converted {test[2]} from {test[0]} to {test[1]}"
                        )
                    elif output_text.strip() != test[3].strip():
                        LOGGER.warning(
                            f"test_langs.py: mapping error: {test[2]} from {test[0]} "
                            f"to {test[1]} should be {test[3]}, got {output_text}"
                        )
                        input_text = await input_el.input_value()
                        if error_count == 0:
                            first_failed_test = [input_text, output_text]
                        error_count += 1
                    else:
                        LOGGER.info(
                            f"Successfully converted {test[2]} from {test[0]} to {test[1]}"
                        )

                # Let the user know we're closing the browser (by exiting the p context
                # manager scope) to explain why there's a delay here.
                LOGGER.info("Closing browser")

        if self.debug and error_count > 0:
            self.assertEqual(
                first_failed_test[0],
                first_failed_test[1],
                f"{error_count} lang mapping test case(s) failed, "
                "look for warnings in the logs above for details.",
            )


if __name__ == "__main__":
    main()
