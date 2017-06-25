#!/usr/bin/env python
from setuptools import setup

version = __import__('monitor_requests').__version__

with open('README.rst', 'r') as f:
    long_description = f.read()

setup(
    author='Dan Pozmanter',
    classifiers=[
        'Development Status :: 5 - Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Testing',
    ],
    description='Check remote calls via request',
    keywords='requests testing monitoring',
    license='BSD',
    long_description=long_description,
    name='Monitor Requests',
    packages=['monitor_requests'],
    setup_requires=['requests>=2.8.0'],
    url='https://github.com/danpozmanter/monitor_requests',
    version=version,
    zip_safe=False,
    )