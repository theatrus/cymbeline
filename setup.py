#!/usr/bin/env python

from distutils.core import setup

setup(name='cymbeline',
      version="1.2.3",
      description='Embedded application framework',
      author='Yann Ramin',
      author_email='atrus@stackworks.net',
      url='http://www.stackworks.net/cymbeline/',
      scripts=['cymbelined'],
      packages=['cymbeline', 'cymbeline/auth'])
