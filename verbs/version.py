
from mods import flux, log

def run(flux_dir, proj_dir, args):
    log.text('flux '+flux.VERSION)

def help():
    return 'print version'

def usage():
    log.text('(?) '+help())