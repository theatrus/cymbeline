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

__version__ = "0.4"


import socket
import sys
import os
import SocketServer

from OpenSSL import SSL

class SSLTCPServer(SocketServer.BaseServer):

    address_family = socket.AF_INET

    socket_type = socket.SOCK_STREAM

    request_queue_size = 5

    allow_reuse_address = 1

    def __init__(self, server_address, RequestHandlerClass):
        """Constructor.  May be extended, do not override."""
        SocketServer.BaseServer.__init__(self, server_address, RequestHandlerClass)

        self.ctx = SSL.Context(SSL.SSLv23_METHOD)
        print "Initing SSL server"
        self.ctx.set_options(SSL.OP_NO_SSLv2)
        dir = os.curdir
        self.ctx.use_privatekey_file(os.path.join(dir, 'server.key'))
        self.ctx.use_certificate_file(os.path.join(dir, 'server.crt'))

        self.socket = SSL.Connection(self.ctx, socket.socket(self.address_family, self.socket_type))
        #self.socket = socket.socket(self.address_family,
        #self.socket_type)
        
        self.server_bind()
        self.server_activate()

    def server_bind(self):

        if self.allow_reuse_address:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)
        self.socket.set_accept_state()

    def server_activate(self):

        self.socket.listen(self.request_queue_size)

    def server_close(self):

        self.socket.close()

    def fileno(self):

        return self.socket.fileno()

    def get_request(self):
        
        (conn, addr) = self.socket.accept()
        #conn.renegoiate()
        #conn.do_handshake()
        #print conn.state_string()
        return (conn, addr)

    def close_request(self, request):

        request.close()

class SSLStreamRequestHandler:

    """Define self.rfile and self.wfile for SSL sockets."""
    def __init__(self, request, client_address, server):
        self.request = request
        self.client_address = client_address
        self.server = server
        try:
            self.rfile = socket._fileobject(self.request, "rb", self.rbufsize)
            self.wfile = socket._fileobject(self.request, "wb", self.wbufsize)
            self.handle()
            self.finish()
        finally:
            sys.exc_traceback = None    # Help garbage collection


