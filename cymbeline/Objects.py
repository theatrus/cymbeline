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

import threading
import sys
import os
import __builtin__

class GC(object):
    """ The Cymbeline Global Context class, registers all other threads and provides objects to call """
    def __getitem__(self, name): # shortcut for getProvider
        return self.getProvider(name)
    def __init__(self):
        self.providers = {} # providers of services, eg, database
        self.threads = {} # threads, by name
    def registerThread(self, name, thread):
        self.threads[name] = thread
    def registerProvider(self, provider):
        name = provider.getName()
        if name[0] != '/':
            name = '/' + name
        self.providers[name] = provider
    def getProvider(self, name):
        try:
            if name[0] != '/':
                name = '/' + name
            return self.providers[name]
        except:
            print
            print "Provider by name: '" + name + "' not found"
            print
            raise


class LocalGC(object):
    """ A version of the global context which can be intialized and provide local paths """
    def __init__(self, gc, local = '/'):
        self.gc = gc
        self.local = local
    def __getitem__(self, name):
        return self.getProvider(name)
    def __getattr__(self, attr):
        if attr == 'providers':
            return self.gc.providers
    def registerProvider(self, provider):
        name = provider.getName()
        if name[0] != '/':
            name = self.local + name
        provider.setName(name)
        self.gc.registerProvider(provider)
    def registerThread(self, name, thread):
        self.gc.registerThread(name, thread)
    def getProvider(self, name):
        try:
            if name[0] != '/':
                name = self.local + name
            return self.gc.getProvider(name)
        except:
            print
            print "Provider by name: '" + name + "' not found in global or local context"
            print
            raise

class RollbackImporter:
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
    def __init__(self, gc = None):
        self.Lock = threading.RLock()
        if gc is not None:
            self.GC = gc
        else:
            self.gc = GC # use the global
            
        
    def lock(self):
        self.Lock.acquire(1) # acquire blocking lock
    def unlock(self):
        self.Lock.release()
        

class Provider(Object):
    def __init__(self, gc = None, name = None):
        Object.__init__(self, gc)
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
    
    def __init__(self, gc = None, name = None, daemon = True):
        threading.Thread.__init__(self)
        Object.__init__(self, gc)
        self.Name = name
        self.setDaemon(daemon)
        gc.registerThread(name, self) # register thread with global context
    def run(self):
        print "Thread not implemented. Thread: " + self.Name + ". Please fix."

        





