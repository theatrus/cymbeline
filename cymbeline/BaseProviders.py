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
import time
import md5
from cymbeline.Objects import Provider,Object,Thread
from threading import Semaphore
import thread
import string

class Log(Provider):
    def __init__(self, name):
        Provider.__init__(self, name)

        self.logs = {}
        self.logs['system'] = []
        self._length = 100 # max number of entries
        self._console = True
    def log(self, service, message, log = 'system', commit = True):
        self.lock()
        if commit is False:
            pass # do something witty
        if log not in self.logs:
            self.logs[log] = []
        m = {}
        m['service'] = service
        m['message'] = message
        m['time'] = time.time()
        self.logs[log].append(m)
        if len(self.logs[log]) > self._length:
            self.logs[log].pop()
        if self._console: # see if we should print to console
            sys.stdout.write(time.ctime(time.time()) + " "+ log+"-" +service+": "+ message+"\n")
        self.unlock()
        


class FilesysManager(Provider):
    def __init__(self, name):
        Provider.__init__(self, name)

        self.fs = {}
    def add_fs(self, name, device):
        self.fs[name] = device;
    def mount_rw(self, filesys):
        os.system("mount -o noatime -wu " + filesys)
    def mount_ro(self, filesys):
        os.system("mount -o noatime -ru " + filesys)

class TimerThread(Thread):
    def __init__(self, name):
        Thread.__init__(self, name)

        self.classes = {}
        self.count_down = {}
        self.options = {}
    def run(self):
        while 1:
            time.sleep(1)
            for x in self.classes:
                self.count_down[x] = self.count_down[x] - 1 
                if self.count_down[x] <= 0:
                    #x.Timer(self.options[x]) # execute
                    x(self.options[x])

                    self.count_down[x] = self.classes[x] # reset timer

                    
    def addFunction(self, c, interval, options=''):
        self.classes[c] = interval
        self.count_down[c] = interval
        self.options[c] = options

class Timer(Provider):
    def __init__(self,  name):
        Provider.__init__(self,  name)

        self.thread = TimerThread(name + "_thread")
        self.thread.start()
    def addFunction(self, c, interval, options=''):
        self.thread.addFunction(c, interval, options)


class License(Provider):
    def __init__(self, name):
        Provider.__init__(self, name)

        
        license = ""

        m = md5.new()   # make environment digest

        file = open('Boostrap.pyo')
        contents = file.readline()
        while contents:
            m.update(contents)
            contents = file.readline()

        # throw in platform + python ver
        m.update(sys.platform)
        (vmajor, vminor, vmicro, vrl, vserial) = sys.version_info
        m.update(`vmajor`)
        m.update(`vminor`)
            
        print
        print "Environment Digest: ", m.hexdigest()
        
        try:
            license = self.GC.getProvider('db_settings').read('_license')
            confirm = self.GC.getProvider('db_settings').read('_license_confirm')
        except:
            print
            print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
            print "No License Key Found"
            sys.stdout.write("Enter license key: ")
            license = sys.stdin.readline().rstrip()

            sys.stdout.write("Enter confirmation code: ")
            confirm = sys.stdin.readline().rstrip()


            print "Validating..."
            self.GC['db_settings'].write('_license', license) #0BAB-12A-87C-76D
            self.GC['db_settings'].write('_license_confirm', confirm)
            
        print "License key: ",license

class Pool(Provider):
    def __init__(self, name, pool = 10, factory = None, factory_param = [] , factory_param_map = {}, one_per_thread = True, more_stats = False):

        self.name = name
        self._items = []

        self._one_per_thread = one_per_thread
        self._more_stats = more_stats

        # Benchmarking stuff
        self._begin = time.time()
        self._transactions = 0
        self._transit_time = 0


        # So we can issue one per thread automagically
        self._checked_out = {}

        self._sem = Semaphore(0)
        self._pool = pool
        self._factory = factory
        self._factory_param = factory_param
        self._factory_param_map = factory_param_map
        
        Provider.__init__(self, name)

        self.manage_pool()

    def manage_pool(self):
        #self.lock()
        while len(self._items) < self._pool:
            self._items.append(apply(self._factory, self._factory_param, self._factory_param_map))
            self._sem.release()
        #self.unlock()
        
    def get(self):
        #self.lock()

        id = thread.get_ident()

        if id in self._checked_out and self._one_per_thread:
            self._checked_out[id]['counter'] = self._checked_out[id]['counter'] + 1
            if self._more_stats:
                self._checked_out[id]['object'].__cympool_checkout = time.time()
                
            return self._checked_out[id]['object']

        self._sem.acquire()

        r = self._items.pop()


        if self._one_per_thread:
            self._checked_out[id] = {}
            self._checked_out[id]['counter'] = 1
            self._checked_out[id]['object'] = r

        if self._more_stats:
            r.__cympool_checkout = time.time()
        #self.unlock()
        return r

    def finish(self, item):
        #self.lock()


        id = thread.get_ident()

        if self._one_per_thread:
            self._checked_out[id]['counter'] = self._checked_out[id]['counter'] - 1

            if self._checked_out[id]['counter'] <= 0:
                del self._checked_out[id]
                self._sem.release()
                self._items.append(item)
        else:
            self._sem.release()
            self._items.append(item)

        if self._more_stats:
            diff = time.time() - item.__cympool_checkout
            self._transit_time = (self._transit_time + diff) / 2
            self._transactions = self._transactions + 1
        

        #self.unlock()
        
    def status(self):
        transit = "%0.4f" % (self._transit_time)
        if self._more_stats:
            return `len(self._items)` + " of " + `self._pool` + " available. Transit avg: " + transit + "s. Trans/sec: " + "%0.2f" % (self._transactions / (time.time() - self._begin))
        else:
            return `len(self._items)` + " of " + `self._pool` + " available."


class Time(Provider):
    def __init__(self,  name):
        Provider.__init__(self,name)

        self._time = time.time()
    def getUptime(self):
        return time.time() - self._time
    def formatTime(self,tim = -1):
        if (tim < 0):
            tim = self.getTime()
        return time.ctime(tim)
    def getTime(self):
        return time.time()
    def status(self):
        return self.formatTime(self.getTime())
