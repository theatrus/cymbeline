#    Cymbeline - a python embedded framework
#    Copyright (C) 2004-2005 Yann Ramin
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
import traceback
#import readline

from cymbeline.Objects import Provider,Object
from cymbeline.DB import HierDB

__version__ = "0.1.2"

class IC_Command(Object):
    
    def __init__(self):
        Object.__init__(self)
        self.commands = {'': self.null }
    def null(self, *other):
        pass

    

class IC_Builtins(IC_Command):
    def __init__(self):
        IC_Command.__init__(self)
        self.commands = {'version' : self.version,
                         'providers' : self.providers,
                         'threads' : self.threads,
                         'exec' : self.cym_exec,
                         'quit' : self.quit,
                         '': self.null }

    def version(self, *other):
        print "Cymbeline Interactive Console Version " + __version__
        print "(c) 2002-2004-2005 Yann Ramin"
        print "All rights reserved."

    def providers(self, *other):
        gc = self.GC
        keys = gc.providers.keys()
        keys.sort()
        for x in keys:
            print string.ljust(x, 30) + string.ljust(gc.providers[x].status(), 40)

    def threads(self, *other):
        gc = self.GC
        for x in gc.threads:
            print x

    def cym_exec(self,*other):
        gc = self.GC
        
        print "Enter python statement to be executed:"
        eval_line = raw_input(" :") 
        try:
            exec(eval_line)
        except:
            print "Error execing that statement. exec aborted."
            print '-'*60
            traceback.print_exc()
            print '-'*60

    def quit(self,*other):
        gc = self.GC
        
        for x in gc.providers.values():
            x.shutdown()
            del x
        print "Have a nice day!"
        return -100
            
                    

class IC_Console(Object):
    def __init__(self, 
                 o = sys.stdout, i = sys.stdin):
        
        Object.__init__(self)
        self.outf = o
        self.inf = i

        
    def ic_console(self): 

        print "Cymbeline Interactive Console Version " + __version__
        gc = self.GC

        ic = gc['/system/ic']
        
        while 1:

            line = raw_input(">")
            linespl = line.split(' ')

            try:
                result = ic.commands[linespl[0]](linespl[1:])
                if result == -100:
                    return # quit :)
            except KeyError:
                print 'Command not found'


class CymbelineIC(Provider): # this is a provider
    def __init__(self, name):
        Provider.__init__(self, name)

        self.commands = {}
        self.command_obj = {'builtin' : IC_Builtins()}
        self.commands.update(self.command_obj['builtin'].commands)
        

    def status(self):
        return `len(self.commands)` + " commands loaded"
    def add_commands(self, cclass, com):

        self.commands.update(com.commands)
        self.command_obj[cclass] = com


    def ic_console(self, outh = sys.stdout, inh = sys.stdin):
        i = IC_Console( outh, inh)
        i.ic_console()



