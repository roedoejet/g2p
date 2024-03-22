""" Setup for g2p
"""

from os import path

from setuptools import find_packages, setup

# Ugly hack to read the current version number without importing g2p:
with open("g2p/_version.py", "r", encoding="utf8") as version_file:
    namespace = {}  # type: ignore
    exec(version_file.read(), namespace)
    VERSION = namespace["VERSION"]

this_directory = path.abspath(path.dirname(__file__))

with open(path.join(this_directory, "README.md"), encoding="utf8") as f:
    long_description = f.read()

with open(
    path.join(this_directory, "requirements", "requirements.txt"), encoding="utf8"
) as f:
    REQS = f.read().splitlines()

setup(
    name="g2p",
    python_requires=">=3.7",
    version=VERSION,
    author="Aidan Pine",
    author_email="hello@aidanpine.ca",
    license="MIT",
    url="https://github.com/roedoejet/g2p",
    description="Module for creating context-aware, rule-based G2P mappings that preserve indices",
    long_description=long_description,
    long_description_content_type="text/markdown",
    platform=["any"],
    packages=find_packages(),
    include_package_data=True,
    install_requires=REQS,
    entry_points={"console_scripts": ["g2p = g2p.cli:cli"]},
    zip_safe=False,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
