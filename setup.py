''' Setup for G2P
'''
from setuptools import setup, find_packages
import g2p

with open('requirements.txt') as f:
    install_requires = f.read().strip().split('\n')

setup(
    name='g2p',
    python_requires='>=3.6',
    version=g2p.VERSION,
    long_description='indexed grapheme to phoneme conversion',
    packages=find_packages(),
    include_package_data=True,
    install_requires=install_requires,
    zip_safe=False
)
