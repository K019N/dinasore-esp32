import sys

def is_micropython():
    try:
        return sys.implementation.name == 'micropython'
    except AttributeError:
        return False