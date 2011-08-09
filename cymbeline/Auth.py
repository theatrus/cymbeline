
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


from cymbeline.Objects import Provider

from cymbeline import auth


class AuthStatus(object):
    duration = 1
    source = ""
    authed = 0
    user = ""

class Auth(Provider):
    def __init__(self, name, modules = None, module_root = 'cymbeline.auth'):
        Provider.__init__(self, name)
        self.modules = {}
        self.active_modules = []
        self._module_root = module_root


        # name, class, extra config
        if modules:
            _modules = modules
            self.load_modules(_modules)



    def get_authents(self):
        return auth.__available_authents__

    def get_modules(self):
        return self.modules.keys()

    def authent_flags(self, authent):
        exec("import "+self._module_root+"."+authent+"")
        exec("flags = "+self._module_root+"."+authent+".__flags_descr__")
        return flags

    
    def load_modules(self, _modules):
        self.lock()
        del self.modules
        self.modules = {}
        
        
        for ml in _modules:
            m = ml[1] # 2nd value for class
            exec("import " + self._module_root + "." + m + "")
            exec("mod = " + self._module_root + "." + m + "." + m + "( ml[0] ,ml[2])")

            #mod = m(self.GC, ml[0], ml[2]) # Expierimental
            self.modules[ml[0]] = mod # first value for name

        self.unlock()


    def status(self):
        return `self.modules`

    def chain(self, mod = []):
        self.lock()
        del self.active_modules
        self.active_modules = []
        for m in mod:
            self.active_modules.append(self.modules[m])
        self.unlock()

    def authenticate(self, fields = []):
        self.lock()
        for m in self.active_modules:

            stat = m.authenticate(fields)

            if stat.authed:
                self.unlock()
                return stat
        self.unlock()
        return None
