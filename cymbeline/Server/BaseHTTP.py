
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


__version__ = "0.2"



import sys
import time
import socket # For gethostbyaddr()
import mimetools
import email.Parser
import email.Message
import SocketServer

from cymbeline.Objects import Object
from cymbeline.BaseProviders import Pool
from cymbeline.Server.Server import BaseTCPServer

#try:
    
#    import cymbeline.Server.SSLSocket
#    __all__ = ["BaseHTTPServer", "BaseHTTPRequestHandler", "BaseSSLHTTPServer"]
#except:
__all__ = ["BaseHTTPServer", "BaseHTTPRequestHandler"]



# Default error message
DEFAULT_ERROR_MESSAGE = """\
<head>
<title>Error response</title>
</head>
<body>
<h1>Error response</h1>
<p>Error code %(code)d.
<p>Message: %(message)s.
<p>Error code explanation: %(code)s = %(explain)s.
</body>
"""

class MimeToolsWrapper(object):
    def __init__(self, message):
        self.message = message
    def __getitem__(self, item):
        try:
            return self.message.get(item)
        except:
            return None
        


class BaseHTTPServer(BaseTCPServer):
    pass




class BaseHTTPRequestHandler(Object):

    rbufsize = -1
    wbufsize = 0

    def __init__(self, server):
        Object.__init__(self)
        self.server = server

        sys.exc_traceback = None    # Help garbage collection


    def setup(self):
        self.connection = self.request
        self.rfile = self.connection.makefile('rb', self.rbufsize)
        self.wfile = self.connection.makefile('wb', self.wbufsize)


    def finish(self):
        self.wfile.flush()
        self.wfile.close()
        self.rfile.close()

    

        

    # The Python system version, truncated to its first component.
    sys_version = "Python/" + sys.version.split()[0]

    # The server software version.  You may want to override this.
    # The format is multiple whitespace-separated strings,
    # where each string is of the form name[/version].
    server_version = "BaseHTTP/" + __version__

    def parse_request(self):
        """Parse a request (internal).

        The request should be stored in self.raw_request; the results
        are in self.command, self.path, self.request_version and
        self.headers.

        Return value is 1 for success, 0 for failure; on failure, an
        error is sent back.

        """
        self.request_version = version = "HTTP/0.9" # Default
        requestline = self.raw_requestline
        if requestline[-2:] == '\r\n':
            requestline = requestline[:-2]
        elif requestline[-1:] == '\n':
            requestline = requestline[:-1]
        self.requestline = requestline
        words = requestline.split()
        if len(words) == 3:
            [command, path, version] = words
            if version[:5] != 'HTTP/':
                self.send_error(400, "Bad request version (%s)" % `version`)
                return False
        elif len(words) == 2:
            [command, path] = words
            if command != 'GET':
                self.send_error(400,
                                "Bad HTTP/0.9 request type (%s)" % `command`)
                return False
        else:
            self.send_error(400, "Bad request syntax (%s)" % `requestline`)
            return False
        self.command, self.path, self.request_version = command, path, version
        self.headers = mimetools.Message(self.rfile, 0)
        self.headers = MimeToolsWrapper(self.headers)
        #parser = email.Parser.Parser()

        #self.headers = parser.parse(self.rfile, 1)

        return True

    def handle(self):
        """Handle a single HTTP request.

        You normally don't need to override this method; see the class
        __doc__ string for information on how to handle specific HTTP
        commands such as GET and POST.

        """


        self.raw_requestline = self.rfile.readline()


        
        if not self.parse_request(): # An error code has been sent, just exit
            return
        mname = 'do_' + self.command
        if not hasattr(self, mname):
            self.send_error(501, "Unsupported method (%s)" % `self.command`)
            print "Unsupported action, " + self.command
            return

        method = getattr(self, mname)

        method()

    def send_error(self, code, message=None):
        """Send and log an error reply.

        Arguments are the error code, and a detailed message.
        The detailed message defaults to the short entry matching the
        response code.

        This sends an error response (so it must be called before any
        output has been generated), logs the error, and finally sends
        a piece of HTML explaining the error to the user.

        """

        try:
            short, long = self.responses[code]
        except KeyError:
            short, long = '???', '???'
        if not message:
            message = short
        explain = long
        self.log_error("code %d, message %s", code, message)
        self.send_response(code, message)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(self.error_message_format %
                         {'code': code,
                          'message': message,
                          'explain': explain})

    error_message_format = DEFAULT_ERROR_MESSAGE

    def send_response(self, code, message=None):
        """Send the response header and log the response code.

        Also send two standard headers with the server software
        version and the current date.

        """
        self.log_request(code)
        if message is None:
            if self.responses.has_key(code):
                message = self.responses[code][0]
            else:
                message = ''
        if self.request_version != 'HTTP/0.9':
            self.wfile.write("%s %s %s\r\n" %
                             (self.protocol_version, str(code), message))
        self.send_header('Server', self.version_string())
        self.send_header('Date', self.date_time_string())

    def send_header(self, keyword, value):
        """Send a MIME header."""
        if self.request_version != 'HTTP/0.9':
            self.wfile.write("%s: %s\r\n" % (keyword, value))

    def end_headers(self):
        """Send the blank line ending the MIME headers."""
        if self.request_version != 'HTTP/0.9':
            self.wfile.write("\r\n")

    def log_request(self, code='-', size='-'):
        """Log an accepted request.

        This is called by send_reponse().

        """

        self.log_message('"%s" %s %s',
                         self.requestline, str(code), str(size))

    def log_error(self, *args):
        """Log an error.

        This is called when a request cannot be fulfilled.  By
        default it passes the message on to log_message().

        Arguments are the same as for log_message().

        XXX This should go to the separate error log.

        """

        apply(self.log_message, args)

    def log_message(self, format, *args):
        """Log an arbitrary message.

        This is used by all other logging functions.  Override
        it if you have specific logging wishes.

        The first argument, FORMAT, is a format string for the
        message to be logged.  If the format string contains
        any % escapes requiring parameters, they should be
        specified as subsequent arguments (it's just like
        printf!).

        The client host and current date/time are prefixed to
        every message.

        """

        sys.stderr.write("%s - - [%s] %s\n" %
                         (self.address_string(),
                          self.log_date_time_string(),
                          format%args))

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

    # Essentially static class variables

    # The version of the HTTP protocol we support.
    # Don't override unless you know what you're doing (hint: incoming
    # requests are required to have exactly this version string).
    protocol_version = "HTTP/1.0"

    # The Message-like class used to parse headers
    #MessageClass = mimetools.Message
    #MessageClass = email.Mess
    # Table mapping response codes to messages; entries have the
    # form {code: (shortmessage, longmessage)}.
    # See http://www.w3.org/hypertext/WWW/Protocols/HTTP/HTRESP.html
    responses = {
        200: ('OK', 'Request fulfilled, document follows'),
        201: ('Created', 'Document created, URL follows'),
        202: ('Accepted',
              'Request accepted, processing continues off-line'),
        203: ('Partial information', 'Request fulfilled from cache'),
        204: ('No response', 'Request fulfilled, nothing follows'),

        301: ('Moved', 'Object moved permanently -- see URI list'),
        302: ('Found', 'Object moved temporarily -- see URI list'),
        303: ('Method', 'Object moved -- see Method and URL list'),
        304: ('Not modified',
              'Document has not changed singe given time'),

        400: ('Bad request',
              'Bad request syntax or unsupported method'),
        401: ('Unauthorized',
              'No permission -- see authorization schemes'),
        402: ('Payment required',
              'No payment -- see charging schemes'),
        403: ('Forbidden',
              'Request forbidden -- authorization will not help'),
        404: ('Not found', 'Nothing matches the given URI'),

        500: ('Internal error', 'Server got itself in trouble'),
        501: ('Not implemented',
              'Server does not support this operation'),
        502: ('Service temporarily overloaded',
              'The server cannot process the request due to a high load'),
        503: ('Gateway timeout',
              'The gateway server did not receive a timely response'),

        }


try:
    class BaseSSLHTTPServer(cymbeline.SSLSocketServer.SSLTCPServer, SocketServer.ThreadingMixIn):

        allow_reuse_address = 1    # Seems to make sense in testing environment

        def finish_request(self, request, client_address):
            """Finish one request by instantiating RequestHandlerClass."""
            self.RequestHandlerClass(request, client_address, self)

except:
    pass

