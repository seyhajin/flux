"""lists stuff"""

import os
import glob
from mods import flux, log, util, verb

#------------------------------------------------------------------------------

def run(flux_dir, proj_dir, args):
    if len(args) > 0 and 'all' not in args:
        for name in args:
            if name in ['all', 'verbs']:
                list_verbs(flux_dir)
            if name in ['all', 'targets']:
                list_targets(flux_dir)

            # check errors
            if name not in ['all', 'verbs', 'targets']:
                log.error('unknown list name: `%s` \t- run `help list` for more informations' % name)
    else:
        # list all
        list_verbs(flux_dir)
        list_targets(flux_dir)


def help():
    return 'lists stuff'

def usage():
    log.text('(?) '+help()+'\n')
    log.optional('usage', 'list [names...]')
    log.item('  list all'         , 'list everything')
    log.item('  list targets'     , 'list available targets')
    log.item('  list verbs'       , 'list available verbs')
    log.item('  list'             , 'same as `list all`')

#------------------------------------------------------------------------------

def list_verbs(flux_dir):
    log.colored(log.YELLOW, '===== verbs =====')
    for verb_name in sorted(verb.verbs):
        log.item(verb_name, verb.verbs[verb_name].help())

def list_targets(flux_dir):
    log.colored(log.YELLOW, '===== targets =====')
    # verbs directory
    target_dir = util.get_targets_dir(flux_dir)
    if os.path.isdir(target_dir):
        # get all .py file in verb dir
        target_files = sorted(glob.glob(target_dir + '/*.yml'))
        if target_files:
            width = max(len(util.split_name(x)) for x in target_files)
            for target_file in target_files:
                target_name = util.split_name(target_file)
                if not target_name.startswith('__'):
                    #if target_name in verb.verbs:
                    log.text(log.style(log.CYAN, target_name).ljust(width+15)) # target['about']
        else:
            log.error('no target was found in `targets` dir: `%s`' % target_dir)
    else:
        log.error('`targets` directory not found: `%s`' % target_dir)