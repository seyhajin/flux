"""logging functions"""

import sys

from mods import util

#------------------------------------------------------------------------------

#from datetime import datetime
#TODO: add datetime - (datetime.now().strftime('%H:%M:%S'))

# log colors
BLACK   = '\033[30m'
RED     = '\033[31m'
GREEN   = '\033[32m'
YELLOW  = '\033[33m'
BLUE    = '\033[34m'
MAGENTA = '\033[35m'
CYAN    = '\033[36m'
WHITE   = '\033[37m'
DEFAULT = '\033[39m'

#------------------------------------------------------------------------------

def fatal(msg, fatal=True):
    """print a fatal error message and exit with error code 10"""
    print('{}fatal:{} {}'.format(MAGENTA, DEFAULT, msg))
    if fatal:
        sys.exit(10)

def error(msg):
    """print a error message"""
    print('{}error:{} {}'.format(RED, DEFAULT, msg))

def warn(msg):
    """print a warning message"""
    print('{}warn:{} {}'.format(YELLOW, DEFAULT, msg))

def info(msg):
    """print a info message"""
    print('{}info:{} {}'.format(GREEN, DEFAULT, msg))

def debug(msg):
    """print a debug message"""
    print('{}debug:{} {}'.format(CYAN, DEFAULT, msg))

def trace(msg):
    """print a trace message"""
    print('{}trace:{} {}'.format(BLUE, DEFAULT, msg))

def text(msg):
    """print a normal message"""
    print(msg)

#------------------------------------------------------------------------------

def success(item, status):
    """print a green 'success' message"""
    print('{}:\t{}{}{}'.format(item, GREEN, status, DEFAULT))

def failed(item, status):
    """print a red 'failed' message"""
    print('{}:\t{}{}{}'.format(item, RED, status, DEFAULT))

def optional(item, status):
    """print a yellow 'optional' message"""
    print('{}:\t{}{}{}'.format(item, YELLOW, status, DEFAULT))

#------------------------------------------------------------------------------

def item(item, text, width=20):
    """print a green 'success' message"""
    print('{}{}{}'.format(CYAN, item.ljust(width if width>len(item) else len(item)+5), DEFAULT)+text)

#------------------------------------------------------------------------------

def colored(color, msg):
    """print a colored message"""
    print(style(color, msg))

def style(color, msg):
    """return a colored message"""
    return '{}{}{}'.format(color, msg, DEFAULT)

#------------------------------------------------------------------------------

def track(msg, file=__file__):
    """print a trace message from file"""
    print('{}track:{} in {}{}{}: {}'.format(CYAN, DEFAULT, YELLOW, util.strip_dir(file), DEFAULT, msg))

def todo(msg, file=__file__):
    """print a todo message from file"""
    print('{}todo:{} in {}{}{}: {}'.format(CYAN, DEFAULT, YELLOW, util.strip_dir(file), DEFAULT, msg)) 