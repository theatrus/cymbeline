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

from cymbeline.Objects import *
from cymbeline.Auth import *

__doc__ = """ Internal Cymbeline user database lookup module. """

__flags_descr__ = [ 'Cymbeline CymMemoryDB to use' ]

class db(CymObject):
    def __init__(self, name, config = []):
        CymObject.__init__(self)
        self.config = config
        self.name = name
        self.db = self.GC[config[0]]


    def authenticate(self, fields):

        status = AuthStatus()
        
        user = fields[0]
        password = fields[1]
        try:
            if self.db.read(user) == password:
                status.authed = 1
                status.duration = 24
                status.source = self.name
                status.user = user
                return status
            else:
                return status
        except:
            return status

