from exceptions import *

# Global Context Error

class GCException(Exception):
    pass




class GCIsRegistered(GCException):
    """An object with this name is already registered"""
