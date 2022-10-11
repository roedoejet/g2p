#!/usr/bin/env python3
import sys

# flake8: noqa: C901
from unittest import IsolatedAsyncioTestCase, main

from playwright.async_api import async_playwright

from g2p.app import APP, SOCKETIO
from g2p.log import LOGGER
from g2p.tests.public.data import load_public_test_data


class StudioTest(IsolatedAsyncioTestCase):
    def setUp(self):
        self.flask_test_client = APP.test_client()
        self.socketio_test_client = SOCKETIO.test_client(
            APP, flask_test_client=self.flask_test_client
        )
        self.debug = True

    def test_socket_connection(self):
        self.assertTrue(self.socketio_test_client.is_connected())

    async def test_sanity(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(channel="chrome", headless=True)
            page = await browser.new_page()
            await page.goto("http://localhost:5000")
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

        async with async_playwright() as p:
            browser = await p.chromium.launch(channel="chrome", headless=True)
            page = await browser.new_page()
            await page.goto("http://localhost:5000", wait_until="networkidle")
            for test in langs_to_test:
                # Define element locators
                input_el = page.locator("#input")
                output_el = page.locator("#output")
                in_lang_selector = page.locator("#input-langselect")
                out_lang_selector = page.locator("#output-langselect")
                # Clear input and output
                await input_el.fill("")
                await output_el.fill("")
                # Select input/output language
                await in_lang_selector.select_option(value=test[0])
                # wait up to 1 second for input lang to be set
                # and for mappings to be populated
                loop_time = 0
                while loop_time <= 1000:
                    input_lang = await in_lang_selector.input_value()
                    if input_lang.strip() == test[0].strip():
                        break
                    await page.wait_for_timeout(100)
                    loop_time += 100
                await out_lang_selector.select_option(value=test[1])
                # wait up to 1 second for output lang to be set
                # and for mappings to be populated
                loop_time = 0
                while loop_time <= 1000:
                    output_lang = await out_lang_selector.input_value()
                    if output_lang.strip() == test[1].strip():
                        break
                    await page.wait_for_timeout(100)
                    loop_time += 100
                # Type fill input, then trigger rendering with keyup events
                await input_el.fill(test[2])
                await input_el.type(" ", delay=100)
                await input_el.press("Backspace")

                loop_time = 0
                # wait up to 1 second for output to be populated
                while loop_time <= 1000:
                    output_text = await output_el.input_value()
                    if output_text.strip() == test[3].strip():
                        break
                    await page.wait_for_timeout(100)
                    loop_time += 100
                # Check that output is correct
                if not self.debug:
                    self.assertEqual(output_text.strip(), test[3].strip())
                    LOGGER.info(
                        f"Successfully converted {test[2]} from {test[0]} to {test[1]}"
                    )
                elif output_text.strip() != test[3].strip():
                    LOGGER.warning(
                        f"test_langs.py: mapping error: {test[2]} from {test[0]} to {test[1]} should be {test[3]}, got {output_text}"
                    )
                    input_text = await input_el.input_value()
                    if error_count == 0:
                        test.append(input_text)
                        test.append(output_text)
                        first_failed_test = test
                    error_count += 1
                else:
                    LOGGER.info(
                        f"Successfully converted {test[2]} from {test[0]} to {test[1]}"
                    )

        if self.debug and error_count > 0:
            self.assertEqual(
                first_failed_test[4],
                first_failed_test[5],
            )


if __name__ == "__main__":
    main()
