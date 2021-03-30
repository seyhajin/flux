"""help commands stuff"""

from mods import flux, log, verb

#------------------------------------------------------------------------------

def run(flux_dir, proj_dir, args):
    """show help text"""
    if len(args) > 0:
        # show help for one verb
        verb_name = args[0]
        if verb_name in verb.verbs:
            verb.verbs[verb_name].usage()
        else:
            log.error('unknown verb `%s`' % verb_name)
    else:
        # show generic help
        usage()

def help():
    return 'show help text'

def usage():
    log.text('(?) '+help()+'\n')
    log.optional('usage', 'help [verb]')
    for verb_name in sorted(verb.verbs):
        log.item('  '+verb_name, verb.verbs[verb_name].help())

#------------------------------------------------------------------------------
    
