#!/usr/bin/env python

from distutils.core import setup

setup(name='cymbeline',
      version="1.3.0",
      description='Embedded application framework',
      author='Yann Ramin',
      author_email='atrus@stackworks.net',
      url='http://www.stackworks.net/cymbeline/',
      scripts=['cymbelined', 'cymbelined.bat'],
      packages=['cymbeline', 'cymbeline/auth', 'cymbeline/Server'])
