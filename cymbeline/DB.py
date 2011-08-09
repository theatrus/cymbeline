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

from cymbeline.Objects import Provider,Object,Thread
import anydbm
import shelve
import time
import re
import cPickle
from threading import *


class MemoryDB(Provider):
    def __init__(self, gc, name, db = '', **flags):
        Provider.__init__(self, gc, name)

        if 'dumpinterval' not in flags:
            flags['dumpinterval'] = -1
        if 'autoload' not in flags:
            flags['autoload'] = 1


        self.gc = gc
        self.name = name
        self._wc = 0
        self._rc = 0
        self._stale = 0
        self._commitable = 0
        self._staletime = int(time.time())
        self._dbfile = db

        self.db = {}

        if flags['autoload'] and db:
            try:
                self.loadFromFile()
            except:
                pass # fail silently

        if flags['dumpinterval'] > 0:
            self.GC['/system/timer'].addFunction(self.Timer, flags['dumpinterval'])


    def setCommitable(self, flag):
        self._commitable = flag
        return flag
    def checkStale(self):
        return self._stale
    def setStale(self, flag):
        self._stale = flag
        return flag
    def loadFromFile(self):
        self.lock()
        try:
            file = open(self._dbfile, "r")
        except:
            print "Unable to open database for input: " + self._dbfile
            self.unlock()
            return

        line = file.readline().rstrip()
        line2 = file.readline().rstrip()
        while line:
            self.write(line, line2)
            #print line+"," + line2
            line = file.readline().rstrip()
            line2 = file.readline().rstrip()
        file.close()
        self.setStale(0)
        self.unlock()
    def dumpToFile(self):
        if not self.checkStale():
            return
        self.lock()
        file = open(self._dbfile, "w")
        for x in self.db:
            file.write(x + "\n" + self.db[x] + "\n")
        file.close()
        self._stale = 0
        self._staletime = int(time.time())
        self.gc['log'].log(self.name, 'database dumped to file')
        self.unlock()
    def read(self, key):
        self._rc = self._rc + 1
        return self.db[key]
    def write(self, key, value):
        self.lock()
        self.db[key] = value
        self._wc = self._wc + 1
        self._staletime = int(time.time())
        self._stale = 1
        self.unlock()
    def keys(self):
        return self.db.keys()
    def has_key(self, key):
        return self.db.has_key(key)
    def del_key(self, key):
        del self.db[key]
    def status(self):
        stalemsg = ""
        if self._stale == 1:
            stalemsg = "STALE"
        else:
            stalemsg = ""
        return "Reads: " + `self._rc` + " Writes: " + `self._wc` + " Last commit: " + `int(time.time()) - self._staletime` + " seconds ago " + stalemsg
    def Timer(self, options=''):
        if self.checkStale:
            self.dumpToFile()
            


class HierDB(Provider):
    def __init__(self, gc, name, **flags):
        Provider.__init__(self, gc, name)
        self.name = name

        if 'mode' not in flags:
            flags['mode'] = 'pickle';
        if 'commit' not in flags:
            flags['commit'] = 0
        if 'dumpinterval' not in flags:
            flags['dumpinterval'] = -1
        if 'autoload' not in flags:
            flags['autoload'] = 1
            

        self.flags = flags
        
        r = re.compile('/')
        self.file_name = r.sub('_', name)
        self._root = {}
        self._reads = 0
        self._writes = 0
        self._stale = 0
        self._staletime = int(time.time())

        if flags['autoload']:
            try:
                self.loadFromFile()
            except:
                pass # fail silently

        if flags['dumpinterval'] > 0:
            self.GC['/system/timer'].addFunction(self.Timer, flags['dumpinterval'])



    def dumpToFile(self):
        self.lock()
        try:
            file = open(self.file_name, "w")
        except:
            self.unlock()
            return
        cPickle.dump(self._root, file)
        file.close()
        self._stale = 0
        self._staletime = int(time.time())
        self.unlock()
        
    def loadFromFile(self):
        self.lock()
        try:
            file = open(self.file_name, "r")
        except:
            self.unlock()
            return
        self._root = cPickle.load(file)
        file.close()
        self.unlock()
        
    def _mktreelist(self, path):
        nodes = re.split('/', path)
        tree = []

        for node in nodes:
            tree.append(node)
        print tree
        return tree

    def status(self):
        stalemsg = ""
        if self._stale == 1:
            stalemsg = "STALE"
        else:
            stalemsg = ""
        return "HierDB 0.2: Reads: " + `self._reads` + " Writes: " + `self._writes` + " Last commit: " + `int(time.time()) - self._staletime` + " seconds ago " + stalemsg


    def read(self, path):
        return self.read_t(self._mktreelist(path))

    def write(self, path, data):
        return self.write_t(self._mktreelist(path), data)
    
    def mktree(self, tree):
        cur = self._root
        for item in tree:
            cur[item] = {}
            cur = cur[item]
            
    def exists_t(self, tree):
        try:
            self.read_t(tree)
        except:
            return False
        return True
            
    def read_t(self, tree):
        self._reads = self._reads + 1
        cur = self._root
        for item in tree:
            cur = cur[item]
        return cur
    
    def del_t(self, tree):
        self._writes = self._writes + 1
        self.set_stale()
        delitem = tree.pop()
        cur = self._root
        for item in tree:
            cur = cur[item]
        del cur[delitem]

    def set_stale(self):
        self._stale = 1
        self._staletime = int(time.time())
    
    def write_t(self, tree, data):
        self._writes = self._writes + 1
        self.set_stale()
        
        cur = self._root
        value = tree.pop()
        for item in tree:
            cur = cur[item]
        cur[value] = data
        return data

    def __getitem__(self, path):
        return self.read(path)
        
    def Timer(self, options=''):
        if self._stale:
            self.dumpToFile()



class AttributeDB(Provider):
    """ Depreceated - Use Hier """
    def __init__(self, gc, name):
        
        Provider.__init__(self, gc, name)
        self._name = name
        r = re.compile('/')
        fname = r.sub('_', name) # replace / with _ for file names of database
        self._dbroot = CymMemoryDB(gc, name + '/root', fname + '_root')
        self._dbattr = CymMemoryDB(gc, name + '/attr', fname + '_attr')
    def loadFromFile(self):
        self._dbroot.loadFromFile()
        self._dbattr.loadFromFile()
    def dumpToFile(self):
        self._dbroot.dumpToFile()
        self._dbattr.dumpToFile()
    def status(self):
        return "Attribute database "+self._name
    def items(self):
        return self._dbroot.keys()
    def hasItem(self, item):
        return self._dbroot.has_key(item)
    def newItem(self, item):
        self._dbroot.write(item, `1`)
        return item
    def delItem(self, item):
        self._dbroot.del_key(item)
        # TODO: delete all attributes
    def writeAttr(self, item, attr, value):
        self._dbroot.write(item, `1`)
        return self._dbattr.write(item + '_' + attr, value)
    def readAttr(self, item, attr):
        return self._dbattr.read(item + '_' + attr)




