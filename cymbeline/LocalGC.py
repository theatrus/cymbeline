
# TODO: Rewrite this

from cymbeline.GC import GC

class LocalGC(object):
    """ A version of the global context which can be intialized to
    provide local paths """
    
    def __init__(self, local = '/'):
        self.gc = GC()
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

