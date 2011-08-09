#    Cymbeline - a python embedded framework
#    Copyright (C) 2004 Yann Ramin
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License (in file COPYING) for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#


import sys
import os
import string
import re
import time

try:
    import readline
except:
    pass



from cymbeline.Objects import Object,Provider,GC,LocalGC
from cymbeline.BaseProviders import Pool,Time,Timer,Log
from cymbeline.DB import HierDB,MemoryDB
from cymbeline.HTTPServer import *
from cymbeline.Network import *
from cymbeline.IC import CymbelineIC


    
def bootstrap(user_boot, ic_console = True, settings_db = None):
    (vmajor, vminor, vmicro, vrl, vserial) = sys.version_info
    print
    print "Welcome to the Cymbeline Framework"
    print "-------------------------------------------"
    print "System Release 1.2.4 on Python " + `vmajor` + "." + `vminor` + "." + `vmicro` + vrl + `vserial` +" " + sys.platform
    print "(c) 2002-2004 Yann Ramin, All Right Reserved."
    print
    print "Beginning bootstrap..."

    print "Current path:"
    print sys.path
    print
    sys.stdout.write("Creating global context... ")
    gc = GC() # create the all mighty global context


    print "OK"


    sys.stdout.write("--- Creating providers...\n")

    sys.stdout.write("Time...     ")
    gc.registerProvider(Time(gc, '/system/time'))
    print "OK"

    sys.stdout.write("Log...      ")
    log = Log(gc, '/system/log')
    gc.registerProvider(log)
    log.log('system', 'Logging started')
    print "OK"


    sys.stdout.write("Timer...    ") # system event timer
    gc.registerProvider(Timer(gc, '/system/timer'))
    print "OK"

    sys.stdout.write("Settings DB... ")
    
    # start up database providers
    # create magic :)

    try:
        filein = settings_db
        gc.registerProvider(MemoryDB(gc, '/system/settings', filein, autoload = 1, dumpinterval = 100))
        sys.stdout.write("(init from " + filein + ") ")
        
       # gc.getProvider('db_settings').loadFromFile()

    except:
        print
        print
        print "No settings database specified, or unable to load."
        print
        return

    print "OK"

    sys.stdout.write("Interactive console...")
    ic = CymbelineIC(gc, "/system/ic")

    gc.registerProvider(ic)
    print "OK"
    

    print "--- System providers created. "
    print "--- Starting user bootstrap code"

    user_boot(gc)

    print "--- User bootstrap completed"

    if ic_console is True:
        print "--- Switching to interactive console"
        print

        ic.ic_console()
        print "Exiting the main console - So long, and thanks for all the fish"
        return
    else:
        while 1:
            time.sleep(100)
            

            

        
