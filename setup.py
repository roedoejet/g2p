''' Setup for gi2pi
'''
from setuptools import setup, find_packages

# Ugly hack to read the current version number without importing gi2pi:
# (works by )
with open("gi2pi/__version__.py", "r", encoding="UTF-8") as version_file:
    namespace = {}
    exec(version_file.read(), namespace)
    VERSION = namespace['VERSION']

setup(
    name='gi2pi',
    python_requires='>=3.7',
    version=VERSION,
    long_description='indexed grapheme to phoneme conversion',
    packages=find_packages(),
    include_package_data=True,
    install_requires=['openpyxl',
                      'coloredlogs',
                      'Flask',
                      'flask_socketio',
                      'flask-talisman',
                      'pyyaml',
                      'regex'],
    zip_safe=False
)
