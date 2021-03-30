"""access to verb modules"""

import sys
import os
import glob

#FIXME: Python2
is_python3 = sys.version_info > (3,5)
if is_python3:
    import importlib.util
else:
    import imp

from collections import OrderedDict
from mods import log, util

# dictionary of 'name: module'
verbs = {}

#------------------------------------------------------------------------------

def import_verbs(flux_dir):
    global verbs

    # make sure flux-verbs find their modules
    #sys.path.insert(0, flux_dir)

    # verbs directory
    verb_dir = util.get_verbs_dir(flux_dir)

    if os.path.isdir(verb_dir):
        # get all .py file in verb dir
        verb_files = glob.glob(verb_dir + '/*.py')
        if verb_files:
            for verb_file in verb_files:
                verb_name = util.split_name(verb_file)
                if not verb_name.startswith('__'):
                    if is_python3:
                        spec = importlib.util.spec_from_file_location(verb_name, verb_file)
                        verb_mod = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(verb_mod)
                    else:
                        #FIXME: Python2
                        fp, pathname, desc = imp.find_module(verb_name, [verb_dir])
                        verb_mod = imp.load_module(verb_name, fp, pathname, desc)
                    verbs[verb_name] = verb_mod
        else:
            log.error('no verb was found in `verbs` dir: `%s`' % verb_dir)
    else:
        log.error('`verbs` directory not found: `%s`' % verb_dir)
