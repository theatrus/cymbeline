#!/usr/bin/env python

import os
import sys
import optparse

global GC

cwd = os.getcwd()
sys.path.append(cwd)
GC = None


parser = optparse.OptionParser()
parser.add_option("-n", "--no-console", dest="console",
                  action="store_false",  default=True,
                  help="Disable the Cymbeline interactive console")
parser.add_option("-s", '--settings', dest='settings',
                  help = 'The Settings database for cymbeline')

(options,args) = parser.parse_args()

from cymbeline.Bootstrap import bootstrap

#import shallot.Boot


def user_bootstrap(gc):
    pass
#    shallot.Boot.boot(gc, '/shallot/')



bootstrap(user_bootstrap, ic_console = options.console, settings_db = options.settings)

print "Heading out..."

sys.exit()






