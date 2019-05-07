''' Setup for G2P
'''
from setuptools import setup, find_packages
import g2p

setup(
    name='g2p',
    python_requires='>=3.6',
    version=g2p.VERSION,
    long_description='indexed grapheme to phoneme conversion',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[]
)