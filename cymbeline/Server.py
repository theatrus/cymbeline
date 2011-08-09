
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

import SocketServer
import socket

from cymbeline.BaseProviders import Pool

class BaseTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):

    allow_reuse_address = 1    # Seems to make sense in testing environment

    def __init__(self, gc, name, server_address, RequestHandlerClass):
        self.gc = gc
        self.name = name
        SocketServer.TCPServer.__init__(self, server_address, RequestHandlerClass)
        
    

    def server_activate(self):
        SocketServer.TCPServer.server_activate(self)
        self._pool = Pool(self.gc, self.name+'_pool', factory = self.RequestHandlerClass, factory_param = [self, self.gc])
        self.gc.registerProvider(self._pool)

    def finish_request(self, request, client_address):
        """Finish one request by instantiating RequestHandlerClass."""
#        self.RequestHandlerClass(request, client_address, self, self.gc)
        handler = self._pool.get()
        
        handler.awake(request, client_address)

        handler.setup()
        handler.handle()
        handler.finish()

        self._pool.finish(handler)
