#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup

with open('README.md') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

requirements = [
    "rlp==0.4.6",
    "pysha3==1.0b1"
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='empyrean',
    version='0.1.0',
    description="Empyrean is a somewhat pythonic API for ethereum JSONRPC and JSONIPC API's",
    long_description=readme + '\n\n' + history,
    author="Ivo van der Wijk",
    author_email='ivo+empyrean@gutstickets.org',
    url='https://github.com/iivvoo/empyrean',
    packages=[
        'empyrean',
    ],
    package_dir={'empyrean':
                 'empyrean'},
    include_package_data=True,
    install_requires=requirements,
    license="BSD license",
    zip_safe=False,
    keywords='empyrean',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
