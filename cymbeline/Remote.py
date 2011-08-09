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
import time

import Pyro.core
import Pyro.naming

from cymbeline.Objects import Provider,Object,Thread


class RemoteNameServer(Thread):
    def run(self):
        Pyro.naming.NameServerStarter()

class RemoteServer(Thread):
    def __init__(self,  name):
        Thread.__init__(self, name)
        Pyro.core.initServer(banner=0)
        self.daemon = Pyro.core.Daemon()
        
        locator = Pyro.naming.NameServerLocator()
        ns = locator.getNS()
        
        self.daemon.useNameServer(ns)
        
    def run(self):
        self.daemon.requestLoop()
        


class Remote(Provider):
    def __init__(self,  name, instance = 'cymbeline'):
        Provider.__init__(self,name)

        self.remotes = {}
        self.published = {}
        self.instance = instance
        
        
        self.nameserver = RemoteServer( name+"_ns_thread")
        self.nameserver.start()

        time.sleep(0.5)

        
        locator = Pyro.naming.NameServerLocator()
        self.ns = locator.getNS()
        
        self.server = RemoteServer( name + "_srv_thread")

        self.server.start()
        Pyro.core.initClient()
    def publish(self, object, name):

        obj = Pyro.core.ObjBase()
        obj.delegateTo(self.GC[object])
        self.published[object] = obj
        self.server.daemon.connect(obj, name)
        return True
        
          
