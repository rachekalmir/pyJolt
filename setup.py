"""
Python JOLT Implementation
"""
from setuptools import setup

with open('requirements.txt') as f:
    install_requires = f.read().splitlines()

with open('test-requirements.txt') as f:
    tests_requires = f.read().splitlines()

setup(
    name='pyjolt',
    version='0.0.1',
    description='Python JOLT Implementation',
    long_description=__doc__,
    author='rachekalmir',
    author_email='rachekalmir@users.noreply.github.com',
    url='https://github.com/rachekalmir/pyjolt/',
    license='Apache 2.0',
    packages=['pyjolt'],
    install_requires=install_requires,
    tests_requires=tests_requires,
)
