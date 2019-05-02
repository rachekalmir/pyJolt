"""
Python JOLT Implementation
"""
from setuptools import setup
import configparser

config = configparser.ConfigParser()
config.read('Pipfile')
install_requires = list(map(lambda v: v[0] + v[1].strip("'"), config['packages'].items()))
tests_requires = list(map(lambda v: v[0] + v[1].strip("'"), config['dev-packages'].items()))
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
    install_requires=install_requires if install_requires else '',
    tests_requires=tests_requires,
)
