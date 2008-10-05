# -*- coding: utf-8 -*-
import os
import ez_setup
ez_setup.use_setuptools()

from setuptools import setup
import dmlt

def list_files(path):
    for fn in os.listdir(path):
        if fn.startswith('.'):
            continue
        fn = os.path.join(path, fn)
        if os.path.isfile(fn):
            yield fn

setup(
    name = 'Descriptive Markup Toolkit',
    version = dmlt.__version__,
    url = 'http://trac.webshox.org/',
    license = 'BSD',
    author = 'Christopher Grebs',
    author_email = 'cg@webshox.org',
    description = ('Just a nice small nice designed markup toolkit.\n'),
    long_description = ('The Descriptive Markup Toolkit is designed to support\n'
                        'programmers while writing a processor for a markup language\n'
                        'like HTML or some descriptive markup languages like the ReStructedText\n'
                        'or something similar.\n'),
    zip_safe = False,
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries',
        'Topic :: Text Processing :: Markup',
        'Topic :: Utilities',
    ],
    packages = ['dmlt'],
    package_dir = {'dmlt': 'dmlt'},
    include_package_data = True,
    platforms = 'any',
    extras_require = {'plugin': ['setuptools>=0.6a2']},
    test_suite = 'nose.collector'
)
