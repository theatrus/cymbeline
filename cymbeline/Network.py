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

import os

from cymbeline.Objects import Provider,Object,Thread

class IFConfig(Provider):
    def __init__(self, gc, name):
        Provider.__init__(self, gc, name)
        self.gc = gc
        self.dhclients = {}
        
    def dhclient_kill(self, interface):
        try:
            os.system("kill "+`self.dhclient[interface]`)
            del self.dhclient[interface]
        except:
            return
        
    def dhclient(self, interface):
        if interface in self.dhclients:
            self.dhclients[interface] = os.spawnlp(os.P_NOWAIT, 'dhclient', interface)
                        
    def ifconfig(self, interf, attrib):
        return os.system('ifconfig ' + interf + ' ' + attrib)
    def if_up(self, interf):
        self.ifconfig(interf, 'up')
    def if_down(self, interf):
        self.ifconfig(interf, 'down')
    def if_dhclient(self, interf): # runs dhclient on an interface
        os.system('dhclient ' + interf)
    def if_setip(self, interf, ip, mask = '255.255.255.0'):
        self.ifconfig(interf, ip + ' netmask '+ mask)
        
        
    

class ARP(Provider):
    def __init__(self, gc, name):
        Provider.__init__(self, gc, name)

    def lookup_arp(self, ip):
        # lookup IP address
        self.lock()
        pipe = os.popen('arp '+ip, "r")
        line = pipe.readline()

        index = line.find(' ') + 1
        line = line[index:]
        
        index = line.find(' ') + 1
        line = line[index:]

        index = line.find(' ') + 1
        line = line[index:]

        index = line.find(' ') 
        line = line[:index]



        self.unlock()
        return line
        
    


class PFConfig(Object):
    def __init__(self, gc):
        Object.__init__(self, gc)
        self.file = []
    def write_config(self, file):
        self.rebuild_config()
        for x in self.file:
            file.write(x + "\n")


class PFManager(Provider):
    def __init__(self, gc, name, pf_config):
        Provider.__init__(self, gc, name)
        self.gc = gc
        self.pf_config = pf_config
    def run_pfctl(self, attrib):
        os.system('pfctl ' + attrib)
    def run_pfctl_pipe(self, attrib):
        return os.popen('pfctl '+ attrib, 'w')
    def enable_pf(self):
        self.run_pfctl('-e')
    def disable_pf(self):
        self.run_pfctl('-d')
    def config(self):
        return self.pf_config
    def load_config(self):
        pipe = self.run_pfctl_pipe('-f -')
        self.pf_config.write_config(pipe)
        pipe.close()
