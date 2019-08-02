''' Setup for g2p
'''
from setuptools import setup, find_packages
import datetime as dt

build_no = dt.datetime.today().strftime('%Y%m%d')

# Ugly hack to read the current version number without importing g2p:
# (works by )
with open("g2p/__version__.py", "r", encoding="UTF-8") as version_file:
    namespace = {}
    exec(version_file.read(), namespace)
    VERSION = namespace['VERSION'] + "." + build_no

setup(
    name='g2p',
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
