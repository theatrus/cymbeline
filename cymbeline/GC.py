from cymbeline.Objects import *
from cymbeline.Exceptions import *



class _GC(object):
    """ The Cymbeline Global Context class/singleton,
    registers all other threads and provides objects to call """
    

    def __init__(self):

        self.providers = {} # providers of services, eg, database
        self.threads = {} # threads, by name

    def __getitem__(self, name): # shortcut for getProvider
        return self.getProvider(name)
    def registerThread(self, name, thread):

        if name in self.threads:
            raise GCIsRegistered
        
        self.threads[name] = thread
    def registerProvider(self, provider):
        name = provider.getName()

        if name[0] != '/':
            name = '/' + name

        if name in self.providers:
            raise GCIsRegistered
        
        self.providers[name] = provider

    def getProvider(self, name):

        if name[0] != '/':
            name = '/' + name
        return self.providers[name]



class GC(object):
    theSingleInstance = _GC()
    def __init__(self):
        self.__dict__ = GC.theSingleInstance.__dict__
        self.__class__ = GC.theSingleInstance.__class__ 
