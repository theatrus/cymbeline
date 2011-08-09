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

import threading
import sys
import os
import __builtin__

from cymbeline.GC import GC

class RollbackImporter(object):
    def __init__(self):
        self.previousModules = sys.modules.copy()
        self.realImport = __builtin__.__import__
        __builtin__.__import__ = self._import
        self.newModules = {}
    def _import(self, name, globals=None, locals=None, fromlist=[]):
        result = apply(self.realImport, (name, globals, locals, fromlist))
        self.newModules[name] = 1

        return result
    def uninstall(self):
        for modname in self.newModules.keys():

            if not self.previousModules.has_key(modname):
                # Force reload when modname next imported
                try:
                    
                    del(sys.modules[modname])
                except:
                    pass
        __builtin__.__import__ = self.realImport
        
        

class Object(object):
    """ Note that this class still supports getting passed a GC """
    def __init__(self, gc = None):
        self.Lock = threading.RLock()
        if gc is not None:
            self.GC = gc
        else:
            self.GC = GC() # use the global
            
        
    def lock(self):
        self.Lock.acquire(1) # acquire blocking lock
    def unlock(self):
        self.Lock.release()
        

class Provider(Object):
    def __init__(self, name = None):
        Object.__init__(self)
        if name is None:
            raise ValueError
        
        self._Name = name
    def getName(self):
        return self._Name
    def setName(self, name):
        self._Name = name
    def status(self):
        return "No Status" # no statistics
    def shutdown(self):
        print self._Name + " going down."
    
class Thread(threading.Thread, Object):
    """ This is an overridden thread class with special features
    It provides registration in the Cymbeline global context, and makes the threads daemon
    by default. """
    
    def __init__(self, name = None, daemon = True):
        threading.Thread.__init__(self)
        Object.__init__(self)
        self.Name = name
        self.setDaemon(daemon)
        self.GC.registerThread(name, self) # register thread with global context
    def run(self):
        print "Thread not implemented. Thread: " + self.Name + ". Please fix."
        raise
        





