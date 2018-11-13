"""Setup script."""
#!/usr/bin/env python
from setuptools import setup

version = __import__('monitor_requests').__version__

with open('README.rst', 'r') as f:
    long_description = f.read()

setup(
    author='Dan Pozmanter',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Testing',
    ],
    description='Check remote calls via request',
    entry_points="""
[console_scripts]
monitor_requests_server = monitor_requests.server:run_server
""",
    keywords='requests testing monitoring',
    license='BSD',
    long_description=long_description,
    name='MonitorRequests',
    packages=['monitor_requests'],
    url='https://github.com/danpozmanter/monitor_requests',
    version=version,
    zip_safe=False,
    )
