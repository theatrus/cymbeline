
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


__version__ = "0.3"



import sys
import time
import socket # For gethostbyaddr()
import mimetools
import email.Parser
import email.Message
import SocketServer
import md5

from cymbeline.BaseProviders import Pool
from cymbeline.Server import Server
from cymbeline.Objects import Object,Provider,Thread,RollbackImporter
from cymbeline.SMTPMessage import SMTPMessage

class BaseSMTPServer(Server.BaseTCPServer): # uses cymbeline server
    pass


class SMTPRequestHandler(Object):

    rbufsize = -1
    wbufsize = 0

    # The Python system version, truncated to its first component.
    sys_version = "Python/" + sys.version.split()[0]

    # The server software version.  You may want to override this.
    # The format is multiple whitespace-separated strings,
    # where each string is of the form name[/version].
    server_version = "BaseSMTP/" + __version__

    def __init__(self, server):

        Object.__init__(self)

        self.server = server


        sys.exc_traceback = None    # Help garbage collection


    def awake(self, request, client_address):

        self.request = request
        self.client_address = client_address
        

    def setup(self):

        self.connection = self.request
        self.rfile = self.connection.makefile('rb', self.rbufsize)
        self.wfile = self.connection.makefile('wb', self.wbufsize)

    def finish(self):
        self.wfile.flush()
        self.wfile.close()
        self.rfile.close()


    def respond(self, code, message):
        self.wfile.write(`code` + " " + message + "\r\n")
    

    def handle_begin(self):
        
        s = self.raw_requestline.split(' ')
        if s[0] == 'HELO' or s[0] == 'EHLO':
            self.respond(250, "Hello " + s[1])
            self.resp_mode = 'mailfrom'


            
            return True
        
        else:
            self.respond(500, "I didn't see what I was expecting")
            return False

    def handle_mail(self):
        s = self.raw_requestline.split(':')
        if s[0] == 'MAIL FROM':
            self.respond(250, "Ok")
            self.resp_mode = 'rcptto'

            self.message.set_mailfrom(s[1])

            
            return True
        
        else:
            self.respond(500, "Yay, garbage!")
            return False

    def handle_rcpto(self):
        s = self.raw_requestline.split(':')
        if s[0] == 'RCPT TO':
            self.respond(250, "Ok")
            self.resp_mode = 'data'

            self.message.set_rcptto(s[1])
            
            return True

        elif s[0] == 'QUIT':
            self.respond(250, "Ok")
            return False
        
        else:
            self.respond(500, "Yay, garbage!")
            return False


    
    def handle_data(self):

        digest = md5.new()
        
        if self.raw_requestline == 'DATA':

            self.respond(354, "End data with <CR><LF>.<CR><LF>")
            r = self.rfile.readline()
            while r:
                rt = r[0:-2]


                
                if rt == "." or rt == "\x04":
                    self.respond(250, "Ok. Queued as " + digest.hexdigest())
                    self.message.set_id(digest.hexdigest())
                    
                    self.resp_mode = 'rcptto'
                    return True

                digest.update(rt)
                self.message.add_message_line(rt) # store message contents
                
                r = self.rfile.readline()
                
                
        elif self.raw_requestline.split(":")[0] == "RCPT TO":
            return self.handle_rcpto()
        else:
            return False
            

    def handle(self): 
        """ Override this method if you want to do something
        very different with mail handling, but would still like to call
        the parse_mail() method to do the message setup.
        """

        self.parse_mail()

        # Do something with the message here



        return
        

    def parse_mail(self):

        self.resp_mode = 'begin'
        self.wfile.write("220 CymSMTP At your Service!\r\n")
        self.message = SMTPMessage()

        self.message.set_client_address(self.client_address)
        

        try:
            self.raw_requestline = self.rfile.readline()[0:-2] # CRLF


            
            while self.raw_requestline:
                
                #print self.raw_requestline


                if self.raw_requestline == 'QUIT':
                    return
                
                if self.resp_mode == 'begin':
                    if not self.handle_begin():
                        return
                    
                elif self.resp_mode == 'mailfrom':
                    if not self.handle_mail():
                        return
                    
                elif self.resp_mode == 'rcptto':
                    
                    if not self.handle_rcpto():
                        return
                    
                elif self.resp_mode == 'data':
                    if not self.handle_data():
                        return
                    
                else:
                    self.respond(500, 'Error!!!')
                    return 

                self.raw_requestline = self.rfile.readline()[0:-2] #CRLF
        except:
            raise
        
                

    def version_string(self):
        """Return the server software version string."""
        return self.server_version + ' ' + self.sys_version

    def date_time_string(self):
        """Return the current date and time formatted for a message header."""
        now = time.time()
        year, month, day, hh, mm, ss, wd, y, z = time.gmtime(now)
        s = "%s, %02d %3s %4d %02d:%02d:%02d GMT" % (
                self.weekdayname[wd],
                day, self.monthname[month], year,
                hh, mm, ss)
        return s

    def log_date_time_string(self):
        """Return the current time formatted for logging."""
        now = time.time()
        year, month, day, hh, mm, ss, x, y, z = time.localtime(now)
        s = "%02d/%3s/%04d %02d:%02d:%02d" % (
                day, self.monthname[month], year, hh, mm, ss)
        return s

    weekdayname = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

    monthname = [None,
                 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

    def address_string(self):
        """Return the client address formatted for logging.

        This version looks up the full hostname using gethostbyaddr(),
        and tries to find a name that contains at least one dot.

        """

        host, port = self.client_address
        return socket.getfqdn(host)




class SMTPServer(Thread,BaseSMTPServer):
    def __init__(self, name, addr = ('', 25), request = SMTPRequestHandler):
        Thread.__init__(self,  name)
        BaseSMTPServer.__init__(self,  name, addr, request)




        sys.stdout.write(" '" + name + "' using port " + `addr` + " ")

        
    def run(self):
        self.serve_forever()

class SMTP(Provider):
    def __init__(self, name, addr = ('', 25), request = SMTPRequestHandler):
        super(SMTP, self).__init__( name)
        self.http = SMTPServer(name, addr, request)
        self.addr =addr

    def start(self):
        self.http.start()

    def status(self):
        return "SMTP Port " + `self.addr`
    
        
