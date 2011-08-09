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


import sys

from cymbeline.Objects import Object



class Dynmodule(Object):

    __restricted_func__ = ['awake', '__init__', 'serve_from_file']

    def __init__(self,gc):
        Object.__init__(self,gc)

        self.gc = gc

    def _awake(self, http):
        self.http = http
        self.awake()

    def awake(self):
        pass
    
    def _startrequest(self):
        pass

    def serve_from_file(self, file):
        file = open(file, "r")
        line = file.readline()
        out = ""
        while line:
            out = out + "\n" + line
            line = file.readline()
        file.close()
        return out
    
    def serve_header(self, response, response_meaning, mime):
        self.http.send_response(response, response_meaning)
        self.http.send_header("Content-Type", mime)
        self.http.send_queued_headers()

    def serve_html_header(self):
        self.serve_header(200, 'OK', 'text/html')

    def check_required(self, keys = [], internal_message = 1):
        first_error = 0
        error = 0
        i = 0
        _errormsg = "<br><b>The form on the previous page contained errors</b><br>"
        for x in keys:
            try:
                t = self.http.form_arg[x]
            except:
                if internal_message:
                    if first_error == 0:
                        self.p(_errormsg)
                        first_error = 1
                        
                    self.p("Form value missing: " + keys[x] + "<br>")
                    
                error = 1
            if t == '':
                if internal_message:
                    if first_error == 0:
                        self.p(_errormsg)
                        first_error = 1
                        self.p("Form value empty: " + keys[x] + "<br>")
                error = 1
            # inc
            i = i + 1
            
        if error:
            self.p("<br>Please press your browser's back button to return to the previous page and correct any errors<br>")

        return error
            
    def p(self, text):
        print >> self.http.wfile,text,
        #self.http.wfile.write(text)
        return text

    def input(self, type, name, value='', other=''):
        self.p('<input type="' + type + '" name="' + name + '" value="' + value + '" ' + other + '>')
