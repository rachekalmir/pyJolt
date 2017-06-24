"""
Python JOLT Implementation
"""
from setuptools import setup
from pip.req import parse_requirements

from pyjolt import __version__

install_requires = [str(ir.req) for ir in parse_requirements('requirements.txt')]
test_requires = [str(ir.req) for ir in parse_requirements('test-requirements.txt')]

setup(
    name='pyjolt',
    version=__version__,
    description='Python JOLT Implementation',
    long_description=__doc__,
    author='rachekalmir',
    author_email='rachekalmir@users.noreply.github.com',
    url='https://github.com/rachekalmir/pyjolt/',
    license='Apache 2.0',
    packages=['pyjolt'],
    install_requires=install_requires,
    tests_requires=test_requires,
)
