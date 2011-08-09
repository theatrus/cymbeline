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

import __builtin__

from cymbeline.Objects import Object,Provider,Thread,RollbackImporter
from cymbeline.Server.BaseHTTP import *
from cymbeline.DB import HierDB

from cymbeline.GC import GC

from urllib import unquote_plus

try:
    import cymbeline.Server.SSLSocket
except:
    pass

# Don't depend on SSL


import re
import os
import sys
import md5
import time
import traceback
import cgi

class HTTPSession(object):
    """ This class is a session. It is not implemented as a provider since it has very limited scope """
    def __init__(self, handler):
        self.re_cookiefetch = re.compile('CYMCOOKIE=(?P<value>.*)')
        self.re_cookiesplit = re.compile('[;]')
        self._addheaders = {}

        self.handler = handler
        self.db = self.handler.GC['/system/httpsession']
        
        cookie = self.handler.headers['Cookie']
        if cookie == None:
            # create a new header
            self.create_session()
        else:
            cookie_split = self.re_cookiesplit.split(cookie)
            for x in cookie_split:
                value = self.re_cookiefetch.search(x)
                if value:
                    self._session = value.group('value')
        if self.check_session():
            # fail the test
            self.create_session()
            

        
        

    def check_session(self):
        try:
            t = self.db.read_t([self._session])
        except:
            return 1
        return 
        
        
    def create_session(self):
        
        m = md5.new()
        m.update(`time.time() + time.clock() / time.time()`)
        self._session = m.hexdigest()
        self.handler._addheaders["Set-Cookie"] = "CYMCOOKIE=" + self._session + "; path=/"
        self.db.mktree([self._session])
        self.db.write_t([self._session, 'timestart'], `time.time()`)

    def del_session(self):
        self.db.del_t([self._session])

    def del_var(self, var):
        self.db.del_t([self._session,var])
    def set_var(self, var, value):
        self.db.write_t([self._session,var], value)
    def get_var(self, var):
        try:
            return self.db.read_t([self._session,var])
        except:
            return None
    

class HTTPHandler(BaseHTTPRequestHandler):

    def __init__(self, server):

        self.server_name = server.name

        self.form_arg = {}
        self._addheaders = {}

        self.re_get = re.compile('[?](?P<get>.*)')
        
        self.re_getarg = re.compile('[&]')
        self.re_getval = re.compile('(?P<key>.*)=(?P<val>.*)')
        
        self.re_dynsplit = re.compile('/(?P<app>.*)/(?P<module>.*)/(?P<command>.*)')


        # Pass None for both Request and Client_address, since these are now handled by awake
        BaseHTTPRequestHandler.__init__(self, server)        

    def awake(self, request, client_address):

        self.form_arg = {}
        self._addheaders = {}
        self.client_address = client_address
        self.request = request


    def version_string(self):
        return "Cymbeline/1.2 - Python"


    def do_POST(self):


        self.session = HTTPSession(self)
        
        len = self.headers['Content-length']

        data = self.rfile.read(int(len))
        
        self.form_arg = cgi.parse_qs(data)

        self.serve()




    def serve(self):
        dyn = self.GC[self.server.dynapp].apps

        if not dyn:
            self.serve_static()
            return
        for app in dyn:

            dynrequest = self.re_dynsplit.search(self.path)
            try:
                if dynrequest:
                    _app = dynrequest.group('app') # figure out our app
                else:
                    self.serve_static()
                    return # stop
                
                if _app == app[0]:
                

                    application = app[1]
                    module = dynrequest.group('module')
                    command = dynrequest.group('command')
                    self.serve_dynamic(application, module, command)
                    return
            
                self.serve_static()
            except:
                self.send_error(500)
        

    def do_GET(self):
        """ This is the get handler, does the get response """

        
        self.session = HTTPSession(self)

        get_group  = self.re_get.search(self.path)
        #if get_group:
        #    get_request = get_group.group('get')
        #    self.path = self.re_get.sub('', self.path)
        #    get_args = self.re_getarg.split(get_request)
        #    for x in get_args:
        #        get_argval = self.re_getval.search(x)
        #        key = unquote_plus(get_argval.group('key'))
        #        val = unquote_plus(get_argval.group('val'))
        #        self.form_arg[key] = val

        if get_group:
            self.form_arg = cgi.parse_qs(get_group.group('get'))
            self.path = self.re_get.sub('', self.path)

        self.serve()

    def serve_dynamic(self, application, module, command = 'default'):

        rollback = RollbackImporter() # install rollback handler
        

        
        try:

            #__builtin__.__import__("dynwebroot." + module, globals(), None, [])

            exec("import "+application+"."+ module + "")


            exec("mmodule = getattr("+
                 application+
                 ", module)")
            mclass = getattr(mmodule, module)

            mod = mclass()

            try:
                mod._awake(self)
            except:
                return

            if command in mod.__restricted_func__:
                self.send_error(403)
                return
            

            mexec = getattr(mod, command)
            mexec()
            


        except:
            print "Error occured in executing dynamic module " + module + " app " + application
            print '-'*60
            traceback.print_exc()
            print '-'*60
            print "Cleaning up dynamic space."
            self.send_error(500, 'Uncaught exception')
            

            self.wfile.write("<pre>")
            traceback.print_exc(file=self.wfile)
            self.wfile.write("</pre>")

        mod = ''
        del mod
        rollback.uninstall() # uninstall rollback handler, uninstalling modules loaded since it was loaded

    def serve_static(self):

        if self.path == '/':
            self.path = '/index.html'

        if re.search('\.\.', self.path):
            self.send_error(500, "Not Allowed")
            return
        
        read_key = 'http-' + self.server_name
        temp_base = self.GC.getProvider('/system/settings').read(read_key + '-webroot')


        try:
            file = open(temp_base + self.path, "r" )
        except:
            try:
                error_404serve = self.GC.getProvider('/system/settings').read(read_key + '-404serve')
                if (error_404serve):
                    self.path = error_404serve
                    self.serve_static()
                    return

            except:
                self.send_error(500, "File not found while looking for 404")


            self.send_error(404, "File not found" + self.path)
            return
            
        mime = self.determine_mime(self.path)

        try:
            self.send_response(200, 'OK')
            self.send_header("Content-Type", mime)
            self.send_queued_headers()
        except:
            print " - Connection closed prematurely"
            return

        



        # I'm not very happy with this, but whatever
        
        
        contents = file.readline()
        while contents:
            try:
                self.wfile.write(contents)
            except:
                # connection died midstream
                return
            contents = file.readline()


    def send_queued_headers(self):
        for x in self._addheaders:
            self.send_header(x, self._addheaders[x])
        self.end_headers()

    def determine_mime(self, p):
        mime = ""
        
        if re.search('.jpg', p):
            mime = 'image/jpeg'
        elif re.search('.html', p):
            mime = 'text/html'
        elif re.search('.png', p):
            mime = 'image/png'
        elif re.search('.gif', p):
            mime = 'image/gif'
        elif re.search('.css', p):
            mime = 'text/css'
        elif re.search('.xml', p):
            mime = 'text/xml'
        elif re.search('.txt', p):
            mime = 'text/plain'
        else:
            mime = 'application/octet-stream'
        return mime


    def do_HEAD(self):

        return self.do_GET()
#        self.send_response(501, 'Not Implemented')
 #       self.send_header("Content-Type", "text/html")

#        self.wfile.write("I don't like to get HEAD requests...")

    def log_request(self, code='-', size='-'):
        pass


try:
    class SSLHTTPHandler(cymbeline.SSLSocketServer.SSLStreamRequestHandler, HTTPHandler):
        def __init__(self, request, client_address, server):

            self.server_name = server.name
            self.client_address = client_address
            self.form_arg = {}
            self._addheaders = {}
            
            cymbeline.SSLSocketServer.SSLStreamRequestHandler.__init__(self, request, client_address, server)
except:
    pass
            

class HTTPServer(Thread,BaseHTTPServer):
    def __init__(self, name, addr = ('', 8000), dynapp = False):
        Thread.__init__(self, name)
        BaseHTTPServer.__init__(self, name, addr, HTTPHandler)
        self.dynapp = dynapp

        #self._httpd = BaseHTTPServer(gc, name, ('', port), HTTPHandler)
        #self._httpd.dynapp = dynapp #ugly hack


        sys.stdout.write(" '" + name + "' using port " + `addr` + " ")

        
    def run(self):
        #self._httpd.serve_forever()
        self.serve_forever()

try:
    class SSLHTTPServer(Thread):
        def __init__(self,  name, port = 8000):
            Thread.__init__(self,  name)
            
            self._httpd = BaseSSLHTTPServer(('', port), SSLHTTPHandler)

            self._httpd.name = name

            sys.stdout.write(" '" + name + "' using port " + `port` + " ")
            
            
        def run(self):
            self._httpd.serve_forever()


except:
    pass


class HTTPApplication(Provider):
    def __init__(self, name):
        super(HTTPApplication, self).__init__( name)

        self.apps = [['dynamic', 'dynwebroot']]
    def add_app(root, code):
        if [root,code] in self.apps:
            raise "Already registered"
        
        self.apps.append([root, code])
    def status(self):
        return `self.apps`


class HTTP(Provider):
    def __init__(self, name, addr = ('', 8000), dynapp = False): #dynapp by name
        super(HTTP, self).__init__( name)
        self.http = HTTPServer( name, addr, dynapp)

        self.addr =addr


    def start(self):
        self.http.start()

    def status(self):
        return "HTTP Port " + `self.addr`
    
        
